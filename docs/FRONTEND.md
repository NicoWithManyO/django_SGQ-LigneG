# Guide développement Frontend V3

## 🏗️ Architecture Alpine.js

### Structure des composants
```
frontendv3/static/frontendv3/js/
├── components/           # Composants Alpine.js
├── mixins/              # Mixins réutilisables
├── services/            # Services métier
└── utils/               # Utilitaires
```

## 🧩 Composants principaux

### shift-form.js
Gestion du formulaire de poste.
```javascript
function shiftForm() {
    return {
        ...window.sessionMixin,
        employeeId: '',
        vacation: '',
        
        init() {
            this.initSession();
            this.watchAndSave('employeeId');
        }
    }
}
```

### roll-grid.js
Grille des épaisseurs avec navigation clavier.
```javascript
// Navigation Tab/Enter entre cellules
navigateToNextThickness(fromRow, fromCol, reverse = false) {
    // Priorité aux cellules vides, sinon suivante
}
```

### sticky-bar.js
Barre fixe avec informations rouleau.
```javascript
// Synchronisation automatique avec OF sélectionné
window.addEventListener('of-changed', (e) => {
    this.ofNumber = e.detail.ofNumber;
});
```

## 🔄 Pattern Session Mixin

### Utilisation
```javascript
function myComponent() {
    return {
        ...window.sessionMixin,
        
        myField: '',
        
        init() {
            this.initSession();
            this.watchAndSave('myField');  // Auto-save avec debounce
        }
    }
}
```

### Méthodes disponibles
- `initSession()` : Initialise la session
- `watchAndSave(field)` : Observe et sauvegarde un champ
- `saveSession()` : Sauvegarde manuelle
- `clearSession()` : Nettoie la session

## 📡 Communication entre composants

### Events JavaScript
```javascript
// Émetteur
window.dispatchEvent(new CustomEvent('of-changed', { 
    detail: { ofNumber: '3249' }
}));

// Récepteur
window.addEventListener('of-changed', (e) => {
    this.ofNumber = e.detail.ofNumber;
});
```

### Events principaux
- `of-changed` : Changement d'OF
- `profile-selected` : Sélection profil
- `roll-saved` : Rouleau sauvegardé
- `kpi-updated` : Mise à jour KPI

## ⌨️ Navigation clavier

### Implémentation
```html
<input 
    @keydown.tab.prevent="navigateToNext($event)"
    @keydown.enter.prevent="navigateToNext($event)"
    @blur="handleBlur">
```

### Logique de navigation
1. **Cellules épaisseur** : Priorité aux vides, puis suivantes
2. **Sticky bar** : tubeMass → length → totalMass
3. **Contrôles qualité** : micromaireG → micromaireD → masseSurfacique → extraitSec
4. **Bouton save** : Si tous les champs remplis

## 🎨 Styles et thèmes

### CSS Structure
```
frontendv3/static/frontendv3/css/
├── main.css              # Styles globaux + dégradé Saint-Gobain
├── manyo-logo.css        # Styles logo manyO.dev
└── pages/
    └── splash.css        # Écran d'accueil
```

### Variables CSS principales
```css
:root {
    --sg-blue: #0066cc;
    --sg-light-blue: #e6f2ff;
    --border-radius: 0.375rem;
}
```

## 🔧 Services

### kpi-service.js
Calculs KPI temps réel.
```javascript
// Calcul TRS automatique
calculateTRS(availability, performance, quality) {
    return availability * performance * quality;
}
```

### Méthodes disponibles
- `calculateAvailability()` : Taux de disponibilité
- `calculatePerformance()` : Performance production  
- `calculateQuality()` : Taux de qualité
- `calculateTRS()` : TRS global

## 🛠️ Utilitaires

### session.js
Gestion session Django.
```javascript
// Sauvegarde avec debounce
const debouncedSave = debounce(saveToSession, 300);
```

### modal-builders.js
Constructeurs de contenu pour modales.
```javascript
buildConfirmationContent(title, message) {
    return `<div class="text-center">...</div>`;
}
```

## 📱 Responsive Design

### Breakpoints Bootstrap 5.3
- **xs** : < 576px
- **sm** : ≥ 576px  
- **md** : ≥ 768px
- **lg** : ≥ 992px
- **xl** : ≥ 1200px

### Adaptations mobiles
- Grille épaisseurs : scroll horizontal
- Sticky bar : stack vertical
- Modales : plein écran sur mobile

## ⚡ Performance

### Optimisations
- Debounce sur auto-save (300ms)
- Events delegation pour les listes
- Lazy loading des composants lourds
- Cache des calculs KPI

### Monitoring
```javascript
// Debug events
window.addEventListener('*', (e) => {
    console.log('Event:', e.type, e.detail);
});
```

## 🧪 Tests Frontend

### Structure recommandée
```
tests/frontend/
├── unit/
│   ├── components/
│   ├── services/
│   └── utils/
└── integration/
    └── user-flows/
```

### Outils suggérés
- **Jest** : Tests unitaires
- **Cypress** : Tests E2E
- **Alpine Testing Utils** : Helpers Alpine.js