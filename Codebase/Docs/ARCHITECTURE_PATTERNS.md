# Architecture et Patterns de Développement

## Vue d'ensemble

SGQ Ligne G utilise une architecture Django avec Django REST Framework (DRF) pour l'API, HTMX pour les interactions dynamiques, et JavaScript vanilla pour la logique côté client.

## Architecture Backend

### Structure des applications Django

```
Codebase/
├── core/           # Modèles de base (Operator, FabricationOrder, Profile, Mode)
├── production/     # Gestion des shifts et de la production
├── quality/        # Types de défauts et spécifications
├── wcm/           # Work Checklist Management
├── livesession/   # Gestion de l'état de session avec DRF
└── frontend/      # Interface utilisateur et templates
```

### API DRF Unifiée

L'API utilise un endpoint unique pour gérer toute la session :

```
/livesession/api/current-session/
  - GET    : Récupère l'état complet avec métriques calculées
  - PATCH  : Met à jour n'importe quel champ
  - DELETE : Réinitialise après sauvegarde du shift
```

### Modèle de Session

Le modèle `CurrentSession` stocke toutes les données dans un champ JSON `session_data` :

```python
class CurrentSession(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    session_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Architecture Frontend

### Technologies utilisées

- **HTMX** : Pour les interactions dynamiques sans JavaScript complexe
- **JavaScript vanilla** : Pour la logique métier et les calculs
- **Bootstrap 5** : Framework CSS pour le responsive
- **CSS personnalisé** : Respectant la charte Saint-Gobain

### Pattern principal JavaScript

```javascript
// Toutes les mises à jour passent par cette fonction
updateFieldViaAPI(fieldName, value)
  .then(data => {
    // Utiliser les métriques retournées
    updateShiftMetrics(data.metrics);
  });
```

### Fonctions JavaScript clés

1. **updateFieldViaAPI()** : Communication avec l'API DRF
2. **updateShiftMetrics()** : Mise à jour des métriques affichées
3. **autoSaveRollData()** : Sauvegarde automatique des données rouleau
4. **saveQualityControlsToSession()** : Sauvegarde des contrôles qualité

## Patterns de développement

### 1. Ajout d'un nouveau champ

Pour ajouter un nouveau champ de données :

1. **Backend** : Ajouter au serializer `CurrentSessionSerializer`
```python
class CurrentSessionSerializer(serializers.Serializer):
    nouveau_champ = serializers.CharField(required=False)
```

2. **Frontend** : Utiliser `updateFieldViaAPI()`
```javascript
updateFieldViaAPI('nouveau_champ', value);
```

3. **Calculs** : Si nécessaire, ajouter dans `get_metrics()`

### 2. Structure des données imbriquées

Les données complexes utilisent une structure imbriquée :

```javascript
// Exemple avec les données du rouleau
current_roll: {
  info: {
    roll_number: "42",
    tube_mass: "50"
  },
  thickness: {
    measurements: [...],
    rattrapage: [...]
  }
}
```

### 3. Gestion des erreurs

```javascript
updateFieldViaAPI(fieldName, value)
  .then(data => {
    // Succès
  })
  .catch(error => {
    console.error('Erreur:', error);
    showNotification('Erreur de sauvegarde', 'error');
  });
```

### 4. Auto-save avec debounce

```javascript
let saveTimeout;
function autoSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    // Logique de sauvegarde
  }, 1000); // 1 seconde de délai
}
```

## Conventions de nommage

### Python/Django
- **Modèles** : PascalCase en anglais (`QualityControl`)
- **Champs** : snake_case (`meter_reading_start`)
- **Méthodes** : snake_case (`calculate_average()`)
- **Commentaires** : En français

### JavaScript
- **Fonctions** : camelCase (`updateShiftMetrics()`)
- **Variables** : camelCase (`rollNumber`)
- **Constantes** : UPPER_SNAKE_CASE (`API_ENDPOINT`)

### CSS
- **Classes** : kebab-case BEM-like (`.thickness-input`, `.roll-header`)
- **IDs** : camelCase (`#rollDataForm`)
- **Variables CSS** : `--sg-primary-color`

## Performance

### Optimisations appliquées

1. **Un seul appel API au chargement**
2. **Debounce sur les sauvegardes automatiques**
3. **Batch des mises à jour similaires**
4. **Calculs côté serveur pour les métriques**

### Bonnes pratiques

- Éviter les appels API multiples
- Utiliser le cache navigateur pour les ressources statiques
- Minimiser les manipulations DOM
- Préférer les calculs côté serveur

## Sécurité

### Mesures en place

1. **CSRF Protection** : Via meta tag pour HTMX
```html
<meta name="csrf-token" content="{{ csrf_token }}">
```

2. **Validation serveur** : Obligatoire sur tous les inputs
3. **Sanitization** : Des données utilisateur
4. **Permissions** : À implémenter (actuellement AllowAny)

## Tests

### Structure des tests recommandée

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_serializers.py
│   └── test_services.py
├── integration/
│   ├── test_api.py
│   └── test_views.py
└── e2e/
    └── test_workflows.py
```

### Commandes de test

```bash
# Tous les tests
python manage.py test

# Tests d'une app spécifique
python manage.py test livesession

# Tests avec couverture
coverage run --source='.' manage.py test
coverage report
```

## Déploiement

### Checklist de déploiement

1. [ ] Exécuter les tests
2. [ ] Vérifier les migrations
3. [ ] Mettre à jour requirements.txt
4. [ ] Collecter les fichiers statiques
5. [ ] Vérifier les variables d'environnement
6. [ ] Backup de la base de données

### Commandes de déploiement

```bash
# Migrations
python manage.py migrate

# Fichiers statiques
python manage.py collectstatic --noinput

# Vérifications
python manage.py check --deploy
```