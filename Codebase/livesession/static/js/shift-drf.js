// Nouveau code avec DRF - BEAUCOUP plus simple !

class ShiftAPI {
    constructor() {
        this.endpoint = '/api/shift-draft/';
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
    
    async updateField(fieldName, value) {
        try {
            const response = await fetch(this.endpoint, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    [fieldName]: value
                })
            });
            
            const data = await response.json();
            
            // UN SEUL APPEL met à jour TOUT !
            if (data.validation && data.validation.is_valid) {
                // Mettre à jour les métriques
                this.updateMetrics(data.metrics);
                
                // Mettre à jour les autres champs si nécessaire
                this.updateRelatedFields(data);
            } else {
                // Afficher les erreurs
                this.showErrors(data.validation.errors);
            }
            
            return data;
            
        } catch (error) {
            console.error('Erreur API:', error);
        }
    }
    
    updateMetrics(metrics) {
        // Mise à jour automatique de TOUTES les métriques
        document.getElementById('temps-ouverture').textContent = metrics.to_formatted;
        document.getElementById('temps-perdu-total').textContent = metrics.tp_formatted;
        document.getElementById('temps-disponible').textContent = metrics.td_formatted;
        document.getElementById('lg-perdue').textContent = metrics.length_lost_formatted;
    }
    
    updateRelatedFields(data) {
        // Si on change la vacation, les heures sont mises à jour côté serveur
        if (data.start_time) {
            document.getElementById('id_start_time').value = data.start_time;
        }
        if (data.end_time) {
            document.getElementById('id_end_time').value = data.end_time;
        }
    }
    
    showErrors(errors) {
        // Affichage unifié des erreurs
        Object.entries(errors).forEach(([field, messages]) => {
            const fieldElement = document.querySelector(`[name="${field}"]`);
            if (fieldElement) {
                // Ajouter classe d'erreur
                fieldElement.classList.add('is-invalid');
                
                // Afficher message
                const errorDiv = fieldElement.nextElementSibling;
                if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv.textContent = messages.join(', ');
                }
            }
        });
    }
}

// Utilisation super simple
const shiftAPI = new ShiftAPI();

// Au lieu de 10 event listeners différents, UN SEUL !
document.querySelectorAll('input, select').forEach(element => {
    element.addEventListener('change', (e) => {
        shiftAPI.updateField(e.target.name, e.target.value);
    });
});


/* 
COMPARAISON :

AVANT (500+ lignes) :
====================
function saveShiftField(field, value) { ... }
function updateProductivityMetrics() { ... }
function updateShiftMetrics() { ... }
function calculateTOFromShiftHours() { ... }
function formatMinutesToHours() { ... }
// + 20 autres fonctions...

APRÈS (50 lignes) :
==================
- Une seule classe
- Un seul endpoint
- Métriques calculées côté serveur
- Validation automatique
- Gestion d'erreurs unifiée
*/