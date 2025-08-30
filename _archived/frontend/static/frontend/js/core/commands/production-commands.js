/**
 * Commandes métier pour la gestion de la production
 */

export function registerProductionCommands(commandBus) {
    
    /**
     * Commande : Sélectionner un profil produit
     */
    commandBus.register(
        'SELECT_PRODUCT_PROFILE',
        async (payload, state) => {
            const { profileId } = payload;
            
            // Charger le profil depuis les données globales ou l'API
            let profile = null;
            
            if (window.productProfiles) {
                profile = window.productProfiles.find(p => p.id == profileId);
            }
            
            if (!profile) {
                // Charger depuis l'API si nécessaire
                try {
                    profile = await window.apiV2.get(`/api/profiles/${profileId}/`);
                } catch (error) {
                    throw new Error('Profil non trouvé');
                }
            }
            
            // Mettre à jour l'état
            state.setState('production.currentProfileId', profileId);
            state.setState('production.currentProfile', profile);
            
            // Extraire les données importantes
            if (profile) {
                state.setState('production.feltWidth', profile.felt_width || 1);
                state.setState('production.beltSpeed', profile.belt_speed || 0);
                state.setState('production.thicknessSpec', profile.specs?.thickness || {});
                state.setState('production.grammageSpec', profile.specs?.grammage || {});
            }
            
            return { profileId, profile };
        },
        // Validateur
        (payload) => {
            if (!payload.profileId) {
                return { valid: false, errors: ['Profil requis'] };
            }
            return { valid: true };
        },
        // Effets
        [
            // Émettre l'événement de changement
            (result) => {
                window.eventBus.emit('profile-changed', {
                    profileId: result.profileId,
                    profile: result.profile,
                    beltSpeed: result.profile?.belt_speed
                });
            }
        ]
    );
    
    /**
     * Commande : Sélectionner un OF
     */
    commandBus.register(
        'SELECT_FABRICATION_ORDER',
        (payload, state) => {
            const { ofNumber, targetLength } = payload;
            
            state.setState('production.currentOfNumber', ofNumber);
            state.setState('production.currentTargetLength', targetLength);
            
            // Réinitialiser le numéro de rouleau
            state.setState('production.nextRollNumber', 1);
            
            return { ofNumber, targetLength };
        },
        // Validateur
        (payload) => {
            const errors = [];
            
            if (!payload.ofNumber) errors.push('Numéro OF requis');
            if (!payload.targetLength || payload.targetLength <= 0) {
                errors.push('Longueur cible doit être positive');
            }
            
            return {
                valid: errors.length === 0,
                errors
            };
        },
        // Effets
        [
            // Émettre l'événement
            (result) => {
                window.eventBus.emit('of-selected', result);
                window.eventBus.emit('target-length-changed', {
                    length: result.targetLength
                });
            }
        ]
    );
    
    /**
     * Commande : Mettre à jour les compteurs de production
     */
    commandBus.register(
        'UPDATE_PRODUCTION_COUNTERS',
        (payload, state) => {
            const { type, length } = payload;
            
            const currentOk = state.getState('counters.woundLengthOk', 0);
            const currentNok = state.getState('counters.woundLengthNok', 0);
            const currentTotal = state.getState('counters.woundLengthTotal', 0);
            
            switch (type) {
                case 'ok':
                    state.setState('counters.woundLengthOk', currentOk + length);
                    state.setState('counters.woundLengthTotal', currentTotal + length);
                    break;
                    
                case 'nok':
                    state.setState('counters.woundLengthNok', currentNok + length);
                    state.setState('counters.woundLengthTotal', currentTotal + length);
                    break;
                    
                case 'reset':
                    state.setState('counters.woundLengthOk', 0);
                    state.setState('counters.woundLengthNok', 0);
                    state.setState('counters.woundLengthTotal', 0);
                    break;
            }
            
            return {
                ok: state.getState('counters.woundLengthOk'),
                nok: state.getState('counters.woundLengthNok'),
                total: state.getState('counters.woundLengthTotal')
            };
        }
    );
    
    /**
     * Commande : Calculer les KPIs de production
     */
    commandBus.register(
        'CALCULATE_PRODUCTION_KPIS',
        (payload, state) => {
            // Récupérer les données nécessaires
            const startTime = state.getState('shift.startTime');
            const endTime = state.getState('shift.endTime');
            const lostTime = state.getState('lostTime.total', 0);
            const okLength = state.getState('counters.woundLengthOk', 0);
            const nokLength = state.getState('counters.woundLengthNok', 0);
            const totalLength = state.getState('counters.woundLengthTotal', 0);
            const beltSpeed = state.getState('production.beltSpeed', 0);
            
            // Calculer le temps d'ouverture (en minutes)
            let openingTime = 0;
            if (startTime && endTime) {
                const start = timeToMinutes(startTime);
                const end = timeToMinutes(endTime);
                openingTime = end > start ? end - start : (1440 - start + end); // Gérer minuit
            }
            
            // Calculer le temps disponible
            const availableTime = Math.max(0, openingTime - lostTime);
            
            // Calculer la production théorique
            const theoreticalProduction = beltSpeed * availableTime;
            
            // Calculer les KPIs
            const availability = openingTime > 0 ? 
                (availableTime / openingTime) * 100 : 0;
                
            const performance = theoreticalProduction > 0 ? 
                (totalLength / theoreticalProduction) * 100 : 0;
                
            const quality = totalLength > 0 ? 
                (okLength / totalLength) * 100 : 0;
                
            const oee = (availability * performance * quality) / 10000;
            
            const kpis = {
                openingTime,
                availableTime,
                lostTime,
                theoreticalProduction: Math.round(theoreticalProduction),
                actualProduction: totalLength,
                okProduction: okLength,
                nokProduction: nokLength,
                availability: Math.round(availability * 10) / 10,
                performance: Math.round(performance * 10) / 10,
                quality: Math.round(quality * 10) / 10,
                oee: Math.round(oee * 10) / 10
            };
            
            // Sauvegarder les KPIs
            state.setState('kpis', kpis);
            
            return kpis;
        }
    );
}

// Fonction utilitaire
function timeToMinutes(time) {
    if (!time) return 0;
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
}