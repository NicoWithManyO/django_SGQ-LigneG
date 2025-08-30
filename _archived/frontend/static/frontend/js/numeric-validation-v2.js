/**
 * Validation numérique pour les champs V2
 * - Empêche la saisie de caractères non numériques
 * - Gère la conversion virgule/point pour les décimales
 * - Formate automatiquement certains champs (ex: numéro de rouleau sur 3 chiffres)
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // Fonction pour mettre à jour l'ID du rouleau
    function updateRollId() {
        if (!window.stateManager) return;
        
        const ofNumber = window.stateManager.getState('of.enCours');
        const rollNumberInput = document.getElementById('roll-number');
        const rollNumber = rollNumberInput?.value;
        
        if (ofNumber && rollNumber && rollNumber !== '--') {
            const rollId = `${ofNumber}_${rollNumber}`;
            
            // Mettre à jour l'affichage dans le bouton
            const saveIdSpan = document.getElementById('save-roll-id');
            if (saveIdSpan) {
                saveIdSpan.textContent = rollId;
            }
            
            // Mettre à jour l'affichage de l'ID
            const rollIdDisplay = document.getElementById('roll-id-display');
            if (rollIdDisplay) {
                rollIdDisplay.textContent = rollId;
            }
            
            // Mettre à jour l'icône
            const rollIdIcon = document.getElementById('roll-id-status-icon');
            if (rollIdIcon) {
                rollIdIcon.classList.remove('bi-dash-circle', 'text-muted');
                rollIdIcon.classList.add('bi-check-circle', 'text-success');
            }
            
            // Sauvegarder dans le state
            window.stateManager.setState('production.currentRollId', rollId);
        } else {
            // Pas d'ID valide
            const saveIdSpan = document.getElementById('save-roll-id');
            if (saveIdSpan) {
                saveIdSpan.textContent = '--';
            }
            
            const rollIdDisplay = document.getElementById('roll-id-display');
            if (rollIdDisplay) {
                rollIdDisplay.textContent = '--';
            }
            
            const rollIdIcon = document.getElementById('roll-id-status-icon');
            if (rollIdIcon) {
                rollIdIcon.classList.remove('bi-check-circle', 'text-success');
                rollIdIcon.classList.add('bi-dash-circle', 'text-muted');
            }
        }
    }
    
    // Exposer globalement pour pouvoir l'appeler depuis d'autres scripts
    window.updateRollId = updateRollId;
    
    // Fonction pour valider et formater les entrées numériques
    function setupNumericField(field, options = {}) {
        const {
            allowDecimal = true,
            decimalPlaces = 2,
            minValue = null,
            maxValue = null,
            padZeros = 0, // Pour formater avec des zéros (ex: 3 pour 001)
            onValidValue = null // Callback quand une valeur valide est entrée
        } = options;
        
        // Sélectionner tout le contenu au clic (sauf si readonly)
        field.addEventListener('click', (e) => {
            if (!e.target.readOnly) {
                e.target.select();
            }
        });
        
        // Sélectionner tout le contenu au focus (sauf si readonly)
        field.addEventListener('focus', (e) => {
            if (!e.target.readOnly) {
                e.target.select();
            }
        });
        
        // Empêcher les caractères non numériques lors de la saisie
        field.addEventListener('keypress', (e) => {
            const char = String.fromCharCode(e.which);
            const currentValue = field.value;
            
            // Permettre les touches de contrôle
            if (e.ctrlKey || e.metaKey) return;
            
            // Bloquer si ce n'est pas un chiffre, virgule ou point
            if (!/[\d.,]/.test(char)) {
                e.preventDefault();
                return;
            }
            
            // Si décimales non autorisées, bloquer virgule et point
            if (!allowDecimal && /[.,]/.test(char)) {
                e.preventDefault();
                return;
            }
            
            // Si déjà une décimale, bloquer une deuxième
            if (/[.,]/.test(char) && /[.,]/.test(currentValue)) {
                e.preventDefault();
                return;
            }
        });
        
        // Convertir virgule en point pendant la saisie
        field.addEventListener('input', (e) => {
            let value = e.target.value;
            
            // Remplacer virgule par point
            value = value.replace(',', '.');
            
            // Retirer les caractères non numériques (sauf le point)
            value = value.replace(/[^\d.]/g, '');
            
            // S'assurer qu'il n'y a qu'un seul point
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }
            
            e.target.value = value;
            
            // Si c'est un champ qui affecte le grammage, recalculer
            const fieldId = e.target.id;
            if (fieldId === 'tube-weight' || fieldId === 'roll-length' || fieldId === 'total-weight') {
                calculateGrammage();
            }
            
            // La gestion des épaisseurs est maintenant dans la commande ADD_THICKNESS_MEASUREMENT
        });
        
        // Formater au blur
        field.addEventListener('blur', (e) => {
            let value = e.target.value;
            
            if (value === '') return;
            
            // Convertir en nombre
            let numValue = parseFloat(value);
            
            if (isNaN(numValue)) {
                e.target.value = '';
                return;
            }
            
            // Appliquer les limites min/max
            if (minValue !== null && numValue < minValue) {
                numValue = minValue;
            }
            if (maxValue !== null && numValue > maxValue) {
                numValue = maxValue;
            }
            
            // Formater avec le bon nombre de décimales
            if (allowDecimal && decimalPlaces !== null) {
                value = numValue.toFixed(decimalPlaces);
                // Retirer les .00 inutiles
                value = value.replace(/\.?0+$/, '');
            } else {
                value = Math.round(numValue).toString();
            }
            
            // Ajouter des zéros devant si nécessaire
            if (padZeros > 0) {
                value = value.padStart(padZeros, '0');
            }
            
            e.target.value = value;
            
            // Callback si valeur valide
            if (onValidValue) {
                onValidValue(numValue, e.target);
            }
            
            // Mettre à jour dans le StateManager si disponible
            if (window.stateManager) {
                const fieldId = e.target.id;
                const stateKey = getStateKeyForField(fieldId);
                if (stateKey) {
                    console.log('📝 Saving to state:', stateKey, numValue);
                    
                    // Pour les chemins imbriqués dans currentRoll, s'assurer que l'objet existe
                    if (stateKey.includes('production.currentRoll.')) {
                        const currentRoll = window.stateManager.getState('production.currentRoll');
                        if (!currentRoll) {
                            window.stateManager.setState('production.currentRoll', {}, 'system');
                        }
                    }
                    
                    window.stateManager.setState(stateKey, numValue, 'user');
                }
            }
        });
    }
    
    // Mapper les IDs de champs aux clés du StateManager
    function getStateKeyForField(fieldId) {
        const mapping = {
            'roll-number': 'production.currentRollNumber',
            'tube-weight': 'production.currentRoll.tubeMass',
            'roll-length': 'production.currentRoll.length',
            'total-weight': 'production.currentRoll.totalMass',
            'next-tube': 'production.nextTubeWeight'
        };
        return mapping[fieldId] || null;
    }
    
    // Configurer les champs de la sticky bar
    const rollNumberField = document.getElementById('roll-number');
    if (rollNumberField) {
        // Fonction pour configurer le champ
        const setupRollNumber = () => {
            if (!rollNumberField.readOnly) {
                setupNumericField(rollNumberField, {
                    allowDecimal: false,
                    padZeros: 3,
                    minValue: 1,
                    maxValue: 999,
                    onValidValue: (value, field) => {
                        // Utiliser la commande pour changer le numéro de rouleau
                        if (window.commandBus) {
                            window.commandBus.execute('CHANGE_ROLL_NUMBER', {
                                rollNumber: parseInt(value)
                            });
                        } else {
                            updateRollId();
                        }
                    }
                });
            }
        };
        
        // Configurer initialement
        setupRollNumber();
        
        // Observer les changements de l'attribut readonly
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'readonly') {
                    // Mettre à jour le cursor selon l'état
                    if (rollNumberField.readOnly) {
                        rollNumberField.style.cursor = 'not-allowed';
                    } else {
                        rollNumberField.style.cursor = 'pointer';
                    }
                    setupRollNumber();
                }
            });
        });
        
        observer.observe(rollNumberField, { attributes: true });
        
        // Définir le cursor initial
        if (rollNumberField.readOnly) {
            rollNumberField.style.cursor = 'not-allowed';
        }
        
        // Écouter les changements manuels du champ (quand on tape directement)
        rollNumberField.addEventListener('input', (e) => {
            const value = e.target.value;
            if (value && /^\d+$/.test(value)) {
                // Utiliser la commande pour mettre à jour et calculer l'ID
                if (window.commandBus) {
                    window.commandBus.execute('CHANGE_ROLL_NUMBER', {
                        rollNumber: parseInt(value)
                    });
                } else {
                    console.log('⚠️ CommandBus not available, updating roll ID directly');
                    updateRollId();
                }
            }
        });
    }
    
    // Masse tube
    const tubeWeightField = document.getElementById('tube-weight');
    if (tubeWeightField) {
        setupNumericField(tubeWeightField, {
            allowDecimal: true,
            decimalPlaces: 1,
            minValue: 0,
            maxValue: 9999,
            onValidValue: (value) => {
                calculateGrammage();
            }
        });
    }
    
    // Longueur
    const rollLengthField = document.getElementById('roll-length');
    if (rollLengthField) {
        setupNumericField(rollLengthField, {
            allowDecimal: true,
            decimalPlaces: 1,
            minValue: 0,
            maxValue: 99999,
            onValidValue: (value) => {
                calculateGrammage();
            }
        });
    }
    
    // Masse totale
    const totalWeightField = document.getElementById('total-weight');
    if (totalWeightField) {
        setupNumericField(totalWeightField, {
            allowDecimal: true,
            decimalPlaces: 1,
            minValue: 0,
            maxValue: 99999,
            onValidValue: (value) => {
                calculateGrammage();
            }
        });
    }
    
    // Tube suivant
    const nextTubeField = document.getElementById('next-tube');
    if (nextTubeField) {
        setupNumericField(nextTubeField, {
            allowDecimal: true,
            decimalPlaces: 1,
            minValue: 0,
            maxValue: 9999
        });
    }
    
    // Calculer le grammage automatiquement
    function calculateGrammage() {
        const totalWeight = parseFloat(document.getElementById('total-weight')?.value) || 0;
        const tubeWeight = parseFloat(document.getElementById('tube-weight')?.value) || 0;
        const length = parseFloat(document.getElementById('roll-length')?.value) || 0;
        
        const grammageDisplay = document.getElementById('grammage-display');
        const netMassLabel = document.getElementById('net-mass-label');
        
        if (totalWeight > 0 && tubeWeight > 0 && length > 0 && totalWeight > tubeWeight) {
            const netWeight = totalWeight - tubeWeight;
            
            // Récupérer la largeur du feutre depuis le profil
            let feltWidth = 1; // Par défaut 1m
            if (window.stateManager) {
                feltWidth = window.stateManager.getState('production.currentProfile.feltWidth') || 1;
            }
            
            const surface = length * feltWidth;
            const grammage = (netWeight / surface).toFixed(1);
            
            // Mettre à jour l'affichage du grammage
            if (grammageDisplay) {
                grammageDisplay.textContent = `${grammage} g/m²`;
            }
            
            // Mettre à jour la masse nette
            if (netMassLabel) {
                // Retirer la décimale si c'est un nombre entier
                const netWeightFormatted = netWeight % 1 === 0 ? netWeight.toFixed(0) : netWeight.toFixed(1);
                netMassLabel.textContent = `${netWeightFormatted} g`;
            }
        } else {
            // Réinitialiser si données incomplètes
            if (grammageDisplay) {
                grammageDisplay.textContent = '-- g/m²';
            }
            if (netMassLabel) {
                netMassLabel.textContent = '-- g';
            }
        }
    }
    
    // Fonction publique pour configurer les champs d'épaisseur dans la grille
    window.setupThicknessField = function(field) {
        setupNumericField(field, {
            allowDecimal: true,
            decimalPlaces: 1,
            minValue: 0,
            maxValue: 99.9
            // La persistence est maintenant gérée par la commande ADD_THICKNESS_MEASUREMENT
            // dans le gestionnaire blur du composant roll-grid-v2
        });
    };
    
    // S'abonner aux changements d'OF pour mettre à jour l'ID du rouleau
    if (window.eventBus) {
        window.eventBus.on('system:ready', () => {
            if (window.stateManager) {
                // S'abonner aux changements d'OF
                window.stateManager.subscribe('of.enCours', (newValue, oldValue, source) => {
                    console.log('📋 OF changed:', oldValue, '->', newValue);
                    
                    // Si on a un OF et un numéro de rouleau, recalculer l'ID
                    const rollNumber = window.stateManager.getState('production.currentRollNumber');
                    if (newValue && rollNumber) {
                        if (window.commandBus) {
                            window.commandBus.execute('CHANGE_ROLL_NUMBER', {
                                rollNumber: parseInt(rollNumber)
                            });
                        } else {
                            updateRollId();
                        }
                    }
                });
                
                // Charger les valeurs initiales depuis le state
                const rollNumber = window.stateManager.getState('production.currentRollNumber');
                if (rollNumber) {
                    const rollNumberField = document.getElementById('roll-number');
                    if (rollNumberField) {
                        rollNumberField.value = String(rollNumber).padStart(3, '0');
                        console.log('✅ Roll number loaded into field:', rollNumberField.value);
                    }
                }
                
                const tubeWeight = window.stateManager.getState('production.currentRoll.tubeMass');
                if (tubeWeight) {
                    const tubeWeightField = document.getElementById('tube-weight');
                    if (tubeWeightField) {
                        tubeWeightField.value = tubeWeight;
                    }
                }
                
                const rollLength = window.stateManager.getState('production.currentRoll.length');
                if (rollLength) {
                    const rollLengthField = document.getElementById('roll-length');
                    if (rollLengthField) {
                        rollLengthField.value = rollLength;
                    }
                }
                
                const totalMass = window.stateManager.getState('production.currentRoll.totalMass');
                if (totalMass) {
                    const totalWeightField = document.getElementById('total-weight');
                    if (totalWeightField) {
                        totalWeightField.value = totalMass;
                    }
                }
                
                const nextTube = window.stateManager.getState('production.nextTubeWeight');
                if (nextTube) {
                    const nextTubeField = document.getElementById('next-tube');
                    if (nextTubeField) {
                        nextTubeField.value = nextTube;
                    }
                }
                
                // Mettre à jour l'ID initial
                updateRollId();
                
                // Calculer le grammage initial si on a les données
                calculateGrammage();
                
                // Vérification immédiate
                const immediateOf = window.stateManager.getState('of.enCours');
                const immediateRoll = window.stateManager.getState('production.currentRollNumber');
                
                if (immediateOf && immediateRoll) {
                    // Calculer l'ID immédiatement
                    updateRollId();
                }
                
                // Vérifier à nouveau après un délai pour être sûr
                setTimeout(() => {
                    const ofEnCours = window.stateManager.getState('of.enCours');
                    const currentRollNumber = window.stateManager.getState('production.currentRollNumber');
                    
                    if (ofEnCours && currentRollNumber) {
                        // Utiliser la commande pour générer l'ID proprement
                        if (window.commandBus) {
                            window.commandBus.execute('CHANGE_ROLL_NUMBER', {
                                rollNumber: parseInt(currentRollNumber)
                            });
                        } else {
                            // Fallback: forcer le recalcul de l'ID
                            updateRollId();
                        }
                    }
                }, 1000);  // Augmenter le délai à 1 seconde
            }
        });
    }
});