#!/usr/bin/env python3
"""
Script de génération de données fake cohérentes
Génère des postes de production avec rouleaux associés pour tester l'interface RC
"""

import os
import sys
import django
from django.utils import timezone
from datetime import datetime, timedelta, time
from decimal import Decimal
import random

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgq_ligne_g.settings')
django.setup()

from production.models import Shift, Roll
from planification.models import Operator, FabricationOrder
from catalog.models import ProfileTemplate, WcmChecklistItem, QualityDefectType
from quality.models import Controls, RollDefect, RollThickness
from wcm.models import TRS, MoodCounter, LostTimeEntry, ChecklistResponse

class FakeDataGenerator:
    """Générateur de données fake cohérentes."""
    
    def __init__(self):
        self.operators = []
        self.ofs = []
        self.profiles = []
        
    def setup_base_data(self):
        """Configure les données de base nécessaires."""
        print("🔧 Configuration des données de base...")
        
        # Utiliser les vrais opérateurs de la BDD
        real_operators = Operator.objects.filter(is_active=True)
        if real_operators.exists():
            self.operators = list(real_operators)
            print(f"  ✓ {len(self.operators)} opérateurs trouvés en BDD:")
            for op in self.operators:
                print(f"    - {op.employee_id}")
        else:
            print("  ⚠️ Aucun opérateur trouvé en BDD, création d'opérateurs de test...")
            # Créer des opérateurs de test seulement si aucun n'existe
            operators_data = [
                {'first_name': 'Martin', 'last_name': 'Dupont'},
                {'first_name': 'Sophie', 'last_name': 'Bernard'},
                {'first_name': 'Pierre', 'last_name': 'Moreau'},
                {'first_name': 'Marie', 'last_name': 'Lefevre'},
            ]
            
            for op_data in operators_data:
                operator, created = Operator.objects.get_or_create(
                    first_name=op_data['first_name'],
                    last_name=op_data['last_name'],
                    defaults={
                        'employee_id': f"{op_data['first_name']}{op_data['last_name'].upper()}",
                        'is_active': True,
                        'training_completed': True
                    }
                )
                self.operators.append(operator)
                if created:
                    print(f"  ✓ Opérateur créé: {operator.employee_id}")
        
        # Créer l'OF 5555 uniquement
        of_obj, created = FabricationOrder.objects.get_or_create(
            order_number='5555',
            defaults={
                'target_length': random.randint(800, 1500),
                'is_active': True
            }
        )
        self.ofs.append(of_obj)
        if created:
            print(f"  ✓ OF créé: 5555")
        
        # Récupérer les profils existants
        self.profiles = list(ProfileTemplate.objects.all()[:5])
        if not self.profiles:
            print("  ⚠️ Aucun profil trouvé, pensez à lancer load_initial_data")
    
    def generate_shift(self, date, vacation, operator):
        """Génère un poste avec des données cohérentes."""
        shift_data = {
            'date': date,
            'operator': operator,
            'vacation': vacation,
            'start_time': self.get_start_time(vacation),
            'end_time': self.get_end_time(vacation),
            'started_at_beginning': random.choice([True, False]),
            'started_at_end': random.choice([True, False]),
            'meter_reading_start': Decimal(str(random.uniform(10000, 50000))),
            'meter_reading_end': Decimal(str(random.uniform(51000, 80000))),
            'checklist_signed': operator.employee_id[:3].upper(),
            'checklist_signed_time': self.get_checklist_time(vacation),
            'operator_comments': random.choice([
                "",
                "RAS",
                "Quelques micro-arrêts",
                "Bon déroulement du poste",
                "Problème mineur résolu"
            ])
        }
        
        shift = Shift.objects.create(**shift_data)
        print(f"  ✓ Poste créé: {shift.shift_id}")
        return shift
    
    def generate_rolls_for_shift(self, shift, num_rolls=None):
        """Génère des rouleaux pour un poste donné."""
        if num_rolls is None:
            num_rolls = random.randint(3, 8)
        
        rolls_created = []
        
        # Trouver le prochain numéro de rouleau disponible pour l'OF 5555
        of = self.ofs[0]  # Toujours utiliser l'OF 5555
        existing_rolls = Roll.objects.filter(fabrication_order=of).order_by('-roll_number')
        if existing_rolls.exists():
            next_roll_number = existing_rolls.first().roll_number + 1
        else:
            next_roll_number = 1
        
        for i in range(num_rolls):
            roll_number = next_roll_number + i
            
            # Données de base
            length = Decimal(str(random.uniform(50, 200)))
            tube_mass = Decimal(str(random.uniform(500, 800)))
            total_mass = Decimal(str(random.uniform(8000, 15000)))
            
            # Épaisseurs cohérentes
            thickness_left = Decimal(str(random.uniform(3.5, 4.2)))
            thickness_right = Decimal(str(random.uniform(3.5, 4.2)))
            
            # Statut (90% conformes)
            status = 'CONFORME' if random.random() > 0.1 else 'NON_CONFORME'
            
            roll_data = {
                'shift': shift,
                'shift_id_str': shift.shift_id,
                'fabrication_order': of,
                'roll_number': roll_number,
                'length': length,
                'tube_mass': tube_mass,
                'total_mass': total_mass,
                'net_mass': total_mass - tube_mass,
                'avg_thickness_left': thickness_left,
                'avg_thickness_right': thickness_right,
                'grammage_calc': Decimal(str(random.uniform(60, 90))),
                'status': status,
                'destination': 'DECOUPE' if status == 'NON_CONFORME' else 'PRODUCTION',
                'has_blocking_defects': status == 'NON_CONFORME',
                'has_thickness_issues': random.choice([True, False]) if status == 'NON_CONFORME' else False,
                'comment': random.choice([
                    "", "", "",  # Plus de chances d'avoir pas de commentaire
                    "RAS",
                    "Épaisseur limite",
                    "Bon rouleau",
                    "Défaut mineur"
                ])
            }
            
            roll = Roll.objects.create(**roll_data)
            rolls_created.append(roll)
        
        print(f"    → {len(rolls_created)} rouleaux créés ({len([r for r in rolls_created if r.status == 'CONFORME'])} conformes)")
        return rolls_created
    
    def generate_quality_controls_for_shift(self, shift, rolls):
        """Génère les contrôles qualité pour un poste."""
        print(f"    → Création contrôles qualité pour {shift.shift_id}")
        
        # Créer un contrôle qualité global pour le poste
        try:
            quality_control = Controls.objects.create(
                shift=shift,
                micromaire_g=Decimal(str(random.uniform(75, 95))),
                micromaire_unit="mlAir/min",
                tension_bobinage=Decimal(str(random.uniform(2.5, 4.0))),
                vitesse_ligne=Decimal(str(random.uniform(180, 220))),
                temperature_etuve=Decimal(str(random.uniform(180, 200))),
                humidite_produit=Decimal(str(random.uniform(8, 12))),
                notes=random.choice([
                    "Contrôles conformes",
                    "RAS",
                    "Paramètres dans les normes",
                    "Léger ajustement tension",
                    ""
                ])
            )
            
            # Générer des grilles d'épaisseur pour quelques rouleaux
            sample_rolls = random.sample(rolls, min(3, len(rolls)))
            for roll in sample_rolls:
                self.generate_thickness_grid_for_roll(roll)
                
        except Exception as e:
            print(f"      ⚠️ Erreur création contrôle qualité: {e}")
    
    def generate_thickness_grid_for_roll(self, roll):
        """Génère une grille d'épaisseur pour un rouleau."""
        try:
            # Créer 15 mesures d'épaisseur (grille 5x3)
            base_thickness_left = float(roll.avg_thickness_left or 3.8)
            base_thickness_right = float(roll.avg_thickness_right or 3.8)
            
            for i in range(15):
                # Variation de ±0.3mm autour de la base
                left_var = random.uniform(-0.3, 0.3)
                right_var = random.uniform(-0.3, 0.3)
                
                RollThickness.objects.create(
                    roll=roll,
                    measurement_number=i + 1,
                    thickness_left=Decimal(str(base_thickness_left + left_var)),
                    thickness_right=Decimal(str(base_thickness_right + right_var))
                )
        except Exception as e:
            print(f"      ⚠️ Erreur grille épaisseur: {e}")
    
    def generate_checklist_for_shift(self, shift):
        """Génère des réponses de checklist pour un poste."""
        print(f"    → Création checklist pour {shift.shift_id}")
        
        try:
            # Récupérer les items de checklist existants
            checklist_items = WcmChecklistItem.objects.filter(is_active=True)
            if not checklist_items.exists():
                print("      ⚠️ Aucun item de checklist trouvé")
                return
            
            # Répondre à chaque item avec des réponses cohérentes
            for item in checklist_items:
                # 95% de chance d'être OK, 5% NOK
                response = "OK" if random.random() > 0.05 else "NOK"
                
                ChecklistResponse.objects.create(
                    shift=shift,
                    checklist_item=item,
                    response=response,
                    comment=random.choice([
                        "", "", "",  # Plus de chances d'être vide
                        "RAS",
                        "Vérifié",
                        "Conforme",
                        "Ajustement mineur effectué" if response == "NOK" else ""
                    ])
                )
        except Exception as e:
            print(f"      ⚠️ Erreur checklist: {e}")
    
    def generate_trs_for_shift(self, shift, rolls):
        """Génère les données TRS pour un poste."""
        print(f"    → Création TRS pour {shift.shift_id}")
        
        try:
            # Calculer les longueurs depuis les rouleaux
            total_length = sum(float(r.length) for r in rolls)
            ok_length = sum(float(r.length) for r in rolls if r.status == 'CONFORME')
            nok_length = total_length - ok_length
            
            # Générer quelques temps perdus
            lost_time_minutes = random.randint(15, 90)
            
            trs = TRS.objects.create(
                shift=shift,
                total_length=Decimal(str(total_length)),
                ok_length=Decimal(str(ok_length)),
                nok_length=Decimal(str(nok_length)),
                raw_waste_length=Decimal(str(random.uniform(10, 30))),
                lost_time_minutes=lost_time_minutes
            )
            
            # Générer quelques entrées de temps perdus
            self.generate_downtime_entries(shift, lost_time_minutes)
            
        except Exception as e:
            print(f"      ⚠️ Erreur TRS: {e}")
    
    def generate_downtime_entries(self, shift, total_minutes):
        """Génère des entrées de temps perdus."""
        try:
            # Types de temps perdus courants
            downtime_types = [
                "Changement bobine",
                "Nettoyage ligne",
                "Micro-arrêt",
                "Réglage tension",
                "Contrôle qualité",
                "Maintenance préventive"
            ]
            
            # Créer 1 à 4 entrées
            num_entries = random.randint(1, 4)
            remaining_minutes = total_minutes
            
            for i in range(num_entries):
                if remaining_minutes <= 0:
                    break
                    
                # Répartir le temps
                if i == num_entries - 1:
                    duration = remaining_minutes
                else:
                    duration = random.randint(5, min(30, remaining_minutes - 5))
                
                LostTimeEntry.objects.create(
                    shift=shift,
                    reason=random.choice(downtime_types),
                    duration_minutes=duration,
                    description=random.choice([
                        "", "RAS", "Intervention rapide", "Réglage standard"
                    ])
                )
                
                remaining_minutes -= duration
                
        except Exception as e:
            print(f"      ⚠️ Erreur temps perdus: {e}")
    
    def generate_mood_counter_for_shift(self, shift):
        """Génère un compteur d'humeur pour le poste."""
        try:
            # 70% chance d'avoir une humeur positive
            mood = random.choice([
                '😊', '😊', '😊',  # 3 chances sur 7 pour content
                '😐', '😐',       # 2 chances sur 7 pour neutre  
                '😞', '😟'        # 2 chances sur 7 pour pas content
            ])
            
            MoodCounter.objects.create(
                shift=shift,
                operator=shift.operator,
                mood=mood,
                comment=random.choice([
                    "", "", "",  # Plus de chances d'être vide
                    "Bonne journée",
                    "RAS", 
                    "Petit souci technique résolu",
                    "Équipe au top"
                ])
            )
        except Exception as e:
            print(f"      ⚠️ Erreur humeur: {e}")
    
    def get_start_time(self, vacation):
        """Retourne l'heure de début selon la vacation."""
        times = {
            'Matin': time(6, 0),
            'ApresMidi': time(14, 0),
            'Nuit': time(22, 0),
            'Journee': time(8, 0)
        }
        return times.get(vacation, time(8, 0))
    
    def get_end_time(self, vacation):
        """Retourne l'heure de fin selon la vacation."""
        times = {
            'Matin': time(14, 0),
            'ApresMidi': time(22, 0),
            'Nuit': time(6, 0),
            'Journee': time(18, 0)
        }
        return times.get(vacation, time(18, 0))
    
    def get_checklist_time(self, vacation):
        """Retourne une heure de signature de checklist cohérente."""
        start = self.get_start_time(vacation)
        # Signature entre 30 min et 2h après le début
        minutes_offset = random.randint(30, 120)
        return (datetime.combine(datetime.today(), start) + timedelta(minutes=minutes_offset)).time()
    
    def generate_data(self, days_back=7, shifts_per_day=3):
        """Génère des données pour les N derniers jours."""
        print(f"🎲 Génération de données fake pour {days_back} jours...")
        
        self.setup_base_data()
        
        vacations = ['Matin', 'ApresMidi', 'Nuit']
        total_shifts = 0
        total_rolls = 0
        
        for day_offset in range(days_back):
            date = (timezone.now().date() - timedelta(days=day_offset))
            print(f"\n📅 Génération pour le {date.strftime('%d/%m/%Y')}:")
            
            day_shifts = min(shifts_per_day, len(self.operators))
            selected_operators = random.sample(self.operators, day_shifts)
            
            for i, operator in enumerate(selected_operators):
                vacation = vacations[i % len(vacations)]
                
                # Éviter les doublons
                existing = Shift.objects.filter(
                    date=date,
                    operator=operator,
                    vacation=vacation
                ).exists()
                
                if not existing:
                    shift = self.generate_shift(date, vacation, operator)
                    rolls = self.generate_rolls_for_shift(shift)
                    
                    # Générer l'écosystème complet pour le poste
                    self.generate_quality_controls_for_shift(shift, rolls)
                    self.generate_checklist_for_shift(shift)
                    self.generate_trs_for_shift(shift, rolls)
                    self.generate_mood_counter_for_shift(shift)
                    
                    total_shifts += 1
                    total_rolls += len(rolls)
        
        print(f"\n✅ Génération terminée:")
        print(f"   • {total_shifts} postes créés")
        print(f"   • {total_rolls} rouleaux créés")
        print(f"   • {Roll.objects.conforming().count()} rouleaux conformes au total")
    
    def clear_fake_data(self):
        """Efface toutes les données fake."""
        print("🧹 Suppression des données fake...")
        
        rolls_count = Roll.objects.count()
        shifts_count = Shift.objects.count()
        
        Roll.objects.all().delete()
        Shift.objects.all().delete()
        
        # Garder les opérateurs et OF pour éviter les erreurs de contraintes
        # Operator.objects.filter(employee_id__endswith='DUPONT').delete()
        # FabricationOrder.objects.filter(order_number__startswith='32').delete()
        
        print(f"   ✓ {rolls_count} rouleaux supprimés")
        print(f"   ✓ {shifts_count} postes supprimés")

def main():
    """Fonction principale."""
    generator = FakeDataGenerator()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--clear':
        generator.clear_fake_data()
        return
    
    # Paramètres par défaut
    days_back = 10
    shifts_per_day = 4
    
    # Lecture des paramètres
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except ValueError:
            print("Erreur: Le nombre de jours doit être un entier")
            return
    
    if len(sys.argv) > 2:
        try:
            shifts_per_day = int(sys.argv[2])
        except ValueError:
            print("Erreur: Le nombre de postes par jour doit être un entier")
            return
    
    generator.generate_data(days_back, shifts_per_day)

if __name__ == '__main__':
    print("=" * 60)
    print("🏭 GÉNÉRATEUR DE DONNÉES FAKE SGQ LIGNE G")
    print("=" * 60)
    print()
    print("Usage:")
    print("  python generate_fake_data.py [jours] [postes_par_jour]")
    print("  python generate_fake_data.py --clear  # Supprime les données")
    print()
    print("Exemples:")
    print("  python generate_fake_data.py 7 3     # 7 jours, 3 postes/jour")
    print("  python generate_fake_data.py 14      # 14 jours, 4 postes/jour")
    print("  python generate_fake_data.py         # 10 jours, 4 postes/jour")
    print()
    
    main()