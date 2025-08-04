/**
 * Composant Alpine.js : Affichage des KPI
 * Responsabilité unique : afficher les indicateurs calculés par le service KPI
 */

function kpiDisplay() {
    return {
        // État local synchronisé avec le service
        TO: 0,
        TD: 0,
        disponibilitePercentage: 0,
        longueurEnroulable: 0,
        longueurEnroulee: 0,
        performancePercentage: 0,
        qualitePercentage: 0,
        longueurRouleauxOK: 0,
        longueurRouleauxNOK: 0,
        trsGlobal: 0,
        
        // Initialisation
        init() {
            debug('KPI Display initialized');
            
            // Charger les valeurs initiales depuis le service
            if (window.kpiService) {
                this.TO = window.kpiService.TO;
                this.TD = window.kpiService.TD;
                this.disponibilitePercentage = window.kpiService.disponibilitePercentage;
                this.longueurEnroulable = window.kpiService.longueurEnroulable;
                this.longueurEnroulee = window.kpiService.longueurEnroulee;
                this.performancePercentage = window.kpiService.performancePercentage;
                this.qualitePercentage = window.kpiService.qualitePercentage;
                this.longueurRouleauxOK = window.kpiService.longueurRouleauxOK;
                this.longueurRouleauxNOK = window.kpiService.longueurRouleauxNOK;
                this.trsGlobal = window.kpiService.trsGlobal;
            }
            
            // Écouter les mises à jour du service
            window.addEventListener('kpi-updated', (e) => {
                this.TO = e.detail.TO;
                this.TD = e.detail.TD;
                this.disponibilitePercentage = e.detail.disponibilitePercentage;
                this.longueurEnroulable = e.detail.longueurEnroulable;
                this.longueurEnroulee = e.detail.longueurEnroulee;
                this.performancePercentage = e.detail.performancePercentage;
                this.qualitePercentage = e.detail.qualitePercentage;
                this.longueurRouleauxOK = e.detail.longueurRouleauxOK;
                this.longueurRouleauxNOK = e.detail.longueurRouleauxNOK;
                this.trsGlobal = e.detail.trsGlobal;
            });
        },
        
        // Utiliser la méthode du service pour formater
        formatMinutes(totalMinutes) {
            return window.kpiService ? window.kpiService.formatMinutes(totalMinutes) : '--';
        },
        
        // Calculer la longueur OK affichée
        get longueurOKAffichee() {
            return Math.max(0, this.longueurEnroulee - this.longueurRouleauxNOK);
        }
    };
}

// Export global pour Alpine
window.kpiDisplay = kpiDisplay;