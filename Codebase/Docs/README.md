# Documentation SGQ Ligne G


## Table des matières

### Documentation technique

1. **[Architecture et Patterns](./ARCHITECTURE_PATTERNS.md)**
   - Vue d'ensemble de l'architecture
   - Patterns de développement
   - Conventions de code
   - Bonnes pratiques

2. **[Changements récents de l'UI](./UI_RECENT_CHANGES.md)**
   - Modifications de l'interface utilisateur
   - Nouvelles fonctionnalités
   - Améliorations UX

### Documentation du projet (racine)

- **[CLAUDE.md](../../CLAUDE.md)** : Guide pour l'utilisation avec Claude Code
- **[README.md](../../README.md)** : Documentation générale du projet
- **[PROJECT_STATUS_REPORT.md](../../PROJECT_STATUS_REPORT.md)** : État actuel du projet
- **[LEGACY_CODE_TO_REMOVE.md](../../LEGACY_CODE_TO_REMOVE.md)** : Code obsolète à supprimer
- **[OBSOLETE_PYTHON_FILES.md](../../OBSOLETE_PYTHON_FILES.md)** : Fichiers Python obsolètes

### Documentation spécifique

- **[DEFECT_BUTTON_CHANGES_SUMMARY.md](../DEFECT_BUTTON_CHANGES_SUMMARY.md)** : Changements sur les boutons de défauts

## Structure du projet

```
SGQ-LigneG/
├── Codebase/
│   ├── Docs/              # Documentation technique
│   ├── core/              # Modèles de base
│   ├── production/        # Gestion de production
│   ├── quality/           # Gestion qualité
│   ├── wcm/              # Work Checklist Management
│   ├── livesession/      # Session management (DRF)
│   └── frontend/         # Interface utilisateur
└── Documentation racine/  # Fichiers .md à la racine
```

## Accès rapide

### Pour les développeurs
- [Architecture et Patterns](./ARCHITECTURE_PATTERNS.md) - Comprendre l'architecture
- [CLAUDE.md](../../CLAUDE.md) - Guide pour Claude Code

### Pour les contributeurs
- [Changements récents](./UI_RECENT_CHANGES.md) - Dernières modifications
- [Status du projet](../../PROJECT_STATUS_REPORT.md) - État actuel

### Pour la maintenance
- [Code legacy](../../LEGACY_CODE_TO_REMOVE.md) - Code à nettoyer
- [Fichiers obsolètes](../../OBSOLETE_PYTHON_FILES.md) - Fichiers à supprimer

## Mise à jour de la documentation

Cette documentation est maintenue à jour avec le code. Lors de modifications importantes :

1. Mettre à jour les fichiers de documentation pertinents
2. Ajouter la date de mise à jour
3. Documenter les breaking changes
4. Inclure des exemples si nécessaire

## Contact

Pour toute question sur la documentation ou le projet, se référer au fichier README.md principal.