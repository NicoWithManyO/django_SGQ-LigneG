from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta
from decimal import Decimal
from .models import Shift, Roll, QualityControl, LostTimeEntry, MachineParameters
from core.models import Operator, FabricationOrder, Profile
from wcm.models import LostTimeReason
from quality.models import DefectType, RollDefect, RollThickness


class ShiftModelTest(TestCase):
    """Tests pour le modèle Shift"""
    
    def setUp(self):
        """Créer des données de test"""
        self.operator = Operator.objects.create(
            first_name="Jean",
            last_name="Dupont"
        )
        
    def test_shift_creation(self):
        """Test de création d'un shift"""
        shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        self.assertEqual(shift.operator, self.operator)
        self.assertEqual(shift.vacation, "Matin")
        self.assertIsNotNone(shift.shift_id)
    
    def test_shift_id_generation(self):
        """Test de génération automatique de l'ID du shift"""
        shift = Shift.objects.create(
            operator=self.operator,
            date=date(2025, 1, 14),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        expected_id = "140125_JeanDupont_Matin"
        self.assertEqual(shift.shift_id, expected_id)
    
    def test_opening_time_calculation(self):
        """Test du calcul de la durée d'ouverture"""
        shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        self.assertEqual(shift.opening_time, 480)  # 8 heures = 480 minutes
    
    def test_opening_time_night_shift(self):
        """Test du calcul pour un poste de nuit (passage minuit)"""
        shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Nuit",
            start_time=time(20, 0),
            end_time=time(4, 0)
        )
        
        self.assertEqual(shift.opening_time, 480)  # 8 heures = 480 minutes
    
    def test_available_time_calculation(self):
        """Test du calcul du temps disponible"""
        shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0),
            lost_time=60  # 1 heure perdue
        )
        
        self.assertEqual(shift.available_time, 420)  # 480 - 60 = 420 minutes
    
    def test_shift_str_representation(self):
        """Test de la représentation string"""
        shift = Shift.objects.create(
            operator=self.operator,
            date=date(2025, 1, 14),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        self.assertEqual(str(shift), "Poste du 2025-01-14 Matin (Jean Dupont)")
    
    def test_operator_deletion_protection(self):
        """Test que la suppression d'un opérateur ne supprime pas le shift"""
        shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        # Supprimer l'opérateur
        self.operator.delete()
        
        # Recharger le shift
        shift.refresh_from_db()
        self.assertIsNone(shift.operator)
        self.assertTrue(Shift.objects.filter(pk=shift.pk).exists())


class RollModelTest(TestCase):
    """Tests pour le modèle Roll"""
    
    def setUp(self):
        """Créer des données de test"""
        self.operator = Operator.objects.create(
            first_name="Jean",
            last_name="Dupont"
        )
        
        self.shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
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
    
    def test_roll_creation(self):
        """Test de création d'un rouleau"""
        roll = Roll.objects.create(
            roll_id="OF12345_001",
            fabrication_order=self.of,
            shift=self.shift,
            roll_number=1,
            length=Decimal('250.5'),
            tube_mass=Decimal('15.2'),
            total_mass=Decimal('245.7'),
            status="CONFORME",
            destination="PRODUCTION"
        )
        
        self.assertEqual(roll.roll_id, "OF12345_001")
        self.assertEqual(roll.net_mass, Decimal('230.5'))  # 245.7 - 15.2
        self.assertEqual(roll.status, "CONFORME")
    
    def test_roll_net_mass_calculation(self):
        """Test du calcul de la masse nette"""
        roll = Roll.objects.create(
            roll_id="OF12345_002",
            fabrication_order=self.of,
            shift=self.shift,
            roll_number=2,
            length=100,
            tube_mass=10,
            total_mass=110
        )
        
        self.assertEqual(roll.net_mass, 100)  # 110 - 10
    
    def test_roll_str_representation(self):
        """Test de la représentation string"""
        roll = Roll.objects.create(
            roll_id="OF12345_003",
            fabrication_order=self.of,
            shift=self.shift,
            roll_number=3,
            length=200
        )
        
        self.assertEqual(str(roll), "Rouleau OF12345_003")
    
    def test_roll_shift_deletion_protection(self):
        """Test que la suppression d'un shift ne supprime pas le rouleau"""
        roll = Roll.objects.create(
            roll_id="OF12345_004",
            fabrication_order=self.of,
            shift=self.shift,
            roll_number=4,
            length=150
        )
        
        # Supprimer le shift
        self.shift.delete()
        
        # Recharger le rouleau
        roll.refresh_from_db()
        self.assertIsNone(roll.shift)
        self.assertTrue(Roll.objects.filter(pk=roll.pk).exists())
    
    def test_roll_without_shift(self):
        """Test de création d'un rouleau sans shift"""
        roll = Roll.objects.create(
            roll_id="OF12345_005",
            fabrication_order=self.of,
            shift=None,  # Pas de shift associé
            roll_number=5,
            length=300,
            session_key="test_session_key"
        )
        
        self.assertIsNone(roll.shift)
        self.assertEqual(roll.session_key, "test_session_key")


class QualityControlModelTest(TestCase):
    """Tests pour le modèle QualityControl"""
    
    def setUp(self):
        """Créer des données de test"""
        self.operator = Operator.objects.create(
            first_name="Jean",
            last_name="Dupont"
        )
        
        self.shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
    
    def test_quality_control_creation(self):
        """Test de création d'un contrôle qualité"""
        qc = QualityControl.objects.create(
            shift=self.shift,
            created_by=self.operator,
            micrometer_left_1=4.5,
            micrometer_left_2=4.6,
            micrometer_left_3=4.4,
            micrometer_right_1=4.7,
            micrometer_right_2=4.5,
            micrometer_right_3=4.6,
            dry_extract=10.5,
            dry_extract_time="10:30",
            surface_mass_gg=78.5,
            surface_mass_gc=79.0,
            surface_mass_dc=78.8,
            surface_mass_dd=79.2,
            loi_given=True,
            loi_time="11:00"
        )
        
        self.assertEqual(qc.micrometer_left_avg, Decimal('4.50'))
        self.assertEqual(qc.micrometer_right_avg, Decimal('4.60'))
        self.assertEqual(qc.surface_mass_left_avg, Decimal('78.75'))
        self.assertEqual(qc.surface_mass_right_avg, Decimal('79.00'))
    
    def test_micrometer_average_calculation(self):
        """Test du calcul des moyennes micronnaire"""
        qc = QualityControl.objects.create(
            shift=self.shift,
            created_by=self.operator,
            micrometer_left_1=4.0,
            micrometer_left_2=5.0,
            micrometer_right_1=4.5,
            micrometer_right_2=5.5
        )
        
        # Avec 2 valeurs, la moyenne est calculée
        self.assertEqual(qc.micrometer_left_avg, Decimal('4.50'))
        self.assertEqual(qc.micrometer_right_avg, Decimal('5.00'))
    
    def test_surface_mass_average_calculation(self):
        """Test du calcul des moyennes de masse surfacique"""
        qc = QualityControl.objects.create(
            shift=self.shift,
            created_by=self.operator,
            surface_mass_gg=80.0,
            surface_mass_gc=82.0,
            surface_mass_dc=81.0,
            surface_mass_dd=83.0
        )
        
        self.assertEqual(qc.surface_mass_left_avg, Decimal('81.00'))
        self.assertEqual(qc.surface_mass_right_avg, Decimal('82.00'))
    
    def test_quality_control_str(self):
        """Test de la représentation string"""
        qc = QualityControl.objects.create(
            shift=self.shift,
            created_by=self.operator
        )
        
        expected = f"Contrôles qualité - Poste du {date.today()} Matin"
        self.assertEqual(str(qc), expected)
    
    def test_quality_control_validation_required(self):
        """Test que is_valid est défini sur True par défaut"""
        qc = QualityControl.objects.create(
            shift=self.shift,
            created_by=self.operator
        )
        
        self.assertTrue(qc.is_valid)


class MachineParametersModelTest(TestCase):
    """Tests pour le modèle MachineParameters"""
    
    def test_machine_parameters_creation(self):
        """Test de création des paramètres machine"""
        params = MachineParameters.objects.create(
            name="Profil 80g/m²",
            oxygen_primary=100.5,
            oxygen_secondary=150.0,
            propane_primary=50.2,
            propane_secondary=75.8,
            speed_primary=10.0,
            speed_secondary=15.5,
            belt_speed=120.0
        )
        
        self.assertEqual(params.name, "Profil 80g/m²")
        self.assertEqual(params.oxygen_primary, Decimal('100.5'))
        self.assertEqual(params.belt_speed, Decimal('120.0'))
    
    def test_belt_speed_conversion(self):
        """Test de la conversion vitesse tapis m/h vers m/min"""
        params = MachineParameters.objects.create(
            name="Test Speed",
            oxygen_primary=100,
            oxygen_secondary=100,
            propane_primary=50,
            propane_secondary=50,
            speed_primary=10,
            speed_secondary=10,
            belt_speed=120  # 120 m/h
        )
        
        self.assertEqual(params.belt_speed_m_per_minute, Decimal('2.00'))  # 120/60 = 2 m/min
    
    def test_only_one_active_profile(self):
        """Test qu'il n'y a qu'un seul profil actif"""
        params1 = MachineParameters.objects.create(
            name="Profil 1",
            oxygen_primary=100,
            oxygen_secondary=100,
            propane_primary=50,
            propane_secondary=50,
            speed_primary=10,
            speed_secondary=10,
            belt_speed=100,
            is_active=True
        )
        
        params2 = MachineParameters.objects.create(
            name="Profil 2",
            oxygen_primary=100,
            oxygen_secondary=100,
            propane_primary=50,
            propane_secondary=50,
            speed_primary=10,
            speed_secondary=10,
            belt_speed=100,
            is_active=True
        )
        
        # Recharger params1
        params1.refresh_from_db()
        self.assertFalse(params1.is_active)
        self.assertTrue(params2.is_active)


class LostTimeEntryModelTest(TestCase):
    """Tests pour le modèle LostTimeEntry"""
    
    def setUp(self):
        """Créer des données de test"""
        self.operator = Operator.objects.create(
            first_name="Jean",
            last_name="Dupont"
        )
        
        self.shift = Shift.objects.create(
            operator=self.operator,
            date=date.today(),
            vacation="Matin",
            start_time=time(4, 0),
            end_time=time(12, 0)
        )
        
        self.reason = LostTimeReason.objects.create(
            reason="Panne machine",
            category="TECHNIQUE"
        )
    
    def test_lost_time_entry_creation(self):
        """Test de création d'une entrée de temps perdu"""
        entry = LostTimeEntry.objects.create(
            shift=self.shift,
            reason=self.reason,
            duration=30,
            comments="Arrêt pour maintenance"
        )
        
        self.assertEqual(entry.duration, 30)
        self.assertEqual(entry.reason.reason, "Panne machine")
        self.assertEqual(entry.comments, "Arrêt pour maintenance")
    
    def test_lost_time_entry_str(self):
        """Test de la représentation string"""
        entry = LostTimeEntry.objects.create(
            shift=self.shift,
            reason=self.reason,
            duration=45
        )
        
        self.assertEqual(str(entry), "Panne machine - 45 min")
    
    def test_lost_time_without_shift(self):
        """Test de création sans shift (session temporaire)"""
        entry = LostTimeEntry.objects.create(
            session_key="test_session",
            reason=self.reason,
            duration=15
        )
        
        self.assertIsNone(entry.shift)
        self.assertEqual(entry.session_key, "test_session")