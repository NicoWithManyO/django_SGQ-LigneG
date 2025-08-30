/**
 * Composant Alpine.js : Gestion des temps perdus
 * Permet de déclarer et suivre les temps d'arrêt
 */

function downtimeTracker() {
    // Charger depuis la session Django (utiliser la clé attendue par le backend)
    const savedData = window.sessionData?.lost_time_entries || window.sessionData?.downtimes || [];
    
    return {
        // Mixin
        ...window.sessionMixin,
        // État local
        downtimes: savedData,          // Liste des temps perdus de la session
        reasons: [],            // Motifs disponibles depuis l'API
        currentDowntime: {
            reason: '',         // ID du motif sélectionné
            comment: '',        // Commentaire optionnel
            duration: ''        // Durée en minutes
        },
        loading: false,
        
        // Initialisation
        async init() {
            debug('Downtime tracker initialized');
            
            // Initialiser le mixin session
            this.initSession();
            
            // Charger les motifs disponibles
            await this.loadReasons();
            
            // Les temps perdus viennent uniquement de la session
            // Pas de chargement depuis la base de données
            
            // Observer les changements de hasStartupDowntime
            this.$watch('hasStartupDowntime', (newValue) => {
                console.log('hasStartupDowntime changed:', newValue);
                window.dispatchEvent(new CustomEvent('downtime-startup-changed', { 
                    detail: { hasStartupDowntime: newValue }
                }));
            });
            
            // Observer les changements dans la liste des temps perdus
            this.$watch('downtimes', () => {
                window.dispatchEvent(new CustomEvent('downtime-changed', {
                    detail: { 
                        downtimes: this.downtimes,
                        totalDowntime: this.totalDowntime
                    }
                }));
            }, { deep: true });
            
            // Écouter la réinitialisation après sauvegarde du shift
            window.addEventListener('shift-reset', () => {
                debug('Réinitialisation des temps perdus après sauvegarde du shift');
                this.downtimes = [];
                this.showAddForm = false;
                this.newDowntime = {
                    reason: '',
                    motif: '',
                    comment: '',
                    duration: ''
                };
                this.saveDowntimeData();
                
                // Notifier que plus de temps de démarrage
                window.dispatchEvent(new CustomEvent('downtime-startup-changed', {
                    detail: { hasStartupDowntime: false }
                }));
            });
            
            // Émettre l'événement initial si on a déjà un temps de démarrage
            if (this.hasStartupDowntime) {
                console.log('Initial hasStartupDowntime:', this.hasStartupDowntime);
                window.dispatchEvent(new CustomEvent('downtime-startup-changed', { 
                    detail: { hasStartupDowntime: true }
                }));
            }
            
            // Écouter quand profile-selector est prêt pour émettre les données
            window.addEventListener('profile-selector-ready', () => {
                window.dispatchEvent(new CustomEvent('downtime-changed', {
                    detail: { 
                        downtimes: this.downtimes,
                        totalDowntime: this.totalDowntime
                    }
                }));
            });
        },
        
        // Vérifier s'il y a un temps perdu de type "démarrage"
        get hasStartupDowntime() {
            return this.downtimes.some(dt => {
                // Vérifier le nom du motif directement (format local)
                if (dt.motif_name) {
                    const name = dt.motif_name.toLowerCase();
                    return name.includes('démarrage') || 
                           name.includes('demarrage') || 
                           name.includes('startup') ||
                           name.includes('mise en route');
                }
                
                // Fallback : chercher dans les raisons (format API)
                if (dt.reason) {
                    const reason = this.reasons.find(r => r.id === parseInt(dt.reason));
                    if (reason) {
                        const name = reason.name.toLowerCase();
                        return name.includes('démarrage') || 
                               name.includes('demarrage') || 
                               name.includes('startup') ||
                               name.includes('mise en route');
                    }
                }
                
                return false;
            });
        },
        
        // Sauvegarder dans la session Django
        saveDowntimeData() {
            // Sauvegarder sous la clé attendue par le backend
            this.saveToSession({ lost_time_entries: this.downtimes });
            debug('Downtimes saved to session as lost_time_entries:', this.downtimes.length);
        },
        
        // Charger les motifs depuis l'API
        async loadReasons() {
            try {
                const response = await fetch('/wcm/api/lost-time-reasons/', {
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || ''
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                this.reasons = data.results || data;
                debug('Loaded reasons:', this.reasons);
                
            } catch (error) {
                if (window.DEBUG) console.error('Erreur chargement motifs:', error);
                showNotification('error', 'Erreur lors du chargement des motifs');
            }
        },
        
        // SUPPRIMÉ - Les temps perdus viennent uniquement de la session, pas de la base
        
        // Ajouter un temps perdu
        addDowntime() {
            // Validation
            if (!this.currentDowntime.reason || !this.currentDowntime.duration) {
                showNotification('error', 'Veuillez sélectionner un motif et indiquer une durée');
                return;
            }
            
            const duration = parseInt(this.currentDowntime.duration);
            if (isNaN(duration) || duration <= 0) {
                showNotification('error', 'La durée doit être un nombre positif');
                return;
            }
            
            // Trouver le motif sélectionné pour récupérer son nom et sa catégorie
            const selectedReason = this.reasons.find(r => r.id === parseInt(this.currentDowntime.reason));
            
            // Créer la nouvelle entrée localement
            const newEntry = {
                id: Date.now(), // ID temporaire unique
                reason: this.currentDowntime.reason,
                motif: selectedReason ? selectedReason.name : '', // Le backend attend 'motif'
                motif_name: selectedReason ? selectedReason.name : '', // Pour l'affichage
                category: selectedReason ? selectedReason.category : '',
                comment: this.currentDowntime.comment,
                duration: duration,
                created_at: new Date().toISOString()
            };
            
            // Ajouter à la liste locale
            this.downtimes.unshift(newEntry);
            
            // Sauvegarder dans la session
            this.saveDowntimeData();
            
            // Réinitialiser le formulaire
            this.currentDowntime = {
                reason: '',
                comment: '',
                duration: ''
            };
            
            // Émettre un événement pour mettre à jour les KPIs
            window.dispatchEvent(new CustomEvent('downtime-added', { 
                detail: { entry: newEntry }
            }));
            
            // Vérifier si c'est un temps perdu de démarrage
            this.$nextTick(() => {
                console.log('After add, hasStartupDowntime:', this.hasStartupDowntime);
                window.dispatchEvent(new CustomEvent('downtime-startup-changed', { 
                    detail: { hasStartupDowntime: this.hasStartupDowntime }
                }));
            });
            
            showNotification('success', 'Temps perdu enregistré');
        },
        
        // Supprimer un temps perdu
        removeDowntime(id) {
            // Retirer de la liste locale
            this.downtimes = this.downtimes.filter(dt => dt.id !== id);
            
            // Sauvegarder dans la session
            this.saveDowntimeData();
            
            // Émettre un événement
            window.dispatchEvent(new CustomEvent('downtime-removed', { 
                detail: { id: id }
            }));
            
            // Vérifier si c'était un temps perdu de démarrage
            this.$nextTick(() => {
                window.dispatchEvent(new CustomEvent('downtime-startup-changed', { 
                    detail: { hasStartupDowntime: this.hasStartupDowntime }
                }));
            });
            
            showNotification('success', 'Temps perdu supprimé');
        },
        
        // Obtenir le nom de la catégorie
        getCategoryName(category) {
            const categories = {
                'arret_programme': 'Arrêt programmé',
                'panne': 'Panne',
                'changement_serie': 'Changement série',
                'reglage': 'Réglage',
                'maintenance': 'Maintenance',
                'qualite': 'Qualité',
                'approvisionnement': 'Appro.',
                'autre': 'Autre'
            };
            return categories[category] || category;
        },
        
        // Calculer le total des temps perdus
        get totalDowntime() {
            return this.downtimes.reduce((total, dt) => total + (dt.duration || 0), 0);
        },
        
        // Formater la durée en heures et minutes
        formatDuration(minutes) {
            if (minutes < 60) {
                return `${minutes} min`;
            }
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            if (mins === 0) {
                return `${hours}h`;
            }
            return `${hours}h${mins}`;
        },
        
        // Total formaté
        get totalDowntimeFormatted() {
            return this.formatDuration(this.totalDowntime);
        },
        
        // Grouper les motifs par catégorie pour un meilleur affichage
        get reasonsByCategory() {
            const grouped = {};
            this.reasons.forEach(reason => {
                const category = reason.category || 'autre';
                if (!grouped[category]) {
                    grouped[category] = {
                        name: this.getCategoryName(category),
                        category: category,
                        reasons: []
                    };
                }
                grouped[category].reasons.push(reason);
            });
            return Object.values(grouped);
        },
        
    };
}

// Export global pour Alpine
window.downtimeTracker = downtimeTracker;