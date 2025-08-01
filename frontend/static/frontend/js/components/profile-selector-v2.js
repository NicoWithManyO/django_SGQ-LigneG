/**
 * Composant V2 pour la sélection et l'affichage des profils produit
 */
class ProfileSelectorV2 {
    constructor() {
        this.container = null;
        this.profiles = [];
        this.modes = [];
        this.init();
    }

    async init() {
        // Attendre que le système soit prêt
        if (window.eventBus) {
            window.eventBus.on('system:ready', () => this.setup());
        } else {
            setTimeout(() => this.init(), 100);
        }
    }

    async setup() {
        this.container = document.getElementById('profile-container');
        if (!this.container) {
            console.error('Container #profile-container non trouvé');
            return;
        }

        // Charger les données initiales
        await this.loadProfiles();
        await this.loadModes();

        // S'abonner aux changements d'état
        this.subscribeToState();

        // Rendre le composant
        this.render();

        // Restaurer l'état depuis la session
        const profileState = window.stateManager.getState('profile');
        if (profileState && profileState.id) {
            // Si on a déjà les données en cache, on re-render juste
            if (profileState.data) {
                this.render();
            } else {
                // Sinon on recharge le profil
                await window.commandBus.execute('CHANGE_PROFILE', { profileId: profileState.id });
            }
        }
    }

    async loadProfiles() {
        try {
            const response = await window.apiV2.get('/catalog/api/profiles/');
            // apiV2.get retourne directement les données, pas un objet avec .data
            this.profiles = response.results || response;
        } catch (error) {
            console.error('Erreur chargement profils:', error);
            this.profiles = [];
        }
    }

    async loadModes() {
        try {
            const response = await window.apiV2.get('/wcm/api/modes/');
            // apiV2.get retourne directement les données, pas un objet avec .data
            this.modes = response.results || response;
        } catch (error) {
            console.error('Erreur chargement modes:', error);
            this.modes = [];
        }
    }

    subscribeToState() {
        // Écouter les changements du profil
        window.eventBus.on('state:changed:profile', () => {
            this.render();
        });
    }

    render() {
        const profileState = window.stateManager.getState('profile') || {};
        const selectedProfile = profileState.data;
        const cardBody = this.container.querySelector('.v2-card-body');

        if (!cardBody) return;

        cardBody.innerHTML = `
            <div class="v2-profile-selector">
                <div class="row align-items-center">
                    <div class="col-3">
                        ${this.renderProfileSelector(profileState.id)}
                    </div>
                    <div class="col-9">
                        ${selectedProfile ? this.renderModes(profileState.modes || {}) : ''}
                    </div>
                </div>
                ${selectedProfile ? this.renderProfileDetails(selectedProfile, profileState.modes || {}) : ''}
            </div>
        `;

        this.attachEventListeners();
    }

    renderProfileSelector(selectedId) {
        return `
            <select id="profile-select" class="form-select v2-input ${selectedId ? 'v2-input-filled' : ''}">
                <option value="">--</option>
                ${this.profiles.map(profile => `
                    <option value="${profile.id}" ${profile.id == selectedId ? 'selected' : ''}>
                        ${profile.name}
                    </option>
                `).join('')}
            </select>
        `;
    }

    renderProfileDetails(profile, modesState) {
        return `
            <div class="v2-profile-details">
                ${this.renderParameters(profile.profileparamvalue_set || [])}
                ${this.renderSpecifications(profile.profilespecvalue_set || [])}
            </div>
        `;
    }

