# Changements récents de l'interface utilisateur

## Date de mise à jour : 14 janvier 2025

Cette documentation décrit les changements récents apportés à l'interface utilisateur du système SGQ Ligne G.

## 1. Affichage de l'ID du rouleau

L'ID du rouleau s'affiche maintenant de manière différente selon le statut du rouleau :

### Rouleau CONFORME
- **Format** : `{OF en cours}_{Numéro rouleau sur 3 chiffres}`
- **Exemple** : `12345_042` pour l'OF 12345 et le rouleau numéro 42
- Le numéro de rouleau est toujours formaté sur 3 chiffres avec des zéros à gauche si nécessaire

### Rouleau NON CONFORME
- **Format** : `{OF de découpe}_{DDMM}`
- **Exemple** : `67890_1401` pour l'OF de découpe 67890 et la date du 14 janvier
- Le numéro de rouleau n'est pas inclus dans l'ID pour les rouleaux non conformes
- La date est formatée en jour-mois (DDMM)

## 2. Calcul dynamique du nombre d'épaisseurs

Le nombre total de cellules d'épaisseur est maintenant calculé dynamiquement :
- **Base de calcul** : 6 cellules par mètre de longueur affichée
- **Formule** : `Nombre de cellules = Longueur affichée (m) × 6`
- **Exemple** : Pour un rouleau de 250m, il y aura 1500 cellules d'épaisseur
- Ce calcul s'applique aussi bien aux mesures normales qu'aux rattrapages

## 3. Badge de statut non cliquable

- Le badge affichant le statut du rouleau (CONFORME/NON CONFORME) n'est plus cliquable
- Cette modification évite les clics accidentels et clarifie que ce badge est purement informatif
- Le style visuel du badge reste inchangé (vert pour CONFORME, rouge pour NON CONFORME)

## 4. Réservation d'espace pour le grammage

- Un espace est maintenant réservé dans la sticky bar pour l'affichage du grammage
- Cela évite les décalages visuels lorsque le grammage est calculé et affiché
- L'espace reste vide jusqu'à ce que le grammage soit disponible
- Cette amélioration garantit une interface plus stable visuellement

## 5. Style des cellules de rattrapage (admin)

- Les cellules de rattrapage peuvent apparaître avec un fond vert lors de l'utilisation des boutons admin
- Ce comportement est considéré comme acceptable et ne nécessite pas de correction
- Il n'affecte pas l'utilisation normale de l'interface par les opérateurs

## 6. Navigation au clavier améliorée

La navigation avec la touche Tab a été optimisée :
1. La touche Tab navigue d'abord vers toutes les cellules d'épaisseur vides
2. Une fois toutes les cellules d'épaisseur parcourues, la navigation continue vers les champs de la sticky bar
3. Cette amélioration facilite la saisie rapide des données d'épaisseur

### Ordre de navigation :
1. Cellules d'épaisseur vides (dans l'ordre de position)
2. Champs de la sticky bar (masse tube, longueur, masse totale, etc.)

## 7. Badge de contrôle qualité

Un nouveau badge remplace le texte "Renseignez les contrôles pour pouvoir sauvegarder le poste" :
- **Badge "Contrôles Qualité Pending"** : Affiché en jaune quand les contrôles ne sont pas complets
- **Badge "Contrôles Qualité Passed"** : Affiché en vert quand tous les contrôles sont conformes
- Design professionnel avec icônes et style cohérent avec la charte graphique

## 8. Vérification de conformité des contrôles qualité

La conformité des contrôles qualité est maintenant vérifiée automatiquement :
- **Extrait sec** : Doit être dans les spécifications
- **Moyennes micronnaire gauche/droite** : Doivent être dans les spécifications
- **Moyennes masse surfacique gauche/droite** : Doivent être dans les spécifications
- **LOI** : Le switch doit être activé (échantillon donné)

## 9. Sauvegarde des rouleaux en base de données

Nouvelle fonctionnalité de sauvegarde des rouleaux :
- **Endpoint API** : `/livesession/api/save-roll/` pour persister les rouleaux
- **Boîte de confirmation** : Demande confirmation avant sauvegarde avec affichage du numéro, statut et longueur
- **Gestion automatique** : Après sauvegarde, incrémentation du numéro de rouleau et transfert de la masse tube suivante
- **Détermination du statut** : CONFORME/NON_CONFORME basé sur les défauts bloquants et la conformité des contrôles qualité

## 10. Navigation Tab améliorée dans tous les formulaires

La navigation Tab a été étendue et optimisée :

### Dans les contrôles qualité :
- Navigation entre les champs vides uniquement
- Une fois tous remplis → première épaisseur vide

### Dans les épaisseurs :
- Navigation en boucle entre les épaisseurs vides
- Une fois toutes remplies → premier champ vide de la sticky bar

### Dans la sticky bar :
- Navigation vers les champs vides uniquement (pas en boucle)
- Après le dernier champ → retour aux épaisseurs vides

### Comportement global :
- Si le curseur n'est nulle part → première épaisseur vide
- Navigation intelligente qui suit le flux de travail naturel

## 11. Affichage du temps total déclaré

Le header "Déclaration de Temps" affiche maintenant le total :
- **Format** : "Déclaration de Temps : 2h30" (ou "45min" si moins d'une heure)
- **Mise à jour automatique** : Le total se recalcule à chaque ajout/suppression
- **Affichage** : "--" si aucun temps n'est déclaré

## 12. Alignement des labels dans les spécifications qualité

Dans le bloc profil, les labels des spécifications sont maintenant alignés à droite :
- Meilleure lisibilité des valeurs Min/Nominal/Max
- Alignement cohérent pour toutes les spécifications
- Padding de 10px pour un espacement optimal

## 13. Correction du code couleur du grammage

Le grammage dans la sticky bar utilise maintenant les bonnes spécifications :
- Comparaison avec les specs de masse surfacique globale (g/m²)
- Code couleur corrigé : vert dans les specs, rouge hors specs
- Recalcul automatique après chargement des spécifications

## Notes techniques

- Ces changements sont implémentés dans le template `production.html` et les fichiers JavaScript associés
- L'API DRF `/livesession/api/current-session/` gère la persistance de toutes ces données
- Les calculs côté serveur garantissent la cohérence des données affichées
- Nouveau endpoint `/livesession/api/save-roll/` pour la sauvegarde des rouleaux