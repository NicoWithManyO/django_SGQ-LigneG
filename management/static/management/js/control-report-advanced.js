/**
 * Interface RC Avancée - Sélection ergonomique de rouleaux
 * Interface Alpine.js pour la sélection avancée de rouleaux conformes
 */
function advancedRCApp() {
    return {
        // État principal
        loading: false,
        darkMode: false,
        
        // Données
        availableRolls: [],
        filteredRolls: [],
        selectedRolls: [],
        operators: [],
        
        // Filtres
        filters: {
            of: '',
            date: '',
            minLength: '',
            maxLength: '',
            operator: ''
        },
        searchQuery: '',
        
        // Pagination
        currentPage: 1,
        itemsPerPage: 100,
        
        // Options d'affichage
        showAssigned: false,
        
        // Génération du rapport
        reportName: '',
        
        /**
         * Initialisation du composant
         */
        init() {
            this.loadTheme();
            this.generateReportName();
            this.loadData();
            
            // Configurer le drag & drop après un court délai pour s'assurer que le DOM est prêt
            setTimeout(() => {
                this.setupDragAndDrop();
            }, 100);
        },
        
        /**
         * Charge le thème depuis localStorage
         */
        loadTheme() {
            this.darkMode = localStorage.getItem('advanced-rc-dark-mode') === 'true';
            this.applyTheme();
        },
        
        /**
         * Applique le thème actuel
         */
        applyTheme() {
            if (this.darkMode) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        },
        
        /**
         * Toggle le thème sombre/clair
         */
        toggleTheme() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('advanced-rc-dark-mode', this.darkMode.toString());
            this.applyTheme();
        },
        
        /**
         * Génère automatiquement un nom de rapport
         */
        generateReportName() {
            const now = new Date();
            const year = now.getFullYear().toString().slice(-2);
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hour = String(now.getHours()).padStart(2, '0');
            const minute = String(now.getMinutes()).padStart(2, '0');
            
            this.reportName = `S${year}${month}${day}${hour}${minute}`;
        },
        
        /**
         * Charge les données depuis l'API
         */
        async loadData() {
            this.loading = true;
            try {
                // Construire les paramètres de l'API
                const params = new URLSearchParams();
                if (this.showAssigned) {
                    params.append('show_assigned', 'true');
                }
                
                // Charger les rouleaux conformes disponibles
                const rollsResponse = await fetch(`/management/api/conforming-rolls/?${params}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });
                if (rollsResponse.ok) {
                    const data = await rollsResponse.json();
                    // L'API retourne probablement { results: [...] } comme la page normale
                    this.availableRolls = data.results || data || [];
                    this.filterRolls();
                } else {
                    console.error('Erreur lors du chargement des rouleaux:', rollsResponse.status);
                    this.showError('Erreur lors du chargement des rouleaux');
                }
                
                // Charger les opérateurs (optionnel - ne pas bloquer si ça échoue)
                try {
                    const operatorsResponse = await fetch('/planification/api/operators/');
                    if (operatorsResponse.ok) {
                        this.operators = await operatorsResponse.json();
                    } else {
                        console.warn('API opérateurs non disponible, filtrage par opérateur désactivé');
                        this.operators = [];
                    }
                } catch (operatorError) {
                    console.warn('Erreur lors du chargement des opérateurs:', operatorError);
                    this.operators = [];
                }
            } catch (error) {
                console.error('Erreur lors du chargement des données:', error);
                this.showError('Erreur lors du chargement des données');
            }
            this.loading = false;
        },
        
        /**
         * Filtre les rouleaux selon les critères
         */
        filterRolls() {
            // S'assurer que availableRolls est un tableau
            if (!Array.isArray(this.availableRolls)) {
                this.availableRolls = [];
                this.filteredRolls = [];
                return;
            }
            
            // Commencer par exclure les rouleaux déjà sélectionnés
            let filtered = this.availableRolls.filter(roll => 
                !this.selectedRolls.includes(roll.id)
            );
            
            // Filtre par recherche générale
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                filtered = filtered.filter(roll => 
                    roll.roll_id.toLowerCase().includes(query) ||
                    roll.fabrication_order.toString().includes(query) ||
                    (roll.operator && roll.operator.toLowerCase().includes(query))
                );
            }
            
            // Filtre par OF
            if (this.filters.of) {
                filtered = filtered.filter(roll => 
                    roll.fabrication_order.toString() === this.filters.of
                );
            }
            
            // Filtre par date
            if (this.filters.date) {
                filtered = filtered.filter(roll => {
                    const rollDate = new Date(roll.created_at).toISOString().split('T')[0];
                    return rollDate === this.filters.date;
                });
            }
            
            // Filtre par longueur min
            if (this.filters.minLength) {
                filtered = filtered.filter(roll => 
                    parseFloat(roll.length) >= parseFloat(this.filters.minLength)
                );
            }
            
            // Filtre par longueur max
            if (this.filters.maxLength) {
                filtered = filtered.filter(roll => 
                    parseFloat(roll.length) <= parseFloat(this.filters.maxLength)
                );
            }
            
            // Filtre par opérateur
            if (this.filters.operator) {
                filtered = filtered.filter(roll => 
                    roll.operator_id === parseInt(this.filters.operator)
                );
            }
            
            this.filteredRolls = filtered;
            this.currentPage = 1; // Reset pagination
        },
        
        /**
         * Efface tous les filtres
         */
        clearFilters() {
            this.filters = {
                of: '',
                date: '',
                minLength: '',
                maxLength: '',
                operator: ''
            };
            this.searchQuery = '';
            this.showAssigned = false;
            this.itemsPerPage = 12;
            this.currentPage = 1;
            this.loadData(); // Recharger avec les nouveaux paramètres
        },
        
        /**
         * Toggle sélection d'un rouleau
         */
        toggleRollSelection(rollId) {
            const index = this.selectedRolls.indexOf(rollId);
            if (index === -1) {
                // Ajout : animer la disparition du rouleau puis l'ajouter
                this.animateRollRemoval(rollId, () => {
                    this.selectedRolls.push(rollId);
                    this.filterRolls();
                });
            } else {
                // Retrait : retirer immédiatement et refiltrer avec animation d'apparition
                this.selectedRolls.splice(index, 1);
                this.filterRolls();
                // Animer l'apparition du rouleau qui revient dans la liste
                setTimeout(() => this.animateRollAppearance(rollId), 50);
            }
        },
        
        /**
         * Retire un rouleau de la sélection
         */
        removeFromSelection(rollId) {
            const index = this.selectedRolls.indexOf(rollId);
            if (index !== -1) {
                this.selectedRolls.splice(index, 1);
                // Refiltrer pour que le rouleau réapparaisse dans la liste du bas
                this.filterRolls();
            }
        },
        
        /**
         * Vide la sélection
         */
        clearSelection() {
            this.selectedRolls = [];
            // Refiltrer pour que tous les rouleaux réapparaissent dans la liste du bas
            this.filterRolls();
        },
        
        /**
         * Sélectionne tout un OF
         */
        selectEntireOF(ofNumber) {
            const ofRolls = this.availableRolls.filter(roll => 
                roll.fabrication_order === ofNumber
            );
            
            ofRolls.forEach(roll => {
                if (!this.selectedRolls.includes(roll.id)) {
                    this.selectedRolls.push(roll.id);
                }
            });
            // Refiltrer pour mettre à jour la liste du bas
            this.filterRolls();
        },
        
        /**
         * Récupère un rouleau par son ID
         */
        getRollById(rollId) {
            return this.availableRolls.find(roll => roll.id === rollId);
        },
        
        /**
         * Calcule la longueur totale sélectionnée
         */
        getTotalLength() {
            return this.selectedRolls.reduce((total, rollId) => {
                const roll = this.getRollById(rollId);
                return total + (roll ? parseFloat(roll.length) : 0);
            }, 0).toFixed(1);
        },
        
        /**
         * Récupère les OF uniques dans la sélection
         */
        getUniqueOFs() {
            const ofs = this.selectedRolls.map(rollId => {
                const roll = this.getRollById(rollId);
                return roll ? roll.fabrication_order : null;
            }).filter(of => of !== null);
            
            return [...new Set(ofs)];
        },
        
        /**
         * Configuration de la pagination
         */
        get paginatedRolls() {
            const start = (this.currentPage - 1) * this.itemsPerPage;
            const end = start + this.itemsPerPage;
            return this.filteredRolls.slice(start, end);
        },
        
        get totalPages() {
            return Math.ceil(this.filteredRolls.length / this.itemsPerPage);
        },
        
        get pageNumbers() {
            const pages = [];
            const maxPages = Math.min(5, this.totalPages);
            let startPage = Math.max(1, this.currentPage - Math.floor(maxPages / 2));
            let endPage = Math.min(this.totalPages, startPage + maxPages - 1);
            
            if (endPage - startPage < maxPages - 1) {
                startPage = Math.max(1, endPage - maxPages + 1);
            }
            
            for (let i = startPage; i <= endPage; i++) {
                pages.push(i);
            }
            return pages;
        },
        
        /**
         * Change de page
         */
        changePage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
            }
        },
        
        /**
         * Formate une date pour affichage
         */
        formatDate(dateString) {
            return new Date(dateString).toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: '2-digit'
            });
        },
        
        /**
         * Configuration du drag and drop
         */
        setupDragAndDrop() {
            // Ajouter les événements sur la zone de drop
            const selectedZone = document.querySelector('.selected-zone .card-body');
            if (selectedZone) {
                selectedZone.addEventListener('dragover', this.handleDragOver.bind(this));
                selectedZone.addEventListener('drop', this.handleDrop.bind(this));
                selectedZone.addEventListener('dragenter', this.handleDragEnter.bind(this));
                selectedZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
            }
        },
        
        /**
         * Début de drag
         */
        dragStart(event, rollId) {
            event.dataTransfer.setData('text/plain', rollId);
            event.dataTransfer.effectAllowed = 'move';
        },
        
        /**
         * Gestion du dragover
         */
        handleDragOver(event) {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'move';
        },
        
        /**
         * Gestion du dragenter
         */
        handleDragEnter(event) {
            event.preventDefault();
            event.target.closest('.selected-zone').classList.add('drag-over');
        },
        
        /**
         * Gestion du dragleave
         */
        handleDragLeave(event) {
            // Ne retirer la classe que si on sort vraiment de la zone
            const selectedZone = event.target.closest('.selected-zone');
            if (selectedZone && !selectedZone.contains(event.relatedTarget)) {
                selectedZone.classList.remove('drag-over');
            }
        },
        
        /**
         * Gestion du drop
         */
        handleDrop(event) {
            event.preventDefault();
            const rollId = parseInt(event.dataTransfer.getData('text/plain'));
            
            // Retirer l'effet visuel
            event.target.closest('.selected-zone').classList.remove('drag-over');
            
            // Ajouter le rouleau à la sélection s'il n'y est pas déjà
            if (rollId && !this.selectedRolls.includes(rollId)) {
                this.selectedRolls.push(rollId);
                // Refiltrer pour mettre à jour la liste du bas
                this.filterRolls();
            }
        },
        
        /**
         * Génère le rapport PDF
         */
        async generateReport() {
            if (this.selectedRolls.length === 0 || !this.reportName.trim()) {
                this.showError('Veuillez sélectionner des rouleaux et saisir un nom de rapport');
                return;
            }
            
            this.loading = true;
            try {
                const response = await fetch('/management/api/generate-control-report/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({
                        roll_ids: this.selectedRolls,
                        report_name: this.reportName.trim()
                    })
                });
                
                if (response.ok) {
                    // Télécharger le PDF
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${this.reportName.trim()}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    this.showSuccess(`Rapport ${this.reportName.trim()}.pdf généré avec succès`);
                    
                    // Actualiser les données pour refléter les assignations
                    await this.loadData();
                    this.clearSelection();
                    this.generateReportName();
                } else {
                    const error = await response.json();
                    this.showError(error.error || 'Erreur lors de la génération du rapport');
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showError('Erreur de connexion lors de la génération du rapport');
            }
            this.loading = false;
        },
        
        /**
         * Récupère le token CSRF
         */
        getCsrfToken() {
            // Utiliser la fonction getCookie du template de base
            return window.getCookie ? window.getCookie('csrftoken') : '';
        },
        
        /**
         * Affiche un message d'erreur
         */
        showError(message) {
            // Utiliser les toasts Bootstrap ou une notification simple
            console.error(message);
            // Ne pas afficher d'alert si c'est juste un problème de chargement
            if (!message.includes('chargement des données')) {
                alert(`Erreur: ${message}`);
            }
        },
        
        /**
         * Affiche un message de succès
         */
        showSuccess(message) {
            console.log(message);
            alert(message);
        },

        /**
         * Anime la disparition d'un rouleau de la liste
         */
        animateRollRemoval(rollId, callback) {
            const rollElement = document.querySelector(`[data-roll-id="${rollId}"]`);
            if (rollElement) {
                rollElement.classList.add('fade-out');
                setTimeout(() => {
                    if (callback) callback();
                }, 300); // Durée de l'animation CSS
            } else {
                // Si l'élément n'est pas trouvé, exécuter le callback immédiatement
                if (callback) callback();
            }
        },

        /**
         * Anime l'apparition d'un rouleau dans la liste
         */
        animateRollAppearance(rollId) {
            // Attendre que le DOM soit mis à jour
            this.$nextTick(() => {
                const rollElement = document.querySelector(`[data-roll-id="${rollId}"]`);
                if (rollElement) {
                    rollElement.classList.add('fade-in');
                    // Retirer la classe après l'animation
                    setTimeout(() => {
                        rollElement.classList.remove('fade-in');
                    }, 300);
                }
            });
        }
    };
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Le composant Alpine.js sera automatiquement initialisé
    console.log('Interface RC Avancée chargée');
});