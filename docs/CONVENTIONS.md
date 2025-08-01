# Conventions de code

## Langues

- **Code** : Anglais
- **Commentaires** : Français  
- **UI** : Français
- **Documentation** : Français
- **Communication avec Claude** : Français

## Nommage

### JavaScript
```javascript
// Variables et fonctions : camelCase
const targetLength = 100;
function calculateGrammage() {}

// Composants Alpine : camelCase
function shiftForm() {}

// Events : kebab-case
window.dispatchEvent(new CustomEvent('roll-saved'));

// IDs HTML : kebab-case
<div id="shift-form"></div>
```

### Python
```python
# Variables et fonctions : snake_case
target_length = 100
def calculate_grammage():
    pass

# Classes : PascalCase
class ProductionRoll(models.Model):
    pass

# Constantes : UPPER_SNAKE_CASE
MAX_ROLL_LENGTH = 3000
```

### CSS
```css
/* Classes : kebab-case */
.kpi-card {
    /* Propriétés : kebab-case */
    background-color: white;
}

/* IDs : kebab-case */
#shift-form {
    margin-top: 1rem;
}
```

## Structure des fichiers

### Composants Alpine.js
Un fichier = un composant = une responsabilité

```javascript
/**
 * Composant Alpine.js : [Nom du composant]
 * [Description de la responsabilité]
 */
function nomComposant() {
    // 1. Récupération données session
    const savedData = window.sessionData?.nomComposant || {};
    
    return {
        // 2. État local
        
        // 3. Méthode init()
        
        // 4. Méthodes métier
        
        // 5. Méthodes utilitaires
    };
}

// Export global
window.nomComposant = nomComposant;
```

### Templates Django
```html
{% extends 'frontendv3/base.html' %}
{% load static %}

{% block title %}Titre de la page{% endblock %}

{% block content %}
<!-- Contenu structuré avec commentaires -->
{% endblock %}

{% block extra_js %}
<!-- Scripts spécifiques à la page -->
{% endblock %}
```

## Bonnes pratiques

### DRY (Don't Repeat Yourself)
- Utiliser des mixins pour code partagé
- Créer des utils pour fonctions communes
- Éviter la duplication de logique

### KISS (Keep It Simple, Stupid)
- Pas de state management complexe
- Alpine.js pur, pas de build process
- Session Django comme persistence simple

### Séparation des responsabilités
- Un composant = une fonctionnalité
- Backend pour logique métier complexe
- Frontend pour UI réactive

### Performance
- Debounce sur auto-save (300ms)
- Lazy loading des données volumineuses
- Éviter les watchers inutiles

### Sécurité
- Validation côté serveur obligatoire
- CSRF token sur toutes les requêtes POST
- Pas de données sensibles côté client

## Formats de données critiques

**Ne JAMAIS modifier ces formats** :

```python
# ID employé
employee_id = "FirstnameLASTNAME"  # Ex: "MartinDUPONT"

# ID poste
shift_id = "DDMMYY_FirstnameName_Vacation"  # Ex: "220725_MartinDupont_Matin"

# ID rouleau  
roll_id = "OF_NumeroRouleau"  # Ex: "3249_001"
```

## Git

### Messages de commit
```
feat: ajouter la gestion des temps perdus
fix: corriger le calcul du grammage
docs: mettre à jour README
style: formater le code CSS
refactor: simplifier la logique de validation
test: ajouter tests pour shift-form
```

### Branches
- `main` : Production
- `develop` : Développement
- `feature/nom-feature` : Nouvelles fonctionnalités
- `fix/nom-bug` : Corrections