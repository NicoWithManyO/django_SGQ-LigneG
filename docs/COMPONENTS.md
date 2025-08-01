# Composants V3

## Vue d'ensemble

Chaque composant Alpine.js gère une partie spécifique de l'interface.

## shift-form.js

**Responsabilité** : Gestion de la fiche de poste

**Fonctionnalités** :
- Sélection opérateur avec auto-complétion
- Sélection date avec affichage jour/semaine
- Choix vacation (Matin/Après-midi/Nuit)
- Génération automatique ID shift
- Saisie heures et longueurs début/fin
- Baguette magique pour récupérer dernière longueur

**Events émis** :
- `operator-changed` : Changement d'opérateur
- `shift-changed` : Changement de shift complet

**Données session** :
```javascript
{
    operatorId: "MartinDUPONT",
    date: "2024-01-15",
    vacation: "Matin",
    shiftId: "150124_MartinDupont_Matin",
    // ...
}
```

## production-order.js

**Responsabilité** : Gestion des ordres de fabrication

**Fonctionnalités** :
- Sélection OF avec recherche
- Affichage infos OF (profil, cible, client)
- Longueur cible éditable
- Sélection OF découpe optionnel

**Events émis** :
- `of-changed` : Changement d'OF
- `target-length-changed` : Modification longueur cible

**Events écoutés** :
- Aucun

## profile-selector.js

**Responsabilité** : Sélection et affichage du profil produit

**Fonctionnalités** :
- Liste déroulante des profils
- Activation/désactivation des modes
- Onglets KPI / Params&Specs
- Affichage spécifications produit
- Gestion temps perdus (downtimeTracker intégré)

**Events émis** :
- `profile-changed` : Changement de profil avec specs

**Events écoutés** :
- `target-length-changed` : Pour afficher la longueur cible
- `operator-changed` : Pour vider temps perdus si besoin

## roll-grid.js

**Responsabilité** : Grille de saisie du rouleau

**Fonctionnalités** :
- Grille adaptative selon longueur (1m, 5m, 10m, etc.)
- Saisie épaisseurs avec validation couleur
- Gestion défauts avec popup contextuelle
- Calcul statistiques épaisseur
- Détermination conformité

**Events émis** :
- `thickness-updated` : Mise à jour épaisseur
- `defect-added` : Ajout défaut
- `conformity-changed` : Changement statut

**Events écoutés** :
- `target-length-changed` : Pour adapter la grille
- `profile-changed` : Pour les limites épaisseur

## sticky-bar.js

**Responsabilité** : Barre d'actions fixe

**Fonctionnalités** :
- Affichage heure temps réel
- ID rouleau auto-généré
- Numéro rouleau incrémentable
- Masses et grammage
- Statut conformité
- Actions principales (nouveau, sauvegarder)

**Events émis** :
- `roll-number-changed` : Changement numéro
- `new-roll` : Création nouveau rouleau

**Events écoutés** :
- `of-changed` : Pour l'ID rouleau
- `conformity-changed` : Pour le badge

## checklist.js

**Responsabilité** : Check-list qualité prise de poste

**Fonctionnalités** :
- 9 items prédéfinis
- Boutons OK/N/A/NOK par item
- Validation complétude
- Signature avec vérification initiales
- Reset automatique si changement opérateur

**Events émis** :
- `checklist-completed` : Check-list signée

**Events écoutés** :
- `operator-changed` : Pour reset signature

## collapsible.js (Mixin)

**Responsabilité** : Comportement enroulable/déroulable

**Fonctionnalités** :
- État expanded/collapsed
- Animation chevron
- Méthode toggle

**Utilisation** :
```javascript
x-data="{ ...collapsibleMixin(true), /* autres props */ }"
```

## session.js (Utilitaire)

**Responsabilité** : Gestion persistence session Django

**API** :
- `window.session.patch(data)` : Sauvegarder partiellement
- `window.session.save(data)` : Sauvegarder tout
- `window.session.get(key)` : Récupérer une valeur

## Relations entre composants

```
shift-form ──operator-changed──> checklist
     │
     └──shift-changed──> tous

production-order ──of-changed──> sticky-bar, roll-grid
     │
     └──target-length-changed──> profile-selector, roll-grid

profile-selector ──profile-changed──> roll-grid

roll-grid ──conformity-changed──> sticky-bar

sticky-bar ──new-roll──> tous (reset)
```