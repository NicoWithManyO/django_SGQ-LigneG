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

## Notes techniques

- Ces changements sont implémentés dans le template `production.html` et les fichiers JavaScript associés
- L'API DRF `/livesession/api/current-session/` gère la persistance de toutes ces données
- Les calculs côté serveur garantissent la cohérence des données affichées