# Architecture V3

## Structure globale

Le projet suit l'architecture Django standard avec des apps par domaine métier.

### Apps Django

- **catalog/** - Données de référence (profiles, spécifications, types défauts)
- **production/** - Gestion des shifts et rouleaux  
- **quality/** - Contrôles qualité et conformité
- **wcm/** - Indicateurs WCM et calculs TRS
- **planification/** - Gestion opérateurs et OF
- **livesession/** - Persistence automatique des formulaires
- **frontendv3/** - Interface utilisateur V3 (en développement)
- **management/** - Dashboard supervision
- **exporting/** - Export Excel

### Frontend V3

Architecture Alpine.js avec composants modulaires :

```
frontendv3/
├── static/frontendv3/
│   ├── css/
│   │   └── main.css           # Styles globaux + dégradé Saint-Gobain
│   ├── js/
│   │   ├── components/        # Un fichier par composant Alpine
│   │   ├── utils/             # Fonctions utilitaires
│   │   └── main.js           # Point d'entrée
│   └── img/
└── templates/frontendv3/
    ├── base.html             # Template de base
    └── production.html       # Page principale
```

## Flux de données

### 1. Entrée utilisateur
- Saisie dans composant Alpine.js
- Validation immédiate côté client

### 2. Persistence session
- Auto-save après 300ms (debounce)
- Stockage dans session Django via livesession

### 3. Communication inter-composants
- Events JavaScript custom
- Pas de store centralisé (KISS)

### 4. Sauvegarde base
- Action explicite utilisateur
- Validation complète avant save
- API Django REST

### 5. Affichage temps réel
- Binding Alpine.js réactif
- Calculs automatiques
- Feedback visuel immédiat

## Patterns de code

### Composant Alpine type
```javascript
function monComposant() {
    const savedData = window.sessionData?.monComposant || {};
    
    return {
        // État
        field1: savedData.field1 || '',
        
        // Init
        init() {
            // Setup watchers
            this.$watch('field1', () => this.autoSave());
            
            // Listen events
            window.addEventListener('event-name', (e) => {
                this.handleEvent(e.detail);
            });
        },
        
        // Auto-save
        autoSave() {
            clearTimeout(this._saveTimeout);
            this._saveTimeout = setTimeout(() => {
                window.session.patch({ field1: this.field1 });
            }, 300);
        }
    };
}
```

### API endpoint type
```python
@api_view(['GET', 'POST'])
def mon_endpoint(request):
    if request.method == 'GET':
        # Retourner données
        pass
    elif request.method == 'POST':
        # Sauvegarder
        pass
```

## Conventions

- Composants Alpine autonomes
- Pas de dépendances circulaires
- Session comme source de vérité temporaire
- Base de données comme source de vérité permanente
- Events pour communication loose coupling