# Code Legacy à Supprimer - SGQ Ligne G

Ce document liste tout le code legacy qui peut être supprimé sans risque suite à la migration vers l'architecture DRF unifiée.

## 1. Modèles Obsolètes

### Dans livesession/models.py

1. **CurrentProductionState** (lignes 7-46)
   - Marqué comme obsolète dans le code
   - Remplacé par CurrentSession.session_data
   - Non utilisé dans l'admin
   - Peut être supprimé après création d'une migration pour supprimer la table

2. **LiveQualityControl** (lignes 156-192)
   - Marqué comme obsolète dans le code
   - Remplacé par CurrentSession.session_data
   - Non utilisé dans l'admin
   - Peut être supprimé après création d'une migration pour supprimer la table

### Dans production/models.py

3. **CurrentProd** (lignes 197-216)
   - Encore utilisé dans production/views.py mais uniquement pour les vues legacy
   - Stocke les données de formulaire temporaires
   - Remplacé par CurrentSession.session_data
   - À supprimer après suppression des vues legacy

## 2. Vues Legacy dans production/views.py

### Vues à supprimer complètement

1. **auto_save_form** (lignes 792-830)
   - Endpoint: /production/auto-save-form/
   - Remplacé par l'API DRF /livesession/api/current-session/
   - Utilise CurrentProd qui est obsolète

2. **save_quality_controls** (lignes 833-839)
   - Déjà désactivée avec message d'erreur
   - Peut être supprimée immédiatement

3. **get_saved_form_data** (lignes 841-855)
   - Endpoint pour récupérer les données sauvegardées
   - Remplacé par GET /livesession/api/current-session/

4. **clear_saved_form_data** (lignes 858-880)
   - Endpoint pour effacer les données
   - Remplacé par DELETE /livesession/api/current-session/

5. **save_roll** (lignes 973-1197)
   - Endpoint pour sauvegarder un rouleau
   - Remplacé par POST /livesession/api/save-roll/
   - Utilise CurrentProd qui est obsolète

6. **check_shift_exists** (lignes 905-971)
   - Vérification de l'existence d'un shift
   - Remplacé par l'API DRF

### Vues qui utilisent CurrentProd (à refactoriser)

7. **shift_block** (lignes 243-721)
   - Utilise CurrentProd pour vérifier les contrôles qualité avant sauvegarde
   - Doit être refactorisé pour utiliser CurrentSession à la place

8. **prod** (lignes 186-241)
   - Vue principale, semble encore utilisée
   - Ne dépend pas de CurrentProd, peut être conservée

### Vues potentiellement encore utilisées (à vérifier)

9. **get_last_meter_reading** (lignes 16-38)
10. **get_previous_shift** (lignes 40-135)
11. **get_profile_parameters** (lignes 137-184)
12. **shift_save_field** (lignes 724-749)
13. **operator_create** (lignes 752-789)
14. **check_roll_id** (lignes 882-902)
15. **get_shift_lost_times** (lignes 1199-1223)
16. **get_previous_shift_meter** (lignes 1225-1266)
17. **get_total_rolled_length** (lignes 1268-1341)

## 3. URLs Commentées

### Dans production/urls.py

Seules 3 URLs sont actives :
- `''` (prod)
- `'profile/<int:profile_id>/parameters/'` (get_profile_parameters)

Toutes les autres sont commentées et doivent être supprimées du fichier.

## 4. Templates Obsolètes

1. **livesession/templates/livesession/test_drf.html**
   - Template de test pour l'API DRF
   - Peut être supprimé

2. **livesession/templates/livesession/partials/shift_metrics.html**
   - À vérifier si encore utilisé

## 5. Code JavaScript Legacy

### Dans frontend/templates/frontend/production.html

1. **autoSaveRollData()** (ligne ~3590)
   - Fonction d'auto-save pour les rouleaux
   - Remplacée par updateFieldViaAPI()
   - Rechercher et supprimer toutes les références

2. **saveStickValue()** (ligne ~2483)
   - Appelle autoSaveRollData()
   - À refactoriser pour utiliser updateFieldViaAPI()

## 6. Imports Non Utilisés

### Dans production/views.py

Après suppression des vues legacy, ces imports deviendront inutiles :
- `HttpResponseClientRedirect` de django_htmx
- Potentiellement d'autres après analyse

## 7. Admin

### Dans production/admin.py

1. **CurrentProdAdmin** (lignes 100-130)
   - Admin pour le modèle CurrentProd obsolète
   - À supprimer avec le modèle

## Plan de Suppression Recommandé

### Phase 1 : Suppression immédiate (sans risque) ✅ COMPLÉTÉ
1. ✅ Supprimer la vue `save_quality_controls` (déjà désactivée)
2. ✅ Supprimer les vues `auto_save_form`, `get_saved_form_data`, `clear_saved_form_data`
3. ✅ Supprimer les vues `check_roll_id`, `check_shift_exists`, `save_roll`
4. ✅ Supprimer la vue `shift_save_field`
5. ✅ Nettoyer les URLs commentées dans `production/urls.py`

### Phase 2 : Migration des dépendances ✅ COMPLÉTÉ
1. ✅ Refactoriser `shift_block` pour utiliser CurrentSession au lieu de CurrentProd
2. ✅ Remplacer tous les appels à `autoSaveRollData()` par `updateFieldViaAPI()`
3. ✅ Vérifier que toutes les fonctionnalités marchent avec l'API DRF

### Phase 3 : Suppression des modèles obsolètes ✅ COMPLÉTÉ
1. ✅ Créer une migration pour supprimer les tables :
   - ✅ `livesession_current_state` (CurrentProductionState)
   - ✅ `livesession_live_quality` (LiveQualityControl)  
   - ✅ `production_currentprod` (CurrentProd)
2. ✅ Supprimer les modèles du code
3. ✅ Supprimer CurrentProdAdmin

### Phase 4 : Nettoyage final ✅ COMPLÉTÉ
1. ✅ Supprimer toutes les vues legacy non utilisées
2. ✅ Nettoyer les imports (HttpResponse, HttpResponseClientRedirect, RollDefect, RollThickness)
3. ✅ Supprimer les templates orphelins (déjà fait)
4. ✅ Faire un audit complet pour s'assurer qu'il ne reste aucune référence

## Notes Importantes

- **TOUJOURS** faire un backup de la base de données avant les migrations
- Tester chaque phase en environnement de développement
- Vérifier que l'API DRF remplace bien toutes les fonctionnalités
- S'assurer qu'aucune fonctionnalité métier n'est perdue

## Commandes Utiles

```bash
# Rechercher les références à un modèle
grep -r "CurrentProd" --include="*.py" --include="*.html" .

# Rechercher les références à une URL
grep -r "auto-save-form" --include="*.py" --include="*.html" --include="*.js" .

# Créer une migration pour supprimer un modèle
python manage.py makemigrations --empty production
# Puis éditer la migration pour ajouter les opérations de suppression
```