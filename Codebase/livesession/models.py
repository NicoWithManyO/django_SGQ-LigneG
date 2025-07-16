from django.db import models


class CurrentSession(models.Model):
    """Session de production courante - État complet de l'interface"""
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    
    # Toutes les données de la session dans un seul champ JSON
    session_data = models.JSONField(default=dict)
    # Structure du JSON:
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
        
        # TO (Temps d'ouverture)
        start = data.get('start_time')
        end = data.get('end_time')
        
        if not start or not end:
            return {'to': 0, 'tp': 0, 'td': 0, 'ta': 0}
            
        try:
            # Gérer le cas où les heures sont des strings
            if isinstance(start, str):
                start_time = datetime.strptime(start, '%H:%M').time()
            else:
                start_time = start
                
            if isinstance(end, str):
                end_time = datetime.strptime(end, '%H:%M').time()
            else:
                end_time = end
            
            # Calculer TO en minutes
            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = datetime.combine(datetime.today(), end_time)
            
            # Si l'heure de fin est avant l'heure de début, on assume qu'on passe minuit
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
                
            to_minutes = int((end_dt - start_dt).total_seconds() / 60)
            
            # TP (Temps perdu) - depuis les temps perdus
            tp_minutes = sum([lt.get('duration', 0) for lt in data.get('lost_times', [])])
            
            # TD (Temps disponible)
            td_minutes = to_minutes - tp_minutes
            
            # TA (Temps d'arrêt) - pas encore implémenté
            ta_minutes = 0
            
            return {
                'to': to_minutes,
                'tp': tp_minutes,
                'td': td_minutes,
                'ta': ta_minutes
            }
            
        except Exception as e:
            print(f"Erreur calcul métriques: {e}")
            return {'to': 0, 'tp': 0, 'td': 0, 'ta': 0}