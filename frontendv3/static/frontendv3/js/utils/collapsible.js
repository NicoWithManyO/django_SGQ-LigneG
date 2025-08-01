/**
 * Mixin Alpine.js pour rendre un composant enroulable/déroulable
 * Avec animation de bordure du header
 */

function collapsibleMixin(defaultExpanded = true) {
    return {
        isExpanded: defaultExpanded,
        
        // Initialiser le composant collapsible
        initCollapsible() {
            // Rien à faire, les styles sont dans main.css
        },
        
        // Basculer l'état
        toggleExpanded() {
            this.isExpanded = !this.isExpanded;
        },
        
        // Getter pour l'icône chevron
        get chevronClass() {
            return this.isExpanded ? 'bi-chevron-down' : 'bi-chevron-up';
        }
    };
}

// Export global
window.collapsibleMixin = collapsibleMixin;