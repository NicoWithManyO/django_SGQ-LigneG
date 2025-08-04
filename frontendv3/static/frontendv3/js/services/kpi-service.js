/**
 * Service centralisé pour le calcul des KPI
 * Responsabilité unique : calculer les indicateurs de performance
 */

// Créer le service comme singleton
window.kpiService = {
    // État des données sources
    shiftData: {
        startTime: null,
        endTime: null
    },
    totalDowntime: 0,
    profileData: null,
    vitesseTheorique: 5, // m/min par défaut
    lengthStart: 0, // Longueur début de poste
    lengthEnd: 0, // Longueur fin de poste
    longueurRouleauxSauves: 0, // Somme des rouleaux coupés
    longueurRouleauxOK: 0, // Somme des rouleaux conformes
    longueurRouleauxNOK: 0, // Somme des rouleaux non conformes
    
    // Résultats calculés
    TO: 0, // Temps d'Ouverture en minutes
    TD: 0, // Temps Disponible en minutes
    disponibilitePercentage: 0,
    longueurEnroulable: 0, // TD × vitesse
    longueurEnroulee: 0, // (lengthEnd - lengthStart) + rouleaux sauvés
    performancePercentage: 0,
    qualitePercentage: 0, // Pourcentage de rouleaux OK
    trsGlobal: 0, // TRS = Dispo × Perf × Qualité
    
    // Initialisation du service
    init() {
        debug('KPI Service initialized');
        debug('Vitesse théorique initiale:', this.vitesseTheorique);
        
        // Charger les données initiales depuis la session
        const sessionData = window.sessionData || {};
        if (sessionData.shift) {
            this.shiftData.startTime = sessionData.shift.startTime || null;
            this.shiftData.endTime = sessionData.shift.endTime || null;
            this.lengthStart = parseFloat(sessionData.shift.lengthStart) || 0;
            this.lengthEnd = parseFloat(sessionData.shift.lengthEnd) || 0;
        }
        
        const downtimes = sessionData.lost_time_entries || [];
        this.totalDowntime = downtimes.reduce((total, dt) => total + (dt.duration || 0), 0);
        
        // Charger la longueur des rouleaux sauvés depuis la session
        this.longueurRouleauxSauves = sessionData.longueur_rouleaux_sauves || 0;
        this.longueurRouleauxOK = sessionData.longueur_rouleaux_ok || 0;
        this.longueurRouleauxNOK = sessionData.longueur_rouleaux_nok || 0;
        
        // Charger le profil actuel et la vitesse directement
        if (window.currentProfileId) {
            // Faire une requête pour récupérer les specs du profil
            fetch(`/api/profiles/${window.currentProfileId}/`, {
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                }
            })
                .then(response => response.json())
                .then(data => {
                    debug('Réponse API profil:', data);
                    if (data.success && data.profile) {
                        // La vitesse est directement dans le profil !
                        if (data.profile.belt_speed) {
                            this.vitesseTheorique = parseFloat(data.profile.belt_speed);
                            debug(`Vitesse chargée du profil: ${this.vitesseTheorique} m/min`);
                            this.calculateAll();
                            this.emitUpdate();
                        }
                    }
                })
                .catch(err => {
                    console.error('Erreur chargement profil:', err);
                });
        } else {
            // Calculer avec les données initiales seulement si pas de profil
            this.calculateAll();
        }
        
        // Écouter les événements
        window.addEventListener('shift-data-changed', (e) => {
            debug('shift-data-changed reçu:', e.detail);
            if (e.detail.startTime !== undefined) this.shiftData.startTime = e.detail.startTime;
            if (e.detail.endTime !== undefined) this.shiftData.endTime = e.detail.endTime;
            if (e.detail.lengthStart !== undefined) this.lengthStart = parseFloat(e.detail.lengthStart) || 0;
            if (e.detail.lengthEnd !== undefined) this.lengthEnd = parseFloat(e.detail.lengthEnd) || 0;
            this.calculateAll();
        });
        
        window.addEventListener('downtime-changed', (e) => {
            this.totalDowntime = e.detail.totalDowntime || 0;
            this.calculateAll();
        });
        
        window.addEventListener('profile-changed', (e) => {
            debug('KPI Service: profile-changed reçu', e.detail);
            this.profileData = e.detail.profile;
            
            // La vitesse est directement dans le profil !
            if (this.profileData && this.profileData.belt_speed) {
                this.vitesseTheorique = parseFloat(this.profileData.belt_speed);
                debug(`Vitesse du profil: ${this.vitesseTheorique} m/min`);
            }
            
            this.calculateAll();
        });
        
        window.addEventListener('roll-saved', (e) => {
            // Ajouter la longueur du rouleau sauvé
            if (e.detail.roll && e.detail.roll.length) {
                const length = parseFloat(e.detail.roll.length) || 0;
                this.longueurRouleauxSauves += length;
                
                // Séparer OK et NOK basé sur le status
                debug('Roll saved:', e.detail.roll);
                if (e.detail.roll.status === 'CONFORME' || e.detail.roll.is_compliant === true) {
                    this.longueurRouleauxOK += length;
                    debug(`Ajout ${length}m aux rouleaux OK. Total OK: ${this.longueurRouleauxOK}m`);
                } else {
                    this.longueurRouleauxNOK += length;
                    debug(`Ajout ${length}m aux rouleaux NOK. Total NOK: ${this.longueurRouleauxNOK}m`);
                }
                
                this.calculateAll(); // Recalculer tout incluant la qualité
                
                // Sauvegarder dans la session
                this.saveLongueurRouleaux();
            }
        });
        
        // Réinitialiser après sauvegarde du shift
        window.addEventListener('shift-saved', () => {
            this.longueurRouleauxSauves = 0;
            this.longueurRouleauxOK = 0;
            this.longueurRouleauxNOK = 0;
            this.lengthStart = 0;
            this.lengthEnd = 0;
            this.saveLongueurRouleaux();
            this.calculateAll();
        });
        
        // Émettre un événement pour dire que le service est prêt
        window.dispatchEvent(new Event('kpi-service-ready'));
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
    
    // Calculer la performance
    calculatePerformance() {
        let longueurEnroulee = 0;
        
        // Si on a lengthEnd, calculer normalement
        if (this.lengthEnd > 0) {
            const longueurProduite = this.lengthEnd - this.lengthStart;
            longueurEnroulee = longueurProduite + this.longueurRouleauxSauves;
        } else {
            // Sinon, les rouleaux coupés représentent la production depuis lengthStart
            // Il faut donc déduire lengthStart qui était déjà enroulé
            longueurEnroulee = this.longueurRouleauxSauves - this.lengthStart;
        }
        
        debug('Calcul Performance:', {
            lengthStart: this.lengthStart,
            lengthEnd: this.lengthEnd,
            longueurRouleauxSauves: this.longueurRouleauxSauves,
            longueurEnroulee: longueurEnroulee
        });
        
        // S'assurer que c'est positif
        this.longueurEnroulee = Math.max(0, longueurEnroulee);
        
        // Longueur enroulable = TD × vitesse théorique
        this.longueurEnroulable = Math.round(this.TD * this.vitesseTheorique);
        
        // Pourcentage de performance
        if (this.longueurEnroulable > 0) {
            this.performancePercentage = Math.round(
                (this.longueurEnroulee / this.longueurEnroulable) * 100
            );
        } else {
            this.performancePercentage = 0;
        }
    },
    
    // Calculer tous les KPI
    calculateAll() {
        this.calculateDisponibilite();
        this.calculatePerformance();
        this.calculateQualite();
        this.calculateTRS();
        this.emitUpdate();
    },
    
    // Émettre la mise à jour
    emitUpdate() {
        window.dispatchEvent(new CustomEvent('kpi-updated', {
            detail: {
                TO: this.TO,
                TD: this.TD,
                disponibilitePercentage: this.disponibilitePercentage,
                longueurEnroulable: this.longueurEnroulable,
                longueurEnroulee: this.longueurEnroulee,
                performancePercentage: this.performancePercentage,
                qualitePercentage: this.qualitePercentage,
                longueurRouleauxOK: this.longueurRouleauxOK,
                longueurRouleauxNOK: this.longueurRouleauxNOK,
                trsGlobal: this.trsGlobal
            }
        }));
    },
    
    // Parser une heure au format HH:MM
    parseTime(timeStr) {
        if (!timeStr) return { hours: 0, minutes: 0 };
        const [hours, minutes] = timeStr.split(':').map(Number);
        return { hours: hours || 0, minutes: minutes || 0 };
    },
    
    // Calculer la qualité
    calculateQualite() {
        // Longueur OK = Longueur totale enroulée - Longueur NOK
        const longueurOKCalculee = Math.max(0, this.longueurEnroulee - this.longueurRouleauxNOK);
        
        // Pourcentage de qualité basé sur la longueur enroulée totale
        if (this.longueurEnroulee > 0) {
            this.qualitePercentage = Math.round(
                (longueurOKCalculee / this.longueurEnroulee) * 100
            );
        } else {
            this.qualitePercentage = 100; // Si pas de production, on considère 100%
        }
        
        debug('Calcul Qualité:', {
            longueurEnroulee: this.longueurEnroulee,
            longueurRouleauxNOK: this.longueurRouleauxNOK,
            longueurOKCalculee: longueurOKCalculee,
            qualitePercentage: this.qualitePercentage
        });
    },
    
    // Calculer le TRS Global
    calculateTRS() {
        // TRS = Disponibilité × Performance × Qualité
        // Les pourcentages sont déjà sur 100, donc on divise par 10000
        const trs = (this.disponibilitePercentage * this.performancePercentage * this.qualitePercentage) / 10000;
        this.trsGlobal = Math.round(trs * 10) / 10; // Arrondir à 1 décimale
    },
    
    // Sauvegarder les longueurs des rouleaux dans la session
    saveLongueurRouleaux() {
        if (window.session) {
            window.session.patch({ 
                longueur_rouleaux_sauves: this.longueurRouleauxSauves,
                longueur_rouleaux_ok: this.longueurRouleauxOK,
                longueur_rouleaux_nok: this.longueurRouleauxNOK
            });
        }
    },
    
    // Formater les minutes en heures:minutes
    formatMinutes(totalMinutes) {
        if (!totalMinutes) return '0min';
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;
        if (hours === 0) return `${minutes}min`;
        if (minutes === 0) return `${hours}h`;
        return `${hours}h${minutes}`;
    }
};

// Initialiser automatiquement quand le DOM est prêt
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Petit délai pour s'assurer que la session est chargée
        setTimeout(() => {
            window.kpiService.init();
        }, 100);
    });
} else {
    // DOM déjà chargé
    setTimeout(() => {
        window.kpiService.init();
    }, 100);
}