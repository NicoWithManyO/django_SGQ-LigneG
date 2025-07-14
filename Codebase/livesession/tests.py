from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, time
from decimal import Decimal
from .models import CurrentSession
from core.models import Operator, FabricationOrder, Profile, MoodCounter
from production.models import MachineParameters, Shift, Roll
from wcm.models import LostTimeReason, ChecklistItem
from quality.models import DefectType, Specification


class CurrentSessionAPITest(APITestCase):
    """Tests pour l'API CurrentSession"""
    
    def setUp(self):
        """Configuration initiale des tests"""
        # Créer les données de base
        self.operator = Operator.objects.create(
            first_name="Jean",
            last_name="Dupont"
        )
        
        # Créer des paramètres machine et profil
        self.machine_params = MachineParameters.objects.create(
            name="Params Test",
            oxygen_primary=100,
            oxygen_secondary=150,
            propane_primary=50,
            propane_secondary=75,
            speed_primary=10,
            speed_secondary=15,
            belt_speed=120
        )
        
        self.profile = Profile.objects.create(
            name="80g/m²",
            machine_parameters=self.machine_params
        )
        
        self.of = FabricationOrder.objects.create(
            order_number="OF12345",
            profile=self.profile
        )
        
        # Créer un mode
        from core.models import Mode
        self.mode = Mode.objects.create(
            name="Maintenance",
            code="maintenance"
        )
        
        # URL de l'API
        self.url = reverse('current-session')
        
        # Forcer la création d'une session
        self.client.get(self.url)
    
    def test_get_current_session(self):
        """Test de récupération de la session courante"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_data', response.data)
        self.assertIn('metrics', response.data)
    
    def test_patch_operator_field(self):
        """Test de mise à jour du champ opérateur"""
        data = {'operator': self.operator.id}
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_data']['operator'], self.operator.id)
    
    def test_patch_shift_data(self):
        """Test de mise à jour des données du shift"""
        data = {
            'operator': self.operator.id,
            'date': '2025-01-14',
            'vacation': 'Matin',
            'start_time': '04:00',
            'end_time': '12:00'
        }
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session_data = response.data['session_data']
        self.assertEqual(session_data['operator'], self.operator.id)
        self.assertEqual(session_data['date'], '2025-01-14')
        self.assertEqual(session_data['vacation'], 'Matin')
        self.assertEqual(session_data['start_time'], '04:00:00')
        self.assertEqual(session_data['end_time'], '12:00:00')
    
    def test_patch_current_roll(self):
        """Test de mise à jour des données du rouleau en cours"""
        data = {
            'current_roll': {
                'info': {
                    'roll_number': 42,
                    'length': 250.5,
                    'tube_mass': 15.2,
                    'total_mass': 245.7
                }
            }
        }
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        roll_info = response.data['session_data']['current_roll']['info']
        self.assertEqual(roll_info['roll_number'], 42)
        self.assertEqual(float(roll_info['length']), 250.5)
    
    def test_metrics_calculation(self):
        """Test du calcul des métriques"""
        # Configurer les données pour avoir des métriques
        data = {
            'operator': self.operator.id,
            'date': '2025-01-14',
            'vacation': 'Matin',
            'start_time': '04:00',
            'end_time': '12:00',
            'lost_times': []
        }
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        metrics = response.data['metrics']
        
        # Vérifier TO (Temps d'Ouverture)
        self.assertEqual(metrics['to_minutes'], 480)  # 8 heures
        self.assertEqual(metrics['to_formatted'], '8h00')
        
        # Vérifier TD (Temps Disponible)
        self.assertEqual(metrics['td_minutes'], 480)  # Pas de temps perdu
        self.assertEqual(metrics['td_formatted'], '8h00')
    
    def test_lost_time_calculation(self):
        """Test du calcul avec temps perdu"""
        # Créer un motif de temps perdu
        reason = LostTimeReason.objects.create(
            reason="Panne",
            category="TECHNIQUE"
        )
        
        data = {
            'operator': self.operator.id,
            'date': '2025-01-14',
            'vacation': 'Matin',
            'start_time': '04:00',
            'end_time': '12:00',
            'lost_times': [
                {
                    'reason': reason.id,
                    'duration': 30,
                    'comment': 'Test'
                }
            ]
        }
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        metrics = response.data['metrics']
        
        # Vérifier TP et TD
        self.assertEqual(metrics['tp_minutes'], 30)
        self.assertEqual(metrics['td_minutes'], 450)  # 480 - 30
    
    def test_delete_session(self):
        """Test de réinitialisation de la session"""
        # D'abord ajouter des données
        self.client.patch(self.url, {'operator': self.operator.id})
        
        # Puis supprimer
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Session réinitialisée')
        
        # Vérifier que la session est vide
        response = self.client.get(self.url)
        self.assertIsNone(response.data['session_data'].get('operator'))


class SaveShiftAPITest(APITestCase):
    """Tests pour l'endpoint de sauvegarde de shift"""
    
    def setUp(self):
        """Configuration initiale"""
        self.operator = Operator.objects.create(
            first_name="Marie",
            last_name="Martin"
        )
        
        # Créer un profil et OF
        self.machine_params = MachineParameters.objects.create(
            name="Params Test",
            oxygen_primary=100,
            oxygen_secondary=150,
            propane_primary=50,
            propane_secondary=75,
            speed_primary=10,
            speed_secondary=15,
            belt_speed=120
        )
        
        self.profile = Profile.objects.create(
            name="80g/m²",
            machine_parameters=self.machine_params
        )
        
        self.of = FabricationOrder.objects.create(
            order_number="OF12345",
            profile=self.profile
        )
        
        # Créer des items de checklist
        self.checklist_item = ChecklistItem.objects.create(
            item_text="Vérifier température",
            order=1
        )
        
        # URLs
        self.session_url = reverse('current-session')
        self.save_shift_url = reverse('save-shift')
        
        # Créer une session avec des données
        self.client.get(self.session_url)
    
    def test_save_shift_success(self):
        """Test de sauvegarde réussie d'un shift"""
        # Préparer les données du shift
        session_data = {
            'operator': self.operator.id,
            'date': '2025-01-14',
            'vacation': 'Matin',
            'start_time': '04:00',
            'end_time': '12:00',
            'current_of': self.of.id,
            'checklist_responses': {
                f'item_{self.checklist_item.id}': 'ok'
            }
        }
        
        # Mettre à jour la session
        self.client.patch(self.session_url, session_data, format='json')
        
        # Sauvegarder le shift
        response = self.client.post(self.save_shift_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('shift_id', response.data)
        self.assertEqual(response.data['message'], 'Poste enregistré avec succès')
        
        # Vérifier que le shift existe en DB
        shift = Shift.objects.get(shift_id=response.data['shift_id'])
        self.assertEqual(shift.operator, self.operator)
        self.assertEqual(shift.vacation, 'Matin')
    
    def test_save_shift_missing_fields(self):
        """Test de sauvegarde avec champs manquants"""
        # Session incomplète
        session_data = {
            'operator': self.operator.id,
            # Manque date, vacation, heures
        }
        
        self.client.patch(self.session_url, session_data, format='json')
        response = self.client.post(self.save_shift_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Champs requis manquants', response.data['error'])
    
    def test_save_shift_with_quality_controls(self):
        """Test de sauvegarde avec contrôles qualité"""
        session_data = {
            'operator': self.operator.id,
            'date': '2025-01-14',
            'vacation': 'Matin',
            'start_time': '04:00',
            'end_time': '12:00',
            'quality_controls': {
                'micronnaire_left_1': 4.5,
                'micronnaire_left_2': 4.6,
                'micronnaire_right_1': 4.7,
                'micronnaire_right_2': 4.8,
                'extrait_sec': 10.5,
                'surface_mass_gg': 78.5,
                'surface_mass_gc': 79.0,
                'surface_mass_dc': 78.8,
                'surface_mass_dd': 79.2,
                'loi_given': True
            }
        }
        
        self.client.patch(self.session_url, session_data, format='json')
        response = self.client.post(self.save_shift_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier les contrôles qualité
        from production.models import QualityControl
        qc = QualityControl.objects.get(shift__shift_id=response.data['shift_id'])
        self.assertEqual(qc.dry_extract, Decimal('10.5'))
        self.assertEqual(qc.created_by, self.operator)  # Auto-rempli
    
    def test_session_reset_after_save(self):
        """Test de réinitialisation intelligente après sauvegarde"""
        # Préparer une session complète
        session_data = {
            'operator': self.operator.id,
            'date': '2025-01-14',
            'vacation': 'Matin',
            'start_time': '04:00',
            'end_time': '12:00',
            'current_of': self.of.id,
            'roll_number': 42,
            'belt_speed': 120.5,
            'started_at_end': True,
            'meter_reading_end': 1000
        }
        
        self.client.patch(self.session_url, session_data, format='json')
        response = self.client.post(self.save_shift_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier la session réinitialisée
        new_session = response.data['session']
        session_data = new_session['session_data']
        
        # Champs qui doivent persister
        self.assertEqual(session_data['current_of'], self.of.id)
        self.assertEqual(session_data['roll_number'], 42)
        self.assertEqual(float(session_data['belt_speed']), 120.5)
        
        # Champs qui doivent être réinitialisés
        self.assertIsNone(session_data['operator'])
        self.assertEqual(session_data['vacation'], 'ApresMidi')  # Vacation suivante
        self.assertEqual(session_data['start_time'], '12:00')  # Heures par défaut
        
        # Report de l'état machine
        self.assertTrue(session_data['started_at_beginning'])
        self.assertEqual(session_data['meter_reading_start'], 1000)


class SaveRollAPITest(APITestCase):
    """Tests pour l'endpoint de sauvegarde de rouleau"""
    
    def setUp(self):
        """Configuration initiale"""
        # Créer les données nécessaires
        self.machine_params = MachineParameters.objects.create(
            name="Params Test",
            oxygen_primary=100,
            oxygen_secondary=150,
            propane_primary=50,
            propane_secondary=75,
            speed_primary=10,
            speed_secondary=15,
            belt_speed=120
        )
        
        self.profile = Profile.objects.create(
            name="80g/m²",
            machine_parameters=self.machine_params
        )
        
        self.of = FabricationOrder.objects.create(
            order_number="OF12345",
            profile=self.profile
        )
        
        self.of_cutting = FabricationOrder.objects.create(
            order_number="OF67890",
            profile=self.profile,
            for_cutting=True
        )
        
        # URLs
        self.session_url = reverse('current-session')
        self.save_roll_url = reverse('save-roll')
        
        # Créer une session
        self.client.get(self.session_url)
    
    def test_save_roll_conforme(self):
        """Test de sauvegarde d'un rouleau conforme"""
        # Préparer les données
        session_data = {
            'current_of': self.of.id,
            'cutting_of': self.of_cutting.id,
            'current_roll': {
                'info': {
                    'roll_number': 1,
                    'length': 250.5,
                    'tube_mass': 15.2,
                    'total_mass': 245.7,
                    'comment': 'Test rouleau'
                }
            }
        }
        
        self.client.patch(self.session_url, session_data, format='json')
        
        # Sauvegarder le rouleau
        roll_data = {
            'status': 'CONFORME',
            'destination': 'PRODUCTION'
        }
        response = self.client.post(self.save_roll_url, roll_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['roll_id'], 'OF12345_001')
        
        # Vérifier en DB
        roll = Roll.objects.get(roll_id='OF12345_001')
        self.assertEqual(roll.fabrication_order, self.of)
        self.assertEqual(roll.status, 'CONFORME')
        self.assertEqual(roll.destination, 'PRODUCTION')
        self.assertEqual(float(roll.length), 250.5)
    
    def test_save_roll_non_conforme(self):
        """Test de sauvegarde d'un rouleau non conforme"""
        session_data = {
            'current_of': self.of.id,
            'cutting_of': self.of_cutting.id,
            'current_roll': {
                'info': {
                    'roll_number': 2,
                    'length': 100,
                    'tube_mass': 10,
                    'total_mass': 80
                }
            }
        }
        
        self.client.patch(self.session_url, session_data, format='json')
        
        roll_data = {
            'status': 'NON_CONFORME',
            'destination': 'DECOUPE'
        }
        response = self.client.post(self.save_roll_url, roll_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('OFDecoupe_', response.data['roll_id'])
        
        # Vérifier que c'est lié à l'OF de découpe
        roll = Roll.objects.get(roll_id=response.data['roll_id'])
        self.assertEqual(roll.fabrication_order, self.of_cutting)
        self.assertEqual(roll.status, 'NON_CONFORME')
    
    def test_save_roll_with_defects(self):
        """Test de sauvegarde avec défauts"""
        # Créer un type de défaut
        defect_type = DefectType.objects.create(
            name="Trou",
            criticality="blocking"
        )
        
        session_data = {
            'current_of': self.of.id,
            'current_roll': {
                'info': {
                    'roll_number': 3,
                    'length': 150,
                    'tube_mass': 12,
                    'total_mass': 120
                },
                'defects': [
                    {
                        'type_id': defect_type.id,
                        'position_m': 50,
                        'position_side': 'G'
                    }
                ]
            }
        }
        
        self.client.patch(self.session_url, session_data, format='json')
        
        roll_data = {
            'status': 'NON_CONFORME',
            'destination': 'DECOUPE'
        }
        response = self.client.post(self.save_roll_url, roll_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier les défauts
        from quality.models import RollDefect
        defects = RollDefect.objects.filter(roll__roll_id=response.data['roll_id'])
        self.assertEqual(defects.count(), 1)
        self.assertEqual(defects.first().defect_name, "Trou")
        self.assertEqual(defects.first().side_position, "left")


class MoodCounterAPITest(APITestCase):
    """Tests pour l'API de compteur d'humeur"""
    
    def setUp(self):
        """Configuration initiale"""
        # Créer les 4 compteurs
        MoodCounter.ensure_all_moods_exist()
        
        self.url = reverse('increment-mood')
    
    def test_increment_happy_mood(self):
        """Test d'incrémentation de l'humeur 'happy'"""
        data = {'mood': 'happy'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mood'], 'happy')
        self.assertEqual(response.data['count'], 1)
        
        # Vérifier tous les compteurs
        all_counts = response.data['all_counts']
        self.assertEqual(all_counts['happy'], 1)
        self.assertEqual(all_counts['unhappy'], 0)
        self.assertEqual(all_counts['neutral'], 0)
        self.assertEqual(all_counts['no_response'], 0)
    
    def test_increment_invalid_mood(self):
        """Test avec une humeur invalide"""
        data = {'mood': 'invalid_mood'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Doit utiliser 'no_response' par défaut
        self.assertEqual(response.data['mood'], 'no_response')
    
    def test_increment_without_mood(self):
        """Test sans spécifier d'humeur"""
        response = self.client.post(self.url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mood'], 'no_response')


class CheckIDsAPITest(APITestCase):
    """Tests pour les endpoints de vérification d'IDs"""
    
    def setUp(self):
        """Configuration initiale"""
        # Créer un shift existant
        self.operator = Operator.objects.create(
            first_name="Test",
            last_name="User"
        )
        
        self.shift = Shift.objects.create(
            shift_id="140125_TestUser_Matin",
            operator=self.operator,
            date=date(2025, 1, 14),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        # Créer un rouleau existant
        machine_params = MachineParameters.objects.create(
            name="Test",
            oxygen_primary=100,
            oxygen_secondary=100,
            propane_primary=50,
            propane_secondary=50,
            speed_primary=10,
            speed_secondary=10,
            belt_speed=100
        )
        
        profile = Profile.objects.create(
            name="Test",
            machine_parameters=machine_params
        )
        
        of = FabricationOrder.objects.create(
            order_number="OF99999",
            profile=profile
        )
        
        self.roll = Roll.objects.create(
            roll_id="OF99999_001",
            fabrication_order=of,
            roll_number=1,
            length=100
        )
    
    def test_check_existing_shift_id(self):
        """Test de vérification d'un ID de shift existant"""
        url = reverse('check-shift-id', args=['140125_TestUser_Matin'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])
    
    def test_check_non_existing_shift_id(self):
        """Test de vérification d'un ID de shift inexistant"""
        url = reverse('check-shift-id', args=['999999_Nobody_Matin'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['exists'])
    
    def test_check_existing_roll_id(self):
        """Test de vérification d'un ID de rouleau existant"""
        url = reverse('check-roll-id', args=['OF99999_001'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])
    
    def test_check_non_existing_roll_id(self):
        """Test de vérification d'un ID de rouleau inexistant"""
        url = reverse('check-roll-id', args=['OF00000_999'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['exists'])