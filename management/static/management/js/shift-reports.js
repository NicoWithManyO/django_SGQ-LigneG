function shiftReports() {
    return {
        // État
        shifts: [],
        operators: [],
        filters: {
            dateFrom: '',
            dateTo: '',
            operator: '',
            vacation: ''
        },
        loading: true,
        currentPage: 1,
        itemsPerPage: 20,
        totalItems: 0,
        shiftDetails: null,
        isLoadingShiftDetails: false,
        
        // Propriétés calculées
        get totalPages() {
            return Math.ceil(this.totalItems / this.itemsPerPage);
        },
        
        get pageNumbers() {
            const pages = [];
            const maxPages = 5;
            let start = Math.max(1, this.currentPage - Math.floor(maxPages / 2));
            let end = Math.min(this.totalPages, start + maxPages - 1);
            
            if (end - start + 1 < maxPages) {
                start = Math.max(1, end - maxPages + 1);
            }
            
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            return pages;
        },
        
        // Initialisation
        async init() {
            // Initialiser les filtres de date (7 derniers jours + 1 jour futur par défaut)
            const today = new Date();
            const tomorrow = new Date(today.getTime() + 1 * 24 * 60 * 60 * 1000);
            const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
            
            this.filters.dateTo = tomorrow.toISOString().split('T')[0];
            this.filters.dateFrom = lastWeek.toISOString().split('T')[0];
            
            // Charger les opérateurs
            await this.loadOperators();
            
            // Charger les shifts
            await this.loadShifts();
        },
        
        // Charger la liste des opérateurs
        async loadOperators() {
            try {
                const response = await fetch('/planification/api/operators/');
                if (!response.ok) throw new Error('Erreur chargement opérateurs');
                
                this.operators = await response.json();
            } catch (error) {
                console.error('Erreur opérateurs:', error);
                this.operators = [];
            }
        },
        
        // Charger les shifts
        async loadShifts() {
            this.loading = true;
            
            try {
                // Construire l'URL avec les paramètres
                const params = new URLSearchParams();
                if (this.filters.dateFrom) params.append('date_from', this.filters.dateFrom);
                if (this.filters.dateTo) params.append('date_to', this.filters.dateTo);
                if (this.filters.operator) params.append('operator', this.filters.operator);
                params.append('page', this.currentPage);
                params.append('page_size', this.itemsPerPage);
                
                const response = await fetch(`/management/api/shift-reports/?${params}`);
                if (!response.ok) throw new Error('Erreur chargement shifts');
                
                const data = await response.json();
                
                // Gérer la pagination
                if (data.results) {
                    this.shifts = data.results;
                    this.totalItems = data.count || 0;
                } else {
                    this.shifts = data;
                    this.totalItems = data.length;
                }
                
                // Calculer les KPIs pour chaque shift
                await this.calculateShiftKPIs();
                
            } catch (error) {
                console.error('Erreur shifts:', error);
                this.shifts = [];
                this.showError('Erreur lors du chargement des rapports');
            } finally {
                this.loading = false;
            }
        },
        
        // Calculer les KPIs pour chaque shift
        async calculateShiftKPIs() {
            // Les KPIs devraient être calculés côté serveur
            // Ici on peut enrichir avec des calculs côté client si nécessaire
            for (let shift of this.shifts) {
                // Calcul du TRS si non fourni
                if (!shift.trs && shift.total_length > 0) {
                    // Formule simplifiée, normalement calculée côté serveur
                    const qualityRate = this.getQualityRate(shift);
                    shift.trs = Math.round(qualityRate * 0.8); // Approximation
                }
            }
        },
        
        // Appliquer les filtres
        applyFilters() {
            this.currentPage = 1;
            this.loadShifts();
        },
        
        // Réinitialiser les filtres
        resetFilters() {
            this.filters = {
                dateFrom: '',
                dateTo: '',
                operator: '',
                vacation: ''
            };
            this.currentPage = 1;
            this.loadShifts();
        },
        
        // Changer de page
        changePage(page) {
            if (page < 1 || page > this.totalPages) return;
            this.currentPage = page;
            this.loadShifts();
        },
        
        // Exporter vers Excel
        async exportToExcel() {
            try {
                const params = new URLSearchParams();
                if (this.filters.dateFrom) params.append('date_from', this.filters.dateFrom);
                if (this.filters.dateTo) params.append('date_to', this.filters.dateTo);
                if (this.filters.operator) params.append('operator', this.filters.operator);
                params.append('format', 'excel');
                
                window.location.href = `/management/api/shift-reports/export/?${params}`;
                
            } catch (error) {
                console.error('Erreur export:', error);
                this.showError('Erreur lors de l\'export Excel');
            }
        },
        
        // Télécharger le PDF d'un shift
        async downloadPDF(shiftId) {
            try {
                window.location.href = `/management/api/shift-reports/${shiftId}/pdf/`;
            } catch (error) {
                console.error('Erreur PDF:', error);
                this.showError('Erreur lors du téléchargement du PDF');
            }
        },
        
        // Formatage des nombres
        formatNumber(value) {
            if (!value) return '0';
            return new Intl.NumberFormat('fr-FR').format(Math.round(value));
        },
        
        // Formatage des dates
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR');
        },
        
        // Calculer le taux de qualité
        getQualityRate(shift) {
            if (!shift.total_length || shift.total_length === 0) return 0;
            const okLength = shift.ok_length || 0;
            return Math.round((okLength / shift.total_length) * 100);
        },
        
        // Classe CSS selon le TRS
        getTRSClass(trs) {
            if (!trs) return 'bg-secondary';
            if (trs >= 80) return 'bg-success';
            if (trs >= 60) return 'bg-warning';
            return 'bg-danger';
        },
        
        // Afficher les détails d'un poste
        async showShiftDetails(shiftId) {
            this.isLoadingShiftDetails = true;
            this.shiftDetails = null;
            
            // Ouvrir la modal immédiatement avec le spinner
            const modalElement = document.getElementById('shiftDetailsModal');
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            try {
                const response = await fetch(`/management/api/shifts/${shiftId}/`);
                
                if (!response.ok) {
                    throw new Error('Erreur lors du chargement des détails');
                }
                
                const shiftDetails = await response.json();
                
                // Stocker les détails dans le contexte
                this.shiftDetails = shiftDetails;
                
            } catch (error) {
                console.error('Erreur détails poste:', error);
                this.showError('Impossible de charger les détails du poste');
                modal.hide();
            } finally {
                this.isLoadingShiftDetails = false;
            }
        },
        
        // Afficher une erreur
        showError(message) {
            // TODO: Implémenter une notification toast
            console.error(message);
            alert(message); // Temporaire
        }
    }
}