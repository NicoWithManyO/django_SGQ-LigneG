/**
 * Écran de démarrage avec animation de glissement
 */
function splashScreen() {
    return {
        isVisible: false,
        isAnimating: false,
        
        init() {
            // Écouter l'événement pour afficher le splash
            window.addEventListener('show-splash', () => {
                this.showSplash();
            });
            
            // Écouter la présélection d'opérateur depuis les nuages
            window.addEventListener('operator-preselected', (e) => {
                // Notification visuelle de la sélection
                const operatorName = e.detail.operator.first_name;
                console.log(`Opérateur ${operatorName} sélectionné`);
            });
        },
        
        showSplash() {
            this.isVisible = true;
            this.isAnimating = false;
            // Empêcher le scroll pendant le splash
            document.body.style.overflow = 'hidden';
        },
        
        startProduction() {
            this.isAnimating = true;
            
            // Attendre la fin de l'animation
            setTimeout(() => {
                this.isVisible = false;
                this.isAnimating = false;
                document.body.style.overflow = '';
            }, 800);
        }
    };
}