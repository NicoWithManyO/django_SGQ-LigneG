/**
 * Composant Alpine.js : Gestion des temps perdus
 * Permet de déclarer et suivre les temps d'arrêt
 */

function downtimeTracker() {
    return {
        // État local
        downtimes: [],          // Liste des temps perdus de la session
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
            
            // Charger les motifs disponibles
            await this.loadReasons();
            
            // Charger les temps perdus existants
            await this.loadDowntimes();
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
        
        // Charger les temps perdus de la session
        async loadDowntimes() {
            try {
                const response = await fetch('/wcm/api/lost-time-entries/', {
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || ''
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                this.downtimes = data.results || data;
                debug('Loaded downtimes:', this.downtimes);
                
            } catch (error) {
                if (window.DEBUG) console.error('Erreur chargement temps perdus:', error);
            }
        },
        
        // Ajouter un temps perdu
        async addDowntime() {
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
            
            this.loading = true;
            
            try {
                const response = await fetch('/wcm/api/lost-time-entries/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || ''
                    },
                    body: JSON.stringify({
                        reason: this.currentDowntime.reason,
                        comment: this.currentDowntime.comment,
                        duration: duration
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const newEntry = await response.json();
                
                // Ajouter à la liste locale
                this.downtimes.unshift(newEntry);
                
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
                
                showNotification('success', 'Temps perdu enregistré');
                
            } catch (error) {
                if (window.DEBUG) console.error('Erreur ajout temps perdu:', error);
                showNotification('error', 'Erreur lors de l\'enregistrement');
            } finally {
                this.loading = false;
            }
        },
        
        // Supprimer un temps perdu
        async removeDowntime(id) {
            try {
                const response = await fetch(`/wcm/api/lost-time-entries/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || ''
                    }
                });
                
                if (!response.ok && response.status !== 204) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                // Retirer de la liste locale
                this.downtimes = this.downtimes.filter(dt => dt.id !== id);
                
                // Émettre un événement
                window.dispatchEvent(new CustomEvent('downtime-removed', { 
                    detail: { id: id }
                }));
                
                showNotification('success', 'Temps perdu supprimé');
                
            } catch (error) {
                if (window.DEBUG) console.error('Erreur suppression temps perdu:', error);
                showNotification('error', 'Erreur lors de la suppression');
            }
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
        }
    };
}

// Export global pour Alpine
window.downtimeTracker = downtimeTracker;