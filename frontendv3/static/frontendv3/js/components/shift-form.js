/**
 * Composant Alpine.js : Formulaire de Fiche de Poste
 * Gère la sélection opérateur, date, vacation et génération ID shift
 */

function shiftForm() {
    // Charger les données sauvegardées AVANT l'initialisation
    const savedData = window.sessionData?.shift || {};
    
    return {
        // Mixins
        ...window.sessionMixin,
        ...window.watcherMixin,
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
        
        // Commentaires - on ne charge que si non vide
        comments: (savedData.comments && savedData.comments.trim()) ? savedData.comments : undefined,
        
        // Champs formation
        isTraining: savedData.isTraining || false,
        traineeId: savedData.traineeId || '',
        
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
            
            // Si machine démarrée en début, il faut une longueur >= 0
            if (this.machineStartedStart && (!this.lengthStart || parseFloat(this.lengthStart) < 0)) {
                return false;
            }
            
            // Si machine démarrée en fin, il faut une longueur >= 0
            if (this.machineStartedEnd && (!this.lengthEnd || parseFloat(this.lengthEnd) < 0)) {
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
            
            // Collecter toutes les raisons de désactivation
            const reasons = [];
            
            // Vérifier les champs obligatoires
            if (!this.operatorId || !this.date || !this.vacation) {
                reasons.push("Renseigner les champs Opérateur, Date & Vacation");
            }
            
            // Vérifier l'ID de poste
            if (this.shiftIdExists === null || this.checkingShiftId) {
                return "Renseigner les champs Opérateur, Date & Vacation"; // Cas spécial : on retourne directement
            }
            
            if (this.shiftIdExists === true) {
                reasons.push("L'ID de poste existe déjà dans la base de données");
            }
            
            // Vérifier la check-list
            if (!this.checklistSigned) {
                reasons.push("La check-list doit être complétée et signée");
            }
            
            // Vérifier le contrôle qualité
            if (this.qcBadgeStatus === 'pending') {
                reasons.push("Le contrôle qualité doit être effectué");
            }
            
            // Vérifier les conditions machine
            if (!this.machineStartedStart && !this.hasStartupDowntime) {
                reasons.push("Déclarer un temps de démarrage (machine non démarrée)");
            }
            
            if (this.machineStartedStart && (!this.lengthStart || parseFloat(this.lengthStart) < 0)) {
                reasons.push("Indiquer une longueur de début >= 0 (machine démarrée)");
            }
            
            if (this.machineStartedEnd && (!this.lengthEnd || parseFloat(this.lengthEnd) < 0)) {
                reasons.push("Indiquer une longueur de fin >= 0 (machine démarrée)");
            }
            
            // Construire le message final
            if (reasons.length === 0) {
                return "Conditions de sauvegarde non remplies";
            } else if (reasons.length === 1) {
                return reasons[0];
            } else {
                return "• " + reasons.join("\n• ");
            }
        },
        
        
        // Initialisation
        init() {
            debug('Shift form initialized');
            
            // Initialiser le mixin session
            this.initSession();
            
            // Trier les opérateurs par ordre alphabétique (nom + prénom)
            this.operators.sort((a, b) => {
                return a.display_name.localeCompare(b.display_name, 'fr-FR');
            });
            
            // Vérifier si un opérateur a été présélectionné depuis le splash
            const sessionData = window.sessionData || {};
            // Si shiftOperator existe dans la session, il override les données sauvegardées
            if ('shiftOperator' in sessionData && sessionData.shiftOperator) {
                this.operatorId = sessionData.shiftOperator;
                debug(`Operator from splash: "${this.operatorId}" (overrides saved: "${savedData.operatorId}")`);
                
                // IMPORTANT: Nettoyer shiftOperator après l'avoir utilisé
                window.session?.patch({ shiftOperator: '' });
                
                // Déclencher le changement pour générer l'ID du shift et émettre les événements
                this.$nextTick(() => {
                    this.handleOperatorChange({ target: { value: this.operatorId } });
                    // Forcer l'émission pour être sûr que sticky-bar se met à jour
                    this.emitShiftDataChanged();
                });
            }
            
            // Vérifier l'ID existant au chargement
            if (this.shiftId) {
                this.checkShiftIdExists();
            }
            
            // Écouter la présélection d'opérateur depuis le splash
            window.addEventListener('operator-preselected', (e) => {
                if (e.detail) {
                    const previousOperatorId = this.operatorId;
                    
                    if (e.detail.operator) {
                        // Sélection d'un opérateur
                        this.operatorId = e.detail.operator.employee_id;
                    } else {
                        // Désélection
                        this.operatorId = '';
                    }
                    
                    // Si l'opérateur a changé, émettre l'événement
                    if (previousOperatorId !== this.operatorId) {
                        window.dispatchEvent(new CustomEvent('operator-changed', {
                            detail: { operatorId: this.operatorId }
                        }));
                    }
                    
                    this.$nextTick(() => {
                        this.handleOperatorChange({ target: { value: this.operatorId } });
                        // Émettre shift-data-changed pour mettre à jour sticky-bar immédiatement
                        this.emitShiftDataChanged();
                    });
                }
            });
            
            // Observer les changements pour la génération automatique
            this.$watch('operatorId', () => {
                this.tryGenerateShiftId();
                this.emitShiftDataChanged();
            });
            this.$watch('date', () => {
                this.tryGenerateShiftId();
                this.emitShiftDataChanged();
            });
            this.$watch('vacation', () => {
                this.tryGenerateShiftId();
                this.emitShiftDataChanged();
            });
            
            // Observer les changements d'heures pour mettre à jour les KPI
            this.$watch('startTime', () => {
                this.emitShiftDataChanged();
            });
            this.$watch('endTime', () => {
                this.emitShiftDataChanged();
            });
            
            // Observer les changements de longueurs pour mettre à jour les KPI
            this.$watch('lengthStart', () => {
                this.emitShiftDataChanged();
            });
            this.$watch('lengthEnd', () => {
                this.emitShiftDataChanged();
            });
            
            // Observer pour la sauvegarde avec debounce - on doit sauver tout l'objet shift
            this.$watch(() => ({
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
                comments: this.comments,
                // Champs formation
                isTraining: this.isTraining,
                traineeId: this.traineeId
            }), () => {
                this.saveShiftData();
            }, { deep: true });
            
            // Watchers optimisés pour la logique métier
            this.watchOptimized('machineStartedStart', (newValue) => {
                if (!newValue) {
                    this.lengthStart = '';
                }
            }, { debounce: 0 }); // Pas de debounce pour la logique immédiate
            
            this.watchOptimized('machineStartedEnd', (newValue) => {
                if (!newValue) {
                    this.lengthEnd = '';
                }
            }, { debounce: 0 });
            
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
            
            // Écouter quand profile-selector est prêt pour émettre les données
            window.addEventListener('profile-selector-ready', () => {
                this.emitShiftDataChanged();
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
            
            // Écouter la mise à jour de la liste des opérateurs
            window.addEventListener('operators-updated', (event) => {
                const data = event.detail;
                if (data.operators) {
                    // Mettre à jour la liste locale des opérateurs
                    this.operators = data.operators;
                    debug('Operators list updated:', this.operators);
                }
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
                this.saveShiftData();
                return;
            }
            
            const [_, prenom, nom] = match;
            
            this.shiftId = `${dateStr}_${prenom}${nom || ''}_${this.vacation}`;
            debug('Shift ID generated:', this.shiftId);
            
            // Vérifier si l'ID existe
            this.checkShiftIdExists();
            
            // Sauvegarder
            this.saveShiftData();
        },
        
        // Sauvegarder dans la session (le debounce est géré par watchOptimized)
        saveShiftData() {
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
                comments: this.comments,
                // Champs formation
                isTraining: this.isTraining,
                traineeId: this.traineeId
            };
            
            // Utiliser la sauvegarde du mixin
            this.saveToSession({ shift: data });
        },
        
        // Handlers pour les changements
        handleOperatorChange(event) {
            const previousOperatorId = this.operatorId;
            this.operatorId = event.target.value;
            if (event.target.classList) {
                event.target.classList.toggle('filled', !!this.operatorId);
            }
            
            // Si on change d'opérateur (pas juste sélection initiale), réinitialiser les longueurs
            if (previousOperatorId && previousOperatorId !== this.operatorId) {
                this.lengthStart = '';
                this.lengthEnd = '';
                this.machineStartedStart = false;
                this.machineStartedEnd = false;
                debug('Opérateur changé - réinitialisation des longueurs');
            }
            
            // Émettre un événement pour notifier le changement d'opérateur
            window.dispatchEvent(new CustomEvent('operator-changed', {
                detail: { operatorId: this.operatorId }
            }));
            
            this.saveShiftData();
        },
        
        handleTrainingToggle() {
            // Si on désactive la formation, nettoyer les champs
            if (!this.isTraining) {
                this.traineeId = '';
            }
            this.saveShiftData();
        },
        
        handleTraineeChange(event) {
            this.traineeId = event.target.value;
            if (event.target.classList) {
                event.target.classList.toggle('filled', !!this.traineeId);
            }
            this.saveShiftData();
            
            // Émettre immédiatement shift-data-changed
            this.emitShiftDataChanged();
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
            const value = event.target.value;
            this.comments = value;
            // Ne sauvegarder que si non vide
            this.saveFieldToSession('shift.comments', value || null);
        },
        
        // Sauvegarder le poste - Afficher la modale de confirmation
        async saveShift() {
            // Validation basique
            if (!this.operatorId || !this.date || !this.vacation) {
                showNotification('error', 'Renseigner les champs Opérateur, Date & Vacation');
                return;
            }
            
            // Préparer les données pour la modale
            const confirmData = this.prepareShiftDataForConfirmation();
            
            // Construire la configuration de la modale
            const modalConfig = window.modalBuilders.buildShiftConfirmation(confirmData);
            
            // Ajouter l'action de confirmation
            modalConfig.confirmAction = async () => {
                await this.performShiftSave();
            };
            
            // Afficher la modale
            const modal = Alpine.$data(document.querySelector('[x-data="confirmModal()"]'));
            modal.show(modalConfig);
        },
        
        // Préparer les données pour l'affichage dans la modale
        prepareShiftDataForConfirmation() {
            const operator = this.operators.find(op => op.employee_id === this.operatorId);
            
            // Compter les temps perdus
            const lostTimeCount = window.sessionData?.lost_time_entries?.length || 0;
            
            return {
                operatorName: operator?.display_name || 'Non défini',
                shiftId: this.shiftId,
                date: this.date,
                vacation: this.vacation,
                startTime: this.startTime,
                endTime: this.endTime,
                machineStartedStart: this.machineStartedStart,
                lengthStart: this.lengthStart,
                machineStartedEnd: this.machineStartedEnd,
                lengthEnd: this.lengthEnd,
                lostTimeCount: lostTimeCount,
                comments: this.comments,
                hasIncompleteRolls: false // TODO: Vérifier si des rouleaux sont en cours
            };
        },
        
        // Effectuer la sauvegarde réelle
        async performShiftSave() {
            // Trouver l'opérateur dans la liste pour récupérer son ID Django
            let operatorId = null;
            if (this.operatorId) {
                const operator = this.operators.find(op => op.employee_id === this.operatorId);
                if (!operator || !operator.id) {
                    showNotification('error', 'Opérateur non trouvé');
                    return;
                }
                operatorId = operator.id;
            }
            
            // Préparer l'ID numérique du trainee si formation activée
            let traineeNumericId = null;
            if (this.isTraining && this.traineeId) {
                const trainee = this.operators.find(op => op.employee_id === this.traineeId);
                if (trainee && trainee.id) {
                    traineeNumericId = trainee.id;
                }
            }

            const data = {
                shift_id: this.shiftId,
                operator: operatorId, // Le backend attend un ID numérique
                date: this.date,
                vacation: this.vacation,
                start_time: this.startTime,
                end_time: this.endTime,
                started_at_beginning: this.machineStartedStart,
                meter_reading_start: this.lengthStart ? parseFloat(this.lengthStart) : null,
                started_at_end: this.machineStartedEnd,
                meter_reading_end: this.lengthEnd ? parseFloat(this.lengthEnd) : null,
                operator_comments: this.comments || '',
                // Champs formation
                is_training_shift: this.isTraining,
                trainee: traineeNumericId
            };
            
            // Ajouter les données de signature checklist depuis la session
            const sessionData = window.sessionData || {};
            const checklistSignature = sessionData.checklist_signature;
            const checklistSignatureTime = sessionData.checklist_signature_time;
            
            if (checklistSignature) {
                data.checklist_signed = checklistSignature;
            }
            if (checklistSignatureTime) {
                data.checklist_signed_time = checklistSignatureTime;
            }
            
            if (window.DEBUG) {
                debug('Données envoyées pour sauvegarde:', data);
                debug('Session actuelle:', window.sessionData);
                debug('Temps perdus dans la session:', window.sessionData?.lost_time_entries);
            }
            
            try {
                const response = await fetch('/production/api/shifts/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                    },
                    body: JSON.stringify(data)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('Erreur API:', errorData);
                    
                    // Afficher les erreurs de validation spécifiques
                    if (errorData.error) {
                        showNotification('error', errorData.error);
                    } else {
                        // Formater les erreurs de champs
                        const errors = Object.entries(errorData)
                            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
                            .join('\n');
                        showNotification('error', `Erreur de validation:\n${errors}`);
                    }
                    return;
                }
                
                const result = await response.json();
                debug('Réponse sauvegarde:', result);
                
                // Vérifier qu'on a bien un ID de shift créé
                if (!result.id || !result.shift_id) {
                    throw new Error('Réponse invalide du serveur');
                }
                
                showNotification('success', `Poste ${result.shift_id} sauvegardé avec succès`);
                
                // Émettre un événement avec les détails complets
                window.dispatchEvent(new CustomEvent('shift-saved', { 
                    detail: { 
                        shift: result,
                        nextShiftData: result.next_shift_data || null
                    }
                }));
                
                // Si on a des données pour le prochain poste, les appliquer SEULEMENT si tout est OK
                if (result.next_shift_data) {
                    try {
                        this.applyNextShiftData(result.next_shift_data);
                    } catch (resetError) {
                        console.error('Erreur lors de la réinitialisation:', resetError);
                        showNotification('warning', 'Poste sauvegardé mais erreur lors de la réinitialisation');
                    }
                }
                
            } catch (error) {
                console.error('Erreur sauvegarde poste:', error);
                showNotification('error', 'Erreur lors de la sauvegarde du poste');
            }
        },
        
        // Appliquer les données du prochain poste après sauvegarde
        applyNextShiftData(nextShiftData) {
            debug('Application des données du prochain poste:', nextShiftData);
            
            // IMPORTANT: Nettoyer SEULEMENT shiftOperator qui pose problème
            window.session?.patch({
                shiftOperator: '',
                selectedOperatorName: ''
            });
            
            // Réinitialiser le formulaire avec les nouvelles données
            this.operatorId = '';
            this.date = nextShiftData.shift_date || '';
            this.vacation = nextShiftData.vacation || 'Matin';
            this.startTime = nextShiftData.start_time || '';
            this.endTime = nextShiftData.end_time || '';
            this.machineStartedStart = nextShiftData.machine_started_start || false;
            this.lengthStart = nextShiftData.length_start || '';
            this.machineStartedEnd = nextShiftData.machine_started_end || true;
            this.lengthEnd = '';
            this.comments = '';
            this.shiftId = ''; // IMPORTANT: réinitialiser le shiftId aussi !
            
            // Réinitialiser les états de validation
            this.shiftIdExists = null;
            this.checkingShiftId = false;
            this.hasStartupDowntime = false;
            
            // Mettre à jour visuellement les champs
            this.$nextTick(() => {
                // Mettre à jour les classes CSS des champs remplis
                const fieldsToUpdate = {
                    'date': this.date,
                    'vacation': this.vacation,
                    'startTime': this.startTime,
                    'endTime': this.endTime,
                    'lengthStart': this.lengthStart
                };
                
                Object.entries(fieldsToUpdate).forEach(([model, value]) => {
                    const input = this.$el.querySelector(`[x-model="${model}"]`);
                    if (input) {
                        input.classList.toggle('filled', !!value);
                    }
                });
                
                // Focus sur le champ opérateur
                const operatorSelect = this.$el.querySelector('[x-model="operatorId"]');
                if (operatorSelect) {
                    operatorSelect.focus();
                }
            });
            
            // Émettre un événement pour notifier les autres composants
            window.dispatchEvent(new CustomEvent('shift-reset', { 
                detail: { nextShiftData }
            }));
            
            // Ne pas sauvegarder ici - le backend a déjà tout sauvegardé dans v3_production.shift
            // Les données sont persistées via saveToSession dans handleFieldChange
            
            showNotification('info', 'Formulaire réinitialisé pour le prochain poste');
        },
        
        // Émettre un événement quand les données du shift changent
        emitShiftDataChanged() {
            window.dispatchEvent(new CustomEvent('shift-data-changed', {
                detail: {
                    operatorId: this.operatorId,
                    date: this.date,
                    vacation: this.vacation,
                    shiftId: this.shiftId,
                    startTime: this.startTime,
                    endTime: this.endTime,
                    lengthStart: this.lengthStart,
                    lengthEnd: this.lengthEnd,
                    isComplete: this.canGenerateId()
                }
            }));
        },
        
        // Récupérer la longueur du dernier poste
        async fetchLastShiftLength() {
            try {
                // Récupérer la longueur
                const response = await fetch('/production/api/shifts/last/');
                const data = await response.json();
                debug('Données du dernier poste:', data);
                if (data && data.wound_length_end !== null && data.wound_length_end !== undefined) {
                    // On a une valeur, on la met dans le champ
                    this.lengthStart = data.wound_length_end.toString();
                    
                    // On ne coche la case QUE si la valeur est > 0
                    if (data.wound_length_end > 0) {
                        this.machineStartedStart = true;
                        showNotification('success', `Longueur récupérée : ${data.wound_length_end} m`);
                    } else {
                        // Valeur à 0, on ne coche PAS la case
                        this.machineStartedStart = false;
                        showNotification('info', 'Longueur à 0 - Machine arrêtée');
                    }
                    
                    // Forcer la sauvegarde en session et l'émission de l'événement
                    this.saveShiftData();
                    this.emitShiftDataChanged();
                    
                    // Mettre à jour visuellement
                    this.$nextTick(() => {
                        const input = this.$el.querySelector('input[x-model="lengthStart"]');
                        if (input) input.classList.add('filled');
                    });
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
        },
        
        // Afficher la modale de création d'opérateur
        showCreateOperatorModal() {
            const modalElement = document.querySelector('#createOperatorModal');
            if (modalElement && modalElement._x_dataStack) {
                const modalComponent = modalElement._x_dataStack[0];
                modalComponent.show();
            }
        }
    };
}

// Export global pour Alpine
window.shiftForm = shiftForm;