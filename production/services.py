from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.db.models import Avg, Q, Sum
from .models import Roll, Shift
from quality.models import RollThickness, RollDefect
from catalog.models import ProfileTemplate
from wcm.models import LostTimeEntry


class RollService:
    """Service contenant toute la logique métier pour les rouleaux."""
    
    @staticmethod
    def calculate_net_mass(total_mass, tube_mass):
        """Calcule la masse nette du rouleau."""
        if not total_mass or not tube_mass:
            return None
        
        net = Decimal(str(total_mass)) - Decimal(str(tube_mass))
        return net if net > 0 else None
    
    @staticmethod
    def calculate_grammage(net_mass, length, width=1):
        """Calcule le grammage (g/m²) du rouleau."""
        if not net_mass or not length or not width:
            return None
        
        # Surface en m²
        surface = Decimal(str(length)) * Decimal(str(width))
        if surface <= 0:
            return None
        
        # Grammage = masse nette (g) / surface (m²)
        grammage = Decimal(str(net_mass)) / surface
        return round(grammage, 2)
    
    @staticmethod
    def calculate_avg_thickness(thicknesses, side='left'):
        """
        Calcule la moyenne des épaisseurs pour un côté.
        side: 'left' pour GG, GC, GD ou 'right' pour DG, DC, DD
        """
        if not thicknesses:
            return None
        
        # Déterminer les points selon le côté
        if side == 'left':
            points = ['GG', 'GC', 'GD']
        else:
            points = ['DG', 'DC', 'DD']
        
        # Filtrer les épaisseurs du côté (exclure les rattrapages)
        side_values = [
            t.thickness_value for t in thicknesses 
            if t.measurement_point in points and not t.is_catchup
        ]
        
        if not side_values:
            return None
        
        # Calculer la moyenne
        avg = sum(side_values) / len(side_values)
        return round(avg, 2)
    
    @staticmethod
    def check_thickness_tolerance(thickness_value, profile_spec):
        """
        Vérifie si une épaisseur est dans les tolérances du profil.
        Retourne True si dans les tolérances, False sinon.
        """
        if not profile_spec:
            return True  # Pas de spec, on considère OK
        
        min_val = profile_spec.get('min')
        max_val = profile_spec.get('max')
        
        if min_val is not None and thickness_value < min_val:
            return False
        if max_val is not None and thickness_value > max_val:
            return False
        
        return True
    
    @staticmethod
    def determine_thickness_issues(thicknesses, profile=None):
        """Détermine s'il y a des problèmes d'épaisseur."""
        if not thicknesses:
            return False
        
        # Si on a un profil, vérifier les tolérances
        if profile:
            # TODO: Récupérer les specs d'épaisseur du profil
            # Pour l'instant, on vérifie juste is_within_tolerance
            pass
        
        # Vérifier s'il y a des épaisseurs hors tolérance
        return any(not t.is_within_tolerance for t in thicknesses)
    
    @staticmethod
    def determine_blocking_defects(defects):
        """Détermine s'il y a des défauts bloquants."""
        if not defects:
            return False
        
        # Un défaut est bloquant si son type a severity='blocking'
        for defect in defects:
            if defect.defect_type.severity == 'blocking':
                return True
        
        return False
    
    @staticmethod
    def determine_roll_status(has_thickness_issues, has_blocking_defects, grammage_ok=True):
        """
        Détermine le statut du rouleau selon les critères de conformité.
        Retourne 'CONFORME' ou 'NON_CONFORME'.
        """
        # Non conforme si :
        # - Défauts bloquants
        # - Problèmes d'épaisseur
        # - Grammage hors spec
        if has_blocking_defects or has_thickness_issues or not grammage_ok:
            return 'NON_CONFORME'
        
        return 'CONFORME'
    
    @staticmethod
    def determine_destination(status, force_cutting=False):
        """
        Détermine la destination du rouleau.
        """
        if force_cutting:
            return 'DECOUPE_FORCEE'
        
        if status == 'NON_CONFORME':
            return 'DECOUPE'
        
        return 'PRODUCTION'
    
    @transaction.atomic
    def create_roll_with_measurements(self, validated_data, session_data):
        """
        Crée un rouleau complet avec toutes ses mesures et calculs.
        
        Args:
            validated_data: Données validées du serializer
            session_data: Données de session (shift_id, session_key, etc.)
        
        Returns:
            Roll: Le rouleau créé
        """
        # Extraire les données nested
        thicknesses_data = validated_data.pop('thicknesses', [])
        defects_data = validated_data.pop('defects', [])
        
        # Pour les rouleaux NON_CONFORME, ajouter l'heure pour l'unicité
        if validated_data.get('status') == 'NON_CONFORME':
            from datetime import datetime
            now = datetime.now()
            hhmm = now.strftime('%H%M')
            # Ajouter HHMM au roll_id pour éviter les doublons
            validated_data['roll_id'] = f"{validated_data['roll_id']}_{hhmm}"
        
        # Gérer l'ordre de fabrication si un numéro est fourni
        roll_id = validated_data.get('roll_id', '')
        if roll_id and '_' in roll_id and not validated_data.get('fabrication_order'):
            # Extraire le numéro d'OF du roll_id (format: OF_NUM ou NUM_NUM)
            of_number = roll_id.split('_')[0]
            if of_number:
                # Chercher ou créer l'OF
                from planification.models import FabricationOrder
                try:
                    fabrication_order = FabricationOrder.objects.get(order_number=of_number)
                except FabricationOrder.DoesNotExist:
                    # Créer l'OF s'il n'existe pas
                    fabrication_order = FabricationOrder.objects.create(
                        order_number=of_number,
                        description=f'OF créé automatiquement depuis roll {roll_id}'
                    )
                validated_data['fabrication_order'] = fabrication_order
        
        # Ajouter les données de session
        validated_data['shift_id_str'] = session_data.get('shift_id')
        validated_data['session_key'] = session_data.get('session_key')
        
        # Calculer la masse nette
        net_mass = self.calculate_net_mass(
            validated_data.get('total_mass'),
            validated_data.get('tube_mass')
        )
        validated_data['net_mass'] = net_mass
        
        # Calculer le grammage
        grammage = self.calculate_grammage(
            net_mass,
            validated_data.get('length'),
            width=1  # TODO: Récupérer depuis le profil
        )
        validated_data['grammage_calc'] = grammage
        
        # Créer le rouleau
        roll = Roll.objects.create(**validated_data)
        
        # Créer les épaisseurs
        thickness_objects = []
        for thickness_data in thicknesses_data:
            thickness = RollThickness.objects.create(
                roll=roll,
                **thickness_data
            )
            thickness_objects.append(thickness)
        
        # Créer les défauts (en évitant les doublons dans la liste)
        defect_objects = []
        seen_defects = set()
        for defect_data in defects_data:
            # Créer une clé unique pour détecter les doublons
            defect_key = (
                defect_data.get('defect_type_id') or defect_data.get('defect_type'),
                defect_data.get('meter_position'),
                defect_data.get('side_position')
            )
            
            # Ignorer si on a déjà vu ce défaut
            if defect_key in seen_defects:
                continue
                
            seen_defects.add(defect_key)
            
            defect = RollDefect.objects.create(
                roll=roll,
                **defect_data
            )
            defect_objects.append(defect)
        
        # Calculer les moyennes d'épaisseur
        roll.avg_thickness_left = self.calculate_avg_thickness(
            thickness_objects, side='left'
        )
        roll.avg_thickness_right = self.calculate_avg_thickness(
            thickness_objects, side='right'
        )
        
        # Déterminer les problèmes
        roll.has_thickness_issues = self.determine_thickness_issues(
            thickness_objects
        )
        roll.has_blocking_defects = self.determine_blocking_defects(
            defect_objects
        )
        
        # Déterminer le statut si non fourni
        if not validated_data.get('status'):
            # TODO: Vérifier le grammage par rapport au profil
            grammage_ok = True  # Pour l'instant
            
            roll.status = self.determine_roll_status(
                roll.has_thickness_issues,
                roll.has_blocking_defects,
                grammage_ok
            )
        
        # Déterminer la destination si non fournie
        if not validated_data.get('destination'):
            roll.destination = self.determine_destination(roll.status)
        
        # Sauvegarder les changements
        roll.save()
        
        return roll


