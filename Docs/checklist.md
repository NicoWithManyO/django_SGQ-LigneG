# ✅ Django Enterprise Deployment Checklist  
### Pour contexte industriel sécurisé

---

## 🔐 Sécurité Django

- [ ] `DEBUG = False` en production
- [ ] `ALLOWED_HOSTS` correctement défini (pas de `*`)
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS > 0`
- [ ] `SECURE_BROWSER_XSS_FILTER = True`
- [ ] `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [ ] `X_FRAME_OPTIONS = "DENY"` ou `"SAMEORIGIN"` (au choix)

---

## 🛡️ Sécurité infrastructure / réseau

- [ ] Accès SSH restreint (IP internes uniquement)
- [ ] Authentification via SSO (SAML2 / Azure AD / OAuth2)
- [ ] Aucune donnée sensible en dur dans le code (`settings.py`)
- [ ] Variables sensibles dans `.env`, vault ou équivalent
- [ ] Accès via HTTPS uniquement (reverse proxy ou WAF)
- [ ] Logging centralisé (`Sentry`, `ELK`, `Syslog`, etc.)

---

## 🔄 Pipeline CI/CD

- [ ] Déploiement via pipeline (GitLab, Jenkins, Azure DevOps)
- [ ] Analyse de sécurité statique (`Bandit`, `SonarQube`, etc.)
- [ ] Tests automatisés (unitaires, intégration)
- [ ] Validation manuelle nécessaire pour la mise en prod

---

## 🗃️ Base de données

- [ ] Accès restreint à la DB (user + IP whitelistées)
- [ ] Aucun accès root DB depuis Django
- [ ] Backups réguliers + testés
- [ ] Champs `created_at` / `updated_at` présents

---

## 🔒 Authentification / Autorisations

- [ ] Authentification via SSO uniquement
- [ ] Groupes & permissions bien définis
- [ ] `/admin` protégé (accès limité IP + groupes)
- [ ] Mécanisme anti-brute-force (`django-axes`, rate limiting...)

---

## 🧪 Recette & Validation

- [ ] Environnement de recette identique à la prod
- [ ] Données anonymisées en préprod
- [ ] Recette fonctionnelle validée
- [ ] Erreurs suivies (logs, Sentry, emails...)

---

## 📦 Packaging & déploiement

- [ ] Image Docker propre (ex: `python:3.x-slim`)
- [ ] `requirements.txt` figé (avec versions précises)
- [ ] Pas de dépendances obsolètes / douteuses
- [ ] `collectstatic` exécuté avant déploiement
- [ ] `MEDIA_ROOT` et `STATIC_ROOT` isolés et sécurisés

---

## 📘 Documentation

- [ ] README clair (install, usage, déploiement)
- [ ] Diagramme d’architecture (PDF/MD)
- [ ] Schéma Django (`graph_models`, etc.)
- [ ] Guide utilisateur métier

---

## 🧯 Résilience & rollback

- [ ] Stratégie de rollback documentée
- [ ] Procédure de restauration DB testée
- [ ] Monitoring actif en place
- [ ] Uptime et alertes configurés

---

## 📜 Conformité RGPD / IT

- [ ] Données personnelles chiffrées (si sensibles)
- [ ] Données minimisées (pas de collecte inutile)
- [ ] Durée de conservation définie
- [ ] Responsable de traitement désigné

---


