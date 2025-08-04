/**
 * Service centralisé pour le calcul des KPI en temps réel
 * Gère TO, TD, Performance, Qualité et TRS
 */

function KPIService() {
    return {
        // Données sources
        shiftData: {
            startTime: null,
            endTime: null,
            date: null,
            machineStartedStart: false,
            lengthStart: 0,
            machineStartedEnd: false,
            lengthEnd: 0
        },
        downtimes: [],
        rolls: [],
        profileData: null,
        
        // Résultats calculés
        kpis: {
            disponibilite: {
                TO: 0,          // Temps d'Ouverture en minutes
                TD: 0,          // Temps Disponible en minutes
                percentage: 0   // TD/TO * 100
            },
            performance: {
                value: 0,       // Pourcentage
                theoretical: 0, // Production théorique
                actual: 0       // Production réelle
            },
            quality: {
                value: 0,       // Pourcentage
                ok: 0,          // Rouleaux conformes
                total: 0        // Total rouleaux
            },
            trs: {
                value: 0        // Disponibilité × Performance × Qualité
            }
        },
        
        // Initialisation
        init() {
            debug('KPI Service initialized');
            
            // Écouter les événements des différents composants
            window.addEventListener('shift-data-changed', (e) => {
                this.updateShiftData(e.detail);
            });
            
            // Écouter spécifiquement les changements de temps perdus
            window.addEventListener('downtime-changed', (e) => {
                // L'événement peut contenir soit la liste complète, soit juste le nouveau temps perdu
                if (e.detail.downtimes !== undefined) {
                    this.downtimes = e.detail.downtimes;
                } else if (e.detail.totalDowntime !== undefined) {
                    // Si on a juste le total, on l'utilise directement
                    // Note: on récupérera la liste complète depuis la session si nécessaire
                    this.updateFromTotalDowntime(e.detail.totalDowntime);
                }
                this.calculateAll();
            });
            
            window.addEventListener('roll-saved', (e) => {
                this.addRoll(e.detail.roll);
            });
            
            window.addEventListener('profile-changed', (e) => {
                this.updateProfileData(e.detail);
            });
            
            // Charger les données initiales depuis la session après un court délai
            // Attendre que la session soit chargée
            const checkAndLoad = () => {
                if (window.sessionData && window.sessionData.shift) {
                    this.loadInitialData();
                } else {
                    // Si pas encore chargé, réessayer
                    setTimeout(checkAndLoad, 100);
                }
            };
            
            // Démarrer la vérification après un court délai
            setTimeout(checkAndLoad, 100);
        },
        
        // Charger les données initiales
        loadInitialData() {
            const sessionData = window.sessionData || {};
            console.log('KPI Service - Loading initial data:', sessionData);
            
            // Données du shift
            if (sessionData.shift) {
                console.log('Found shift data:', sessionData.shift);
                this.updateShiftData(sessionData.shift);
            }
            
            // Temps perdus
            if (sessionData.lost_time_entries) {
                this.downtimes = sessionData.lost_time_entries;
            }
            
            // Rouleaux (si disponibles dans la session)
            if (sessionData.rolls) {
                this.rolls = sessionData.rolls;
            }
            
            // Toujours calculer même si pas de données
            this.calculateAll();
        },
        
        // Mise à jour des données du shift
        updateShiftData(data) {
            if (data.startTime !== undefined) this.shiftData.startTime = data.startTime;
            if (data.endTime !== undefined) this.shiftData.endTime = data.endTime;
            if (data.date !== undefined) this.shiftData.date = data.date;
            if (data.machineStartedStart !== undefined) this.shiftData.machineStartedStart = data.machineStartedStart;
            if (data.lengthStart !== undefined) this.shiftData.lengthStart = parseFloat(data.lengthStart) || 0;
            if (data.machineStartedEnd !== undefined) this.shiftData.machineStartedEnd = data.machineStartedEnd;
            if (data.lengthEnd !== undefined) this.shiftData.lengthEnd = parseFloat(data.lengthEnd) || 0;
            
            this.calculateAll();
        },
        
        // Mise à jour depuis le total des temps perdus
        updateFromTotalDowntime(totalMinutes) {
            // On utilise directement le total pour le calcul
            // sans avoir besoin du détail
            this._totalDowntimeOverride = totalMinutes;
            this.calculateAll();
        },
        
        // Mise à jour des données du profil
        updateProfileData(data) {
            this.profileData = data.profile;
            this.calculateAll();
        },
        
        // Ajouter un rouleau
        addRoll(roll) {
            this.rolls.push(roll);
            this.calculateAll();
        },
        
        // Calculer tous les KPI
        calculateAll() {
            this.calculateDisponibilite();
            this.calculatePerformance();
            this.calculateQuality();
            this.calculateTRS();
            
            // Émettre l'événement de mise à jour
            this.emitUpdate();
        },
        
        // Calculer la disponibilité
        calculateDisponibilite() {
            console.log('calculateDisponibilite called with:', this.shiftData);
            
            // TO = Temps d'Ouverture (durée du poste en minutes)
            if (this.shiftData.startTime && this.shiftData.endTime) {
                const start = this.parseTime(this.shiftData.startTime);
                const end = this.parseTime(this.shiftData.endTime);
                
                console.log('Start time parsed:', start);
                console.log('End time parsed:', end);
                
                // Gérer le cas où la fin est le lendemain (ex: 20:00 -> 04:00)
                let diffMinutes = (end.hours * 60 + end.minutes) - (start.hours * 60 + start.minutes);
                if (diffMinutes < 0) {
                    diffMinutes += 24 * 60; // Ajouter 24h
                }
                
                this.kpis.disponibilite.TO = diffMinutes;
                console.log('TO calculated:', diffMinutes);
            } else {
                this.kpis.disponibilite.TO = 0;
                console.log('No start/end time, TO = 0');
            }
            
            // TD = TO - temps perdus déclarés
            const totalDowntime = this._totalDowntimeOverride !== undefined 
                ? this._totalDowntimeOverride 
                : this.downtimes.reduce((total, dt) => total + (dt.duration || 0), 0);
            
            this.kpis.disponibilite.TD = Math.max(0, this.kpis.disponibilite.TO - totalDowntime);
            
            // Pourcentage de disponibilité
            if (this.kpis.disponibilite.TO > 0) {
                this.kpis.disponibilite.percentage = Math.round(
                    (this.kpis.disponibilite.TD / this.kpis.disponibilite.TO) * 100
                );
            } else {
                this.kpis.disponibilite.percentage = 0;
            }
        },
        
        // Calculer la performance
        calculatePerformance() {
            // Production réelle = longueur fin - longueur début
            let actualProduction = 0;
            if (this.shiftData.lengthEnd && this.shiftData.lengthStart !== null) {
                actualProduction = this.shiftData.lengthEnd - this.shiftData.lengthStart;
            }
            
            // Production théorique = TD * vitesse théorique
            // TODO: Récupérer la vitesse théorique depuis le profil ou les paramètres
            const theoreticalSpeed = 5; // m/min par défaut
            const theoreticalProduction = this.kpis.disponibilite.TD * theoreticalSpeed;
            
            this.kpis.performance.actual = actualProduction;
            this.kpis.performance.theoretical = theoreticalProduction;
            
            // Pourcentage de performance
            if (theoreticalProduction > 0) {
                this.kpis.performance.value = Math.min(100, Math.round(
                    (actualProduction / theoreticalProduction) * 100
                ));
            } else {
                this.kpis.performance.value = 0;
            }
        },
        
        // Calculer la qualité
        calculateQuality() {
            // Compter les rouleaux conformes vs total
            const totalRolls = this.rolls.length;
            const okRolls = this.rolls.filter(r => r.conformity === true).length;
            
            this.kpis.quality.total = totalRolls;
            this.kpis.quality.ok = okRolls;
            
            // Pourcentage de qualité
            if (totalRolls > 0) {
                this.kpis.quality.value = Math.round((okRolls / totalRolls) * 100);
            } else {
                this.kpis.quality.value = 100; // Par défaut 100% si pas de rouleaux
            }
        },
        
        // Calculer le TRS
        calculateTRS() {
            // TRS = Disponibilité × Performance × Qualité
            this.kpis.trs.value = Math.round(
                (this.kpis.disponibilite.percentage / 100) *
                (this.kpis.performance.value / 100) *
                (this.kpis.quality.value / 100) * 100
            );
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
        
        // Émettre l'événement de mise à jour
        emitUpdate() {
            window.dispatchEvent(new CustomEvent('kpi-updated', {
                detail: {
                    kpis: this.kpis,
                    formatMinutes: this.formatMinutes
                }
            }));
            
            debug('KPI updated:', this.kpis);
        }
    };
}

// Créer une instance globale du service et l'initialiser automatiquement
window.kpiService = KPIService();

// Initialiser automatiquement quand le DOM est prêt
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.kpiService.init();
    });
} else {
    // DOM déjà chargé
    window.kpiService.init();
}

// Export pour utilisation dans d'autres modules
window.KPIService = KPIService;