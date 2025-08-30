# Guide de déploiement

## 🚀 Déploiement Production

### Prérequis serveur
- **Python 3.12+**
- **PostgreSQL 13+** (recommandé pour production)
- **Nginx** (serveur web)
- **Gunicorn** (serveur WSGI)
- **Supervisor** (gestion processus)

## 📦 Préparation du déploiement

### 1. Configuration de production
```python
# settings/production.py
DEBUG = False
ALLOWED_HOSTS = ['votre-domaine.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sgq_ligne_g',
        'USER': 'sgq_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. Variables d'environnement
```bash
# .env
SECRET_KEY=your-super-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/sgq_ligne_g
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
```

### 3. Collecte des fichiers statiques
```bash
python manage.py collectstatic --noinput
```

## 🐧 Installation serveur Ubuntu

### 1. Dépendances système
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
sudo apt install postgresql postgresql-contrib
sudo apt install nginx supervisor
sudo apt install git
```

### 2. Configuration PostgreSQL
```bash
sudo -u postgres psql

CREATE DATABASE sgq_ligne_g;
CREATE USER sgq_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE sgq_ligne_g TO sgq_user;
ALTER USER sgq_user CREATEDB;
\q
```

### 3. Déploiement application
```bash
# Créer utilisateur dédié
sudo adduser sgq
sudo su - sgq

# Cloner le projet
git clone https://github.com/your-repo/sgq-ligne-g.git
cd sgq-ligne-g

# Environnement virtuel
python3.12 -m venv .venv
source .venv/bin/activate

# Dépendances
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Configuration
cp .env.example .env
# Éditer .env avec les bonnes valeurs

# Base de données
python manage.py migrate
python manage.py load_initial_data
python manage.py collectstatic --noinput
```

## ⚙️ Configuration Gunicorn

### gunicorn.conf.py
```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
```

### Service systemd
```ini
# /etc/systemd/system/sgq-gunicorn.service
[Unit]
Description=SGQ Ligne G Gunicorn
After=network.target

[Service]
User=sgq
Group=sgq
WorkingDirectory=/home/sgq/sgq-ligne-g
ExecStart=/home/sgq/sgq-ligne-g/.venv/bin/gunicorn --config gunicorn.conf.py wcm.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable sgq-gunicorn
sudo systemctl start sgq-gunicorn
```

## 🔧 Configuration Nginx

### /etc/nginx/sites-available/sgq-ligne-g
```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location /static/ {
        alias /home/sgq/sgq-ligne-g/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/sgq/sgq-ligne-g/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 100M;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/sgq-ligne-g /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 SSL avec Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

## 📊 Monitoring et logs

### Configuration Supervisor
```ini
# /etc/supervisor/conf.d/sgq-ligne-g.conf
[program:sgq-gunicorn]
command=/home/sgq/sgq-ligne-g/.venv/bin/gunicorn --config gunicorn.conf.py wcm.wsgi:application
directory=/home/sgq/sgq-ligne-g
user=sgq
autostart=true
autorestart=true
stdout_logfile=/var/log/sgq/gunicorn.log
stderr_logfile=/var/log/sgq/gunicorn-error.log
```

### Rotation des logs
```bash
# /etc/logrotate.d/sgq
/var/log/sgq/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 sgq sgq
}
```

## 🔄 Script de déploiement automatisé

### deploy.sh
```bash
#!/bin/bash
set -e

echo "🚀 Début du déploiement..."

# Pull des dernières modifications
git pull origin main

# Activation environnement virtuel
source .venv/bin/activate

# Mise à jour dépendances
pip install -r requirements.txt

# Migrations base de données
python manage.py migrate

# Collecte fichiers statiques
python manage.py collectstatic --noinput

# Redémarrage services
sudo systemctl reload sgq-gunicorn
sudo systemctl reload nginx

echo "✅ Déploiement terminé avec succès!"
```

## 🏠 Mode local (développement)

### Docker Compose (optionnel)
```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: sgq_ligne_g
      POSTGRES_USER: sgq_user
      POSTGRES_PASSWORD: sgq_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data/

volumes:
  postgres_data:
```

## 🚨 Sauvegarde et restauration

### Sauvegarde base de données
```bash
pg_dump sgq_ligne_g > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restauration
```bash
psql sgq_ligne_g < backup_20240829_143000.sql
```

## 🔧 Maintenance

### Mise à jour de sécurité
```bash
# Mise à jour système
sudo apt update && sudo apt upgrade

# Mise à jour dépendances Python
pip install --upgrade -r requirements.txt

# Vérification sécurité Django
python manage.py check --deploy
```