# Instance singleton du service
roll_service = RollService()


class ShiftService:
    """Service contenant toute la logique métier pour les postes."""
    
    @staticmethod
    def calculate_lost_time(lost_time_entries):
        """
        Calcule le temps perdu total à partir des entrées.
        Retourne un timedelta.
        """
        if not lost_time_entries:
            return timedelta(0)
        
        total_minutes = sum(entry.duration for entry in lost_time_entries)
        return timedelta(minutes=total_minutes)
    
    @staticmethod
    def calculate_availability_time(start_time, end_time, lost_time, vacation='Journee'):
        """
        Calcule le temps de disponibilité.
        Temps disponible = Temps d'ouverture - Temps perdu
        """
        if not start_time or not end_time:
            return None
        
        # Calculer le temps d'ouverture
        from datetime import datetime, date
        
        # Pour vacation Nuit, l'heure de fin est le jour suivant
        if vacation == 'Nuit':
            # Créer des datetime pour calculer la durée
            start_dt = datetime.combine(date.today(), start_time)
            end_dt = datetime.combine(date.today() + timedelta(days=1), end_time)
        else:
            start_dt = datetime.combine(date.today(), start_time)
            end_dt = datetime.combine(date.today(), end_time)
        
        opening_time = end_dt - start_dt
        
        # Soustraire le temps perdu
        if lost_time:
            availability_time = opening_time - lost_time
        else:
            availability_time = opening_time
        
        return availability_time if availability_time.total_seconds() > 0 else timedelta(0)
    
    @staticmethod
    def calculate_production_totals(rolls, shift=None):
        """
        Calcule les totaux de production à partir des rouleaux et de la production enroulée.
        
        Args:
            rolls: QuerySet des rouleaux du poste
            shift: Instance du Shift pour récupérer les métrages début/fin
            
        Retourne un dict avec: total_length, ok_length, nok_length, raw_waste_length
        """
        totals = {
            'total_length': 0,
            'ok_length': 0,
            'nok_length': 0,
            'raw_waste_length': 0
        }
        
        # Calculer les totaux des rouleaux coupés
        if rolls:
            for roll in rolls:
                if roll.length:
                    totals['total_length'] += roll.length
                    
                    # Répartir selon le statut ET la destination
                    if roll.status == 'CONFORME':
                        totals['ok_length'] += roll.length
                    elif roll.destination == 'DECHETS':
                        totals['raw_waste_length'] += roll.length
                    else:
                        totals['nok_length'] += roll.length
        
        # Gérer la production enroulée début/fin de poste
        if shift:
            # Soustraire la longueur qui était déjà enroulée en début de poste
            if shift.started_at_beginning and shift.meter_reading_start is not None:
                length_start = float(shift.meter_reading_start)
                if length_start > 0:
                    # Cette longueur était déjà comptée dans les rouleaux précédents
                    totals['total_length'] = float(totals['total_length']) - length_start
                    totals['ok_length'] = float(totals['ok_length']) - length_start
            
            # Ajouter la longueur enroulée en fin de poste
            if shift.started_at_end and shift.meter_reading_end is not None:
                length_end = float(shift.meter_reading_end)
                if length_end > 0:
                    # Cette longueur est produite mais pas encore coupée
                    totals['total_length'] = float(totals['total_length']) + length_end
                    totals['ok_length'] = float(totals['ok_length']) + length_end
        
        return totals
    
    @staticmethod
    def calculate_shift_averages(rolls):
        """
        Calcule les moyennes du poste à partir des rouleaux.
        Retourne un dict avec: avg_thickness_left, avg_thickness_right, avg_grammage
        """
        if not rolls:
            return {
                'avg_thickness_left_shift': None,
                'avg_thickness_right_shift': None,
                'avg_grammage_shift': None
            }
        
        # Collecter les valeurs non nulles
        thickness_left_values = []
        thickness_right_values = []
        grammage_values = []
        
        for roll in rolls:
            if roll.avg_thickness_left is not None:
                thickness_left_values.append(roll.avg_thickness_left)
            if roll.avg_thickness_right is not None:
                thickness_right_values.append(roll.avg_thickness_right)
            if roll.grammage_calc is not None:
                grammage_values.append(roll.grammage_calc)
        
        # Calculer les moyennes
        averages = {}
        
        if thickness_left_values:
            averages['avg_thickness_left_shift'] = round(
                sum(thickness_left_values) / len(thickness_left_values), 2
            )
        else:
            averages['avg_thickness_left_shift'] = None
        
        if thickness_right_values:
            averages['avg_thickness_right_shift'] = round(
                sum(thickness_right_values) / len(thickness_right_values), 2
            )
        else:
            averages['avg_thickness_right_shift'] = None
        
        if grammage_values:
            averages['avg_grammage_shift'] = round(
                sum(grammage_values) / len(grammage_values), 1
            )
        else:
            averages['avg_grammage_shift'] = None
        
        return averages
    
    @transaction.atomic
    def create_shift_with_associations(self, validated_data, session_data):
        """
        Crée un poste complet avec toutes ses associations et calculs.
        
        Args:
            validated_data: Données validées du serializer
            session_data: Données de session (session_key, checklist_responses, quality_control, etc.)
        
        Returns:
            Shift: Le poste créé
        """
        # Extraire les données nested du serializer
        checklist_responses_data = validated_data.pop('checklist_responses', [])
        
        # Créer le poste
        shift = Shift.objects.create(**validated_data)
        
        # Créer les réponses de checklist depuis la session
        if session_data.get('checklist_responses'):
            from wcm.models import ChecklistResponse
            
            # Créer un seul objet ChecklistResponse avec toutes les réponses
            checklist_data = {}
            
            # Récupérer les items depuis la session
            checklist_items = session_data.get('checklist_items', {})
            checklist_items_order = session_data.get('checklist_items_order', [])
            
            # Stocker les items utilisés et leur ordre
            if checklist_items:
                checklist_data['_items'] = checklist_items
            if checklist_items_order:
                checklist_data['_items_order'] = checklist_items_order
            
            # Récupérer toutes les réponses valides
            for item_id, response_value in session_data['checklist_responses'].items():
                if response_value:
                    # response_value est toujours une string ('ok', 'nok', 'na')
                    checklist_data[item_id] = response_value.lower()  # Normaliser en minuscules
            
            # Ajouter les commentaires pour les items NOK
            checklist_comments = session_data.get('checklist_comments', {})
            if checklist_comments:
                checklist_data['_comments'] = checklist_comments
            
            if checklist_data:
                # Récupérer les initiales depuis la session
                signature_initials = session_data.get('checklist_signature', '')
                
                # Créer la réponse checklist
                from django.utils import timezone
                
                ChecklistResponse.objects.create(
                    shift=shift,
                    operator=shift.operator,  # L'opérateur vient du shift
                    responses=checklist_data,
                    operator_signature=signature_initials,  # Juste les initiales
                    operator_signature_date=timezone.now()
                )
        
        # Créer les temps perdus depuis la session
        session_key = session_data.get('session_key')
        lost_time_entries_data = session_data.get('lost_time_entries', [])
        
        # Créer les LostTimeEntry depuis les données de session
        created_entries = []
        if lost_time_entries_data:
            from catalog.models import WcmLostTimeReason
            
            for entry_data in lost_time_entries_data:
                try:
                    # Récupérer le motif
                    reason = None
                    if entry_data.get('reason'):
                        reason = WcmLostTimeReason.objects.get(id=entry_data['reason'])
                    
                    # Créer l'entrée
                    entry = LostTimeEntry.objects.create(
                        shift=shift,
                        session_key=session_key,
                        reason=reason,
                        motif=entry_data.get('motif', ''),
                        comment=entry_data.get('comment', ''),
                        duration=entry_data.get('duration', 0),
                        created_by=shift.operator
                    )
                    created_entries.append(entry)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erreur création temps perdu: {str(e)}", exc_info=True)
        
        # Associer aussi les temps perdus existants (créés via API)
        if session_key:
            existing_entries = LostTimeEntry.objects.filter(
                session_key=session_key,
                shift__isnull=True
            )
            existing_entries.update(shift=shift)
            
            # Combiner toutes les entrées pour le calcul
            all_entries = list(created_entries) + list(existing_entries)
        else:
            all_entries = created_entries
        
        # Calculer le temps perdu total
        if all_entries:
            shift.lost_time = self.calculate_lost_time(all_entries)
        else:
            shift.lost_time = timedelta(0)
        
        # Calculer le temps de disponibilité
        shift.availability_time = self.calculate_availability_time(
            shift.start_time,
            shift.end_time,
            shift.lost_time,
            shift.vacation
        )
        
        # Récupérer les rouleaux du poste
        rolls = Roll.objects.filter(shift_id_str=shift.shift_id)
        
        # Lier les rouleaux au poste via la ForeignKey
        rolls.update(shift=shift)
        
        # Calculer les totaux de production (incluant la production enroulée)
        production_totals = self.calculate_production_totals(rolls, shift)
        
        # Calculer les moyennes
        averages = self.calculate_shift_averages(rolls)
        shift.avg_thickness_left_shift = averages['avg_thickness_left_shift']
        shift.avg_thickness_right_shift = averages['avg_thickness_right_shift']
        shift.avg_grammage_shift = averages['avg_grammage_shift']
        
        # Sauvegarder les changements
        shift.save()
        
        # Créer les contrôles qualité si présents dans la session
        if session_data.get('quality_control'):
            from quality.services import quality_control_service
            try:
                quality_control_service.create_controls_from_session(shift, session_data)
            except Exception as e:
                # Logger l'erreur mais ne pas faire échouer la création du poste
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur création contrôles qualité: {str(e)}", exc_info=True)
        
        # Calculer et créer le TRS avec les totaux de production
        from wcm.services import calculate_and_create_trs
        try:
            calculate_and_create_trs(shift, production_totals)
        except Exception as e:
            # Logger l'erreur mais ne pas faire échouer la création du poste
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur création TRS: {str(e)}", exc_info=True)
        
        return shift


# Instance singleton du service
shift_service = ShiftService()