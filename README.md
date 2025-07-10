# SGQ Ligne G - Système de Gestion de Production

[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![HTMX](https://img.shields.io/badge/HTMX-2.0-orange.svg)](https://htmx.org/)

Système de gestion de production de feutre pour **Saint-Gobain Quartz SAS - Nemours**, conforme aux exigences **ISO 9001**, **ISO 14001** et **ISO 45001**.

## 🎯 Fonctionnalités Principales

### 📋 Gestion des Postes de Production
- **Fiche de Poste** : Gestion complète des shifts (opérateur, vacation, horaires début/fin)
- **Création Rapide** : Boutons "+" discrets pour ajouter opérateurs et OF via modales
- **Continuité Machine** : Report automatique des états machine entre postes
- **Validation** : Contrôles obligatoires avant sauvegarde
- **Traçabilité** : ID unique dynamique `JJMMAA_PrenomNom_Vacation`

### 🏭 Suivi de Production
- **Ordres de Fabrication (OF)** : Gestion avec statut terminé/actif
- **Rouleaux** : Suivi complet avec ID automatique `OF_NumRouleau` (format 3 chiffres : `3254_001`)
- **Paramètres Machine** : Métrages début/fin, états machine
- **Temps de Production** : Calcul automatique disponible/perdu

### ⏱️ Gestion du Temps
- **Déclaration Temps Perdu** : Motifs, durées, calculs automatiques
- **Temps Disponible** : Calcul en temps réel (ouverture - temps perdu)
- **Validation** : Contrôle cohérence temps démarrage machine

### 💾 Sauvegarde Intelligente
- **Auto-Save** : Sauvegarde continue de toutes les données saisies
- **Persistance Session** : Restauration automatique après rechargement
- **Données Préservées** : Maintien OF/rouleau après save de poste
- **Rouleaux Sans Poste** : Possibilité de sauvegarder des rouleaux avant le poste (liaison automatique ultérieure)

## 🏗️ Architecture Technique

### Structure des Applications Django
```
├── core/           # Modèles partagés (Operator, FabricationOrder)
├── production/     # Gestion des postes et production
├── quality/        # Contrôles qualité (DefectType, RollDefect, ThicknessMeasurement)
└── reports/        # Génération documents Excel (à venir)
```

### Technologies Utilisées
- **Backend** : Django 5.2, Python 3.11+
- **Frontend** : Bootstrap 5.3, HTMX 2.0
- **Base de données** : SQLite (développement)
- **Styling** : CSS custom avec variables CSS

### Modèles de Données Clés

#### Shift (Poste)
```python
- shift_id: str       # Auto-généré JJMMAA_PrenomNom_Vacation
- date: date          # Date du poste
- operator: FK        # Opérateur responsable
- vacation: str       # Matin/ApresMidi/Nuit/Journée
- start_time: time    # Heure de début du poste
- end_time: time      # Heure de fin du poste
- opening_time: property # Durée calculée (end_time - start_time)
- started_at_*: bool  # États machine début/fin
- meter_reading_*: int # Métrages début/fin
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

## 🎨 Interface Utilisateur

### Design System
- **Couleurs** : Palette Saint-Gobain avec variables CSS
- **Layout** : Grid responsive Bootstrap avec sidebar fixe
- **Composants** : Cards modulaires avec headers bleus
- **UX** : Champs disabled avec boutons d'édition + confirmation

### Blocs Principaux
1. **Fiche de Poste** (sidebar gauche) - Layout 3 colonnes avec durée calculée
2. **Ordre de Fabrication & Fibrage** (top-right) - Bouton création OF intégré
3. **Déclaration de Temps** (bottom-right) - Affichage conditionnel selon état machine

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
- [x] Auto-save et restauration données
- [x] Gestion OF avec statuts
- [x] Interface responsive et intuitive
- [x] Module Qualité : modèles DefectType, RollDefect, ThicknessMeasurement
- [x] Interface admin pour gestion des types de défauts
- [x] Visualisation rouleau avec champs défauts intégrés
- [x] Sélection défauts depuis datalists
- [x] Boutons d'effacement rapide des défauts
- [x] Création rapide opérateurs et OF via modales
- [x] Calcul automatique durée postes (support minuit)
- [x] Vacation "Journée" avec horaires par défaut
- [x] Sauvegarde rouleaux indépendante du poste
- [x] Formatage automatique numéros rouleaux (001, 020, 100)
- [x] Détection rouleaux existants avec indicateur visuel

### Phase 2 (À venir)
- [ ] Intégration complète mesures d'épaisseur
- [ ] Contrôles qualité par poste
- [ ] Alertes dépassement seuils
- [ ] Validation automatique des tolérances

### Phase 3 (Future)
- [ ] Génération documents Excel
- [ ] Certificats de conformité
- [ ] Rapports de production
- [ ] API REST pour intégrations

## 📞 Support

**Client** : Saint-Gobain Quartz SAS - Nemours 77140  
**Conformité** : ISO 9001, ISO 14001, ISO 45001  
**Support** : [Créer une issue](https://github.com/votre-repo/django_SGQ-LigneG/issues)

---

*Développé avec ❤️ pour l'industrie textile française*
