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

### Shift (Poste)
- ID unique dynamique (format : JJMMAA_PrenomNom_Vacation)
- Date de production
- Opérateur responsable (FK vers Operator avec SET_NULL)
- Vacation (Matin/ApresMidi/Nuit/Journée)
- Heures début/fin avec calcul automatique durée
- Temps disponible (TO - TP calculé automatiquement)
- États machine début/fin (started_at_beginning/end)
- Métrages début/fin pour continuité
- Commentaires opérateur
- Signature check-list avec heure

### Roll (Rouleau)
- ID unique dynamique :
  - Format conformes : OF_NumRouleau (ex: 3254_001)
  - Format non-conformes : OFDecoupe_JJMMAA_HHMM
- Ordre de fabrication (FK vers FabricationOrder)
- Numéro rouleau (formaté 3 chiffres : 001, 020, 100)
- Shift nullable (peut être sauvegardé avant le poste)
- Longueur, masses tube/totale/nette (auto-calculée)
- Moyennes épaisseur gauche/droite (auto-calculées via signals)
- Statut (CONFORME/NON_CONFORME)
- Destination (PRODUCTION/DECOUPE/DECHETS)
- Indicateurs défauts bloquants et problèmes épaisseur

### RollThickness (Mesure d'Épaisseur)
- Rouleau associé (FK avec cascade)
- Position sur le rouleau (tous les 5m à partir de 3m)
- Points de mesure : GG, GC, GD, DG, DC, DD
- Valeur épaisseur en mm
- Flag mesure de rattrapage (is_catchup)
- Validation automatique tolérances (is_within_tolerance)
- Signal pour calcul automatique des moyennes

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

### QualityControl (Contrôles Qualité)
- Shift associé (FK avec cascade)
- Session_key pour liaison temporaire
- Micronnaire : 6 valeurs (3G + 3D) avec moyennes auto
- Extrait sec : valeur % + heure
- Masses surfaciques : GG, GC, DC, DD (g/25cm²) avec moyennes
- LOI : booléen donnée + heure
- Validation automatique is_valid
- OBLIGATOIRE avant sauvegarde du poste

## Logique Métier

### Contrôle Qualité
- Mesures d'épaisseur tous les 5m à partir de 3m
- 6 points de mesure par section (3 côté droit, 3 côté gauche)
- Validation automatique selon critères définis
- Contrôles globaux Quality : obligatoires avant save poste, mises à jour possibles en cours de poste
- Vérification automatique : moyennes micronnaire G/D, masses surfacique G/D, extrait sec, LOI
- Auto-remplissage created_by avec l'opérateur du poste

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

## Modèles de la Migration DRF

### CurrentSession (Gestion de Session DRF)
- session_key unique par utilisateur
- session_data JSON avec tout l'état de la session
- Sauvegarde automatique via API avec debounce 1s
- Réinitialisation intelligente après save poste
- Endpoint unifié `/livesession/api/current-session/`

### LostTimeEntry (Temps Perdus)
- Shift nullable (liaison via session avant save)
- Motif, commentaire, durée en minutes
- Signal pour calcul automatique lost_time du shift
- Affichage avec heure dans l'interface

### MachineParameters (Paramètres Machine)
- Profils de configuration nommés
- Débits oxygène/propane primaire/secondaire
- Vitesses primaire/secondaire
- Vitesse tapis (m/h) avec conversion m/min
- Flag is_active pour profil actif

### Specification (Spécifications Qualité)
- Types : thickness, micrometer, surface_mass, dry_extract, global_surface_mass
- Valeurs min/max critiques et alertes
- Valeur nominale cible
- Unité de mesure configurable
- Max NOK autorisés pour épaisseurs

### MoodCounter (Compteur d'Humeur)
- 4 objets fixes : happy, unhappy, neutral, no_response
- Comptage anonyme sans données personnelles
- Endpoint `/livesession/api/increment-mood/`
- Affichage admin sous "MoOOoOods"
- RGPD compliant

## Interface Utilisateur Améliorée

### Layout Principal
- **Colonne gauche** : Productivité + Déclaration temps (verticaux)
- **Colonne droite** : Check-list avec boutons 3 états (N/A, OK, NOK)
- **Sticky Bar** : Gestion rouleau en cours avec actions cut/waste
- **Blocs repliables** : Tous les blocs avec chevrons

### Bloc Productivité
- Onglets intégrés dans le header
- 3 onglets : Temps, Production, Qualité
- 3 colonnes × 2 lignes de métriques par onglet
- Métriques temps réel mises à jour dynamiquement

### Check-list de Fin de Poste
- 6 points de contrôle avec boutons 3 états
- Champ signature avec heure automatique
- Largeur fixe même repliée

### Modals de Confirmation
- **Modal Save Poste** : Métriques (rendement, taux OK, TO) + sélecteur humeur
- **Modal Save Rouleau** : Numéro, statut, longueur avec confirmation
- **Info-bulles dynamiques** : Sur boutons désactivés (Save Poste)
- **Vérification contrôles** : Badge Pending/Passed selon complétion

### Visualisation Rouleau
- Grille dynamique selon longueur
- Défauts positionnés visuellement
- Indicateurs épaisseur et conformité
- Validation temps réel

## Architecture API DRF
- Endpoint principal : `/livesession/api/current-session/`
- Méthodes : GET (récupération), PATCH (mise à jour), DELETE (réinit)
- Endpoints spécifiques :
  - `/save-shift/` : Sauvegarde du poste avec réinit intelligente
  - `/save-roll/` : Sauvegarde d'un rouleau
  - `/check-shift-id/<id>/` : Vérification ID shift
  - `/check-roll-id/<id>/` : Vérification ID rouleau
  - `/increment-mood/` : Incrémentation compteur humeur
- Frontend utilise `updateFieldViaAPI()` pour toutes les mises à jour

## Génération de Documents (Prévue Phase 3)
- Module reports en attente d'implémentation
- Export Excel avec openpyxl prévu
- Templates personnalisables planifiés

## Architecture Technique

### Backend
- Django 5.2.4 avec Python 3.11+
- django-htmx 1.23.2 pour interactivité
- Signals Django pour calculs automatiques
- Sessions pour persistance données

### Frontend
- Bootstrap 5.1.3 pour le responsive
- HTMX 2.0 pour les mises à jour dynamiques
- JavaScript vanilla pour validations temps réel
- CSS avec variables pour thème Saint-Gobain

### Sécurité & Performance
- CSRF tokens pour HTMX via meta tag
- Debounce auto-save 1 seconde
- Validation côté client et serveur
- Admin Django hautement personnalisé avec inlines

### Points d'Attention Production
- DEBUG = False obligatoire
- PostgreSQL recommandé (SQLite en dev)
- Static files via serveur web
- Session middleware requis
- Signals critiques pour intégrité données