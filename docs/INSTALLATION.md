# Guide d'installation et développement

## 🛠️ Prérequis

- **Python 3.12+**
- **Git**

## ⚡ Installation rapide

### 1. Cloner le projet
```bash
git clone [url-du-repo]
cd django_SGQ-LigneG_beta
```

### 2. Créer l'environnement virtuel
```bash
python -m venv .venv
```

### 3. Activer l'environnement
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac  
source .venv/bin/activate
```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 5. Configuration base de données
```bash
# Migrations initiales
python manage.py makemigrations
python manage.py migrate

# Charger données initiales
python manage.py load_initial_data
```

### 6. Lancer le serveur de développement
```bash
python manage.py runserver
```

Le projet sera disponible sur : http://localhost:8000/

## 🔧 Commandes utiles

### Base de données

```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Charger données initiales (types défauts, profils, spécifications)
python manage.py load_initial_data

# Options avancées
python manage.py load_initial_data --clear          # Efface avant rechargement
python manage.py load_initial_data --only models    # Charge seulement certains modèles  
python manage.py load_initial_data --skip models    # Ignore certains modèles
python manage.py load_initial_data --dry-run        # Simulation sans execution
```

### Tests
```bash
# Tests complets
python manage.py test

# Tests d'une app spécifique
python manage.py test catalog --parallel
```

### Administration
```bash
# Créer super utilisateur (optionnel)
python manage.py createsuperuser

# Admin Django accessible sur :
# http://localhost:8000/admin/
```

## 🗃️ Reset base de données

Si besoin de repartir de zéro :
```bash
rm db.sqlite3
python manage.py migrate  
python manage.py load_initial_data
```

## 🚨 Dépannage

### Problème de migration
```bash
python manage.py makemigrations --empty [app_name]
python manage.py migrate --fake-initial
```

### Problème de dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Problème de permissions
```bash
# Vérifier que .venv est bien activé
which python
# Doit pointer vers .venv/bin/python
```

## 🎯 URLs principales après installation

- **Interface production V3** : `/`
- **Admin Django** : `/admin/`
- **Dashboard supervision** : `/management/`
- **Debug sessions** : `/admin/sessions/session/`

## 📝 Structure du projet après installation

```
django_SGQ-LigneG_beta/
├── .venv/                    # Environnement virtuel (pas versionné)
├── manage.py                 # Point d'entrée Django
├── db.sqlite3               # Base de données (créée après migrate)
├── requirements.txt         # Dépendances Python
├── CLAUDE.md               # Instructions pour Claude
├── catalog/                # App données de référence
├── production/             # App gestion production
├── quality/                # App contrôle qualité
├── frontendv3/             # App interface V3
├── wcm/                    # App indicateurs WCM
├── management/             # App dashboard supervision
└── ...
```