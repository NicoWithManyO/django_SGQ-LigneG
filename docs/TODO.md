# TODO - Ce qui reste à implémenter

## Priorité HAUTE 🔴

### 1. Compléter sticky-bar
- [ ] Ajouter champs masses (brute, nette, tube)
- [ ] Calculer grammage automatique
- [ ] Gérer l'incrémentation du numéro rouleau
- [ ] Bouton "Nouveau rouleau" fonctionnel
- [ ] Bouton "Sauvegarder" avec validation

### 2. Sauvegarde shift en base
- [ ] Endpoint API `/api/shifts/` POST
- [ ] Validation des données obligatoires
- [ ] Gestion des erreurs
- [ ] Feedback utilisateur

### 3. Sauvegarde rouleau complet
- [ ] Endpoint API `/api/rolls/` POST
- [ ] Inclure toutes les épaisseurs
- [ ] Inclure tous les défauts
- [ ] Transaction atomique
- [ ] Confirmation avant save

### 4. Calculs KPI temps réel
- [ ] Longueur enroulable = heures travaillées × vitesse tapis
- [ ] Taux de performance = production réelle / longueur enroulable
- [ ] Taux qualité = rouleaux conformes / total rouleaux
- [ ] TRS = Performance × Qualité × Disponibilité

## Priorité MOYENNE 🟡

### 5. Gestion temps perdus (downtimeTracker)
- [ ] Interface de saisie dans profile-selector
- [ ] Catégories de temps perdus depuis API
- [ ] Calcul impact sur disponibilité
- [ ] Historique par shift

### 6. Calculs backend KPI
- [ ] Service Python pour calculs complexes
- [ ] API endpoints pour récupérer KPI
- [ ] Cache pour performances
- [ ] Mise à jour temps réel

### 7. Validation complète avant save
- [ ] Vérifier tous champs obligatoires
- [ ] Valider cohérence données
- [ ] Afficher erreurs clairement
- [ ] Empêcher save si erreurs

### 8. Tests end-to-end
- [ ] Scénario complet de production
- [ ] Tests de non-régression
- [ ] Tests de performance
- [ ] Tests multi-utilisateurs

## Priorité BASSE 🟢

### 9. Améliorations UI/UX
- [ ] Transitions plus fluides
- [ ] Animations de feedback
- [ ] Tooltips d'aide
- [ ] Raccourcis clavier

### 10. Optimisations
- [ ] Lazy loading composants
- [ ] Compression assets
- [ ] Cache navigateur
- [ ] Réduire requêtes API

### 11. Documentation
- [ ] Guide utilisateur
- [ ] Vidéos de formation
- [ ] FAQ
- [ ] Changelog

## Bugs connus 🐛

- [ ] Les chevrons des cards ne pivotent pas à l'enroulement
- [ ] La grille peut dépasser sur mobile
- [ ] Le focus se perd après validation épaisseur

## Améliorations futures 💡

- Export PDF du rouleau
- Graphiques temps réel
- Mode hors-ligne
- Application mobile native
- Intégration ERP
- Scan code-barres
- Reconnaissance vocale pour saisie

## Notes techniques

### Formule longueur enroulable
```
Longueur enroulable (m) = Durée poste (min) × Vitesse tapis (m/min) × Coefficient utilisation
```

### Structure données rouleau à sauvegarder
```javascript
{
    shift_id: "220725_MartinDupont_Matin",
    roll_id: "3249_001", 
    of_number: "3249",
    profile_id: 5,
    length_start: 0,
    length_end: 2500,
    mass_net: 125.5,
    mass_gross: 130.2,
    mass_tube: 4.7,
    grammage: 50.2,
    conformity: true,
    thicknesses: [
        { position: 5, value: 2.05 },
        { position: 10, value: 2.03 },
        // ...
    ],
    defects: [
        { position: 15, type: "PLI", count: 1 },
        { position: 45, type: "TROU", count: 2 },
        // ...
    ]
}
```