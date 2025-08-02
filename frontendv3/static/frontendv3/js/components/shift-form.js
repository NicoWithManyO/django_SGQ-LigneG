/**
 * Composant Alpine.js : Formulaire de Fiche de Poste
 * Gère la sélection opérateur, date, vacation et génération ID shift
 */

function shiftForm() {
    // Charger les données sauvegardées AVANT l'initialisation
    const savedData = window.sessionData?.shift || {};
    
    return {
        // État local avec les valeurs sauvegardées
        operatorId: savedData.operatorId || '',
        date: savedData.date || new Date().toISOString().split('T')[0],
        vacation: savedData.vacation || '',
        shiftId: savedData.shiftId || '',
        operators: window.operatorsData || [],
        shiftIdExists: null, // null, true, false
        checkingShiftId: false,
        
        // État de la check-list
        checklistSigned: false,
        
        // État du temps perdu démarrage
        hasStartupDowntime: false,
        
        // État du contrôle qualité
        qcBadgeStatus: 'pending',
        
        // Nouveaux champs pour prise de poste
        startTime: savedData.startTime || '',
        machineStartedStart: savedData.machineStartedStart || false,
        lengthStart: savedData.lengthStart || '',
        
        // Champs pour fin de poste
        endTime: savedData.endTime || '',
        machineStartedEnd: savedData.machineStartedEnd || false,
        lengthEnd: savedData.lengthEnd || '',
        
        // Commentaires
        comments: savedData.comments || '',
        
        // Options de vacation
        vacationOptions: [
            { value: 'Matin', label: 'Matin' },
            { value: 'ApresMidi', label: 'Après-midi' },
            { value: 'Nuit', label: 'Nuit' },
            { value: 'Journee', label: 'Journée' }
        ],
        
        
        // Computed: peut-on sauvegarder le poste ?
        get canSaveShift() {
            // Conditions de base
            if (this.shiftIdExists !== false || !this.checklistSigned || this.qcBadgeStatus === 'pending') {
                return false;
            }
            
            // Si machine PAS démarrée au début, il faut OBLIGATOIREMENT un temps perdu démarrage
            if (!this.machineStartedStart && !this.hasStartupDowntime) {
                return false;
            }
            
            // Si machine démarrée en début, il faut une longueur > 0
            if (this.machineStartedStart && (!this.lengthStart || parseFloat(this.lengthStart) <= 0)) {
                return false;
            }
            
            // Si machine démarrée en fin, il faut une longueur > 0
            if (this.machineStartedEnd && (!this.lengthEnd || parseFloat(this.lengthEnd) <= 0)) {
                return false;
            }
            
            return true;
        },
        
        // Computed: message du tooltip pour le bouton sauvegarder
        get saveButtonTooltip() {
            // Si le bouton est actif, pas de tooltip
            if (this.canSaveShift) {
                return '';
            }
            
            // Vérifier les conditions dans l'ordre de priorité
            if (!this.operatorId || !this.date || !this.vacation) {
                return "Veuillez remplir tous les champs obligatoires (opérateur, date, vacation)";
            }
            
            if (this.shiftIdExists === null || this.checkingShiftId) {
                return "Vérification de l'ID de poste en cours...";
            }
            
            if (this.shiftIdExists === true) {
                return "L'ID de poste existe déjà dans la base de données";
            }
            
            if (!this.checklistSigned) {
                return "La check-list de prise de poste doit être complétée et signée";
            }
            
            if (this.qcBadgeStatus === 'pending') {
                return "Le contrôle qualité doit être effectué (badge QC en attente)";
            }
            
            // Conditions machine
            if (!this.machineStartedStart && !this.hasStartupDowntime) {
                return "Machine non démarrée : vous devez déclarer un temps perdu de type 'démarrage'";
            }
            
            if (this.machineStartedStart && (!this.lengthStart || parseFloat(this.lengthStart) <= 0)) {
                return "Machine démarrée : la longueur de début doit être supérieure à 0";
            }
            
            if (this.machineStartedEnd && (!this.lengthEnd || parseFloat(this.lengthEnd) <= 0)) {
                return "Machine démarrée en fin : la longueur de fin doit être supérieure à 0";
            }
            
            // Si on arrive ici, c'est un cas non géré
            return "Conditions de sauvegarde non remplies";
        },
        
        
        // Initialisation
        init() {
            debug('Shift form initialized');
            
            // Trier les opérateurs par ordre alphabétique (nom + prénom)
            this.operators.sort((a, b) => {
                return a.display_name.localeCompare(b.display_name, 'fr-FR');
            });
            
            // Vérifier l'ID existant au chargement
            if (this.shiftId) {
                this.checkShiftIdExists();
            }
            
            // Observer les changements pour la génération automatique ET la sauvegarde
            this.$watch('operatorId', () => {
                this.tryGenerateShiftId();
                this.saveToSession();
            });
            this.$watch('date', () => {
                this.tryGenerateShiftId();
                this.saveToSession();
            });
            this.$watch('vacation', () => {
                this.tryGenerateShiftId();
                this.saveToSession();
            });
            
            // Observer les nouveaux champs
            this.$watch('startTime', () => this.saveToSession());
            this.$watch('machineStartedStart', () => {
                if (!this.machineStartedStart) {
                    this.lengthStart = '';
                }
                this.saveToSession();
            });
            this.$watch('lengthStart', () => this.saveToSession());
            
            // Observer les champs de fin
            this.$watch('endTime', () => this.saveToSession());
            this.$watch('machineStartedEnd', () => {
                if (!this.machineStartedEnd) {
                    this.lengthEnd = '';
                }
                this.saveToSession();
            });
            this.$watch('lengthEnd', () => this.saveToSession());
            
            // Observer les commentaires
            this.$watch('comments', () => this.saveToSession());
            
            // Écouter l'événement de signature de la check-list
            window.addEventListener('checklist-signed-changed', (event) => {
                this.checklistSigned = event.detail.signed;
            });
            
            // Écouter l'événement de temps perdu démarrage
            window.addEventListener('downtime-startup-changed', (event) => {
                this.hasStartupDowntime = event.detail.hasStartupDowntime;
                debug('Startup downtime changed:', this.hasStartupDowntime);
            });
            
            // Écouter l'événement de changement du badge QC
            window.addEventListener('qc-badge-changed', (event) => {
                this.qcBadgeStatus = event.detail.status;
                debug('QC badge status changed:', this.qcBadgeStatus);
            });
            
            // Appliquer les styles initiaux après le rendu
            this.$nextTick(() => {
                this.updateFieldStyles();
            });
            
            // Observer les changements d'état du bouton pour gérer le tooltip
            this.$watch('canSaveShift', (newValue) => {
                this.$nextTick(() => {
                    if (this.$refs.saveButtonWrapper) {
                        const existingTooltip = bootstrap.Tooltip.getInstance(this.$refs.saveButtonWrapper);
                        
                        if (newValue && existingTooltip) {
                            // Si le bouton devient actif, détruire le tooltip
                            existingTooltip.dispose();
                        } else if (!newValue && !existingTooltip) {
                            // Si le bouton devient inactif, créer le tooltip
                            new bootstrap.Tooltip(this.$refs.saveButtonWrapper);
                        }
                    }
                });
            });
            
            // Observer les changements de tooltip pour mettre à jour l'instance Bootstrap
            this.$watch('saveButtonTooltip', () => {
                this.$nextTick(() => {
                    if (this.$refs.saveButtonWrapper && !this.canSaveShift) {
                        const tooltip = bootstrap.Tooltip.getInstance(this.$refs.saveButtonWrapper);
                        if (tooltip) {
                            tooltip.setContent({ '.tooltip-inner': this.saveButtonTooltip || '' });
                        }
                    }
                });
            });
        },
        
        // Mettre à jour les styles des champs
        updateFieldStyles() {
            const operatorSelect = this.$el.querySelector('select[x-model="operatorId"]');
            const dateInput = this.$el.querySelector('input[x-model="date"]');
            const vacationSelect = this.$el.querySelector('select[x-model="vacation"]');
            
            if (operatorSelect) {
                operatorSelect.classList.toggle('filled', !!this.operatorId);
                if (this.operatorId) operatorSelect.value = this.operatorId;
            }
            if (dateInput) {
                dateInput.classList.toggle('filled', !!this.date);
                if (this.date) dateInput.value = this.date;
            }
            if (vacationSelect) {
                vacationSelect.classList.toggle('filled', !!this.vacation);
                if (this.vacation) vacationSelect.value = this.vacation;
            }
        },
        
        // Vérifier si on peut générer l'ID
        canGenerateId() {
            return this.operatorId && this.date && this.vacation;
        },
        
        // Générer l'ID shift si possible
        tryGenerateShiftId() {
            if (!this.canGenerateId()) {
                this.shiftId = '';
                this.shiftIdExists = null;
                return;
            }
            
            // Format: DDMMYY_PrenomNom_Vacation
            const operator = this.operators.find(op => op.employee_id === this.operatorId);
            if (!operator) return;
            
            const [year, month, day] = this.date.split('-');
            const dateStr = `${day}${month}${year.slice(2)}`;
            
            // Extraire prénom et nom de l'employee_id
            // Format possible : PrenomNOM ou juste Prenom
            const match = operator.employee_id.match(/^([A-Z][a-z]+)([A-Z]+)?$/);
            if (!match) {
                // Si ça ne match pas, utiliser tel quel
                this.shiftId = `${dateStr}_${operator.employee_id}_${this.vacation}`;
                debug('Shift ID generated (fallback):', this.shiftId);
                this.checkShiftIdExists();
                this.saveToSession();
                return;
            }
            
            const [_, prenom, nom] = match;
            
            this.shiftId = `${dateStr}_${prenom}${nom || ''}_${this.vacation}`;
            debug('Shift ID generated:', this.shiftId);
            
            // Vérifier si l'ID existe
            this.checkShiftIdExists();
            
            // Sauvegarder
            this.saveToSession();
        },
        
        // Sauvegarder dans la session
        saveToSession() {
            const data = {
                operatorId: this.operatorId,
                date: this.date,
                vacation: this.vacation,
                shiftId: this.shiftId,
                startTime: this.startTime,
                machineStartedStart: this.machineStartedStart,
                lengthStart: this.lengthStart,
                endTime: this.endTime,
                machineStartedEnd: this.machineStartedEnd,
                lengthEnd: this.lengthEnd,
                comments: this.comments
            };
            
            // Utiliser la sauvegarde simple
            window.saveToSession('shift', data);
        },
        
        // Handlers pour les changements
        handleOperatorChange(event) {
            this.operatorId = event.target.value;
            event.target.classList.toggle('filled', !!this.operatorId);
            
            // Émettre un événement pour notifier le changement d'opérateur
            window.dispatchEvent(new CustomEvent('operator-changed', {
                detail: { operatorId: this.operatorId }
            }));
        },
        
        handleDateChange(event) {
            this.date = event.target.value;
            event.target.classList.toggle('filled', !!this.date);
        },
        
        handleVacationChange(event) {
            this.vacation = event.target.value;
            event.target.classList.toggle('filled', !!this.vacation);
            
            // Remplir automatiquement les horaires selon la vacation
            const vacationHours = {
                'Matin': { start: '04:00', end: '12:00' },
                'ApresMidi': { start: '12:00', end: '20:00' },
                'Nuit': { start: '20:00', end: '04:00' },
                'Journee': { start: '07:30', end: '15:30' }
            };
            
            if (vacationHours[this.vacation]) {
                this.startTime = vacationHours[this.vacation].start;
                this.endTime = vacationHours[this.vacation].end;
                
                // Mettre à jour les classes visuelles
                this.$nextTick(() => {
                    const startInput = this.$el.querySelector('input[x-model="startTime"]');
                    const endInput = this.$el.querySelector('input[x-model="endTime"]');
                    if (startInput) startInput.classList.add('filled');
                    if (endInput) endInput.classList.add('filled');
                });
            }
        },
        
        // Nouveaux handlers
        handleStartTimeChange(event) {
            this.startTime = event.target.value;
            event.target.classList.toggle('filled', !!this.startTime);
        },
        
        handleMachineStartChange(event) {
            this.machineStartedStart = event.target.checked;
        },
        
        handleLengthStartChange(event) {
            this.lengthStart = event.target.value;
            event.target.classList.toggle('filled', !!this.lengthStart);
        },
        
        // Handlers pour fin de poste
        handleEndTimeChange(event) {
            this.endTime = event.target.value;
            event.target.classList.toggle('filled', !!this.endTime);
        },
        
        handleMachineEndChange(event) {
            this.machineStartedEnd = event.target.checked;
        },
        
        handleLengthEndChange(event) {
            this.lengthEnd = event.target.value;
            event.target.classList.toggle('filled', !!this.lengthEnd);
        },
        
        // Handler pour commentaires
        handleCommentsChange(event) {
            this.comments = event.target.value;
        },
        
        // Sauvegarder le poste
        async saveShift() {
            // Validation basique
            if (!this.operatorId || !this.date || !this.vacation) {
                showNotification('error', 'Veuillez remplir tous les champs obligatoires');
                return;
            }
            
            const data = {
                shift_id: this.shiftId,
                operator_id: this.operatorId,
                date: this.date,
                vacation: this.vacation,
                start_time: this.startTime,
                end_time: this.endTime,
                started_at_beginning: this.machineStartedStart,
                meter_reading_start: this.lengthStart || null,
                started_at_end: this.machineStartedEnd,
                meter_reading_end: this.lengthEnd || null,
                operator_comments: this.comments || ''
            };
            
            try {
                const response = await fetch('/production/api/shifts/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                    },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                showNotification('success', 'Poste sauvegardé avec succès');
                
                // Émettre un événement
                window.dispatchEvent(new CustomEvent('shift-saved', { 
                    detail: { shift: result }
                }));
                
            } catch (error) {
                console.error('Erreur sauvegarde poste:', error);
                showNotification('error', 'Erreur lors de la sauvegarde du poste');
            }
        },
        
        // Récupérer la longueur du dernier poste
        async fetchLastShiftLength() {
            try {
                // Récupérer la longueur
                const response = await fetch('/production/api/shifts/last/');
                const data = await response.json();
                if (data && data.wound_length_end) {
                    this.lengthStart = data.wound_length_end.toString();
                    this.machineStartedStart = true; // Cocher la case si on a une valeur
                    
                    // Mettre à jour visuellement
                    this.$nextTick(() => {
                        const input = this.$el.querySelector('input[x-model="lengthStart"]');
                        if (input) input.classList.add('filled');
                    });
                    
                    showNotification('success', `Longueur récupérée : ${data.wound_length_end} m`);
                } else {
                    showNotification('info', 'Aucune longueur trouvée pour le dernier poste');
                }
            } catch (error) {
                console.error('Erreur récupération longueur:', error);
                showNotification('error', 'Erreur lors de la récupération');
            }
        },
        
        // Vérifier si l'ID shift existe en base
        async checkShiftIdExists() {
            if (!this.shiftId) {
                this.shiftIdExists = null;
                return;
            }
            
            this.checkingShiftId = true;
            try {
                const response = await fetch(`/production/api/shifts/check-id/?shift_id=${this.shiftId}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                this.shiftIdExists = data.exists;
            } catch (error) {
                console.error('Erreur vérification ID shift:', error);
                this.shiftIdExists = null;
            } finally {
                this.checkingShiftId = false;
            }
        }
    };
}

// Export global pour Alpine
window.shiftForm = shiftForm;