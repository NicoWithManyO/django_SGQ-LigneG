/**
 * Composant V2 pour la gestion des champs verrouillables
 * Utilise le CommandBus et l'EventBus pour une architecture découplée
 */

class FieldLockManager {
    constructor() {
        this.fields = new Map();
        this.init();
    }
    
    init() {
        // Écouter les événements de verrouillage/déverrouillage
        window.eventBus.on('field:locked', this.handleFieldLocked.bind(this));
        window.eventBus.on('field:unlocked', this.handleFieldUnlocked.bind(this));
        
        // Attendre que le système soit prêt
        if (window.eventBus) {
            window.eventBus.on('system:ready', () => {
                this.scanAndInitFields();
            });
        } else {
            // Fallback si eventBus pas encore disponible
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => this.scanAndInitFields(), 500);
            });
        }
    }
    
    /**
     * Scanner le DOM pour trouver tous les champs verrouillables
     */
    scanAndInitFields() {
        const unlockButtons = document.querySelectorAll('.btn-unlock');
        const fieldIds = [];
        
        unlockButtons.forEach(btn => {
            const inputGroup = btn.closest('.input-group');
            if (!inputGroup) return;
            
            const field = inputGroup.querySelector('input, select');
            if (!field || !field.id) return;
            
            // Enregistrer le champ
            this.registerField(field.id, {
                element: field,
                button: btn,
                inputGroup: inputGroup
            });
            
            fieldIds.push(field.id);
            
            // Attacher les événements au bouton
            this.attachButtonEvents(btn, field.id);
            
            // Attacher les événements au champ
            this.attachFieldEvents(field);
        });
        
        // Initialiser l'état de verrouillage
        if (fieldIds.length > 0 && window.commandBus) {
            window.commandBus.execute('INIT_FIELD_LOCKS', { fields: fieldIds });
        }
    }
    
    /**
     * Enregistrer un champ verrouillable
     */
    registerField(fieldId, config) {
        this.fields.set(fieldId, config);
    }
    
    /**
     * Attacher les événements au bouton de déverrouillage
     */
    attachButtonEvents(button, fieldId) {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (window.commandBus) {
                await window.commandBus.execute('UNLOCK_FIELD', { fieldId });
            }
        });
    }
    
    /**
     * Attacher les événements au champ
     */
    attachFieldEvents(field) {
        // Sur blur, reverrouiller le champ
        field.addEventListener('blur', async (e) => {
            const fieldId = e.target.id;
            const value = e.target.value;
            
            if (window.commandBus) {
                await window.commandBus.execute('LOCK_FIELD', { 
                    fieldId, 
                    value 
                });
            }
        });
        
        // Sur Enter, valider et reverrouiller
        field.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                field.blur();
            }
        });
    }
    
    /**
     * Gérer l'événement de verrouillage
     */
    handleFieldLocked(data) {
        const { fieldId } = data;
        const config = this.fields.get(fieldId);
        
        if (!config) return;
        
        const { element, button } = config;
        
        // Verrouiller le champ
        if (element.tagName === 'SELECT') {
            element.setAttribute('disabled', 'disabled');
        }
        element.setAttribute('readonly', 'readonly');
        
        // Ajouter la classe visuelle
        element.classList.add('v2-input-locked');
        
        // Activer le bouton
        button.disabled = false;
        
        // Animation du crayon
        this.animateIcon(button, 'lock');
    }
    
    /**
     * Gérer l'événement de déverrouillage
     */
    handleFieldUnlocked(data) {
        const { fieldId } = data;
        const config = this.fields.get(fieldId);
        
        if (!config) return;
        
        const { element, button } = config;
        
        // Déverrouiller le champ
        if (element.tagName === 'SELECT') {
            element.removeAttribute('disabled');
        }
        element.removeAttribute('readonly');
        
        // Retirer la classe visuelle
        element.classList.remove('v2-input-locked');
        
        // Focus sur le champ
        element.focus();
        
        // Sélectionner le contenu si c'est un input
        if (element.tagName === 'INPUT' && element.type !== 'checkbox') {
            element.select();
        }
        
        // Désactiver temporairement le bouton
        button.disabled = true;
        
        // Animation du crayon
        this.animateIcon(button, 'unlock');
    }
    
    /**
     * Animer l'icône du bouton
     */
    animateIcon(button, action) {
        const icon = button.querySelector('i');
        if (!icon) return;
        
        // Ajouter une classe d'animation
        icon.classList.add('v2-icon-animate');
        
        // Changer l'icône temporairement
        if (action === 'unlock') {
            icon.classList.remove('bi-pencil');
            icon.classList.add('bi-pencil-fill');
        }
        
        // Retirer l'animation après 300ms
        setTimeout(() => {
            icon.classList.remove('v2-icon-animate');
            if (action === 'unlock') {
                icon.classList.add('bi-pencil');
                icon.classList.remove('bi-pencil-fill');
            }
        }, 300);
    }
    
    /**
     * Obtenir l'état de verrouillage d'un champ
     */
    isLocked(fieldId) {
        if (window.stateManager) {
            return window.stateManager.getState(`ui.locks.${fieldId}`, true);
        }
        return true;
    }
    
    /**
     * Verrouiller tous les champs
     */
    async lockAll() {
        for (const [fieldId] of this.fields) {
            if (window.commandBus) {
                await window.commandBus.execute('LOCK_FIELD', { fieldId });
            }
        }
    }
    
    /**
     * Déverrouiller tous les champs
     */
    async unlockAll() {
        for (const [fieldId] of this.fields) {
            if (window.commandBus) {
                await window.commandBus.execute('UNLOCK_FIELD', { fieldId });
            }
        }
    }
}

// Créer et exposer l'instance globale
window.fieldLockManager = new FieldLockManager();