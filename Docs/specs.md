# Spécifications du Projet Django - Gestion Production Feutre

## Contexte et Conformité

**Client :** Saint-Gobain Quartz SAS - Nemours 77140

**Exigences de Conformité :**
- **ISO 9001** : Système de Management de la Qualité (certification obligatoire Saint-Gobain)
- **ISO 14001** : Système de Management Environnemental (standard Saint-Gobain)
- **OHSAS 18001 / ISO 45001** : Santé et Sécurité au Travail
- **Système de Management Intégré (SMI)** : conforme aux standards Saint-Gobain
- Traçabilité complète pour audits qualité et conformité réglementaire
- Documentation et archivage conformes aux standards industriels
- Respect des exigences spécifiques Saint-Gobain Advanced Ceramic Composites

## Description du Projet

Système de gestion de production de rouleaux de feutre permettant de tracer et contrôler la qualité des rouleaux produits par différents postes, en conformité avec les exigences ISO 9001 et les standards Saint-Gobain.

## Fonctionnalités Principales

- Gestion des postes de production
- Suivi des rouleaux fabriqués
- Contrôle qualité avec mesures d'épaisseur
- Gestion des défauts (bloquants/non-bloquants)
- Contrôles globaux par poste
- Traçabilité complète poste-rouleau
- Génération de documents Excel (relevés de contrôle, certificats de conformité)

## Modèles de Données

### Poste
- ID unique dynamique (format : date_operator_vacation)
- Date de production
- Opérateur responsable
- Vacation (Matin/ApresMidi/Nuit)
- Caractéristiques techniques
- Statut (actif/inactif)

### Rouleau
- ID unique dynamique (format : OFNumber_NumeroRoll)
- Numéro d'ordre de fabrication (OF)
- Numéro séquentiel dans l'OF
- Poste de fabrication (relation avec Poste)
- Date/heure de production
- Longueur totale
- Statut qualité

### Mesure d'Épaisseur
- Rouleau associé
- Position sur le rouleau (tous les 5m à partir de 3m)
- 6 points de mesure (3 à droite, 3 à gauche)
- Valeurs d'épaisseur

### DefectType (Type de Défaut)
- ID unique
- Nom du défaut (unique)
- Description
- Criticité (non_blocking/blocking/threshold)
- Seuil de tolérance (pour les défauts à seuil)
- Statut actif/inactif
- Timestamps de création/modification

### RollDefect (Défaut Constaté)
- ID unique
- Rouleau concerné (roll_id)
- Type de défaut (FK vers DefectType)
- Description détaillée
- Position sur le rouleau (mètre)
- Côté (gauche/centre/droite)
- Statut (pending/resolved/blocking)
- Gravité calculée automatiquement
- Timestamps détection/résolution
- Commentaires opérateur

### ThicknessMeasurement (Mesure d'Épaisseur)
- ID unique
- Rouleau concerné (roll_id)
- Position (mètre)
- Point de mesure (G1/G2/G3/D1/D2/D3)
- Valeur d'épaisseur (mm)
- Validation tolérances automatique
- Tolérances min/max configurables
- Timestamp de mesure
- Commentaires opérateur

### Contrôle Global (Quality)
- Poste concerné
- Date/heure du contrôle
- Paramètres qualité contrôlés
- Valeurs mesurées
- Opérateur responsable
- Fréquence : au moins une fois par poste, possibilité de mises à jour multiples par l'opérateur

## Logique Métier

### Contrôle Qualité
- Mesures d'épaisseur tous les 5m à partir de 3m
- 6 points de mesure par section (3 côté droit, 3 côté gauche)
- Validation automatique selon critères définis
- Contrôles globaux Quality : au moins une sauvegarde par poste, mises à jour possibles en cours de poste

### Gestion des Défauts
- Défauts non-bloquants : production continue
- Défauts bloquants : arrêt de production
- Défauts à seuil : bloquant selon quantité/fréquence

### Traçabilité
- Chaque poste et rouleau ont un ID unique
- Liaison bidirectionnelle poste ↔ rouleau
- Historique complet des mesures et défauts

## Interface Utilisateur

### Modules Principaux de l'Interface

#### Module Poste/Shift
- **Fiche de Poste** : Date, opérateur, vacation, heures
- **État machine** : statut début/fin de poste
- **Gestion des shifts** : changement d'équipe, continuité production

#### Module Rouleau
- **Représentation graphique** : vue déroulée sur la longueur
- **Grille métrique** : une ligne par mètre selon la longueur du rouleau
- **Zones de saisie** : 
  - Mesures d'épaisseur tous les 5m (6 points : 3 gauche, 3 droite)
  - Déclaration de défauts positionnés sur le rouleau avec sélection depuis liste prédéfinie
  - Boutons d'effacement rapide pour les défauts (apparition au survol)
  - Visualisation des zones de contrôle
- **Interface défauts** :
  - Champs sans bordures pour aspect épuré
  - Datalists avec types de défauts créés dans l'admin
  - Bouton "×" rouge pour effacement instantané

#### Module Ordre de Fabrication
- **OF en cours** : numéro OF, statut
- **Longueur cible** : objectif production
- **Découpe** : planification et exécution

#### Module Déclaration Temps Perdu
- **Suivi des arrêts** : causes, durées
- **Déclaration déchets** : types, quantités

#### Module Info Qualité
- **Seuils qualité** : limites acceptables
- **Défauts** : types, criticité, seuils de tolérance
- **Alertes** : notifications dépassement seuils
- **Contrôles généraux** : paramètres qualité par poste

#### Module Fibrage en Cours
- **Suivi production** : rouleau en cours, masses, longueur
- **Contrôles finaux** : validation conformité
- **Actions** : garder rouleau, découper, déchets

#### Module Paramètres Machine
- **Réglages techniques** : configuration machine
- **Paramètres process** : températures, vitesses, pressions
- **Historique réglages** : traçabilité des modifications

## Génération de Documents

### Documents Excel
- **Relevé de contrôle** : mesures d'épaisseur par rouleau avec graphiques
- **Certificat de conformité** : validation qualité finale du rouleau
- **Rapport de poste** : synthèse des contrôles globaux Quality
- **Historique des défauts** : liste des défauts par période/rouleau

### Fonctionnalités d'Export
- Templates Excel personnalisables
- Génération automatique ou manuelle
- Filtres par période, poste, rouleau
- Intégration de graphiques et tableaux

## Exigences Techniques

### Librairies Python
- `openpyxl` : génération et manipulation de fichiers Excel
- `pandas` : manipulation des données pour export
- `matplotlib` : génération de graphiques intégrés aux exports

### Performance
- Génération asynchrone pour gros volumes
- Cache des templates Excel
- Optimisation des requêtes pour l'export