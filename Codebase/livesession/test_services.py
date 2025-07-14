from django.test import TestCase
from datetime import date, time, datetime
from decimal import Decimal
from .services import MetricsCalculator, ShiftMetricsService
from core.models import Operator, FabricationOrder, Profile
from production.models import MachineParameters, Shift, Roll
from wcm.models import LostTimeReason
from quality.models import Specification


class MetricsCalculatorTest(TestCase):
    """Tests pour le calculateur de métriques"""
    
    def setUp(self):
        """Configuration initiale"""
        self.calculator = MetricsCalculator()
    
    def test_calculate_opening_time_normal(self):
        """Test du calcul du temps d'ouverture normal"""
        session_data = {
            'start_time': '04:00',
            'end_time': '12:00'
        }
        
        result = self.calculator.calculate_opening_time(session_data)
        
        self.assertEqual(result, 480)  # 8 heures = 480 minutes
    
    def test_calculate_opening_time_night_shift(self):
        """Test du calcul pour un poste de nuit"""
        session_data = {
            'start_time': '20:00',
            'end_time': '04:00'
        }
        
        result = self.calculator.calculate_opening_time(session_data)
        
        self.assertEqual(result, 480)  # 8 heures = 480 minutes
    
    def test_calculate_opening_time_with_time_objects(self):
        """Test avec des objets time au lieu de strings"""
        session_data = {
            'start_time': time(4, 0),
            'end_time': time(12, 0)
        }
        
        result = self.calculator.calculate_opening_time(session_data)
        
        self.assertEqual(result, 480)
    
    def test_calculate_opening_time_missing_times(self):
        """Test avec des heures manquantes"""
        session_data = {}
        
        result = self.calculator.calculate_opening_time(session_data)
        
        self.assertEqual(result, 0)
    
    def test_calculate_lost_time_empty(self):
        """Test du calcul sans temps perdu"""
        session_data = {
            'lost_times': []
        }
        
        result = self.calculator.calculate_lost_time(session_data)
        
        self.assertEqual(result, 0)
    
    def test_calculate_lost_time_multiple_entries(self):
        """Test avec plusieurs entrées de temps perdu"""
        session_data = {
            'lost_times': [
                {'duration': 30},
                {'duration': 15},
                {'duration': 45}
            ]
        }
        
        result = self.calculator.calculate_lost_time(session_data)
        
        self.assertEqual(result, 90)  # 30 + 15 + 45
    
    def test_calculate_available_time(self):
        """Test du calcul du temps disponible"""
        session_data = {
            'start_time': '04:00',
            'end_time': '12:00',
            'lost_times': [
                {'duration': 30},
                {'duration': 20}
            ]
        }
        
        # TO = 480, TP = 50, donc TD = 430
        result = self.calculator.calculate_available_time(session_data)
        
        self.assertEqual(result, 430)
    
    def test_calculate_ok_length_no_rolls(self):
        """Test de la longueur OK sans rouleaux"""
        saved_rolls = []
        current_roll = {}
        
        result = self.calculator.calculate_ok_length(saved_rolls, current_roll)
        
        self.assertEqual(result, 0)
    
    def test_calculate_ok_length_with_conforme_rolls(self):
        """Test avec des rouleaux conformes"""
        # Créer des données de test
        self.operator = Operator.objects.create(
            first_name="Test",
            last_name="User"
        )
        
        self.shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        # Créer un OF
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
            order_number="OF12345",
            profile=profile
        )
        
        # Créer des rouleaux
        roll1 = Roll.objects.create(
            roll_id="OF12345_001",
            fabrication_order=of,
            shift=self.shift,
            roll_number=1,
            length=100,
            status="CONFORME"
        )
        
        roll2 = Roll.objects.create(
            roll_id="OF12345_002",
            fabrication_order=of,
            shift=self.shift,
            roll_number=2,
            length=150,
            status="CONFORME"
        )
        
        roll3 = Roll.objects.create(
            roll_id="OF12345_003",
            fabrication_order=of,
            shift=self.shift,
            roll_number=3,
            length=50,
            status="NON_CONFORME"
        )
        
        saved_rolls = Roll.objects.filter(shift=self.shift)
        current_roll = {
            'info': {
                'length': 200
            }
        }
        
        # 100 + 150 (conformes uniquement) + 200 (current)
        result = self.calculator.calculate_ok_length(saved_rolls, current_roll)
        
        self.assertEqual(result, 450)
    
    def test_calculate_nok_length(self):
        """Test de la longueur NON OK"""
        # Utiliser les mêmes données que le test précédent
        self.test_calculate_ok_length_with_conforme_rolls()
        
        saved_rolls = Roll.objects.filter(shift=self.shift)
        
        # Seulement le rouleau non conforme: 50
        result = self.calculator.calculate_nok_length(saved_rolls)
        
        self.assertEqual(result, 50)
    
    def test_format_time_minutes(self):
        """Test du formatage des minutes en heures"""
        self.assertEqual(self.calculator.format_time(0), '--')
        self.assertEqual(self.calculator.format_time(30), '30min')
        self.assertEqual(self.calculator.format_time(60), '1h00')
        self.assertEqual(self.calculator.format_time(90), '1h30')
        self.assertEqual(self.calculator.format_time(480), '8h00')
    
    def test_calculate_percent_safe(self):
        """Test du calcul de pourcentage sécurisé"""
        self.assertEqual(self.calculator.calculate_percent_safe(50, 100), 50.0)
        self.assertEqual(self.calculator.calculate_percent_safe(0, 100), 0.0)
        self.assertEqual(self.calculator.calculate_percent_safe(100, 0), 0.0)  # Division par zéro
        self.assertEqual(self.calculator.calculate_percent_safe(25, 50), 50.0)


