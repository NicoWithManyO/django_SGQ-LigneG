from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from catalog.models import (
    ParamItem, SpecItem, ProfileTemplate,
    WcmLostTimeReason, WcmChecklistTemplate, 
    WcmChecklistItem, QualityDefectType
)
from planification.models import Operator, FabricationOrder
from wcm.models import Mode, MoodCounter
import sys


class Command(BaseCommand):
    help = 'Charge les données initiales de référence dans la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Vider les données existantes avant de charger',
        )
        parser.add_argument(
            '--only',
            type=str,
            help='Charger seulement certains modèles (séparés par des virgules)',
        )
        parser.add_argument(
            '--skip',
            type=str,
            help='Ignorer certains modèles (séparés par des virgules)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation - afficher ce qui serait créé sans le faire',
        )

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run', False)
        self.clear = options.get('clear', False)
        
        # Déterminer quels modèles charger
        only_models = options.get('only', '').split(',') if options.get('only') else []
        skip_models = options.get('skip', '').split(',') if options.get('skip') else []
        
        # Liste ordonnée des fixtures à charger
        fixtures = [
            ('defect_types', self.load_defect_types),
            ('spec_items', self.load_spec_items),
            ('param_items', self.load_param_items),
            ('profiles', self.load_profiles),
            ('lost_time_reasons', self.load_lost_time_reasons),
            ('checklist_items', self.load_checklist_items),
            ('operators', self.load_operators),
            ('modes', self.load_modes),
            ('mood_counters', self.load_mood_counters),
            ('fabrication_orders', self.load_fabrication_orders),
        ]
        
        # Statistiques
        self.stats = {name: {'created': 0, 'updated': 0, 'skipped': 0} for name, _ in fixtures}
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('MODE SIMULATION - Aucune donnée ne sera créée'))
        
        try:
            with transaction.atomic():
                for fixture_name, loader_func in fixtures:
                    # Vérifier si on doit charger ce fixture
                    if only_models and fixture_name not in only_models:
                        continue
                    if skip_models and fixture_name in skip_models:
                        continue
                    
                    self.stdout.write(f'\n{self.style.MIGRATE_HEADING(f"Chargement: {fixture_name}")}')
                    loader_func()
                
                if self.dry_run:
                    # Annuler la transaction en mode dry-run
                    transaction.set_rollback(True)
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {str(e)}'))
            raise CommandError(f'Échec du chargement des données: {str(e)}')
        
        # Afficher le résumé
        self.print_summary()

    def print_summary(self):
        """Affiche un résumé des opérations."""
        self.stdout.write('\n' + self.style.SUCCESS('=== RÉSUMÉ ==='))
        
        total_created = 0
        total_updated = 0
        total_skipped = 0
        
        for fixture_name, stats in self.stats.items():
            if stats['created'] or stats['updated'] or stats['skipped']:
                self.stdout.write(
                    f"{fixture_name}: "
                    f"{stats['created']} créés, "
                    f"{stats['updated']} mis à jour, "
                    f"{stats['skipped']} ignorés"
                )
                total_created += stats['created']
                total_updated += stats['updated']
                total_skipped += stats['skipped']
        
        self.stdout.write(f"\nTOTAL: {total_created} créés, {total_updated} mis à jour, {total_skipped} ignorés")

    def load_defect_types(self):
        """Charge les types de défauts qualité."""
        defect_types = [
            {
                'name': 'Autre',
                'severity': 'non_blocking',
                'description': 'Autre type de défaut'
            },
            {
                'name': 'Epaisseurs',
                'severity': 'threshold',
                'threshold_value': 3,
                'description': 'Défaut d\'épaisseur'
            },
            {
                'name': 'Infibré',
                'severity': 'threshold',
                'threshold_value': 3,
                'description': 'Défaut de fibrage'
            },
            {
                'name': 'Insectes',
                'severity': 'blocking',
                'description': 'Présence d\'insectes'
            },
            {
                'name': 'Marque Tapis',
                'severity': 'blocking',
                'description': 'Marque du tapis visible'
            },
            {
                'name': 'Shot',
                'severity': 'threshold',
                'threshold_value': 3,
                'description': 'Défaut de shot'
            },
            {
                'name': 'Trou',
                'severity': 'blocking',
                'description': 'Perforation dans le matériau'
            },
        ]
        
        if self.clear and not self.dry_run:
            QualityDefectType.objects.all().delete()
        
        for data in defect_types:
            if self.dry_run:
                exists = QualityDefectType.objects.filter(name=data['name']).exists()
                if not exists:
                    self.stdout.write(f"  Créerait QualityDefectType: {data['name']}")
                    self.stats['defect_types']['created'] += 1
                else:
                    self.stats['defect_types']['skipped'] += 1
            else:
                obj, created = QualityDefectType.objects.get_or_create(
                    name=data['name'],
                    defaults=data
                )
                if created:
                    self.stdout.write(f"  ✓ Créé QualityDefectType: {obj.name}")
                    self.stats['defect_types']['created'] += 1
                else:
                    self.stats['defect_types']['skipped'] += 1

    def load_spec_items(self):
        """Charge les items de spécifications."""
        spec_items = [
            {
                'name': 'Micronaire',
                'display_name': 'Micronaire',
                'unit': 'mlAir/min',
                'description': '',
                'order': 1
            },
            {
                'name': 'Épaisseur',
                'display_name': 'Épaisseur',
                'unit': 'mm',
                'description': '',
                'order': 2
            },
            {
                'name': 'Masse Surfacique',
                'display_name': 'Masse Surfacique',
                'unit': 'g/25cm²',
                'description': '',
                'order': 3
            },
            {
                'name': 'Masse Surfacique Globale',
                'display_name': 'Masse Surfacique Globale',
                'unit': 'g/m2',
                'description': '',
                'order': 4
            },
            {
                'name': 'Extrait Sec',
                'display_name': 'Extrait Sec',
                'unit': '%',
                'description': '',
                'order': 5
            },
        ]
        
        if self.clear and not self.dry_run:
            SpecItem.objects.all().delete()
        
        for data in spec_items:
            if self.dry_run:
                exists = SpecItem.objects.filter(name=data['name']).exists()
                if not exists:
                    self.stdout.write(f"  Créerait SpecItem: {data['display_name']}")
                    self.stats['spec_items']['created'] += 1
                else:
                    self.stats['spec_items']['skipped'] += 1
            else:
                obj, created = SpecItem.objects.get_or_create(
                    name=data['name'],
                    defaults=data
                )
                if created:
                    self.stdout.write(f"  ✓ Créé SpecItem: {obj.display_name}")
                    self.stats['spec_items']['created'] += 1
                else:
                    self.stats['spec_items']['skipped'] += 1

    def load_param_items(self):
        """Charge les items de paramètres machine."""
        param_items = [
            {
                'name': 'Oxygène Primaire',
                'display_name': 'Oxygène Primaire',
                'category': 'fibrage',
                'unit': '',
                'default_value': '0.00',
                'order': 1
            },
            {
                'name': 'Oxygène Secondaire',
                'display_name': 'Oxygène Secondaire',
                'category': 'fibrage',
                'unit': '',
                'default_value': '0.00',
                'order': 2
            },
            {
                'name': 'Propane Primaire',
                'display_name': 'Propane Primaire',
                'category': 'fibrage',
                'unit': '',
                'default_value': '0.00',
                'order': 3
            },
            {
                'name': 'Propane Secondaire',
                'display_name': 'Propane Secondaire',
                'category': 'fibrage',
                'unit': '',
                'default_value': '0.00',
                'order': 4
            },
            {
                'name': 'Vitesse Rouleaux Primaire',
                'display_name': 'Vitesse Primaire',
                'category': 'fibrage',
                'unit': 'm/h',
                'default_value': '0.00',
                'order': 5
            },
            {
                'name': 'Vitesse Rouleaux Secondaire',
                'display_name': 'Vitesse Secondaire',
                'category': 'fibrage',
                'unit': 'm/h',
                'default_value': '0.00',
                'order': 6
            },
            {
                'name': 'Vitesse Convoyeur',
                'display_name': 'Vitesse Convoyeur',
                'category': 'ensimeuse',
                'unit': 'm/h',
                'default_value': '0.00',
                'order': 7
            },
            {
                'name': 'Vitesse Tapis',
                'display_name': 'Vitesse Tapis',
                'category': 'ensimeuse',
                'unit': 'm/h',
                'default_value': '0.00',
                'order': 8
            },
        ]
        
        if self.clear and not self.dry_run:
            ParamItem.objects.all().delete()
        
        for data in param_items:
            if self.dry_run:
                exists = ParamItem.objects.filter(name=data['name']).exists()
                if not exists:
                    self.stdout.write(f"  Créerait ParamItem: {data['display_name']}")
                    self.stats['param_items']['created'] += 1
                else:
                    self.stats['param_items']['skipped'] += 1
            else:
                obj, created = ParamItem.objects.get_or_create(
                    name=data['name'],
                    defaults=data
                )
                if created:
                    self.stdout.write(f"  ✓ Créé ParamItem: {obj.display_name}")
                    self.stats['param_items']['created'] += 1
                else:
                    self.stats['param_items']['skipped'] += 1


    def load_profiles(self):
        """Charge les profils (templates) produits."""
        from catalog.models import ProfileSpecValue, ProfileParamValue
        
        profiles = [
            {
                'name': 'std 80gr/m²',
                'description': '',
                'belt_speed_m_per_minute': 0.29,
                'oee_target': 85.0,
                'is_default': True,
                'specs': {
                    'Extrait Sec': {'min': 0.16, 'min_alert': 0.22, 'nominal': 0.26, 'max_alert': 0.30, 'max': 0.34},
                    'Masse Surfacique': {'min': 0.008, 'min_alert': 0.01, 'nominal': 0.0112, 'max_alert': 0.116, 'max': 0.118},
                    'Masse Surfacique Globale': {'min': 72.0, 'min_alert': 80.0, 'nominal': 81.0, 'max_alert': 83.0, 'max': 88.0},
                    'Micronaire': {'min': 25.0, 'min_alert': 29.0, 'nominal': 32.0, 'max_alert': 36.0, 'max': 42.0},
                    'Épaisseur': {'min': 3.2, 'min_alert': 4.0, 'nominal': 6.5, 'max_alert': 9.0, 'max': None},
                },
                'params': {
                    'Vitesse Tapis': 17.40,
                    'Vitesse Rouleaux Primaire': 34.00,
                    'Vitesse Convoyeur': 26.00,
                    'Vitesse Rouleaux Secondaire': 41.00,
                    'Oxygène Primaire': 0.00,
                    'Oxygène Secondaire': 0.00,
                    'Propane Primaire': 0.00,
                    'Propane Secondaire': 0.00,
                }
            },
            {
                'name': '40gr/m²',
                'description': '',
                'belt_speed_m_per_minute': 0.58,
                'oee_target': 85.0,
                'is_default': False,
                'specs': {
                    'Extrait Sec': {'min': None, 'min_alert': None, 'nominal': 0.22, 'max_alert': None, 'max': None},
                    'Masse Surfacique': {'min': None, 'min_alert': None, 'nominal': 0.0, 'max_alert': None, 'max': None},
                    'Masse Surfacique Globale': {'min': None, 'min_alert': None, 'nominal': 0.0, 'max_alert': None, 'max': None},
                    'Micronaire': {'min': None, 'min_alert': None, 'nominal': 0.0, 'max_alert': None, 'max': None},
                    'Épaisseur': {'min': None, 'min_alert': None, 'nominal': 0.0, 'max_alert': None, 'max': None},
                },
                'params': {
                    'Vitesse Rouleaux Primaire': 35.00,
                    'Vitesse Tapis': 35.00,
                }
            },
            {
                'name': 'temp',
                'description': '',
                'belt_speed_m_per_minute': 1.67,
                'oee_target': 85.0,
                'is_default': False,
                'specs': {},
                'params': {
                    'Vitesse Tapis': 100.00,
                }
            },
        ]
        
        if self.clear and not self.dry_run:
            ProfileTemplate.objects.all().delete()
        
        for profile_data in profiles:
            if self.dry_run:
                exists = ProfileTemplate.objects.filter(name=profile_data['name']).exists()
                if not exists:
                    self.stdout.write(f"  Créerait ProfileTemplate: {profile_data['name']}")
                    self.stats['profiles']['created'] += 1
                else:
                    self.stats['profiles']['skipped'] += 1
            else:
                # Extraire les specs et params
                specs = profile_data.pop('specs', {})
                params = profile_data.pop('params', {})
                
                # Créer uniquement avec les champs qui existent dans le modèle
                profile_fields = {
                    'name': profile_data['name'],
                    'description': profile_data.get('description', ''),
                    'belt_speed_m_per_minute': profile_data['belt_speed_m_per_minute'],
                    'oee_target': profile_data['oee_target'],
                    'is_default': profile_data.get('is_default', False)
                }
                
                # Créer le profil
                profile, created = ProfileTemplate.objects.get_or_create(
                    name=profile_fields['name'],
                    defaults=profile_fields
                )
                
                if created:
                    self.stdout.write(f"  ✓ Créé ProfileTemplate: {profile.name}")
                    self.stats['profiles']['created'] += 1
                    
                    # Créer les ProfileSpecValue pour chaque spec
                    for spec_name, values in specs.items():
                        try:
                            spec_item = SpecItem.objects.get(name=spec_name)
                            ProfileSpecValue.objects.create(
                                profile=profile,
                                spec_item=spec_item,
                                value_min=values.get('min'),
                                value_min_alert=values.get('min_alert'),
                                value_nominal=values.get('nominal', 0.0),
                                value_max_alert=values.get('max_alert'),
                                value_max=values.get('max')
                            )
                            self.stdout.write(f"    → Associé spec {spec_name}")
                        except SpecItem.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f"    ⚠ Spec {spec_name} non trouvée"))
                    
                    # Créer les ProfileParamValue pour chaque param
                    for param_name, value in params.items():
                        try:
                            param_item = ParamItem.objects.get(name=param_name)
                            ProfileParamValue.objects.create(
                                profile=profile,
                                param_item=param_item,
                                value=str(value)
                            )
                            self.stdout.write(f"    → Associé param {param_name}: {value}")
                        except ParamItem.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f"    ⚠ Param {param_name} non trouvé"))
                else:
                    self.stats['profiles']['skipped'] += 1

    def load_lost_time_reasons(self):
        """Charge les motifs de temps perdu WCM."""
        reasons = [
            {'name': 'Démarrage', 'category': None, 'is_planned': False},
            {'name': 'Maintenance opérateur', 'category': None, 'is_planned': False},
            {'name': 'Panne', 'category': None, 'is_planned': False},
            {'name': 'Réamorçage', 'category': None, 'is_planned': False},
        ]
        
        if self.clear and not self.dry_run:
            WcmLostTimeReason.objects.all().delete()
        
        for i, data in enumerate(reasons):
            data['order'] = i + 1
            
            if self.dry_run:
                exists = WcmLostTimeReason.objects.filter(name=data['name']).exists()
                if not exists:
                    self.stdout.write(f"  Créerait WcmLostTimeReason: {data['name']}")
                    self.stats['lost_time_reasons']['created'] += 1
                else:
                    self.stats['lost_time_reasons']['skipped'] += 1
            else:
                obj, created = WcmLostTimeReason.objects.get_or_create(
                    name=data['name'],
                    defaults=data
                )
                if created:
                    self.stdout.write(f"  ✓ Créé WcmLostTimeReason: {obj.name}")
                    self.stats['lost_time_reasons']['created'] += 1
                else:
                    self.stats['lost_time_reasons']['skipped'] += 1

    def load_checklist_items(self):
        """Charge les items de checklist WCM."""
        from catalog.models import WcmChecklistTemplateItem
        
        # D'abord créer les templates
        template_standard = None
        template_prise_poste = None
        
        if not self.dry_run:
            # Template standard
            template_standard, _ = WcmChecklistTemplate.objects.get_or_create(
                name='Template Standard',
                defaults={
                    'description': 'Template de checklist standard pour tous les profils',
                    'is_default': True,
                    'is_active': True
                }
            )
            
            # Template pour prise/fin de poste (référencé dans migration 0012)
            template_prise_poste, _ = WcmChecklistTemplate.objects.get_or_create(
                name='Checklist Prise/Fin de poste',
                defaults={
                    'description': 'Checklist pour la prise et fin de poste',
                    'is_default': False,
                    'is_active': True
                }
            )
        
        items = [
            {'category': '', 'text': 'Contrôler l\'état des outils et équipements', 'order': 1},
            {'category': '', 'text': 'Contrôler le stock de consommables (étiquettes, film, cartons)', 'order': 2},
            {'category': '', 'text': 'Contrôler les dispositifs d\'arrêt d\'urgence', 'order': 3},
            {'category': '', 'text': 'Contrôler les paramètres machine selon la fiche de production', 'order': 4},
            {'category': '', 'text': 'Lire les consignes du poste précédent dans le cahier de liaison', 'order': 5},
            {'category': '', 'text': 'Noter les événements et anomalies dans le cahier de liaison', 'order': 6},
            {'category': '', 'text': 'Vérifier l\'état de la plante, et l\'entretenir si nécéssaire et/ou avertir', 'order': 7},
            {'category': '', 'text': 'Vérifier la conformité des matières premières disponibles', 'order': 8},
            {'category': '', 'text': 'Vérifier la propreté et le rangement du poste de travail', 'order': 9},
            {'category': '', 'text': 'Vérifier la présence et l\'état des EPI (casque, lunettes, chaussures)', 'order': 10},
            {'category': '', 'text': 'Vérifier le bon fonctionnement des instruments de mesure', 'order': 11},
            {'category': '', 'text': 'Vérifier le niveau des bacs de récupération', 'order': 12},
        ]
        
        if self.clear and not self.dry_run:
            WcmChecklistItem.objects.all().delete()
        
        for data in items:
            order = data.pop('order')
            if self.dry_run:
                self.stdout.write(f"  Créerait WcmChecklistItem: {data['text']}")
                self.stats['checklist_items']['created'] += 1
            else:
                obj, created = WcmChecklistItem.objects.get_or_create(
                    text=data['text'],
                    defaults={
                        'category': data['category'],
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f"  ✓ Créé WcmChecklistItem: {obj.text}")
                    self.stats['checklist_items']['created'] += 1
                else:
                    self.stats['checklist_items']['skipped'] += 1
                
                # Associer au template standard via la table intermédiaire
                if template_standard:
                    WcmChecklistTemplateItem.objects.get_or_create(
                        template=template_standard,
                        item=obj,
                        defaults={'order': order, 'is_required': True}
                    )

    def load_operators(self):
        """Charge les opérateurs."""
        operators = [
            {'first_name': 'Jerry', 'last_name': 'BABET', 'is_active': True},
            {'first_name': 'Nicolas', 'last_name': 'BOULAIS', 'is_active': True},
            {'first_name': 'Houy', 'last_name': 'DAVID', 'is_active': True},
            {'first_name': 'Nicolas', 'last_name': 'FOUGERARD', 'is_active': True},
            {'first_name': 'Demba', 'last_name': 'HAÏDARA', 'is_active': True},
            {'first_name': 'Morgan', 'last_name': 'HOUY', 'is_active': True},
            {'first_name': 'Thomas', 'last_name': 'NAU', 'is_active': True},
            {'first_name': 'Jonathan', 'last_name': 'NESTORET', 'is_active': True},
        ]
        
        if self.clear and not self.dry_run:
            Operator.objects.all().delete()
        
        for data in operators:
            if self.dry_run:
                # L'employee_id sera généré automatiquement
                employee_id = f"{data['first_name']}{data['last_name'].upper()}"
                exists = Operator.objects.filter(employee_id=employee_id).exists()
                if not exists:
                    self.stdout.write(f"  Créerait Operator: {data['first_name']} {data['last_name']}")
                    self.stats['operators']['created'] += 1
                else:
                    self.stats['operators']['skipped'] += 1
            else:
                # L'employee_id est généré automatiquement par le modèle
                employee_id = f"{data['first_name']}{data['last_name'].upper()}"
                obj, created = Operator.objects.get_or_create(
                    employee_id=employee_id,
                    defaults=data
                )
                if created:
                    self.stdout.write(f"  ✓ Créé Operator: {obj.first_name} {obj.last_name} ({obj.employee_id})")
                    self.stats['operators']['created'] += 1
                else:
                    self.stats['operators']['skipped'] += 1

    def load_modes(self):
        """Charge les modes de fonctionnement."""
        modes = [
            {
                'name': 'Normal',
                'description': 'Mode de fonctionnement normal',
                'is_enabled': True,
                'is_active': True
            },
            {
                'name': 'Permissif',
                'description': 'Mode permissif - Autorise certains écarts',
                'is_enabled': False,
                'is_active': True
            },
            {
                'name': 'Dégradé',
                'description': 'Mode dégradé - Fonctionnement limité',
                'is_enabled': False,
                'is_active': True
            },
            {
                'name': 'Maintenance',
                'description': 'Mode maintenance - Pour les interventions',
                'is_enabled': False,
                'is_active': True
            },
        ]
        
        if self.clear and not self.dry_run:
            Mode.objects.all().delete()
        
        for data in modes:
            if self.dry_run:
                exists = Mode.objects.filter(name=data['name']).exists()
                if not exists:
                    self.stdout.write(f"  Créerait Mode: {data['name']}")
                    self.stats['modes']['created'] += 1
                else:
                    self.stats['modes']['skipped'] += 1
            else:
                obj, created = Mode.objects.get_or_create(
                    name=data['name'],
                    defaults=data
                )
                if created:
                    self.stdout.write(f"  ✓ Créé Mode: {obj.name}")
                    self.stats['modes']['created'] += 1
                else:
                    self.stats['modes']['skipped'] += 1

    def load_mood_counters(self):
        """Initialise les compteurs d'humeur."""
        moods = ['happy', 'neutral', 'unhappy', 'no_response']
        
        if self.clear and not self.dry_run:
            MoodCounter.objects.all().delete()
        
        for mood in moods:
            if self.dry_run:
                exists = MoodCounter.objects.filter(mood_type=mood).exists()
                if not exists:
                    self.stdout.write(f"  Créerait MoodCounter: {mood}")
                    self.stats['mood_counters']['created'] += 1
                else:
                    self.stats['mood_counters']['skipped'] += 1
            else:
                obj, created = MoodCounter.objects.get_or_create(
                    mood_type=mood,
                    defaults={'count': 0}
                )
                if created:
                    self.stdout.write(f"  ✓ Créé MoodCounter: {obj.get_mood_type_display()}")
                    self.stats['mood_counters']['created'] += 1
                else:
                    self.stats['mood_counters']['skipped'] += 1

    def load_fabrication_orders(self):
        """Charge l'OF de découpe 9999."""
        from catalog.models import ProfileTemplate
        
        # Récupérer le profil par défaut
        try:
            default_profile = ProfileTemplate.objects.get(is_default=True)
        except ProfileTemplate.DoesNotExist:
            default_profile = ProfileTemplate.objects.first()
        
        if not default_profile:
            self.stdout.write(self.style.WARNING("  ⚠ Aucun profil disponible pour créer l'OF"))
            return
        
        orders = [
            {
                'order_number': '9999',
                'required_length': None,
                'target_roll_length': None,
                'for_cutting': True
            }
        ]
        
        if self.clear and not self.dry_run:
            FabricationOrder.objects.filter(order_number='9999').delete()
        
        for data in orders:
            if self.dry_run:
                exists = FabricationOrder.objects.filter(order_number=data['order_number']).exists()
                if not exists:
                    self.stdout.write(f"  Créerait FabricationOrder: {data['order_number']}")
                    self.stats['fabrication_orders']['created'] += 1
                else:
                    self.stats['fabrication_orders']['skipped'] += 1
            else:
                obj, created = FabricationOrder.objects.get_or_create(
                    order_number=data['order_number'],
                    defaults=data
                )
                if created:
                    self.stdout.write(f"  ✓ Créé FabricationOrder: {obj.order_number} (découpe)")
                    self.stats['fabrication_orders']['created'] += 1
                else:
                    self.stats['fabrication_orders']['skipped'] += 1