function checklistReview() {
    return {
        // État
        pendingCount: 0,
        signedToday: 0,
        avgSignatureTime: '--',
        conformityRate: 0,
        currentChecklistId: null,
        currentShiftId: '',
        visa: '',
        isSubmitting: false,
        visaModal: null,
        
        // Initialisation
        init() {
            // Initialiser le modal Bootstrap
            this.visaModal = new bootstrap.Modal(this.$refs.visaModal);
            
            // Charger les statistiques
            this.loadStatistics();
            
            // Écouter l'événement de signature
            window.addEventListener('checklist-signed', () => {
                this.reloadPage();
            });
            
            // Calculer le nombre en attente depuis le DOM
            const pendingRows = document.querySelectorAll('.checklist-pending');
            this.pendingCount = pendingRows.length;
        },
        
        // Charger les statistiques
        async loadStatistics() {
            try {
                // TODO: Créer un endpoint pour les statistiques des checklists
                // Pour l'instant, utiliser des valeurs par défaut
                this.signedToday = 0;
                this.avgSignatureTime = '2.5h';
                this.conformityRate = 95;
            } catch (error) {
                console.error('Erreur chargement statistiques:', error);
            }
        },
        
        // Ouvrir le modal de visa
        openVisaModal(checklistId, shiftId) {
            this.currentChecklistId = checklistId;
            this.currentShiftId = shiftId;
            this.visa = '';
            this.isSubmitting = false;
            this.visaModal.show();
            
            // Focus sur le champ visa après ouverture
            setTimeout(() => {
                document.getElementById('visaInput')?.focus();
            }, 300);
        },
        
        // Soumettre le visa
        async submitVisa() {
            // Validation
            if (!this.visa || this.visa.length < 2) {
                alert('Veuillez entrer vos initiales (minimum 2 caractères)');
                return;
            }
            
            this.isSubmitting = true;
            
            try {
                const response = await fetch(`/management/api/checklists/${this.currentChecklistId}/sign/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        visa: this.visa.toUpperCase()
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Erreur lors de la signature');
                }
                
                // Succès
                this.visaModal.hide();
                this.showSuccess('Checklist visée avec succès');
                
                // Émettre l'événement
                window.dispatchEvent(new Event('checklist-signed'));
                
            } catch (error) {
                console.error('Erreur signature:', error);
                alert(error.message || 'Erreur lors de la signature de la checklist');
            } finally {
                this.isSubmitting = false;
            }
        },
        
        // Recharger la page
        reloadPage() {
            window.location.reload();
        },
        
        // Récupérer le cookie CSRF
        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },
        
        // Afficher un message de succès
        showSuccess(message) {
            // Créer une notification toast Bootstrap
            const toastHtml = `
                <div class="toast align-items-center text-white bg-success border-0" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="bi bi-check-circle me-2"></i>${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            // Créer un container si nécessaire
            let toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container';
                toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
                document.body.appendChild(toastContainer);
            }
            
            // Ajouter le toast
            toastContainer.insertAdjacentHTML('beforeend', toastHtml);
            const toast = toastContainer.lastElementChild;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            // Supprimer après fermeture
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        }
    }
}