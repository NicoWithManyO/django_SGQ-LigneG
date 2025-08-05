/**
 * Composant pour gérer les nuages d'opérateurs sur le splash screen
 */
function operatorClouds() {
    return {
        operators: [],
        selectedOperator: null,
        selectedOperatorId: null,
        cloudPositions: [],
        
        async init() {
            try {
                const response = await fetch('/planification/api/operators/');
                const data = await response.json();
                
                // Ajouter l'initiale du nom pour tous les opérateurs
                this.operators = data.map(op => {
                    let displayName = op.first_name;
                    if (op.last_name) {
                        displayName += ` ${op.last_name.charAt(0)}.`;
                    }
                    return {
                        ...op,
                        cloud_display_name: displayName
                    };
                });
                
                // Générer des positions sans collision
                this.generateNonCollidingPositions();
            } catch (error) {
                console.error('Erreur lors du chargement des opérateurs:', error);
            }
        },
        
        generateNonCollidingPositions() {
            const positions = [
                { top: 8, left: 15 },
                { top: 18, left: 65 },
                { top: 35, left: 10 },
                { top: 45, left: 70 },
                { top: 55, left: 35 },
                { top: 10, left: 40 },
                { top: 30, left: 85 },
                { top: 50, left: 20 }
            ];
            
            // Mélanger les positions pour plus de variété
            this.cloudPositions = positions.sort(() => Math.random() - 0.5);
        },
        
        getCloudStyle(index) {
            const pos = this.cloudPositions[index] || { top: 20, left: 50 };
            return `top: ${pos.top}%; left: ${pos.left}%;`;
        },
        
        selectOperator(operator) {
            // Si c'est déjà sélectionné, on désélectionne
            if (this.selectedOperatorId === operator.employee_id) {
                this.selectedOperator = null;
                this.selectedOperatorId = null;
                
                // Vider la session - utiliser les bonnes clés pour shift-form
                window.session?.patch({ 
                    shift: {
                        operatorId: ''
                    },
                    shiftOperator: '',
                    selectedOperatorName: ''
                    // Ne PAS mettre operatorCleared car ça empêche la persistence
                });
                
                // Dispatch event pour notifier la désélection
                window.dispatchEvent(new CustomEvent('operator-preselected', { 
                    detail: { operator: null }
                }));
            } else {
                // Sinon on sélectionne
                this.selectedOperator = operator;
                this.selectedOperatorId = operator.employee_id;
                
                // Sauvegarder dans la session pour pré-remplir
                window.session?.patch({ 
                    shift: {
                        operatorId: operator.employee_id
                    },
                    shiftOperator: operator.employee_id,
                    selectedOperatorName: `${operator.first_name} ${operator.last_name}`
                    // Ne PAS mettre operatorCleared
                });
                
                // Dispatch event pour notifier la sélection
                window.dispatchEvent(new CustomEvent('operator-preselected', { 
                    detail: { operator }
                }));
            }
        }
    };
}