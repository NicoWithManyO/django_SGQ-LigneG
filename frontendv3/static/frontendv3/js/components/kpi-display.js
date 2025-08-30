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
                
                // Mettre à jour les bordures KPI (supprimez cette ligne pour désactiver)
                this.$nextTick(() => this.updateKpiTiers());
            });
            
            // Appliquer les tiers initiaux (supprimez cette ligne pour désactiver)
            this.$nextTick(() => this.updateKpiTiers());
        },
        
        // Utiliser la méthode du service pour formater
        formatMinutes(totalMinutes) {
            return window.kpiService ? window.kpiService.formatMinutes(totalMinutes) : '--';
        },
        
        // Calculer la longueur OK affichée
        get longueurOKAffichee() {
            return Math.max(0, this.longueurEnroulee - this.longueurRouleauxNOK);
        },
        
        /* ============================================ */
        /* DEBUT - Calcul des tiers pour bordures KPI */
        /* ============================================ */
        // Supprimez cette section pour retirer la fonctionnalité
        
        // Calculer le tier en fonction du pourcentage
        getPercentageTier(percentage) {
            if (percentage >= 90) return 'excellent';
            if (percentage >= 80) return 'good';
            if (percentage >= 60) return 'moderate';
            if (percentage >= 40) return 'low';
            return 'critical';
        },
        
        // Appliquer les data attributes pour le CSS
        updateKpiTiers() {
            // Trouver le conteneur des KPI
            const kpiContainer = this.$el || document.querySelector('[x-data="kpiDisplay()"]');
            if (!kpiContainer) return;
            
            const cards = kpiContainer.querySelectorAll('.kpi-card');
            
            // Disponibilité (1ère carte)
            if (cards[0]) {
                cards[0].setAttribute('data-percentage-tier', this.getPercentageTier(this.disponibilitePercentage));
                cards[0].style.setProperty('--kpi-percentage', `${this.disponibilitePercentage}%`);
            }
            
            // Performance (2ème carte)
            if (cards[1]) {
                cards[1].setAttribute('data-percentage-tier', this.getPercentageTier(this.performancePercentage));
                cards[1].style.setProperty('--kpi-percentage', `${this.performancePercentage}%`);
            }
            
            // Qualité (3ème carte)
            if (cards[2]) {
                cards[2].setAttribute('data-percentage-tier', this.getPercentageTier(this.qualitePercentage));
                cards[2].style.setProperty('--kpi-percentage', `${this.qualitePercentage}%`);
            }
            
            // TRS Global (4ème carte)
            if (cards[3]) {
                cards[3].setAttribute('data-percentage-tier', this.getPercentageTier(this.trsGlobal));
                cards[3].style.setProperty('--kpi-percentage', `${this.trsGlobal}%`);
            }
        }
        
        /* ============================================ */
        /* FIN - Calcul des tiers pour bordures KPI */
        /* ============================================ */
    };
}

// Export global pour Alpine
window.kpiDisplay = kpiDisplay;