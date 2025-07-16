# Code Legacy à Supprimer - Migration DRF

## Vue d'ensemble
Ce document liste tout le code legacy qui doit être supprimé suite à la migration vers l'API DRF unifiée. Chaque section doit être vérifiée avant suppression pour s'assurer qu'aucune fonctionnalité n'est perdue.

## 1. Endpoints à supprimer dans `production/urls.py`

### ❌ À SUPPRIMER
```python
# Anciens endpoints de sauvegarde
path('auto-save-form/', views.auto_save_form, name='auto_save_form'),
path('get-saved-data/', views.get_saved_form_data, name='get_saved_form_data'),
path('clear-saved-data/', views.clear_saved_form_data, name='clear_saved_form_data'),
path('save-quality-controls/', views.save_quality_controls, name='save_quality_controls'),
```

### ✅ À GARDER (utilisés ailleurs)
```python
# Endpoints de lecture seule et utilitaires
path('get-previous-shift/', views.get_previous_shift, name='get_previous_shift'),
path('get-last-meter-reading/', views.get_last_meter_reading, name='get_last_meter_reading'),
path('get-total-rolled-length/', views.get_total_rolled_length, name='get_total_rolled_length'),
path('check-roll-id/', views.check_roll_id, name='check_roll_id'),
path('check-shift-exists/', views.check_shift_exists, name='check_shift_exists'),
path('operator/create/', views.operator_create, name='operator_create'),
path('roll/save/', views.save_roll, name='save_roll'),  # À migrer vers DRF plus tard
path('profile/<int:profile_id>/parameters/', views.get_profile_parameters, name='get_profile_parameters'),
```

## 2. Vues à supprimer dans `production/views.py`

### ❌ Functions complètes à supprimer
```python
def auto_save_form(request):  # Lignes ~792-831
def save_quality_controls(request):  # Lignes ~833-839
def get_saved_form_data(request):  # Lignes ~841-856
def clear_saved_form_data(request):  # Lignes ~858-880
```

## 3. Modèles obsolètes dans `livesession/models.py`

### ❌ À SUPPRIMER (avec migration)
```python
class CurrentProductionState(models.Model):  # Lignes 7-45
    # Remplacé par CurrentSession.session_data

class LiveQualityControl(models.Model):  # Lignes 199-235
    # Données maintenant dans CurrentSession.session_data.quality_controls
```

### ⚠️ À VÉRIFIER
```python
class LiveRoll(models.Model):  # Lignes 152-194
    # Peut-être encore utilisé ? Vérifier si on peut migrer vers current_roll dans session_data
```

## 4. JavaScript à supprimer dans `production.html`

### ❌ Anciennes fonctions de sauvegarde
```javascript
// Supprimer ces appels directs aux anciens endpoints
function autoSaveFormData() {
    // Ancienne implémentation avec fetch('/production/auto-save-form/')
}

function restoreSavedData() {
    // Si elle utilise encore l'ancien endpoint
}

function clearAllSavedData() {
    // Si elle utilise encore fetch('/production/clear-saved-data/')
}

// Fonctions de contrôles qualité obsolètes
function loadQualityControls() { }  // Supprimée
function saveQualityControl() { }   // Supprimée
function updateQualityAverages() { } // Supprimée
```

### ❌ Appels aux anciens endpoints
Rechercher et remplacer tous les:
```javascript
fetch('/production/auto-save-form/')
fetch('/production/get-saved-data/')
fetch('/production/clear-saved-data/')
fetch('/production/save-quality-controls/')
fetch('/livesession/save-active-roll/')  // Si existe encore
```

Par:
```javascript
updateFieldViaAPI(fieldName, value)
```

## 5. Templates à nettoyer

### `shift_block.html`
- Supprimer les anciens attributs `hx-post` vers les endpoints legacy
- Vérifier que tous les inputs utilisent les bons event handlers

### `production.html`
- Nettoyer les commentaires de code désactivé
- Supprimer les fonctions JavaScript commentées

## 6. Fichiers potentiellement obsolètes

### À vérifier si encore utilisés
- `/static/js/shift-api.js` - Probablement obsolète si utilise anciens endpoints
- `/livesession/static/js/shift-drf.js` - Vérifier s'il duplique du code
- Tous les fichiers de test liés aux anciens endpoints

## 7. Code dupliqué à factoriser

### Calculs de métriques
- `production/views.py` contient des calculs qui devraient être dans `livesession/services.py`
- Centraliser tous les calculs dans `MetricsCalculator` et `ShiftMetricsService`

### Validation
- Déplacer toute la validation métier des vues vers les serializers/modèles
- Utiliser les validators Django REST Framework

## 8. Imports inutilisés

Après suppression, nettoyer les imports dans:
- `production/views.py`
- `production/urls.py`
- `livesession/models.py`

## 9. Migrations à créer

```bash
# Après suppression des modèles obsolètes
python manage.py makemigrations livesession -n remove_obsolete_models
```

## 10. Tests à mettre à jour

Tous les tests qui utilisent les anciens endpoints doivent être réécrits pour utiliser l'API DRF unifiée.

## Ordre de suppression recommandé

1. **Phase 1** : Vérifier que tout fonctionne avec DRF
   - Tester toutes les fonctionnalités
   - Vérifier les logs pour les appels aux anciens endpoints

2. **Phase 2** : Supprimer le JavaScript obsolète
   - Commencer par les fonctions non utilisées
   - Mettre à jour les appels restants

3. **Phase 3** : Supprimer les vues Python
   - D'abord les vues de sauvegarde
   - Puis les URLs correspondantes

4. **Phase 4** : Nettoyer les modèles
   - Créer les migrations
   - Supprimer les modèles obsolètes

5. **Phase 5** : Optimisation finale
   - Factoriser le code dupliqué
   - Nettoyer les imports
   - Mettre à jour la documentation

## Checklist avant suppression

Pour chaque élément à supprimer:
- [ ] Vérifier qu'il n'est plus appelé nulle part
- [ ] S'assurer que la fonctionnalité est migrée vers DRF
- [ ] Tester la fonctionnalité après suppression
- [ ] Mettre à jour les tests associés
- [ ] Documenter le changement

## Notes importantes

⚠️ **ATTENTION** : Ne PAS supprimer:
- Les endpoints de lecture (`get-previous-shift`, etc.)
- Les fonctions utilitaires qui ne font pas de sauvegarde
- Le modèle `CurrentSession` (c'est le nouveau modèle DRF)
- La fonction `updateFieldViaAPI()` (c'est la nouvelle façon de faire)

✅ **Bénéfices après nettoyage**:
- Code plus maintenable
- Une seule source de vérité (DRF)
- Performance améliorée (moins d'appels)
- Architecture plus claire