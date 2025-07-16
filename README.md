refacto

# SGQ Ligne G - Système de Gestion de Production

[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![HTMX](https://img.shields.io/badge/HTMX-2.0-orange.svg)](https://htmx.org/)

Système de gestion de production de feutre pour **Saint-Gobain Quartz SAS - Nemours**, conforme aux exigences **ISO 9001**, **ISO 14001** et **ISO 45001**.

## 🎯 Fonctionnalités Principales

### 📋 Gestion des Postes de Production
- **Fiche de Poste** : Gestion complète des shifts (opérateur, vacation, horaires début/fin)
- **Création Rapide** : Boutons "+" pour opérateurs (endpoints à implémenter)
- **Continuité Machine** : Report automatique des états machine entre postes
- **Validation** : Contrôles obligatoires avant sauvegarde avec info-bulles dynamiques
- **Traçabilité** : ID unique dynamique `JJMMAA_PrenomNom_Vacation`

### 🏭 Suivi de Production
- **Ordres de Fabrication (OF)** : Gestion avec statut terminé/actif
- **Rouleaux** : Suivi complet avec ID automatique `OF_NumRouleau` (format 3 chiffres : `3254_001`)
- **Paramètres Machine** : Profils de configuration machine (débits, vitesses)
- **Temps de Production** : Calcul automatique disponible/perdu
- **Productivité** : Tableau de bord avec métriques temps réel (Temps, Production, Qualité)
- **Check-list** : Contrôles de fin de poste avec boutons 3 états (N/A, OK, NOK)

### ⏱️ Gestion du Temps
- **Déclaration Temps Perdu** : Motifs, durées, calculs automatiques
- **Temps Disponible** : Calcul en temps réel (ouverture - temps perdu)
- **Validation** : Contrôle cohérence temps démarrage machine

### 💾 Sauvegarde Intelligente
- **Auto-Save** : Sauvegarde continue de toutes les données saisies (y compris date)
- **Persistance Session** : Restauration automatique après rechargement
- **Données Préservées** : Maintien OF/rouleau après save de poste
- **Rouleaux Sans Poste** : Possibilité de sauvegarder des rouleaux avant le poste (liaison automatique ultérieure)
- **Protection Données** : Rouleaux préservés lors de la suppression d'un poste

## 🏗️ Architecture Technique

### Structure des Applications Django
```
├── core/           # Modèles partagés (Operator, FabricationOrder, Profile, Mode, MoodCounter)
├── production/     # Gestion des postes et production (Shift, Roll, QualityControl, LostTimeEntry, MachineParameters)
├── quality/        # Contrôles qualité (DefectType, Specification, RollDefect, RollThickness)
├── livesession/    # Gestion de session avec DRF (API unifiée, CurrentSession)
├── wcm/            # Work Checklist Management (ChecklistTemplate, ChecklistItem, ChecklistResponse, LostTimeReason, MachineParametersHistory)
├── frontend/       # Templates et composants UI (blocks, components, modals)
└── reports/        # Génération documents Excel (à venir)
```

### Technologies Utilisées
- **Backend** : Django 5.2, Python 3.11+, Django REST Framework
- **Frontend** : Bootstrap 5.3, HTMX 2.0, JavaScript vanilla
- **Base de données** : SQLite (développement), PostgreSQL (production recommandé)
- **API** : DRF avec endpoint unifié `/livesession/api/current-session/`
- **Styling** : CSS custom avec variables CSS

### Modèles de Données Clés

#### Shift (Poste)
```python
- shift_id: str       # Auto-généré JJMMAA_PrenomNom_Vacation
- date: date          # Date du poste
- operator: FK        # Opérateur responsable (SET_NULL si supprimé)
- vacation: str       # Matin/ApresMidi/Nuit/Journée
- start_time: time    # Heure de début du poste
- end_time: time      # Heure de fin du poste
- opening_time: property # Durée calculée (end_time - start_time)
- available_time: property # TO - TP (calculé automatiquement)
- started_at_*: bool  # États machine début/fin
- meter_reading_*: int # Métrages début/fin
- signature: str      # Signature check-list
- signature_time: datetime # Heure de signature
```

#### CurrentProd (Auto-Save)
```python
- session_key: str    # Clé de session utilisateur
- form_data: JSON     # Toutes les données du formulaire
- updated_at: datetime # Dernière modification
```

#### FabricationOrder (OF)
```python
- order_number: str   # Numéro OF unique
- required_length: decimal    # Longueur totale (0 = illimité)
- target_roll_length: decimal # Longueur par rouleau (0 = illimité)
- for_cutting: bool   # Destiné découpe
- terminated: bool    # OF terminé (masqué des listes)
```

#### Roll (Rouleau)
```python
- roll_id: str        # Auto-généré OF_NumRouleau
- fabrication_order: FK # Ordre de fabrication
- shift: FK           # Poste (nullable, SET_NULL si supprimé)
- length: decimal     # Longueur du rouleau
- tube_mass: decimal  # Masse du tube
- total_mass: decimal # Masse totale
- net_mass: decimal   # Masse nette (auto-calculée)
- avg_thickness_left: decimal  # Moyenne épaisseur gauche (auto-calculée)
- avg_thickness_right: decimal # Moyenne épaisseur droite (auto-calculée)
- status: str         # CONFORME/NON_CONFORME
- destination: str    # PRODUCTION/DECOUPE/DECHETS
```

#### MachineParameters (Paramètres Machine)
```python
- name: str           # Nom du profil
- oxygen_primary: decimal     # Débit oxygène primaire
- oxygen_secondary: decimal   # Débit oxygène secondaire
- propane_primary: decimal    # Débit propane primaire
- propane_secondary: decimal  # Débit propane secondaire
- speed_primary: decimal      # Vitesse primaire
- speed_secondary: decimal    # Vitesse secondaire
- belt_speed: decimal         # Vitesse tapis (m/h)
- belt_speed_m_per_minute: property # Conversion m/min
```

## 🎨 Interface Utilisateur

### Design System
- **Couleurs** : Palette Saint-Gobain avec variables CSS
- **Layout** : Grid responsive Bootstrap avec sidebar fixe
- **Composants** : Cards modulaires avec headers bleus
- **UX** : Champs disabled avec boutons d'édition + confirmation

### Blocs Principaux
1. **Fiche de Poste** (sidebar gauche) - Layout 3 colonnes avec durée calculée
2. **Ordre de Fabrication & Fibrage** (top) - Bouton création OF intégré
3. **Productivité & Déclaration de Temps** (colonne gauche) - Disposés verticalement
   - Productivité : 3 onglets (Temps, Production, Qualité) avec métriques 3×2
   - Déclaration de temps : Affichage conditionnel avec total calculé
4. **Check-list** (colonne droite) - 6 points de contrôle avec boutons 3 états
5. **Sticky Bar** (bas fixe) - Actions rouleau avec boutons save/cut/waste

### Conventions UX
- **Champs vides** : Affichage cohérent `--`
- **Édition** : Clic crayon → activation → confirmation
- **Création Rapide** : Boutons "+" avec transparence hover (opérateurs, OF)
- **Validation** : Messages d'erreur clairs en français
- **Auto-save** : Indicateurs visuels de sauvegarde

## 🔧 Installation & Déploiement

### Prérequis
```bash
Python 3.11+
Django 5.2
```

### Installation
```bash
git clone https://github.com/votre-repo/django_SGQ-LigneG.git
cd django_SGQ-LigneG/Codebase
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Configuration
- **DEBUG** : `False` en production
- **ALLOWED_HOSTS** : Configurer selon environnement
- **DATABASE** : PostgreSQL recommandé en production

## 📝 Conventions de Développement

### Nommage
- **Modèles** : PascalCase anglais (`FabricationOrder`)
- **Champs** : snake_case anglais (`created_at`)
- **Variables** : snake_case anglais (`current_roll`)
- **Templates** : snake_case anglais (`shift_form.html`)
- **URLs** : kebab-case anglais (`/fabrication-orders/`)

### Code Style
- **Python** : PEP 8 strict, Black formatter (88 chars)
- **JavaScript** : camelCase, fonctions françaises si métier
- **CSS** : BEM methodology, variables CSS
- **Commentaires** : Français uniquement

### Business Rules
- **ID Postes** : `JJMMAA_PrenomNom_Vacation`
- **ID Rouleaux** : `OFNumber_NumeroRouleau`
- **Vacations** : Matin (4h-12h), ApresMidi (12h-20h), Nuit (20h-4h), Journée (7h30-15h30)
- **Unités** : mètres (m), grammes (g), minutes (min)
- **Statuts** : Anglais technique (`active`, `terminated`)

## 🛡️ Conformité & Qualité

### Standards Respectés
- **ISO 9001** : Système Management Qualité
- **ISO 14001** : Management Environnemental  
- **ISO 45001** : Santé Sécurité au Travail
- **SMI Saint-Gobain** : Standards intégrés

### Traçabilité
- **Complète** : Chaque action tracée avec timestamps
- **Identifiants uniques** : Postes et rouleaux
- **Audit Trail** : Historique modifications
- **Documentation** : Conforme standards industriels

## 🚀 Roadmap

### Phase 1 (Actuelle) ✅
- [x] Gestion des postes de production avec horaires début/fin
- [x] Auto-save et restauration données (incluant champs date)
- [x] Gestion OF avec statuts
- [x] Interface responsive et intuitive
- [x] Module Qualité : modèles DefectType, RollDefect, ThicknessMeasurement
- [x] Interface admin pour gestion des types de défauts
- [x] Visualisation rouleau avec champs défauts intégrés
- [x] Sélection défauts depuis datalists
- [x] Boutons d'effacement rapide des défauts
- [ ] Création rapide opérateurs et OF via modales (interfaces présentes, endpoints manquants)
- [x] Calcul automatique durée postes (support minuit)
- [x] Vacation "Journée" avec horaires par défaut
- [x] Sauvegarde rouleaux indépendante du poste
- [x] Formatage automatique numéros rouleaux (001, 020, 100)
- [x] Détection rouleaux existants avec indicateur visuel
- [x] Protection des rouleaux lors suppression poste (SET_NULL)
- [x] Gestion temps perdus avec calcul automatique TD = TO - TP
- [x] Paramètres machine avec profils configurables
- [x] Tableau de bord productivité avec onglets intégrés
- [x] Check-list fin de poste avec boutons 3 états
- [x] Calcul automatique moyennes épaisseur via signals
- [x] Bouton cut pour forcer découpe rouleaux conformes
- [x] Badge de statut contrôles qualité (Pending/Passed/Failed)
- [x] Vérification conformité contrôles qualité automatique
- [x] Sauvegarde rouleaux en base via API avec confirmation
- [x] Navigation Tab intelligente dans tous les formulaires
- [x] Affichage temps total déclaré dans le header
- [x] Alignement labels spécifications qualité
- [x] Correction code couleur grammage avec bonnes specs
- [x] Modal de confirmation save poste avec métriques et sélecteur humeur
- [x] Modal de confirmation save rouleau avec animations
- [x] Système de comptage d'humeur anonyme (MoodCounter)
- [x] Vérification contrôles qualité requis avant activation bouton Save Poste
- [x] Auto-remplissage created_by dans QualityControl
- [x] Info-bulles dynamiques indiquant les éléments manquants

### Phase 2 (À venir)
- [ ] Restauration endpoints création opérateurs/OF
- [ ] Suppression complète du code legacy
- [ ] Tests automatiques pour l'API DRF
- [ ] Documentation OpenAPI/Swagger

### Phase 3 (Future)
- [ ] Génération documents Excel
- [ ] Certificats de conformité
- [ ] Rapports de production
- [ ] API REST pour intégrations externes
- [ ] Authentification et permissions (actuellement AllowAny)

## 📞 Support
**Conformité** : ISO 9001, ISO 14001, ISO 45001  
**Support** : [Créer une issue](https://github.com/votre-repo/django_SGQ-LigneG/issues)

---

*Développé avec ❤️ pour l'industrie textile française*