class ShiftMetricsServiceTest(TestCase):
    """Tests pour le service de métriques de shift"""
    
    def setUp(self):
        """Configuration initiale"""
        self.service = ShiftMetricsService()
        
        # Créer des données de test
        self.operator = Operator.objects.create(
            first_name="Test",
            last_name="User"
        )
        
        self.shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        # Créer un OF et profil
        self.machine_params = MachineParameters.objects.create(
            name="Test Params",
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
        
        # Créer des spécifications
        self.spec_grammage = Specification.objects.create(
            name="Grammage 80g/m²",
            spec_type="global_surface_mass",
            min_value=75.0,
            max_value=85.0,
            nominal_value=80.0,
            unit="g/m²"
        )
        
        # Associer la spec au profil
        self.profile.specifications.add(self.spec_grammage)
    
    def test_calculate_grammage_complete_data(self):
        """Test du calcul du grammage avec toutes les données"""
        session_data = {
            'belt_speed': 120,  # 120 m/h = 2 m/min
            'current_roll': {
                'info': {
                    'length': 100,
                    'tube_mass': 10,
                    'total_mass': 90
                }
            }
        }
        
        # Net mass = 90 - 10 = 80 kg
        # Area = 100m * 2.5m = 250 m²
        # Grammage = 80000g / 250m² = 320 g/m²
        result = self.service.calculate_grammage(
            session_data, 
            self.machine_params, 
            self.profile
        )
        
        self.assertEqual(result['value'], 320.0)
        self.assertEqual(result['status'], 'out_of_spec')  # 320 > 85 (max)
    
    def test_calculate_grammage_missing_data(self):
        """Test du grammage avec données manquantes"""
        session_data = {
            'belt_speed': 120,
            'current_roll': {
                'info': {
                    'length': 100
                    # Manque les masses
                }
            }
        }
        
        result = self.service.calculate_grammage(
            session_data,
            self.machine_params,
            self.profile
        )
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['status'], 'unknown')
    
    def test_calculate_yield(self):
        """Test du calcul du rendement"""
        session_data = {
            'start_time': '04:00',
            'end_time': '12:00',
            'lost_times': [
                {'duration': 60}  # 1 heure perdue
            ]
        }
        
        # TO = 480 min, TP = 60 min, TD = 420 min
        # Rendement = (420 / 480) * 100 = 87.5%
        result = self.service.calculate_yield(session_data)
        
        self.assertEqual(result, 87.5)
    
    def test_calculate_ok_rate_no_rolls(self):
        """Test du taux OK sans rouleaux"""
        saved_rolls = Roll.objects.none()
        
        result = self.service.calculate_ok_rate(saved_rolls)
        
        self.assertEqual(result, 0.0)
    
    def test_calculate_ok_rate_with_rolls(self):
        """Test du taux OK avec rouleaux"""
        # Créer des rouleaux
        Roll.objects.create(
            roll_id="TEST_001",
            fabrication_order=self.of,
            shift=self.shift,
            roll_number=1,
            length=100,
            status="CONFORME"
        )
        
        Roll.objects.create(
            roll_id="TEST_002",
            fabrication_order=self.of,
            shift=self.shift,
            roll_number=2,
            length=100,
            status="CONFORME"
        )
        
        Roll.objects.create(
            roll_id="TEST_003",
            fabrication_order=self.of,
            shift=self.shift,
            roll_number=3,
            length=100,
            status="NON_CONFORME"
        )
        
        saved_rolls = Roll.objects.filter(shift=self.shift)
        
        # 2 conformes sur 3 = 66.67%
        result = self.service.calculate_ok_rate(saved_rolls)
        
        self.assertAlmostEqual(result, 66.67, places=2)
    
    def test_get_specifications_for_profile(self):
        """Test de récupération des spécifications d'un profil"""
        specs = self.service.get_specifications_for_profile(self.profile)
        
        self.assertIn('global_surface_mass', specs)
        spec = specs['global_surface_mass']
        self.assertEqual(spec['min'], 75.0)
        self.assertEqual(spec['max'], 85.0)
        self.assertEqual(spec['nominal'], 80.0)
    
    def test_check_value_against_spec(self):
        """Test de vérification d'une valeur contre une spec"""
        spec = {
            'min': 75.0,
            'max': 85.0,
            'nominal': 80.0
        }
        
        # Dans les specs
        self.assertEqual(
            self.service.check_value_against_spec(80.0, spec),
            'in_spec'
        )
        
        # Trop bas
        self.assertEqual(
            self.service.check_value_against_spec(70.0, spec),
            'out_of_spec'
        )
        
        # Trop haut
        self.assertEqual(
            self.service.check_value_against_spec(90.0, spec),
            'out_of_spec'
        )
        
        # Spec None
        self.assertEqual(
            self.service.check_value_against_spec(80.0, None),
            'unknown'
        )