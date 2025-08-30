# Documentation API

## 🔗 Endpoints principaux

### Base URL
- Production : `/`
- API base : `/api/`

## 📡 API Session (Persistence automatique)

### POST/PATCH `/api/session/`
Gestion de la persistence des données de formulaires.

**Paramètres :**
```json
{
  "session_key": "string",
  "data": {
    "field_name": "value",
    "nested_object": {...}
  }
}
```

**Usage :**
- Sauvegarde automatique des champs avec debounce 300ms
- Utilisé par le session mixin Alpine.js

## 🏭 API Production

### GET `/production/api/rolls/`
Liste des rouleaux existants.

### POST `/production/api/rolls/`
Création d'un nouveau rouleau.

**Payload :**
```json
{
  "roll_id": "3249_001",
  "of_number": "3249",
  "profile_template": 1,
  "thicknesses": [...],
  "defects": [...],
  "quality_controls": {...}
}
```

### GET `/production/api/shifts/`
Liste des postes de travail.

### POST `/production/api/shifts/`
Création d'un nouveau poste.

**Payload :**
```json
{
  "shift_id": "220725_MartinDupont_Matin",
  "employee_id": "MartinDUPONT",
  "vacation": "Matin",
  "date": "2022-07-25"
}
```

## 📋 API Catalog

### GET `/api/defect-types/`
Liste des types de défauts disponibles (13 catégories).

**Réponse :**
```json
[
  {
    "id": 1,
    "name": "Défaut de surface",
    "category": "SURFACE"
  }
]
```

### GET `/api/profiles/`
Liste des profils produits disponibles.

### GET `/api/current-profile/`
Profil actuellement sélectionné avec ses spécifications.

**Réponse :**
```json
{
  "id": 1,
  "name": "Profil Standard",
  "min_thickness": 0.5,
  "max_thickness": 2.0,
  "target_thickness": 1.25,
  "specifications": [...]
}
```

## 🔧 Formats de données

### IDs Métier
```
employee_id = "FirstnameLASTNAME"              # Ex: "MartinDUPONT"
shift_id = "DDMMYY_FirstnameName_Shift"        # Ex: "220725_MartinDupont_Matin"
roll_id = "OF_RollNumber"                      # Ex: "3249_001"
roll_id_non_conforme = "9999_JJMMAA_HHMM"     # Ex: "9999_040825_1423"
```

### Structure Défaut
```json
{
  "defect_type_id": 1,
  "position": 125.5,
  "description": "Description optionnelle",
  "severity": "MINOR"
}
```

### Structure Épaisseur
```json
{
  "position": 0,
  "thickness": 1.25,
  "is_valid": true
}
```

## 🚨 Codes d'erreur

- **400** : Données invalides
- **404** : Ressource non trouvée  
- **409** : Conflit (ex: rouleau existant)
- **500** : Erreur serveur

## 🔐 Authentification

Actuellement basée sur les sessions Django. Pas d'authentification API spécifique requise pour les endpoints internes.

## 📊 API Management (Dashboard)

### GET `/management/api/kpi/`
KPI temps réel de production.

**Réponse :**
```json
{
  "trs": 0.85,
  "availability": 0.92,
  "performance": 0.94,
  "quality": 0.98,
  "total_production": 1250.5,
  "conformity_rate": 0.96
}
```