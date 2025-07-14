from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Operator, FabricationOrder, Profile, Mode, MoodCounter
from production.models import MachineParameters


class OperatorModelTest(TestCase):
    """Tests pour le modèle Operator"""
    
    def setUp(self):
        """Créer un opérateur de test"""
        self.operator = Operator.objects.create(
            first_name="Jean",
            last_name="Dupont",
            training_completed=True,
            is_active=True
        )
    
    def test_operator_creation(self):
        """Test de création d'un opérateur"""
        self.assertEqual(self.operator.first_name, "Jean")
        self.assertEqual(self.operator.last_name, "Dupont")
        self.assertTrue(self.operator.training_completed)
        self.assertTrue(self.operator.is_active)
    
    def test_operator_str_representation(self):
        """Test de la représentation string de l'opérateur"""
        self.assertEqual(str(self.operator), "Jean Dupont")
    
    def test_operator_full_name(self):
        """Test de la propriété full_name"""
        self.assertEqual(self.operator.full_name, "Jean Dupont")
    
    def test_operator_full_name_no_space(self):
        """Test de la propriété full_name_no_space"""
        self.assertEqual(self.operator.full_name_no_space, "JeanDupont")
    
    def test_auto_employee_id_generation(self):
        """Test de la génération automatique de l'employee_id"""
        self.assertEqual(self.operator.employee_id, "JeanDUPONT")
    
    def test_custom_employee_id(self):
        """Test avec un employee_id personnalisé"""
        operator = Operator.objects.create(
            first_name="Marie",
            last_name="Martin",
            employee_id="MM001"
        )
        self.assertEqual(operator.employee_id, "MM001")


class FabricationOrderModelTest(TestCase):
    """Tests pour le modèle FabricationOrder"""
    
    def setUp(self):
        """Créer des données de test"""
        # Créer des paramètres machine
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
        
        # Créer un profil
        self.profile = Profile.objects.create(
            name="80g/m²",
            machine_parameters=self.machine_params,
            is_active=True,
            is_default=True
        )
    
    def test_fabrication_order_creation(self):
        """Test de création d'un ordre de fabrication"""
        of = FabricationOrder.objects.create(
            order_number="OF12345",
            profile=self.profile,
            required_length=1000,
            target_roll_length=100,
            for_cutting=False,
            terminated=False
        )
        
        self.assertEqual(of.order_number, "OF12345")
        self.assertEqual(of.profile, self.profile)
        self.assertEqual(of.required_length, 1000)
        self.assertEqual(of.target_roll_length, 100)
        self.assertFalse(of.for_cutting)
        self.assertFalse(of.terminated)
    
    def test_fabrication_order_str(self):
        """Test de la représentation string"""
        of = FabricationOrder.objects.create(
            order_number="OF12345",
            profile=self.profile
        )
        self.assertEqual(str(of), "OF OF12345")
    
    def test_fabrication_order_validation_negative_length(self):
        """Test de validation avec longueur négative"""
        of = FabricationOrder(
            order_number="OF12346",
            profile=self.profile,
            required_length=-100
        )
        with self.assertRaises(ValidationError):
            of.full_clean()
    
    def test_fabrication_order_validation_target_exceeds_total(self):
        """Test de validation quand la longueur cible dépasse la longueur totale"""
        of = FabricationOrder(
            order_number="OF12347",
            profile=self.profile,
            required_length=100,
            target_roll_length=200
        )
        with self.assertRaises(ValidationError):
            of.full_clean()
    
    def test_fabrication_order_unlimited_length(self):
        """Test avec longueur illimitée (0)"""
        of = FabricationOrder.objects.create(
            order_number="OF12348",
            profile=self.profile,
            required_length=0,
            target_roll_length=0
        )
        self.assertEqual(of.required_length, 0)
        self.assertEqual(of.target_roll_length, 0)


