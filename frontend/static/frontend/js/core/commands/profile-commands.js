/**
 * Commandes pour la gestion des profils produit
 */
function registerProfileCommands(commandBus) {
    if (!commandBus) {
        console.error('CommandBus requis pour enregistrer les commandes profil');
        return;
    }

    /**
     * Change le profil sélectionné et charge ses données
     */
    commandBus.register('CHANGE_PROFILE', async (data) => {
        const { profileId } = data;
        
        if (!profileId) {
            // Réinitialiser si aucun profil sélectionné
            await commandBus.stateManager.setState('profile', {
                id: null,
                data: null,
                modes: {}
            }, 'system');
            return { success: true };
        }

        try {
            // Charger les données du profil depuis l'API
            const profileData = await window.apiV2.get(`/catalog/api/profiles/${profileId}/`);

            // Charger les modes disponibles
            const modesResponse = await window.apiV2.get('/wcm/api/modes/');
            const availableModes = modesResponse.results || modesResponse;

            // Initialiser l'état des modes (tous désactivés par défaut)
            const modesState = {};
            availableModes.forEach(mode => {
                modesState[mode.id] = false;
            });

            // Mettre à jour l'état
            await commandBus.stateManager.setState('profile', {
                id: profileId,
                data: profileData,
                modes: modesState
            }, 'system');

            // Persister en BDD
            await window.apiV2.post('/production/api/current-profile/', {
                profile_id: profileId
            });

            return { success: true, profileData };
        } catch (error) {
            console.error('Erreur lors du chargement du profil:', error);
            throw error;
        }
    });

    /**
     * Active/désactive un mode de fonctionnement
     */
    commandBus.register('TOGGLE_MODE', async (data) => {
        const { modeId, enabled } = data;
        
        if (!modeId) {
            throw new Error('ID du mode requis');
        }

        const currentModes = commandBus.stateManager.getState('profile.modes') || {};
        
        // Mettre à jour l'état du mode
        await commandBus.stateManager.setState(
            `profile.modes.${modeId}`,
            enabled,
            'user'
        );

        // Persister en BDD si nécessaire
        // TODO: Implémenter l'endpoint si requis

        return { success: true };
    });

    /**
     * Recharge les données du profil actuel
     */
    commandBus.register('RELOAD_PROFILE_DATA', async () => {
        const profileId = commandBus.stateManager.getState('profile.id');
        
        if (!profileId) {
            return { success: false, message: 'Aucun profil sélectionné' };
        }

        // Utiliser la commande CHANGE_PROFILE pour recharger
        return await commandBus.execute('CHANGE_PROFILE', { profileId });
    });
}

// Exposer globalement pour l'architecture V2
window.registerProfileCommands = registerProfileCommands;