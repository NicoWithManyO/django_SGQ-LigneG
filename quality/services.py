from decimal import Decimal
from django.db import transaction
from .models import Controls


class QualityControlService:
    """Service pour gérer les contrôles qualité."""
    
    def create_controls_from_session(self, shift, session_data):
        """
        Crée un enregistrement de contrôles qualité depuis les données de session.
        
        Args:
            shift: Le poste associé
            session_data: Dictionnaire contenant quality_control depuis la session
            
        Returns:
            Controls: L'instance créée ou None si pas de données
        """
        qc_data = session_data.get('quality_control', {})
        if not qc_data:
            return None
            
        # Préparer les données pour le modèle
        controls_data = {
            'shift': shift,
            'session_key': session_data.get('session_key', ''),
        }
        
        # Ajouter l'opérateur s'il existe sur le shift
        if shift.operator:
            controls_data['created_by'] = shift.operator
        
        # Mapper les données depuis la structure frontend
        if 'micrometry' in qc_data:
            micro = qc_data['micrometry']
            # Micronnaire gauche
            if 'left' in micro:
                for i, val in enumerate(micro['left'][:3]):
                    if val is not None:
                        controls_data[f'micrometer_left_{i+1}'] = Decimal(str(val))
            if 'averageLeft' in micro and micro['averageLeft'] is not None:
                controls_data['micrometer_left_avg'] = Decimal(str(micro['averageLeft']))
                
            # Micronnaire droite  
            if 'right' in micro:
                for i, val in enumerate(micro['right'][:3]):
                    if val is not None:
                        controls_data[f'micrometer_right_{i+1}'] = Decimal(str(val))
            if 'averageRight' in micro and micro['averageRight'] is not None:
                controls_data['micrometer_right_avg'] = Decimal(str(micro['averageRight']))
        
        # Mapper les masses surfaciques
        if 'surfaceMass' in qc_data:
            mass = qc_data['surfaceMass']
            if 'leftLeft' in mass and mass['leftLeft'] is not None:
                controls_data['surface_mass_gg'] = Decimal(str(mass['leftLeft']))
            if 'leftCenter' in mass and mass['leftCenter'] is not None:
                controls_data['surface_mass_gc'] = Decimal(str(mass['leftCenter']))
            if 'rightCenter' in mass and mass['rightCenter'] is not None:
                controls_data['surface_mass_dc'] = Decimal(str(mass['rightCenter']))
            if 'rightRight' in mass and mass['rightRight'] is not None:
                controls_data['surface_mass_dd'] = Decimal(str(mass['rightRight']))
            if 'averageLeft' in mass and mass['averageLeft'] is not None:
                controls_data['surface_mass_left_avg'] = Decimal(str(mass['averageLeft']))
            if 'averageRight' in mass and mass['averageRight'] is not None:
                controls_data['surface_mass_right_avg'] = Decimal(str(mass['averageRight']))
        
        # Mapper l'extrait sec
        if 'dryExtract' in qc_data:
            extract = qc_data['dryExtract']
            if 'value' in extract and extract['value'] is not None:
                controls_data['dry_extract'] = Decimal(str(extract['value']))
            if 'timestamp' in extract and extract['timestamp'] is not None:
                controls_data['dry_extract_time'] = extract['timestamp']
            if 'sample' in extract and extract['sample'] is not None:
                controls_data['loi_given'] = bool(extract['sample'])
            if 'loiTimestamp' in extract and extract['loiTimestamp'] is not None:
                controls_data['loi_time'] = extract['loiTimestamp']
        
        # Déterminer la validité globale
        controls_data['is_valid'] = qc_data.get('status', 'pending') != 'failed'
        
        # Créer l'enregistrement
        return Controls.objects.create(**controls_data)
    
    def calculate_average(self, values):
        """Calcule la moyenne de valeurs non nulles."""
        valid_values = [v for v in values if v is not None]
        if not valid_values:
            return None
        return sum(valid_values) / len(valid_values)


# Instance singleton
quality_control_service = QualityControlService()