class ProfileModelTest(TestCase):
    """Tests pour le modèle Profile"""
    
    def setUp(self):
        """Créer des paramètres machine de test"""
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
    
    def test_profile_creation(self):
        """Test de création d'un profil"""
        profile = Profile.objects.create(
            name="40g/m²",
            machine_parameters=self.machine_params,
            is_active=True
        )
        
        self.assertEqual(profile.name, "40g/m²")
        self.assertEqual(profile.machine_parameters, self.machine_params)
        self.assertTrue(profile.is_active)
        self.assertFalse(profile.is_default)
    
    def test_only_one_default_profile(self):
        """Test qu'il n'y a qu'un seul profil par défaut"""
        profile1 = Profile.objects.create(
            name="Profile 1",
            is_default=True
        )
        self.assertTrue(profile1.is_default)
        
        profile2 = Profile.objects.create(
            name="Profile 2",
            is_default=True
        )
        
        # Recharger profile1 depuis la DB
        profile1.refresh_from_db()
        self.assertFalse(profile1.is_default)
        self.assertTrue(profile2.is_default)


class ModeModelTest(TestCase):
    """Tests pour le modèle Mode"""
    
    def test_mode_creation(self):
        """Test de création d'un mode"""
        mode = Mode.objects.create(
            name="Mode Maintenance",
            code="maintenance",
            description="Mode pour maintenance",
            is_enabled=True,
            is_active=True
        )
        
        self.assertEqual(mode.name, "Mode Maintenance")
        self.assertEqual(mode.code, "maintenance")
        self.assertTrue(mode.is_enabled)
        self.assertTrue(mode.is_active)
    
    def test_mode_str_enabled(self):
        """Test de la représentation string quand activé"""
        mode = Mode.objects.create(
            name="Mode Test",
            code="test",
            is_enabled=True
        )
        self.assertEqual(str(mode), "Mode Test (Activé)")
    
    def test_mode_str_disabled(self):
        """Test de la représentation string quand désactivé"""
        mode = Mode.objects.create(
            name="Mode Test",
            code="test",
            is_enabled=False
        )
        self.assertEqual(str(mode), "Mode Test (Désactivé)")


class MoodCounterModelTest(TestCase):
    """Tests pour le modèle MoodCounter"""
    
    def setUp(self):
        """Créer les 4 compteurs d'humeur"""
        MoodCounter.ensure_all_moods_exist()
    
    def test_mood_counter_creation(self):
        """Test que les 4 humeurs sont créées"""
        self.assertEqual(MoodCounter.objects.count(), 4)
        
        # Vérifier chaque type d'humeur
        moods = ['no_response', 'happy', 'unhappy', 'neutral']
        for mood in moods:
            self.assertTrue(
                MoodCounter.objects.filter(mood_type=mood).exists()
            )
    
    def test_mood_counter_increment(self):
        """Test de l'incrémentation du compteur"""
        # Incrémenter 'happy' 3 fois
        for _ in range(3):
            MoodCounter.increment('happy')
        
        happy_counter = MoodCounter.objects.get(mood_type='happy')
        self.assertEqual(happy_counter.count, 3)
    
    def test_mood_counter_get_all_counts(self):
        """Test de récupération de tous les compteurs"""
        # Incrémenter différentes humeurs
        MoodCounter.increment('happy')
        MoodCounter.increment('happy')
        MoodCounter.increment('unhappy')
        MoodCounter.increment('neutral')
        
        counts = MoodCounter.get_all_counts()
        self.assertEqual(counts['happy'], 2)
        self.assertEqual(counts['unhappy'], 1)
        self.assertEqual(counts['neutral'], 1)
        self.assertEqual(counts['no_response'], 0)
    
    def test_mood_counter_get_percentages(self):
        """Test du calcul des pourcentages"""
        # Créer une distribution connue
        for _ in range(6):
            MoodCounter.increment('happy')
        for _ in range(3):
            MoodCounter.increment('unhappy')
        MoodCounter.increment('neutral')
        
        percentages = MoodCounter.get_percentages()
        self.assertEqual(percentages['happy'], 60.0)
        self.assertEqual(percentages['unhappy'], 30.0)
        self.assertEqual(percentages['neutral'], 10.0)
        self.assertEqual(percentages['no_response'], 0.0)
    
    def test_mood_counter_percentages_no_data(self):
        """Test des pourcentages sans données"""
        percentages = MoodCounter.get_percentages()
        for mood in ['happy', 'unhappy', 'neutral', 'no_response']:
            self.assertEqual(percentages[mood], 0)
    
    def test_mood_counter_str(self):
        """Test de la représentation string"""
        counter = MoodCounter.objects.get(mood_type='happy')
        counter.count = 5
        counter.save()
        self.assertEqual(str(counter), "Content : 5")