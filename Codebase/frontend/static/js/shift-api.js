/**
 * API centralisée pour la gestion du shift avec DRF
 */
class ShiftAPI {
    constructor() {
        this.endpoint = '/livesession/api/shift-draft/';
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
    }
    
    /**
     * Met à jour un ou plusieurs champs du shift
     * @param {Object} data - Les champs à mettre à jour
     * @returns {Promise<Object>} - Les données complètes avec métriques
     */
    async updateFields(data) {
        try {
            const response = await fetch(this.endpoint, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Gérer les erreurs de validation
            if (result.validation && !result.validation.is_valid) {
                console.error('Erreurs de validation:', result.validation.errors);
                // Afficher les erreurs à l'utilisateur
                this.showValidationErrors(result.validation.errors);
            }
            
            return result;
        } catch (error) {
            console.error('Erreur API:', error);
            throw error;
        }
    }
    
    /**
     * Récupère toutes les données du shift
     * @returns {Promise<Object>} - Les données complètes avec métriques
     */
    async getShiftData() {
        try {
            const response = await fetch(this.endpoint, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur API:', error);
            return {};
        }
    }
    
    /**
     * Efface toutes les données du shift
     * @returns {Promise<void>}
     */
    async clearShift() {
        try {
            const response = await fetch(this.endpoint, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error('Erreur API:', error);
            throw error;
        }
    }
    
    /**
     * Affiche les erreurs de validation
     * @param {Object} errors - Les erreurs par champ
     */
    showValidationErrors(errors) {
        // Retirer les anciennes erreurs
        document.querySelectorAll('.field-error').forEach(el => el.remove());
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        
        // Afficher les nouvelles erreurs
        Object.entries(errors).forEach(([field, messages]) => {
            const fieldElement = document.querySelector(`[name="${field}"]`);
            if (fieldElement) {
                fieldElement.classList.add('is-invalid');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'text-danger small field-error mt-1';
                errorDiv.textContent = Array.isArray(messages) ? messages.join(', ') : messages;
                fieldElement.parentElement.appendChild(errorDiv);
            }
        });
    }
}

// Instance globale
window.shiftAPI = new ShiftAPI();