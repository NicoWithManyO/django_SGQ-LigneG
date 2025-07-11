# Plan de l'Application Reporting - Dashboard Chef d'Atelier

## 🎯 Objectif
Créer un dashboard temps réel pour la chef d'atelier permettant de superviser la production, identifier les problèmes et prendre des décisions rapides.

## 📊 Fonctionnalités Principales

### 1. **Dashboard Principal** (`/reporting/dashboard/`)
Vue d'ensemble en temps réel de la production

#### Indicateurs Clés (KPIs)
- **Production du jour**
  - Longueur totale produite (m)
  - Nombre de rouleaux
  - Taux de conformité (%)
  - Comparaison avec objectif journalier

- **Performance des Postes**
  - Temps d'ouverture (TO)
  - Temps disponible (TD) 
  - Temps perdu et causes principales
  - Taux de rendement (TD/TO)

- **Qualité**
  - Taux de rouleaux conformes/non-conformes
  - Défauts les plus fréquents
  - Tendance qualité sur 7 jours

### 2. **Vue Poste en Cours** (`/reporting/current-shift/`)
Monitoring du poste actuellement en production

- Opérateur actuel
- Progression OF en cours
- Métrages temps réel
- Alertes qualité en direct
- Temps d'arrêt cumulé

### 3. **Analyse des Temps d'Arrêt** (`/reporting/downtime/`)
- Top 5 des causes d'arrêt (graphique)
- Évolution sur la semaine/mois
- Analyse par vacation
- Temps d'arrêt par opérateur

### 4. **Suivi des Ordres de Fabrication** (`/reporting/of-tracking/`)
- Liste des OF en cours/terminés
- Taux d'avancement par OF
- Prévision de fin
- Historique de production par OF

### 5. **Rapports Périodiques** (`/reporting/reports/`)
- Rapport journalier automatique
- Rapport hebdomadaire
- Export Excel/PDF
- Envoi par email programmé

## 🗃️ Modèles de Données

### DashboardConfig
```python
class DashboardConfig(models.Model):
    """Configuration du dashboard pour chaque chef d'atelier"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    refresh_rate = models.IntegerField(default=30)  # secondes
    email_daily_report = models.BooleanField(default=True)
    alert_threshold_quality = models.DecimalField(max_digits=5, decimal_places=2, default=95.0)
    alert_threshold_downtime = models.IntegerField(default=30)  # minutes
```

### ProductionSnapshot
```python
class ProductionSnapshot(models.Model):
    """Capture périodique des métriques de production"""
    timestamp = models.DateTimeField(auto_now_add=True)
    shift = models.ForeignKey('production.Shift', on_delete=models.CASCADE)
    total_length = models.DecimalField(max_digits=10, decimal_places=2)
    conformity_rate = models.DecimalField(max_digits=5, decimal_places=2)
    downtime_minutes = models.IntegerField()
```

## 📐 Architecture Technique

### Views
- `DashboardView` - Vue principale avec WebSocket pour temps réel
- `CurrentShiftAPIView` - API REST pour données du poste en cours
- `DowntimeAnalyticsView` - Analyse des temps d'arrêt
- `ReportGeneratorView` - Génération des rapports

### Templates
- `reporting/dashboard.html` - Dashboard principal
- `reporting/components/` - Composants réutilisables
  - `kpi_card.html`
  - `production_chart.html`
  - `alert_panel.html`

### API Endpoints
- `/api/v1/reporting/current-metrics/` - Métriques temps réel
- `/api/v1/reporting/shift-performance/` - Performance par poste
- `/api/v1/reporting/quality-trends/` - Tendances qualité

### JavaScript/HTMX
- Auto-refresh des données via HTMX polling
- Charts.js pour les graphiques
- WebSocket pour alertes temps réel

## 🔔 Système d'Alertes

### Types d'Alertes
1. **Qualité** - Taux de conformité < seuil
2. **Production** - Retard sur objectif OF
3. **Temps d'arrêt** - Dépassement seuil
4. **Machine** - Non démarrée en début de poste

### Canaux de Notification
- Notification dans le dashboard
- Email (optionnel)
- SMS pour alertes critiques (futur)

## 📱 Responsive Design
- Optimisé pour tablettes (utilisation principale)
- Adaptatif desktop pour bureau
- Mode plein écran pour affichage mural

## 🔐 Permissions
- `view_dashboard` - Accès au dashboard
- `view_all_shifts` - Voir tous les postes
- `generate_reports` - Générer des rapports
- `configure_alerts` - Configurer les alertes

## 🚀 Phases de Développement

### Phase 1 - MVP (Sprint 1)
- Dashboard principal avec KPIs
- Vue poste en cours
- Refresh automatique

### Phase 2 - Analytics (Sprint 2)
- Analyse temps d'arrêt
- Graphiques de tendance
- Suivi OF

### Phase 3 - Reporting (Sprint 3)
- Génération rapports
- Export Excel/PDF
- Envoi email automatique

### Phase 4 - Alertes (Sprint 4)
- Système d'alertes
- Configuration personnalisée
- Notifications temps réel

## 🎨 Mockups Suggérés

### Dashboard Principal
```
+------------------+------------------+------------------+
|  Production Jour |  Taux Conformité |  Temps Perdu     |
|    1,250 m       |     97.5%        |    45 min        |
|    ↑ +12%        |     ↓ -1.2%      |    ↑ +15 min     |
+------------------+------------------+------------------+

+-----------------------------------------------------+
|         Graphique Production Temps Réel             |
|         (Courbe dernières 8 heures)                 |
+-----------------------------------------------------+

+-------------------------+---------------------------+
| Top Défauts (Pie Chart) | Temps d'Arrêt par Motif  |
+-------------------------+---------------------------+
```

## 📝 Notes Techniques

- Utiliser le cache Django pour optimiser les requêtes
- Implémenter des indexes sur les champs de date
- Prévoir l'archivage des données > 1 an
- API versionnée pour évolutions futures