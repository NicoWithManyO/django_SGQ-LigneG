console.log('Dashboard JS loaded');

// Fonction utilitaire pour récupérer le token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Est-ce que ce cookie commence par le nom qu'on cherche ?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function managementDashboard() {
    console.log('managementDashboard function called');
    return {
        // État du dashboard
        kpis: {
            avg_trs: null,
            total_production: null,
            avg_quality: null,
            avg_availability: null
        },
        pendingChecklists: [],
        allChecklists: [],
        checklistTab: 'all', // Onglet actif par défaut : Toutes
        recentShifts: [],
        recentRolls: [],  // Liste des derniers rouleaux
        filteredRolls: [],  // Liste filtrée des rouleaux
        rollsLimit: 50,  // Nombre de rouleaux à afficher
        rollFilters: {  // Filtres pour les rouleaux
            of: '',
            showOk: true,    // Par défaut on affiche les OK
            showNok: true,   // Par défaut on affiche les NOK
            date: ''
        },
        alerts: [],
        dailyTrends: [],
        trendChart: null,
        loading: true,
        // Données d'humeur
        moodCounters: {},
        moodPercentages: {},
        moodTotal: 0,
        lastMoodReset: null,
        userDefaultVisa: '',  // Visa par défaut de l'utilisateur
        selectedDate: (() => {
            // Par défaut, afficher J-1 (hier)
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            return yesterday.toISOString().split('T')[0];
        })(),  // Date sélectionnée (J-1 par défaut)
        editMode: false,  // Mode édition de la date
        dateInput: '',  // Valeur du champ de saisie de date
        rollDetails: null,  // Détails du rouleau pour la modale
        shiftDetails: null,  // Détails du poste pour la modale
        
        // Propriétés calculées
        get displayedChecklists() {
            if (this.checklistTab === 'all') {
                return this.allChecklists;
            } else {
                return this.pendingChecklists;
            }
        },
        
        get pendingChecklistsCount() {
            return this.pendingChecklists.length;
        },
        
        // Initialisation
        init() {
            console.log('Dashboard init called');
            this.loadUserDefaultVisa();  // Charger le visa par défaut
            this.loadDashboardData();
            // Rafraîchissement automatique toutes les 30 secondes
            setInterval(() => this.loadDashboardData(), 30000);
        },
        
        // Chargement des données du dashboard
        async loadDashboardData() {
            try {
                console.log('Loading dashboard data...');
                let url = '/management/api/dashboard-stats/';
                
                // Toujours utiliser la date sélectionnée
                url += `?mode=custom&date=${this.selectedDate}`;
                
                const response = await fetch(url);
                if (!response.ok) throw new Error('Erreur lors du chargement');
                
                const data = await response.json();
                console.log('Dashboard data:', data);
                
                // Mise à jour des KPIs
                this.kpis = data.current_kpis || {};
                
                // Mise à jour des alertes
                this.alerts = data.alerts || [];
                
                // Mise à jour des tendances
                this.dailyTrends = data.daily_trends || [];
                
                // Mise à jour des données d'humeur
                if (data.mood_data) {
                    console.log('Mood data received:', data.mood_data);
                    this.moodCounters = data.mood_data.counters || {};
                    this.moodPercentages = data.mood_data.percentages || {};
                    this.moodTotal = data.mood_data.total || 0;
                    this.lastMoodReset = data.mood_data.last_reset || null;
                    console.log('Mood counters:', this.moodCounters);
                    console.log('Mood percentages:', this.moodPercentages);
                }
                
                // Charger les checklists en attente
                await this.loadPendingChecklists();
                
                // Charger toutes les checklists aussi
                await this.loadAllChecklists();
                
                // Charger les shifts récents
                await this.loadRecentShifts();
                
                // Charger les rouleaux récents
                await this.loadRecentRolls();
                
                // Mettre à jour le graphique
                this.updateTrendChart();
                
            } catch (error) {
                console.error('Erreur dashboard:', error);
                this.showError('Erreur lors du chargement des données');
            } finally {
                this.loading = false;
            }
        },
        
        // Chargement des checklists en attente
        async loadPendingChecklists() {
            try {
                const response = await fetch('/management/api/checklists/pending/');
                if (!response.ok) throw new Error('Erreur chargement checklists');
                
                const checklists = await response.json();
                // Ajouter les propriétés nécessaires pour le formulaire
                this.pendingChecklists = checklists.map(c => ({
                    ...c,
                    visa: this.userDefaultVisa || '',  // Utiliser le visa par défaut
                    isSubmitting: false
                }));
            } catch (error) {
                console.error('Erreur checklists:', error);
                this.pendingChecklists = [];
            }
        },
        
        // Chargement de toutes les checklists
        async loadAllChecklists() {
            try {
                const response = await fetch('/management/api/checklists/?days=7');
                if (!response.ok) throw new Error('Erreur chargement toutes checklists');
                
                const checklists = await response.json();
                // Ajouter les propriétés nécessaires pour le formulaire
                this.allChecklists = checklists.map(c => ({
                    ...c,
                    visa: c.management_visa || this.userDefaultVisa || '',  // Utiliser le visa par défaut si pas déjà visé
                    isSubmitting: false
                }));
            } catch (error) {
                console.error('Erreur toutes checklists:', error);
                this.allChecklists = [];
            }
        },
        
        // Chargement des shifts récents
        async loadRecentShifts() {
            try {
                const response = await fetch('/management/api/shift-reports/recent/?days=7&limit=10');
                if (!response.ok) throw new Error('Erreur chargement shifts');
                
                this.recentShifts = await response.json();
            } catch (error) {
                console.error('Erreur shifts:', error);
                this.recentShifts = [];
            }
        },
        
        // Mise à jour du graphique de tendance
        updateTrendChart() {
            const ctx = document.getElementById('trendChart');
            if (!ctx) return;
            
            // Détruire le graphique existant
            if (this.trendChart) {
                this.trendChart.destroy();
            }
            
            // Préparer les données
            const labels = this.dailyTrends.map(d => this.formatDate(d.date));
            const productionData = this.dailyTrends.map(d => d.total_production);
            const trsData = this.dailyTrends.map(d => d.avg_trs);
            
            // Créer le nouveau graphique
            this.trendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Production (m)',
                            data: productionData,
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.1)',
                            yAxisID: 'y-production',
                            tension: 0.4
                        },
                        {
                            label: 'TRS (%)',
                            data: trsData,
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.1)',
                            yAxisID: 'y-trs',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: false
                        }
                    },
                    scales: {
                        'y-production': {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Production (m)'
                            }
                        },
                        'y-trs': {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'TRS (%)'
                            },
                            min: 0,
                            max: 100,
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });
        },
        
        // Charger le visa par défaut de l'utilisateur
        async loadUserDefaultVisa() {
            try {
                const response = await fetch('/management/api/user-visa/');
                if (!response.ok) throw new Error('Erreur chargement visa');
                
                const data = await response.json();
                this.userDefaultVisa = data.default_visa || '';
                console.log('Visa par défaut chargé:', this.userDefaultVisa);
            } catch (error) {
                console.error('Erreur chargement visa par défaut:', error);
                this.userDefaultVisa = '';
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
            return date.toLocaleDateString('fr-FR', { 
                day: '2-digit', 
                month: '2-digit' 
            });
        },
        
        // Déterminer la classe CSS selon la valeur du TRS
        getTRSClass(trs) {
            if (trs >= 80) return 'bg-success';
            if (trs >= 60) return 'bg-warning';
            return 'bg-danger';
        },
        
        // Afficher une notification d'erreur
        showError(message) {
            this.showNotification(message, 'danger');
        },
        
        // Afficher une notification de succès
        showSuccess(message) {
            this.showNotification(message, 'success');
        },
        
        // Afficher une notification toast
        showNotification(message, type = 'info') {
            const toastContainer = document.querySelector('.toast-container');
            if (!toastContainer) {
                console.error('Container de toast non trouvé');
                alert(message); // Fallback
                return;
            }
            
            const toastHtml = `
                <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">
                            ${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            const toastElement = document.createElement('div');
            toastElement.innerHTML = toastHtml;
            const toast = toastElement.firstElementChild;
            toastContainer.appendChild(toast);
            
            const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
            bsToast.show();
            
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        },
        
        // Remplir toutes les cases de visa
        fillAllVisas() {
            // Utiliser en priorité le visa par défaut, sinon chercher une case remplie
            let visaToUse = this.userDefaultVisa;
            
            if (!visaToUse || visaToUse.length < 2) {
                // Si pas de visa par défaut, chercher la première case avec un visa valide
                visaToUse = this.displayedChecklists.find(c => !c.management_visa && c.visa && c.visa.length >= 2)?.visa;
                
                if (!visaToUse) {
                    alert('Veuillez d\'abord remplir au moins une case avec vos initiales ou définir un visa par défaut dans votre profil');
                    return;
                }
            }
            
            // Propager cette valeur dans toutes les cases vides non visées
            this.displayedChecklists.forEach(checklist => {
                if (!checklist.management_visa && !checklist.visa) {
                    checklist.visa = visaToUse;
                }
            });
        },
        
        // Valider un visa
        isValidVisa(visa) {
            return visa && visa.length >= 2;
        },
        
        // Envoyer la signature d'une checklist
        async sendChecklistSignature(checklist) {
            const response = await fetch(`/management/api/checklists/${checklist.id}/sign/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    visa: checklist.visa.toUpperCase()
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erreur lors de la signature');
            }
            
            return response;
        },
        
        // Signer une checklist individuelle
        async signChecklist(checklist) {
            if (!this.isValidVisa(checklist.visa)) {
                this.showError('Veuillez entrer des initiales valides (minimum 2 caractères)');
                return;
            }
            
            checklist.isSubmitting = true;
            
            try {
                await this.sendChecklistSignature(checklist);
                
                // Succès - mettre à jour les listes
                checklist.management_visa = checklist.visa.toUpperCase();
                checklist.management_visa_date = new Date().toISOString();
                
                // Retirer de la liste des pending
                this.pendingChecklists = this.pendingChecklists.filter(c => c.id !== checklist.id);
                
                // Si on est sur l'onglet "all", mettre à jour la checklist
                const allIndex = this.allChecklists.findIndex(c => c.id === checklist.id);
                if (allIndex !== -1) {
                    this.allChecklists[allIndex] = checklist;
                }
                
                this.showSuccess(`Checklist ${checklist.shift_id} visée avec succès`);
                
            } catch (error) {
                console.error('Erreur:', error);
                this.showError(`Erreur lors de la signature : ${error.message}`);
                checklist.isSubmitting = false;
            }
        },
        
        // Vérifier s'il y a des checklists à signer
        hasChecklistsToSign() {
            const checklistsToSign = this.displayedChecklists.slice(0, 5).filter(c => !c.management_visa);
            return checklistsToSign.length > 0 && (this.userDefaultVisa.length >= 2 || checklistsToSign.some(c => c.visa && c.visa.length >= 2));
        },
        
        // Signer toutes les checklists visibles
        async signAllChecklists() {
            // Traiter uniquement les checklists visibles non visées (maximum 5)
            const checklistsToSign = this.displayedChecklists.slice(0, 5).filter(c => !c.management_visa && this.isValidVisa(c.visa));
            
            if (checklistsToSign.length === 0) {
                this.showError('Veuillez remplir au moins une case avec des initiales valides (minimum 2 caractères)');
                return;
            }
            
            // Marquer toutes les checklists comme en cours de traitement
            checklistsToSign.forEach(c => c.isSubmitting = true);
            
            let successCount = 0;
            let failures = [];
            
            // Traiter les signatures en séquence pour éviter les conflits SQLite
            for (const checklist of checklistsToSign) {
                try {
                    await this.sendChecklistSignature(checklist);
                    
                    // Signature réussie
                    successCount++;
                    
                    // Mettre à jour les listes
                    checklist.management_visa = checklist.visa.toUpperCase();
                    checklist.management_visa_date = new Date().toISOString();
                    
                    // Retirer de la liste des pending
                    this.pendingChecklists = this.pendingChecklists.filter(c => c.id !== checklist.id);
                    
                    // Si on est sur l'onglet "all", mettre à jour la checklist
                    const allIndex = this.allChecklists.findIndex(c => c.id === checklist.id);
                    if (allIndex !== -1) {
                        this.allChecklists[allIndex] = checklist;
                    }
                    
                } catch (error) {
                    failures.push({
                        checklist,
                        error: error.message
                    });
                    checklist.isSubmitting = false;
                }
            }
            
            // Afficher le résumé
            if (successCount > 0) {
                this.showSuccess(`${successCount} checklist(s) visée(s) avec succès`);
            }
            
            if (failures.length > 0) {
                const errorMsg = failures.map(f => `${f.checklist.shift_id}: ${f.error}`).join('<br>');
                this.showError(`Erreur pour ${failures.length} checklist(s):<br>${errorMsg}`);
            }
        },
        
        // Confirmer le reset des compteurs d'humeur
        confirmResetMoodCounters() {
            if (confirm('Êtes-vous sûr de vouloir remettre à zéro tous les compteurs d\'humeur ?\n\nCette action est irréversible.')) {
                this.resetMoodCounters();
            }
        },
        
        // Reset des compteurs d'humeur
        async resetMoodCounters() {
            try {
                const response = await fetch('/api/mood-counter/reset/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Erreur lors du reset');
                }
                
                const data = await response.json();
                
                // Mettre à jour l'affichage
                this.moodCounters = {
                    happy: 0,
                    neutral: 0,
                    unhappy: 0,
                    no_response: 0
                };
                this.moodPercentages = {
                    happy: 0,
                    neutral: 0,
                    unhappy: 0,
                    no_response: 0
                };
                this.moodTotal = 0;
                this.lastMoodReset = data.reset_time || new Date().toLocaleString('fr-FR');
                
                this.showSuccess('Les compteurs d\'humeur ont été remis à zéro avec succès');
            } catch (error) {
                console.error('Erreur reset humeur:', error);
                this.showError('Erreur lors de la remise à zéro des compteurs');
            }
        },
        
        // Remplir et signer toutes les checklists en une seule action
        async fillAndSignAll() {
            // D'abord remplir tous les visas avec le visa par défaut
            if (this.userDefaultVisa && this.userDefaultVisa.length >= 2) {
                this.displayedChecklists.forEach(checklist => {
                    if (!checklist.management_visa && !checklist.visa) {
                        checklist.visa = this.userDefaultVisa;
                    }
                });
            } else {
                // Si pas de visa par défaut, utiliser fillAllVisas pour propager un visa existant
                this.fillAllVisas();
            }
            
            // Ensuite signer toutes les checklists
            await this.signAllChecklists();
        },
        
        // Changer de date (ajouter des jours)
        changeDate(days) {
            const currentDate = new Date(this.selectedDate);
            currentDate.setDate(currentDate.getDate() + days);
            this.selectedDate = currentDate.toISOString().split('T')[0];
            this.loadDashboardData();
        },
        
        // Vérifier si on peut aller en avant
        canGoForward() {
            const selected = new Date(this.selectedDate);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            selected.setHours(0, 0, 0, 0);
            return selected < today;
        },
        
        // Formater l'affichage de la date
        formatDateDisplay(dateString) {
            if (!dateString) return '--';
            const date = new Date(dateString);
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            return date.toLocaleDateString('fr-FR', options);
        },
        
        // Obtenir le résumé des postes du jour
        getDayShiftsSummary() {
            const shifts = this.kpis.shifts_count || 0;
            if (shifts === 0) return 'Aucun poste';
            if (shifts === 1) return '1 poste';
            if (shifts === 2) return '2 postes';
            if (shifts === 3) return '3 postes (journée complète)';
            return `${shifts} postes`;
        },
        
        // Charger les rouleaux récents
        async loadRecentRolls() {
            try {
                const response = await fetch(`/management/api/recent-rolls/?limit=${this.rollsLimit}`);
                if (!response.ok) throw new Error('Erreur chargement rouleaux');
                
                const data = await response.json();
                this.recentRolls = data;
                this.filterRolls();  // Appliquer les filtres après chargement
            } catch (error) {
                console.error('Erreur rouleaux:', error);
                this.recentRolls = [];
                this.filteredRolls = [];
            }
        },
        
        // Changer la limite d'affichage des rouleaux
        setRollsLimit(limit) {
            this.rollsLimit = limit;
            this.loadRecentRolls();
        },
        
        // Filtrer les rouleaux
        filterRolls() {
            // Si aucun filtre actif, afficher tous les rouleaux
            if (!this.hasActiveFilters()) {
                this.filteredRolls = [...this.recentRolls];
                return;
            }
            
            this.filteredRolls = this.recentRolls.filter(roll => {
                // Filtre OF
                if (this.rollFilters.of && !roll.roll_id.toLowerCase().includes(this.rollFilters.of.toLowerCase())) {
                    return false;
                }
                
                // Filtre statut (avec les checkboxes)
                if (!this.rollFilters.showOk && roll.is_conform) {
                    return false;
                }
                if (!this.rollFilters.showNok && !roll.is_conform) {
                    return false;
                }
                
                // Filtre date
                if (this.rollFilters.date) {
                    const rollDate = new Date(roll.created_at).toISOString().split('T')[0];
                    if (rollDate !== this.rollFilters.date) {
                        return false;
                    }
                }
                
                return true;
            });
        },
        
        // Réinitialiser les filtres
        resetRollFilters() {
            this.rollFilters = {
                of: '',
                showOk: true,
                showNok: true,
                date: ''
            };
            this.filterRolls();
        },
        
        // Vérifier si des filtres sont actifs
        hasActiveFilters() {
            return this.rollFilters.of || 
                   !this.rollFilters.showOk || 
                   !this.rollFilters.showNok || 
                   this.rollFilters.date;
        },
        
        // Appliquer la date saisie manuellement
        applyDateInput() {
            if (!this.dateInput) {
                this.editMode = false;
                return;
            }
            
            // Parser la date au format JJ/MM/AA ou JJ/MM/AAAA
            const parts = this.dateInput.split('/');
            if (parts.length !== 3) {
                this.showError('Format invalide. Utilisez JJ/MM/AA');
                return;
            }
            
            let day = parseInt(parts[0]);
            let month = parseInt(parts[1]) - 1;  // Les mois sont 0-indexés en JS
            let year = parseInt(parts[2]);
            
            // Gérer les années sur 2 chiffres
            if (year < 100) {
                year = 2000 + year;
            }
            
            // Valider la date
            const date = new Date(year, month, day);
            if (isNaN(date.getTime()) || date.getDate() !== day || date.getMonth() !== month) {
                this.showError('Date invalide');
                return;
            }
            
            // Vérifier que la date n'est pas dans le futur
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            if (date > today) {
                this.showError('La date ne peut pas être dans le futur');
                return;
            }
            
            // Appliquer la date
            this.selectedDate = date.toISOString().split('T')[0];
            this.editMode = false;
            this.dateInput = '';
            this.loadDashboardData();
        },
        
        // Afficher les détails d'un rouleau
        async showRollDetails(rollId) {
            try {
                // Charger les détails du rouleau
                const response = await fetch(`/management/api/rolls/${rollId}/`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    credentials: 'same-origin'
                });
                if (!response.ok) throw new Error(`Erreur ${response.status}: ${response.statusText}`);
                
                const rollDetails = await response.json();
                
                // Stocker les détails dans le contexte de la modale
                this.rollDetails = rollDetails;
                
                // Ouvrir la modale
                const modalElement = document.getElementById('rollDetailsModal');
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                
                // Construire la grille d'épaisseurs après un court délai
                setTimeout(() => {
                    this.buildThicknessGrid(rollDetails);
                }, 100);
                
            } catch (error) {
                console.error('Erreur détails rouleau:', error);
                this.showError('Impossible de charger les détails du rouleau');
            }
        },
        
        // Construire la grille d'épaisseurs
        buildThicknessGrid(rollDetails) {
            const tbody = document.getElementById('thicknessGridBody');
            if (!tbody || !rollDetails.thicknesses) return;
            
            tbody.innerHTML = '';
            
            // Grouper les épaisseurs par ligne
            const thicknessesByRow = {};
            rollDetails.thicknesses.forEach(t => {
                if (!thicknessesByRow[t.row]) {
                    thicknessesByRow[t.row] = {};
                }
                thicknessesByRow[t.row][t.col] = t;
            });
            
            // Grouper les défauts par position
            const defectsByPosition = {};
            if (rollDetails.defects) {
                rollDetails.defects.forEach(d => {
                    if (!defectsByPosition[d.position]) {
                        defectsByPosition[d.position] = [];
                    }
                    defectsByPosition[d.position].push(d);
                });
            }
            
            // Colonnes dans l'ordre
            const columns = ['GG', 'GC', 'GD', 'length', 'DG', 'DC', 'DD'];
            
            // Obtenir toutes les positions (épaisseurs + défauts)
            const allPositions = new Set([
                ...Object.keys(thicknessesByRow).map(p => parseInt(p)),
                ...Object.keys(defectsByPosition).map(p => parseInt(p))
            ]);
            
            // Créer les lignes
            Array.from(allPositions).sort((a, b) => a - b).forEach(rowNum => {
                const row = document.createElement('tr');
                
                // Colonnes d'épaisseur
                columns.forEach(col => {
                    const cell = document.createElement('td');
                    cell.className = 'text-center';
                    
                    const thickness = thicknessesByRow[rowNum] && thicknessesByRow[rowNum][col];
                    const defectsAtPosition = defectsByPosition[rowNum] || [];
                    
                    if (thickness) {
                        const valueSpan = document.createElement('span');
                        valueSpan.textContent = thickness.value.toFixed(2);
                        
                        // Ajouter un indicateur de rattrapage
                        if (thickness.is_catchup) {
                            const catchupIcon = document.createElement('sup');
                            catchupIcon.textContent = 'R';
                            catchupIcon.className = 'text-info fw-bold ms-1';
                            catchupIcon.title = 'Rattrapage';
                            valueSpan.appendChild(catchupIcon);
                        }
                        
                        // Appliquer le code couleur
                        const status = this.getThicknessStatus(thickness.value, rollDetails.thickness_spec);
                        if (status === 'nok' || thickness.is_nok) {
                            valueSpan.className = 'text-danger fw-bold';
                        } else if (status === 'alert') {
                            valueSpan.className = 'text-warning';
                        } else {
                            valueSpan.className = 'text-success';
                        }
                        
                        cell.appendChild(valueSpan);
                        
                        // Ajouter les défauts pour cette position et colonne
                        const defectsForCol = defectsAtPosition.filter(d => {
                            if (!d.side) return true;
                            // Mapper la position latérale vers la colonne
                            const sideMapping = {
                                'Gauche Gauche': 'GG',
                                'Gauche Centre': 'GC',
                                'Gauche Droite': 'GD',
                                'Droite Gauche': 'DG',
                                'Droite Centre': 'DC',
                                'Droite Droite': 'DD'
                            };
                            const mappedSide = sideMapping[d.side] || d.side;
                            return mappedSide === col;
                        });
                        
                        if (defectsForCol.length > 0) {
                            const defectBadge = document.createElement('span');
                            // Utiliser la couleur selon la sévérité
                            const severity = defectsForCol[0].severity;
                            const badgeClass = severity === 'blocking' ? 'bg-danger' : 'bg-warning text-dark';
                            defectBadge.className = `badge ${badgeClass} ms-1`;
                            defectBadge.style.fontSize = '0.65rem';
                            defectBadge.style.padding = '0.1rem 0.3rem';
                            defectBadge.textContent = defectsForCol[0].type.substring(0, 3);
                            defectBadge.title = defectsForCol.map(d => d.type).join(', ');
                            cell.appendChild(defectBadge);
                        }
                    } else if (col === 'length') {
                        // Colonne longueur affiche la position
                        cell.textContent = `${rowNum} m`;
                        cell.className += ' text-muted';
                    } else {
                        // Vérifier s'il y a un défaut sans épaisseur
                        const defectsForCol = defectsAtPosition.filter(d => {
                            if (!d.side) return false;
                            const sideMapping = {
                                'Gauche Gauche': 'GG',
                                'Gauche Centre': 'GC',
                                'Gauche Droite': 'GD',
                                'Droite Gauche': 'DG',
                                'Droite Centre': 'DC',
                                'Droite Droite': 'DD'
                            };
                            const mappedSide = sideMapping[d.side] || d.side;
                            return mappedSide === col;
                        });
                        
                        if (defectsForCol.length > 0) {
                            const defectBadge = document.createElement('span');
                            // Utiliser la couleur selon la sévérité
                            const severity = defectsForCol[0].severity;
                            const badgeClass = severity === 'blocking' ? 'bg-danger' : 'bg-warning text-dark';
                            defectBadge.className = `badge ${badgeClass}`;
                            defectBadge.style.fontSize = '0.7rem';
                            defectBadge.textContent = defectsForCol[0].type;
                            defectBadge.title = defectsForCol.map(d => d.type).join(', ');
                            cell.appendChild(defectBadge);
                        } else {
                            cell.textContent = '--';
                            cell.className += ' text-muted';
                        }
                    }
                    
                    row.appendChild(cell);
                });
                
                tbody.appendChild(row);
            });
        },
        
        // Déterminer le statut d'une épaisseur
        getThicknessStatus(value, spec) {
            if (!spec) return 'ok';
            
            if (value < spec.min || value > spec.max) {
                return 'nok';
            } else if (
                (spec.alert_min && value <= spec.alert_min) || 
                (spec.alert_max && value >= spec.alert_max)
            ) {
                return 'alert';
            }
            return 'ok';
        },
        
        // Afficher une erreur
        showError(message) {
            // Utiliser une alerte Bootstrap ou un toast
            alert(message);
        },
        
        // Afficher les détails d'un poste
        async showShiftDetails(shiftId) {
            try {
                // Charger les détails du poste
                const response = await fetch(`/management/api/shifts/${shiftId}/`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    credentials: 'same-origin'
                });
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                    console.error('Erreur API:', response.status, errorData);
                    throw new Error(`Erreur ${response.status}: ${errorData.detail || errorData.error || response.statusText}`);
                }
                
                const shiftDetails = await response.json();
                
                // Stocker les détails dans le contexte
                this.shiftDetails = shiftDetails;
                
                // Ouvrir la modale
                const modalElement = document.getElementById('shiftDetailsModal');
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                
            } catch (error) {
                console.error('Erreur détails poste:', error);
                this.showError('Impossible de charger les détails du poste');
            }
        }
    }
}