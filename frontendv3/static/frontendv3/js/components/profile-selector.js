/**
 * Composant Alpine.js : Sélecteur de Profil
 * Gère la sélection du profil de production
 */

function profileSelector() {
    // Charger les données sauvegardées
    const savedData = window.sessionData?.modes || {};
    
    return {
        // Mixin pour la fonctionnalité collapsible
        ...collapsibleMixin(true),
        
        // État local
        selectedProfileId: '',
        profiles: [],
        selectedProfile: null,
        profileDetails: null,
        loadingDetails: false,
        modes: {},
        availableModes: [],
        targetLength: 0,
        activeTab: 'kpi', // Gérer les onglets ici
        
        // Données KPI temps réel - Charger depuis la session
        shiftData: {
            startTime: window.sessionData?.shift?.startTime || null,
            endTime: window.sessionData?.shift?.endTime || null
        },
        totalDowntime: (window.sessionData?.lost_time_entries || []).reduce((total, dt) => total + (dt.duration || 0), 0),
        TO: 0, // Temps d'Ouverture en minutes
        TD: 0, // Temps Disponible en minutes  
        disponibilitePercentage: 0,
        
        // Initialisation
        init() {
            debug('Profile selector initialized');
            
            // Initialiser le comportement collapsible
            this.initCollapsible();
            
            
            // Charger les profils depuis Django
            this.profiles = window.profilesData || [];
            debug('Profiles loaded:', this.profiles);
            
            // Charger les modes depuis Django
            this.availableModes = window.modesData || [];
            // Initialiser l'état des modes
            this.availableModes.forEach(mode => {
                this.modes[mode.id] = savedData[mode.id] !== undefined ? savedData[mode.id] : mode.is_enabled;
            });
            
            // Charger le profil actuel depuis le contexte Django
            if (window.currentProfileId) {
                // Attendre le prochain tick pour que Alpine soit prêt
                this.$nextTick(() => {
                    this.selectedProfileId = String(window.currentProfileId);
                    this.selectedProfile = this.profiles.find(p => String(p.id) === this.selectedProfileId);
                    // Profile chargé
                    // Charger les détails au démarrage
                    this.loadProfileDetails(this.selectedProfileId).then(() => {
                        // Émettre l'événement avec les specs une fois chargées
                        if (this.profileDetails?.specifications) {
                            window.dispatchEvent(new CustomEvent('profile-changed', { 
                                detail: { 
                                    profile: this.selectedProfile,
                                    profileSpecs: this.profileDetails.specifications
                                }
                            }));
                        }
                    });
                });
            }
            
            // Observer les changements pour sauvegarder
            this.$watch('selectedProfileId', async (value) => {
                if (value) {
                    this.selectedProfile = this.profiles.find(p => p.id == value);
                    // Sauvegarder dans la base de données
                    await this.saveCurrentProfile(value);
                    // Charger les détails du profil
                    await this.loadProfileDetails(value);
                    // Émettre un événement pour les autres composants
                    window.dispatchEvent(new CustomEvent('profile-changed', { 
                        detail: { 
                            profile: this.selectedProfile,
                            profileSpecs: this.profileDetails?.specifications || null
                        }
                    }));
                } else {
                    this.selectedProfile = null;
                    this.profileDetails = null;
                    await this.saveCurrentProfile(null);
                }
            });
            
            // Observer les changements de modes
            this.$watch('modes', (value) => {
                this.saveModes();
            }, { deep: true });
            
            // Écouter les changements de longueur cible
            window.addEventListener('target-length-changed', (e) => {
                this.$nextTick(() => {
                    // Ne mettre à jour que si la nouvelle valeur est valide
                    const newLength = parseFloat(e.detail.targetLength || e.detail.length);
                    if (!isNaN(newLength) && newLength > 0) {
                        this.targetLength = newLength;
                    }
                });
            });
            
            // Récupérer la longueur cible depuis la session
            const ofData = window.sessionData?.of || {};
            if (ofData.targetLength) {
                this.targetLength = ofData.targetLength;
            }
            
            // Calculer immédiatement avec les données initiales
            this.calculateDisponibilite();
            
            // Observer les changements pour recalculer automatiquement
            this.$watch('shiftData.startTime', () => this.calculateDisponibilite());
            this.$watch('shiftData.endTime', () => this.calculateDisponibilite());
            this.$watch('totalDowntime', () => this.calculateDisponibilite());
            
            // Écouter les changements de données du shift
            window.addEventListener('shift-data-changed', (e) => {
                if (e.detail.startTime !== undefined) this.shiftData.startTime = e.detail.startTime;
                if (e.detail.endTime !== undefined) this.shiftData.endTime = e.detail.endTime;
            });
            
            // Écouter les changements de temps perdus
            window.addEventListener('downtime-changed', (e) => {
                this.totalDowntime = e.detail.totalDowntime || 0;
            });
            
        },
        
        // Calculer la disponibilité
        calculateDisponibilite() {
            // Calculer TO (Temps d'Ouverture)
            if (this.shiftData.startTime && this.shiftData.endTime) {
                const start = this.parseTime(this.shiftData.startTime);
                const end = this.parseTime(this.shiftData.endTime);
                
                // Gérer le cas où la fin est le lendemain (ex: 20:00 -> 04:00)
                let diffMinutes = (end.hours * 60 + end.minutes) - (start.hours * 60 + start.minutes);
                if (diffMinutes < 0) {
                    diffMinutes += 24 * 60; // Ajouter 24h
                }
                
                this.TO = diffMinutes;
            } else {
                this.TO = 0;
            }
            
            // Calculer TD (Temps Disponible)
            this.TD = Math.max(0, this.TO - this.totalDowntime);
            
            // Calculer le pourcentage
            if (this.TO > 0) {
                this.disponibilitePercentage = Math.round((this.TD / this.TO) * 100);
            } else {
                this.disponibilitePercentage = 0;
            }
        },
        
        // Parser une heure au format HH:MM
        parseTime(timeStr) {
            if (!timeStr) return { hours: 0, minutes: 0 };
            const [hours, minutes] = timeStr.split(':').map(Number);
            return { hours: hours || 0, minutes: minutes || 0 };
        },
        
        // Formater les minutes en heures:minutes
        formatMinutes(totalMinutes) {
            if (!totalMinutes) return '0min';
            const hours = Math.floor(totalMinutes / 60);
            const minutes = totalMinutes % 60;
            if (hours === 0) return `${minutes}min`;
            if (minutes === 0) return `${hours}h`;
            return `${hours}h${minutes}`;
        },
        
        
        // Sauvegarder le profil actuel dans la base de données
        async saveCurrentProfile(profileId) {
            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || '';
                const response = await fetch('/api/current-profile/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        profile_id: profileId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    debug('Profile saved to database:', data.profile);
                } else {
                    if (window.DEBUG) console.error('Erreur sauvegarde profil:', data.error);
                }
            } catch (error) {
                if (window.DEBUG) console.error('Erreur sauvegarde profil:', error);
            }
        },
        
        // Charger les détails du profil
        async loadProfileDetails(profileId) {
            this.loadingDetails = true;
            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || '';
                const response = await fetch(`/api/profiles/${profileId}/`, {
                    headers: {
                        'X-CSRFToken': csrfToken
                    }
                });
                const data = await response.json();
                
                if (data.success) {
                    this.profileDetails = data.profile;
                    debug('Profile details loaded:', this.profileDetails);
                    
                    // Émettre un événement avec les specs pour les autres composants
                    if (this.profileDetails.specifications) {
                        window.dispatchEvent(new CustomEvent('profile-specs-changed', {
                            detail: { 
                                specifications: this.profileDetails.specifications,
                                profileId: profileId 
                            }
                        }));
                    }
                } else {
                    if (window.DEBUG) console.error('Erreur chargement détails:', data.error);
                }
            } catch (error) {
                if (window.DEBUG) console.error('Erreur chargement détails:', error);
            } finally {
                this.loadingDetails = false;
            }
        },
        
        // Sauvegarder les modes dans la base
        async saveModes() {
            try {
                await window.session.saveNow('modes', this.modes);
                debug('Modes saved:', this.modes);
            } catch (error) {
                if (window.DEBUG) console.error('Erreur sauvegarde modes:', error);
            }
        },
        
        // Computed: le body doit-il être visible ?
        get bodyVisible() {
            return this.activeTab === 'kpi' || this.isExpanded;
        }
    };
}

// Export global pour Alpine
window.profileSelector = profileSelector;