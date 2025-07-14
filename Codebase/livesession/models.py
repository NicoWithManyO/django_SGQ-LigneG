from django.db import models
from django.contrib.auth.models import User


# NOTE: Ce modèle est obsolète - tout est maintenant dans CurrentSession.session_data
# À supprimer dans une future migration
class CurrentProductionState(models.Model):
    """Données persistantes entre les postes - préférences utilisateur"""
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    # OF et paramètres qui restent entre les sessions
    current_of = models.ForeignKey('core.FabricationOrder', null=True, blank=True, on_delete=models.SET_NULL)
    cutting_of = models.ForeignKey('core.FabricationOrder', null=True, blank=True, related_name='cutting_sessions', on_delete=models.SET_NULL)
    target_length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Profil et modes actifs
    selected_profile = models.ForeignKey('core.Profile', null=True, blank=True, on_delete=models.SET_NULL)
    active_modes = models.JSONField(default=dict)  # {"maintenance": true, "permissive": false}
    
    # Onglet actif dans le bloc productivité
    active_productivity_tab = models.CharField(
        max_length=20,
        default='temps',
        choices=[('temps', 'TRS'), ('parametres', 'Params & Specs')],
        verbose_name="Onglet actif productivité"
    )
    
    # Numéro de rouleau persistant
    roll_number = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name="Numéro de rouleau actuel"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'livesession_current_state'
        verbose_name = 'État de production persistant'
        verbose_name_plural = 'États de production persistants'
    
    def __str__(self):
        return f"Session {self.session_key[:8]}... - {self.updated_at.strftime('%d/%m %H:%M')}"


class CurrentSession(models.Model):
    """Session de production courante - État complet de l'interface"""
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    
    # Toutes les données de la session en JSON
    session_data = models.JSONField(default=dict)
    # Structure attendue:
    # {
    #     "operator": 1,
    #     "date": "2024-01-15", 
    #     "vacation": "Matin",
    #     "start_time": "06:00",
    #     "end_time": "14:00",
    #     "quality_controls": {...},
    #     "rolls": [...],
    #     "lost_times": [...],
    #     "checklist": {...}
    # }
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'livesession_currentsession'
        verbose_name = 'Session de production'
        verbose_name_plural = 'Sessions de production'
    
    def __str__(self):
        # Le champ est stocké comme 'operator' 
        # Si c'est un ID, essayer de récupérer le nom de l'opérateur
        operator_value = self.session_data.get('operator', 'Sans opérateur')
        
        # Si la valeur ressemble à un ID (nombre), essayer de récupérer le nom
        if operator_value and str(operator_value).isdigit():
            try:
                from core.models import Operator
                operator_obj = Operator.objects.get(pk=int(operator_value))
                operator_name = operator_obj.full_name
            except:
                operator_name = f"Opérateur #{operator_value}"
        else:
            operator_name = operator_value or 'Sans opérateur'
            
        date = self.session_data.get('date', 'Sans date')
        return f"Session: {operator_name} - {date}"
    
    def calculate_metrics(self):
        """Calcule les métriques du poste (TO, TP, TD, TA) depuis le draft.
        Réutilise la logique du modèle Shift pour éviter la duplication."""
        from datetime import datetime, timedelta
        
        data = self.session_data
        metrics = {
            'to': 0,  # Temps d'ouverture
            'tp': 0,  # Temps perdu
            'td': 0,  # Temps disponible
            'ta': 0,  # Temps d'arrêt (pour l'instant = TD)
            'trs': 0  # Taux de rendement synthétique
        }
        
        # Calcul du temps d'ouverture (TO)
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time:
            try:
                # Parser les heures (format HH:MM)
                start = datetime.strptime(start_time, '%H:%M')
                end = datetime.strptime(end_time, '%H:%M')
                
                # Si l'heure de fin est avant l'heure de début, c'est le lendemain
                if end < start:
                    end += timedelta(days=1)
                
                # Calculer la différence en minutes
                opening_time = (end - start).total_seconds() / 60
                metrics['to'] = int(opening_time)
                
                # Calcul du temps perdu (TP) - somme des temps d'arrêt
                lost_times = data.get('lost_times', [])
                total_lost_minutes = sum(entry.get('duration', 0) for entry in lost_times)
                metrics['tp'] = int(total_lost_minutes)
                
                # Temps disponible (TD) = TO - TP
                metrics['td'] = metrics['to'] - metrics['tp']
                
                # Pour l'instant, TA = TD (temps d'arrêt sera géré plus tard)
                metrics['ta'] = metrics['td']
                
            except (ValueError, TypeError):
                pass
        
        # Calcul du TRS (rendement)
        # Utilise la longueur OK depuis les métriques de productivité
        length_ok = float(data.get('meter_reading_end', 0) or 0)
        
        # La longueur cible vient maintenant de session_data
        target_length = float(data.get('target_length', 0) or 0)
        if target_length > 0:
            metrics['trs'] = round((length_ok / target_length) * 100, 1)
        
        return metrics




# NOTE: Ce modèle n'est plus utilisé - tout est maintenant dans CurrentSession.session_data
# À supprimer dans une future migration
class LiveQualityControl(models.Model):
    """Brouillon des contrôles qualité - calculs des moyennes côté serveur"""
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    
    # Données des contrôles qualité en JSON
    quality_data = models.JSONField(default=dict)
    # Structure attendue:
    # {
    #     "micronnaire_left": [valeur1, valeur2, valeur3],
    #     "micronnaire_right": [valeur1, valeur2, valeur3],
    #     "micronnaire_left_avg": moyenne_calculée,
    #     "micronnaire_right_avg": moyenne_calculée,
    #     "extrait_sec": valeur,
    #     "extrait_sec_time": "HH:MM",
    #     "surface_mass_gg": valeur,
    #     "surface_mass_gc": valeur,
    #     "surface_mass_dc": valeur,
    #     "surface_mass_dd": valeur,
    #     "surface_mass_left_avg": moyenne_calculée,
    #     "surface_mass_right_avg": moyenne_calculée,
    #     "loi_given": true/false,
    #     "loi_time": "HH:MM"
    # }
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'livesession_live_quality'
        verbose_name = 'Brouillon contrôles qualité'
        verbose_name_plural = 'Brouillons contrôles qualité'
    
    def __str__(self):
        data = self.quality_data
        micronnaire_count = len([v for v in data.get('micronnaire_left', []) + data.get('micronnaire_right', []) if v])
        surface_mass_count = len([v for k, v in data.items() if k.startswith('surface_mass_') and not k.endswith('_avg') and v])
        return f"Draft qualité: {micronnaire_count} micronnaires, {surface_mass_count} masses surfaciques"