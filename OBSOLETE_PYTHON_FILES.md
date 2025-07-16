# Fichiers Python obsolètes à analyser

## 📋 Analyse des fichiers Python à la racine

### 1. **add_missing_specs.py**
**Status**: ❌ OBSOLÈTE  
**Utilité**: Script one-shot pour ajouter des specs manquantes au profil 80gr/m²  
**Dépendances**: quality.models.Specification, core.models.Profile  
**Verdict**: Peut être supprimé, c'était une migration ponctuelle

### 2. **check_machine_params.py**
**Status**: ⚠️ PEUT-ÊTRE UTILE  
**Utilité**: Vérifie et crée des paramètres machine exemples  
**Dépendances**: production.models.MachineParameters  
**Verdict**: À garder si on veut initialiser des données de test

### 3. **check_profiles.py**
**Status**: ❓ À VÉRIFIER  
**Utilité**: Probablement pour vérifier l'état des profils  
**Verdict**: Analyser le contenu pour décider

### 4. **check_shifts.py**
**Status**: ❓ À VÉRIFIER  
**Utilité**: Probablement pour vérifier/debugger les shifts  
**Verdict**: Peut être utile pour le debug

### 5. **check_specs.py**
**Status**: ❓ À VÉRIFIER  
**Utilité**: Vérification des spécifications  
**Verdict**: Analyser le contenu

### 6. **create_checklist_items.py**
**Status**: ✅ ENCORE UTILE  
**Utilité**: Crée les items de checklist par défaut  
**Dépendances**: wcm.models.ChecklistTemplate, ChecklistItem  
**Verdict**: À garder pour initialiser la checklist en production

### 7. **create_superuser.py**
**Status**: ✅ UTILE  
**Utilité**: Script pour créer le superuser initial  
**Verdict**: À garder pour les déploiements

### 8. **test_shift_save.py**
**Status**: ⚠️ TEST MANUEL  
**Utilité**: Test manuel de création de shift  
**Dépendances**: production.models.Shift, core.models.Operator  
**Verdict**: Peut être converti en vrai test unitaire

### 9. **update_checklist_items.py**
**Status**: ❌ PROBABLEMENT OBSOLÈTE  
**Utilité**: Mise à jour ponctuelle de la checklist  
**Verdict**: À vérifier mais probablement one-shot

### 10. **update_machine_params.py**
**Status**: ❌ PROBABLEMENT OBSOLÈTE  
**Utilité**: Mise à jour ponctuelle des paramètres machine  
**Verdict**: À vérifier mais probablement one-shot

### 11. **update_shift_averages.py**
**Status**: ⚠️ MIGRATION  
**Utilité**: Recalcule les moyennes pour les shifts existants  
**Dépendances**: production.models.Shift  
**Verdict**: Script de migration, peut être supprimé après usage

## 📁 Fichiers JavaScript potentiellement obsolètes

### 1. **frontend/static/js/shift-api.js**
**Status**: ❌ PROBABLEMENT OBSOLÈTE  
**Raison**: Utilise probablement les anciens endpoints  
**Vérifier**: Si contient des appels à `/production/auto-save-form/`

### 2. **livesession/static/js/shift-drf.js**
**Status**: ❓ À VÉRIFIER  
**Raison**: Peut dupliquer du code avec production.html  
**Vérifier**: Si le code est déjà intégré dans production.html

## 🗄️ Modèles et migrations obsolètes

### Dans livesession/models.py
- **CurrentProductionState** : Remplacé par CurrentSession
- **LiveQualityControl** : Données dans CurrentSession.session_data
- **LiveRoll** : À vérifier si encore utilisé

### Migrations à analyser
- Les migrations avec "obsolete" dans le nom
- Les migrations de renommage (ex: 0006_rename_liveshift_to_currentsession.py)

## 🎯 Recommandations

### À supprimer immédiatement
1. `add_missing_specs.py` - Migration one-shot terminée
2. `update_checklist_items.py` - Si c'était une mise à jour ponctuelle
3. `update_machine_params.py` - Si c'était une mise à jour ponctuelle

### À convertir en commandes Django
```bash
# Au lieu de scripts standalone, utiliser:
python manage.py create_checklist_items
python manage.py init_machine_params
```

### À convertir en tests
- `test_shift_save.py` → `production/tests/test_models.py`
- `check_*.py` → Tests unitaires appropriés

### À garder (avec documentation)
1. `create_checklist_items.py` - Pour l'initialisation
2. `create_superuser.py` - Pour les déploiements
3. Scripts de vérification utiles pour le debug

## 📝 Plan d'action

1. **Créer un dossier `scripts/`** pour les scripts utiles
   ```
   scripts/
   ├── init/           # Scripts d'initialisation
   ├── migrations/     # Scripts de migration one-shot
   └── debug/          # Scripts de debug/vérification
   ```

2. **Documenter chaque script** conservé avec:
   - But du script
   - Quand l'utiliser
   - Dépendances requises

3. **Supprimer les obsolètes** après backup
   ```bash
   # Créer un backup avant suppression
   mkdir -p obsolete_scripts
   mv add_missing_specs.py obsolete_scripts/
   ```

4. **Intégrer dans Django** les scripts récurrents
   - Commandes de management pour l'initialisation
   - Tests unitaires pour les vérifications