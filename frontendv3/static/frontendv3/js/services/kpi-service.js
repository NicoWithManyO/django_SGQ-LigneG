/**
 * Service centralisé pour le calcul des KPI
 * Responsabilité unique : calculer les indicateurs de performance
 */

// Créer les fonctions de calcul mémoizées
const memoizedDisponibilite = window.memoizeKPI('disponibilite', (TO, totalDowntime) => {
    const TD = Math.max(0, TO - totalDowntime);
    const percentage = TO > 0 ? Math.round((TD / TO) * 100) : 0;
    return { TD, percentage };
});

const memoizedPerformance = window.memoizeKPI('performance', (TD, vitesse, lengthStart, lengthEnd, rouleauxSauves) => {
    let longueurEnroulee = 0;
    
    if (lengthEnd > 0) {
        const longueurProduite = lengthEnd - lengthStart;
        longueurEnroulee = longueurProduite + rouleauxSauves;
    } else {
        longueurEnroulee = rouleauxSauves - lengthStart;
    }
    
    longueurEnroulee = Math.max(0, longueurEnroulee);
    const longueurEnroulable = Math.round(TD * vitesse);
    const percentage = longueurEnroulable > 0 ? Math.round((longueurEnroulee / longueurEnroulable) * 100) : 0;
    
    return { longueurEnroulee, longueurEnroulable, percentage };
});

const memoizedQualite = window.memoizeKPI('qualite', (longueurEnroulee, longueurNOK) => {
    const longueurOK = Math.max(0, longueurEnroulee - longueurNOK);
    const percentage = longueurEnroulee > 0 ? Math.round((longueurOK / longueurEnroulee) * 100) : 100;
    return { longueurOK, percentage };
});

const memoizedTRS = window.memoizeKPI('trs', (dispo, perf, qualite) => {
    const trs = (dispo * perf * qualite) / 10000;
    return Math.round(trs * 10) / 10; // Arrondir à 1 décimale
});

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
            
            debug('Loaded lengths from session:', {
                lengthStart: this.lengthStart,
                lengthEnd: this.lengthEnd
            });
        }
        
        const downtimes = sessionData.lost_time_entries || [];
        this.totalDowntime = downtimes.reduce((total, dt) => total + (dt.duration || 0), 0);
        
        // Charger la longueur des rouleaux sauvés depuis la session
        this.longueurRouleauxSauves = sessionData.v3_production?.longueur_rouleaux_sauves || sessionData.longueur_rouleaux_sauves || 0;
        this.longueurRouleauxOK = sessionData.v3_production?.longueur_rouleaux_ok || sessionData.longueur_rouleaux_ok || 0;
        this.longueurRouleauxNOK = sessionData.v3_production?.longueur_rouleaux_nok || sessionData.longueur_rouleaux_nok || 0;
        
        debug('Loaded roll lengths from session:', {
            longueurRouleauxSauves: this.longueurRouleauxSauves,
            longueurRouleauxOK: this.longueurRouleauxOK,
            longueurRouleauxNOK: this.longueurRouleauxNOK
        });
        
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
        
        window.addEventListener('roll:saved', (e) => {
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
                
                // Invalider le cache pour les calculs affectés
                window.memoizationService.invalidatePatterns(['performance', 'qualite', 'trs']);
                
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
        
        // Faire un calcul initial
        this.calculateAll();
        
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
        
        // Utiliser la fonction mémoizée
        const result = memoizedDisponibilite(this.TO, this.totalDowntime);
        this.TD = result.TD;
        this.disponibilitePercentage = result.percentage;
    },
    
    // Calculer la performance
    calculatePerformance() {
        // Utiliser la fonction mémoizée
        const result = memoizedPerformance(
            this.TD,
            this.vitesseTheorique,
            this.lengthStart,
            this.lengthEnd,
            this.longueurRouleauxSauves
        );
        
        this.longueurEnroulee = result.longueurEnroulee;
        this.longueurEnroulable = result.longueurEnroulable;
        this.performancePercentage = result.percentage;
        
        debug('Calcul Performance:', {
            lengthStart: this.lengthStart,
            lengthEnd: this.lengthEnd,
            longueurRouleauxSauves: this.longueurRouleauxSauves,
            longueurEnroulee: this.longueurEnroulee
        });
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
        const result = memoizedQualite(this.longueurEnroulee, this.longueurRouleauxNOK);
        this.qualitePercentage = result.percentage;
        
        debug('Calcul Qualité:', {
            longueurEnroulee: this.longueurEnroulee,
            longueurRouleauxNOK: this.longueurRouleauxNOK,
            longueurOKCalculee: result.longueurOK,
            qualitePercentage: this.qualitePercentage
        });
    },
    
    // Calculer le TRS Global
    calculateTRS() {
        this.trsGlobal = memoizedTRS(
            this.disponibilitePercentage,
            this.performancePercentage,
            this.qualitePercentage
        );
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