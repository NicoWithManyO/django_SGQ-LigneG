# Applications archivées

Ce dossier contient les anciennes versions des applications qui ne sont plus utilisées mais conservées pour référence.

## Applications archivées :

### livesession/
- **Version** : V1/V2
- **Rôle** : Gestion des sessions et API session
- **Stockage** : À la racine de `request.session`
- **Remplacé par** : `frontendv3` avec stockage dans `request.session['v3_production']`

### frontend/
- **Version** : V2
- **Rôle** : Interface frontend complète V2
- **Remplacé par** : `frontendv3`

## Notes importantes :
- Ces applications ont été retirées de `INSTALLED_APPS` dans `settings.py`
- Les URLs sont désactivées dans `urls.py`
- Conservées uniquement pour référence ou récupération de code si besoin