# SGQ Ligne G - Documentation

## 📋 Vue d'ensemble

SGQ Ligne G est un système de gestion de production et de qualité pour l'industrie de la fibre optique, spécifiquement conçu pour la ligne de production G.

**Stack technique :** Django 5.2.4 + Alpine.js 3.x + Bootstrap 5.3

## 🚀 Démarrage rapide

1. **Installation** : Voir [INSTALLATION.md](INSTALLATION.md)
2. **API** : Voir [API.md](API.md) 
3. **Frontend** : Voir [FRONTEND.md](FRONTEND.md)
4. **Déploiement** : Voir [DEPLOYMENT.md](DEPLOYMENT.md)

## 📖 Fonctionnalités principales

### Production
- Suivi en temps réel des ordres de fabrication (OF)
- Gestion des rouleaux avec numérotation automatique
- Traçabilité complète de la production
- Calcul automatique des métrages et grammages

### Contrôle Qualité
- Check-list de prise de poste obligatoire
- Enregistrement des défauts par position
- Contrôle des épaisseurs avec validation automatique
- Suivi de conformité en temps réel

### Indicateurs de Performance  
- TRS (Taux de Rendement Synthétique) global
- Taux de qualité et conformité
- Performance de production
- Suivi des temps perdus avec catégorisation

### Gestion Opérateurs
- Identification unique par opérateur
- Traçabilité des actions et validations
- Gestion des vacations (Matin/Après-midi/Nuit)

## 🏗️ Architecture

### Apps Django
- **catalog/** - Données de référence (profils, spécifications, défauts)
- **production/** - Gestion des shifts et rouleaux
- **quality/** - Contrôles qualité et conformité  
- **wcm/** - Indicateurs WCM et calculs TRS
- **planification/** - Gestion opérateurs et OF
- **frontendv3/** - Interface utilisateur V3 (Alpine.js)
- **management/** - Dashboard supervision
- **exporting/** - Export Excel

### Frontend V3
- Architecture Alpine.js avec composants modulaires
- Session Django pour persistence automatique
- Communication par events JavaScript
- Validation temps réel et feedback immédiat

## 📚 Convention linguistique

- **Communication** avec Claude : français
- **Code** : anglais
- **Commentaires** : français  
- **UI et documentation** : français

## 🔗 Navigation rapide

- [Guide d'installation](INSTALLATION.md)
- [Documentation API](API.md)
- [Guide développement Frontend](FRONTEND.md)
- [Guide de déploiement](DEPLOYMENT.md)
- [Historique des versions](CHANGELOG.md)

## 📞 Support

Pour toute question ou problème, consulter le fichier `CLAUDE.md` à la racine du projet.