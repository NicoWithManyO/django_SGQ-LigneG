# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Vue d'ensemble

SGQ Ligne G est un système de gestion de production pour l'industrie fibre optique.

**Stack technique :**
- Backend : Django 5.2.4 + Django REST Framework
- Frontend : Alpine.js 3.x + Bootstrap 5.3
- Base de données : SQLite (dev), PostgreSQL (prod)
- Export : openpyxl pour les fichiers Excel

## Convention linguistique

- **Communication en français** avec Claude
- Code en anglais, commentaires en français
- UI et documentation en français

## Installation et setup

```bash
# Installation dépendances
pip install -r requirements.txt

# Configuration base de données
python manage.py migrate

# Charger données initiales obligatoires
python manage.py load_initial_data

# Créer superutilisateur (optionnel)
python manage.py createsuperuser
```

## Commandes essentielles

```bash
# Serveur développement
python manage.py runserver

# Migrations base de données
python manage.py makemigrations
python manage.py migrate

# Charger données initiales (types défauts, profils, spécifications, etc.)
python manage.py load_initial_data
# Options : --clear, --only models, --skip models, --dry-run

# Tests
python manage.py test
python manage.py test catalog --parallel

# Admin Django
# URL: http://localhost:8000/admin/
```

## Architecture du projet

### Applications Django

- **catalog/** : Données de référence (profils, spécifications, défauts)
- **production/** : Shifts et rouleaux, cœur de la production
- **quality/** : Contrôle qualité et enregistrement défauts
- **planification/** : Gestion opérateurs et OF
- **wcm/** : Modèles WCM (TRS, humeur équipe, temps perdus)
- **frontendv3/** : Interface utilisateur V3 (Alpine.js)
- **management/** : Dashboard supervision
- **exporting/** : Export Excel des données
- **_archived/** : Anciennes versions (V1/V2) - ne plus utiliser

### Frontend V3 (en développement actif)

```
frontendv3/
├── static/frontendv3/
│   ├── css/
│   │   ├── main.css         # Styles globaux avec dégradé Saint-Gobain
│   │   ├── manyo-logo.css   # Styles du logo manyO.dev
│   │   └── pages/
│   │       └── splash.css   # Styles de l'écran d'accueil
│   ├── js/components/       # Composants Alpine.js
│   │   ├── shift-form.js    # Gestion du poste
│   │   ├── production-order.js  # Sélection OF
│   │   ├── profile-selector.js  # Sélection profil produit
│   │   ├── roll-grid.js     # Grille épaisseurs
│   │   ├── sticky-bar.js    # Barre fixe infos rouleau
│   │   ├── quality-control.js   # Contrôles qualité
│   │   ├── checklist.js     # Check-list prise poste
│   │   ├── downtime-tracker.js  # Gestion temps perdus
│   │   ├── confirm-modal.js # Modal de confirmation réutilisable
│   │   └── kpi-display.js   # Affichage des KPI temps réel
│   ├── js/services/         # Services métier
│   │   ├── event-bus.js     # Event bus centralisé pour communication
│   │   ├── kpi-service.js   # Calculs KPI (Dispo, Perf, Qualité, TRS)
│   │   ├── cache-service.js # Service de cache pour performances
│   │   └── validation-service.js # Validation centralisée
│   ├── js/mixins/
│   │   ├── session-mixin.js # Mixin réutilisable pour gestion session
│   │   └── watcher-mixin.js # Mixin pour observation de données
│   └── js/utils/
│       ├── session.js       # Gestion session Django
│       ├── collapsible.js   # Mixin cards enroulables
│       └── modal-builders.js # Builders pour contenus modales
```

### Patterns de développement

#### Persistence automatique avec mixin
```javascript
function myComponent() {
    return {
        ...window.sessionMixin,
        
        fieldName: '',
        
        init() {
            this.initSession();
            // Auto-save avec debounce 300ms intégré
            this.watchAndSave('fieldName');
        }
    }
}
```

#### Communication entre composants
```javascript
// Via event bus centralisé (recommandé)
window.eventBus.emit('of:changed', { ofNumber: '3249' });
window.eventBus.on('of:changed', (data) => {
    this.ofNumber = data.ofNumber;
});

// Via événements natifs (legacy)
window.dispatchEvent(new CustomEvent('of-changed', { 
    detail: { ofNumber: '3249' }
}));
window.addEventListener('of-changed', (e) => {
    this.ofNumber = e.detail.ofNumber;
});
```

### IDs métier (formats stricts)
```python
employee_id = "FirstnameLASTNAME"              # Ex: "MartinDUPONT"
shift_id = "DDMMYY_FirstnameName_Shift"        # Ex: "220725_MartinDupont_Matin"
roll_id = "OF_RollNumber"                      # Ex: "3249_001"
roll_id_non_conforme = "9999_JJMMAA_HHMM"      # Ex: "9999_040825_1423"
```

## Modèles de données principaux

- **Shift** : Poste de production avec opérateur et vacation
- **Roll** : Rouleau avec toutes ses mesures et défauts
- **ProfileTemplate** : Profils produits avec limites min/max
- **QualityDefectType** : Types de défauts (13 catégories)
- **SpecItem/ParamItem** : Spécifications et paramètres machine

## API Endpoints V3

Base : `/`
- `/api/session/` : Gestion session persistence
- `/api/defect-types/` : Types de défauts disponibles
- `/api/profiles/` : Profils produits
- `/api/current-profile/` : Profil actif
- `/production/api/rolls/` : Création et gestion des rouleaux
- `/production/api/shifts/` : Création et gestion des postes

## État actuel et priorités

### Implémenté ✅
- Interface V3 complète avec tous les composants
- Persistence session pour tous les champs
- Contrôle qualité avec calculs automatiques
- Sticky bar avec synchronisation OF
- Modal de confirmation pour save poste
- Nettoyage session après save (temps perdus)
- Check-list qualité fonctionnelle
- Sauvegarde complète des rouleaux avec gestion session
- Gestion automatique conformité (CONFORME vs NON_CONFORME → découpe)
- Validation et tooltips dynamiques sur bouton sauvegarde rouleau
- Splash screen avec sélection opérateur animée
- Gestion temps perdus complète
- Session mixin pour éviter duplication code
- Calculs grammage automatiques
- Gestion masses et épaisseurs avec validation
- Calculs KPI temps réel (Disponibilité, Performance, Qualité, TRS)
- Service KPI centralisé avec architecture event-driven
- Prise en compte longueurs début/fin de poste dans les calculs

### À faire (priorité haute)
- Tests unitaires et d'intégration
- Export Excel des données de production
- Mode hors-ligne pour résilience

### Points d'attention
- **Ne pas mélanger V1/V2/V3** - Seul V3 est actif
- **Session Django** est le stockage principal (pas de state management complexe)
- **Formats d'ID** sont business critiques - ne jamais modifier
- **Auto-save** doit être testé pour chaque nouveau champ
- **OF 9999** est l'OF de découpe par défaut

## URLs principales

- `/production-v3/` - Interface production V3
- `/admin/` - Django admin
- `/admin/sessions/session/` - Debug des sessions (voir données V3)
- `/management/` - Dashboard superviseur

## Base de données

SQLite en développement. Pour reset complet :
```bash
rm db.sqlite3
python manage.py migrate
python manage.py load_initial_data
```

## Debugging

- Session persistence : vérifier Network > api/session/ PATCH
- Events JS : `window.addEventListener` dans console
- Django admin pour vérifier données sauvées
- `print()` statements apparaissent dans terminal runserver
- Session mixin : vérifier `this._saveTimeouts` pour debug debounce