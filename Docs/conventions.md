# Conventions du Projet Django - Gestion Production Feutre

## Conventions de Nommage

### Modèles Django
- Noms de modèles en anglais, PascalCase : `WorkStation`, `FeltRoll`, `ThicknessReading`
- Noms de champs en anglais, snake_case : `created_at`, `thickness_value`, `is_active`
- Relations : `workstation`, `felt_roll`, `defect_type`

### Variables et Fonctions
- Variables en anglais, snake_case : `current_roll`, `measurement_points`, `defect_count`
- Fonctions en anglais, snake_case : `calculate_thickness()`, `validate_quality()`, `get_active_workstations()`
- Constantes en anglais, UPPER_CASE : `MEASUREMENT_INTERVAL`, `MIN_THICKNESS`, `MAX_DEFECTS`

### Base de Données
- Tables en anglais, snake_case : `workstations`, `felt_rolls`, `thickness_readings`
- Colonnes en anglais, snake_case : `workstation_id`, `roll_length`, `created_at`
- Index et contraintes : préfixe du type (`idx_`, `fk_`, `uk_`)

## Architecture du Projet

### Structure des Dossiers
- Applications Django en anglais : `production/`, `quality/`, `defects/`
- Modules utilitaires : `utils/`, `helpers/`, `validators/`
- Templates : structure par app puis par fonction

### Applications Django
- `production` : gestion des postes et rouleaux
- `quality` : contrôles qualité avec modèles DefectType, RollDefect, ThicknessMeasurement
- `reports` : génération de documents Excel
- `core` : modèles partagés et utilitaires (Operator, FabricationOrder)

## Conventions de Code

### Style Python
- Respect strict de PEP 8
- Imports groupés : standard library, third-party, local
- Longueur de ligne : 88 caractères (Black formatter)
- Type hints obligatoires pour les fonctions publiques

### Templates
- Noms de fichiers en anglais : `roll_detail.html`, `quality_dashboard.html`
- Variables de contexte en anglais : `{{ roll.thickness_average }}`
- Classes CSS en anglais : `.quality-indicator`, `.defect-warning`

### API/Vues
- URLs en anglais : `/workstations/`, `/rolls/`, `/quality/`
- Paramètres de requête en anglais : `?status=active&sort=created_at`
- Réponses JSON avec clés en anglais

## Conventions Business

### Identifiants
- **Postes** : format dynamique `date_operator_vacation`
  - Exemple : `120525_XxxxxYYYYYY_Matin`
  - Date : format JJMMAA
  - Opérateur : prénom + nom (sans espaces)
  - Vacation : `Matin`, `ApresMidi`, `Nuit`
- **Rouleaux** : format dynamique `OFNumber_NumeroRoll`
  - Exemple : `OF12345_001`, `OF12345_002`
  - OF Number : numéro d'ordre de fabrication
  - Numéro Roll : numéro séquentiel du rouleau dans l'OF
  - Construction automatique à partir des données du formulaire

### Unités de Mesure
- Épaisseur : millimètres (mm)
- Longueur : mètres (m)
- Distances de mesure : mètres (m)

### Statuts
- Anglais pour cohérence avec le code
- Postes : `active`, `inactive`, `maintenance`
- Rouleaux : `in_progress`, `completed`, `defective`
- Défauts : `resolved`, `pending`, `blocking`

## Commentaires

### Règles Générales
- Commentaires en français uniquement
- Commentaires utiles, professionnels et pertinents
- Éviter les commentaires évidents
- Privilégier les docstrings pour les fonctions/classes

### Exemples
```python
class FeltRoll(models.Model):
    """Modèle représentant un rouleau de feutre produit."""
    
    # Identifiant unique du rouleau (ex: FR001)
    roll_id = models.CharField(max_length=10, unique=True)
    
    def calculate_average_thickness(self):
        """Calcule l'épaisseur moyenne sur toute la longueur du rouleau."""
        # Récupère toutes les mesures d'épaisseur pour ce rouleau
        measurements = self.thickness_readings.all()
        # Calcule la moyenne en excluant les valeurs nulles
        return measurements.aggregate(avg=models.Avg('thickness_value'))['avg']
```