    renderSpecifications(specifications) {
        if (!specifications.length) return '';

        return `
            <div class="v2-section">
                <h5 class="v2-section-title" style="color: var(--v2-gray-600); font-weight: normal; font-size: 0.875rem;">Spécifications</h5>
                <table class="table table-sm w-100">
                    <thead>
                        <tr>
                            <th class="fw-normal"></th>
                            <th class="text-center fw-normal">Min Alert</th>
                            <th class="text-center fw-normal">Min</th>
                            <th class="text-center fw-normal">Nominal</th>
                            <th class="text-center fw-normal">Max</th>
                            <th class="text-center fw-normal">Max Alert</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${specifications.map(spec => {
                            const name = spec.spec_item.display_name || spec.spec_item.name || '';
                            const isMasseSurfacique25cm = name.includes('(g/25cm²)') || name.includes('g/25cm');
                            const decimals = isMasseSurfacique25cm ? 4 : 2;
                            
                            const formatValue = (val) => {
                                if (!val && val !== 0) return '-';
                                return parseFloat(val).toFixed(decimals);
                            };
                            
                            return `
                                <tr>
                                    <td class="text-end">${spec.spec_item.display_name || spec.spec_item.name} ${spec.spec_item.unit ? `(${spec.spec_item.unit})` : ''}</td>
                                    <td class="text-center text-danger">${formatValue(spec.value_min_alert)}</td>
                                    <td class="text-center text-warning">${formatValue(spec.value_min)}</td>
                                    <td class="text-center" style="color: #198754;"><strong>${formatValue(spec.value_nominal)}</strong></td>
                                    <td class="text-center text-warning">${formatValue(spec.value_max)}</td>
                                    <td class="text-center text-danger">${formatValue(spec.value_max_alert)}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderParameters(parameters) {
        if (!parameters.length) return '';

        return `
            <div class="v2-section">
                <h5 class="v2-section-title" style="color: var(--v2-gray-600); font-weight: normal; font-size: 0.875rem;">Paramètres Machine</h5>
                <table class="table table-sm w-100">
                    <thead>
                        <tr>
                            <th class="fw-normal"></th>
                            <th class="text-center fw-normal">Valeur</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${parameters.map(param => `
                            <tr>
                                <td class="text-end">${param.param_item.display_name || param.param_item.name} ${param.param_item.unit ? `(${param.param_item.unit})` : ''}</td>
                                <td class="text-center"><strong>${param.value}</strong></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderModes(modesState) {
        if (!this.modes.length) return '';

        return `
            <div class="v2-modes-grid">
                ${this.modes.map(mode => `
                    <div class="v2-mode-item">
                        <label class="v2-checkbox-label">
                            <input type="checkbox" 
                                class="v2-checkbox" 
                                data-mode-id="${mode.id}"
                                ${modesState[mode.id] ? 'checked' : ''}>
                            <span>${mode.name}</span>
                        </label>
                    </div>
                `).join('')}
            </div>
        `;
    }

    attachEventListeners() {
        // Sélecteur de profil
        const profileSelect = this.container.querySelector('#profile-select');
        if (profileSelect) {
            // Visual feedback on input (pour que le changement soit immédiat)
            profileSelect.addEventListener('input', (e) => {
                const hasValue = !!e.target.value;
                // Gérer les classes comme le champ opérateur
                if (hasValue) {
                    e.target.classList.remove('v2-input');
                    e.target.classList.add('v2-input-filled');
                } else {
                    e.target.classList.remove('v2-input-filled');
                    e.target.classList.add('v2-input');
                }
            });
            
            // Business logic on change
            profileSelect.addEventListener('change', async (e) => {
                const profileId = e.target.value;
                
                await window.commandBus.execute('CHANGE_PROFILE', { 
                    profileId: profileId || null 
                });
            });
        }

        // Checkboxes des modes
        const modeCheckboxes = this.container.querySelectorAll('.v2-checkbox[data-mode-id]');
        modeCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', async (e) => {
                const modeId = e.target.dataset.modeId;
                await window.commandBus.execute('TOGGLE_MODE', {
                    modeId,
                    enabled: e.target.checked
                });
            });
        });
    }
}

// Initialiser le composant
const profileSelectorV2 = new ProfileSelectorV2();

// Exposer globalement si nécessaire
window.profileSelectorV2 = profileSelectorV2;