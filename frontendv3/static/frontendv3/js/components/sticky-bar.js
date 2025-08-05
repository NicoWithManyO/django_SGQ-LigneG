/**
 * Composant Alpine.js : Barre Sticky
 * Affiche les informations en temps réel et actions globales
 */

function stickyBar() {
    return {
        // État local
        currentDateTime: '',
        rollId: '',
        ofStatus: '',
        rollNumber: '',
        ofNumber: '',
        shiftId: '',
        rollSaved: false,
        shiftSaved: false,
        rollStatus: '', // '', 'ok', 'nok'
        rollIdExists: null, // null, true, false
        checkingRollId: false,
        
        // Données du rouleau
        tubeMass: '',
        length: '',
        totalMass: '',
        netMass: '',
        grammage: '',
        nextTubeMass: '',
        
        // Specs du profil et statut grammage
        profileSpecs: null,
        grammageStatus: '', // '', 'ok', 'alert', 'nok'
        
        // Statut QC temps réel
        currentQcStatus: '',
        
        // Timer pour l'horloge
        clockTimer: null,
        
        // État pour le bouton de sauvegarde
        rollConformityStatus: 'CONFORME',
        allThicknessesFilled: false,
        operatorId: '',
        shiftDate: '',
        vacation: '',
        
        // Initialisation
        init() {
            debug('Sticky bar initialized');
            
            // Enregistrer dans le registry
            window.componentRegistry.initComponent(this, 'stickyBar');
            
            // Démarrer l'horloge
            this.updateClock();
            this.clockTimer = setInterval(() => this.updateClock(), window.stickyBarConfig.clock.updateInterval);
            
            // Charger les données initiales depuis la session
            this.loadFromSession();
            
            // Écouter les changements globaux
            this.listenToGlobalEvents();
            
            // Calculer les valeurs initiales et émettre les événements
            // Attendre un peu pour que roll-grid soit initialisé
            setTimeout(() => {
                this.calculateValues();
                // Forcer le recalcul et l'émission du statut initial du grammage
                this.checkGrammageStatus();
                debug(`Initial grammage status: "${this.grammageStatus}", grammage: "${this.grammage}"`);
                
                // Émettre même si le statut est vide pour initialiser roll-grid
                window.eventBus.emit(window.eventBus.EVENTS.GRAMMAGE_STATUS_CHANGED, {
                    status: this.grammageStatus, 
                    value: this.grammage !== '--' ? parseFloat(this.grammage) : null,
                    grammage: this.grammage
                });
                
                // Forcer aussi un $nextTick pour s'assurer que Alpine met à jour le DOM
                this.$nextTick(() => {
                    debug(`DOM should be updated with grammage color. Status: ${this.grammageStatus}`);
                });
            }, 200); // Augmenter le délai pour être sûr
            
            // Watchers pour auto-save dans la session SEULEMENT (pas de recalcul)
            this.$watch('tubeMass', () => {
                window.session.save('sticky_tube_mass', this.tubeMass);
                // PAS de calculateValues() ici - seulement au blur
            });
            this.$watch('length', () => {
                window.session.save('sticky_length', this.length);
                // PAS de calculateValues() ici - seulement au blur
            });
            this.$watch('totalMass', () => {
                window.session.save('sticky_total_mass', this.totalMass);
                // PAS de calculateValues() ici - seulement au blur
            });
            this.$watch('nextTubeMass', () => window.session.save('sticky_next_tube_mass', this.nextTubeMass));
            
            // Cleanup se fera automatiquement quand le composant est détruit
        },
        
        // Charger depuis la session
        loadFromSession() {
            const ofData = window.sessionData?.of || {};
            const rollData = window.sessionData?.roll || {};
            const shiftData = window.sessionData?.shift || {};
            
            this.ofNumber = ofData.ofEnCours || '';
            this.rollNumber = window.sessionData?.sticky_roll_number || '';
            this.shiftId = shiftData.shiftId || '';
            
            // Charger les données du shift
            this.operatorId = shiftData.operatorId || '';
            this.shiftDate = shiftData.date || '';
            this.vacation = shiftData.vacation || '';
            
            // Charger les données du rouleau
            this.tubeMass = window.sessionData?.sticky_tube_mass || '';
            this.length = window.sessionData?.sticky_length || '';
            this.totalMass = window.sessionData?.sticky_total_mass || '';
            this.nextTubeMass = window.sessionData?.sticky_next_tube_mass || '';
            
            // Charger le statut QC initial
            this.currentQcStatus = window.sessionData?.qc_status || '';
            
            this.updateRollId();
            this.updateOFStatus();
            this.calculateValues();
            
            // Forcer le calcul initial du grammage et son statut TOUJOURS
            // Même si grammage est '--', on doit vérifier pour appliquer le style blanc par défaut
            this.checkGrammageStatus();
        },
        
        // Mettre à jour l'horloge
        updateClock() {
            const now = new Date();
            this.currentDateTime = now.toLocaleDateString(
                window.stickyBarConfig.clock.locale, 
                window.stickyBarConfig.clock.options
            );
        },
        
        // Écouter les événements globaux
        listenToGlobalEvents() {
            // Écouter les changements d'OF
            window.eventBus.on(window.eventBus.EVENTS.OF_CHANGED, (event) => {
                this.ofNumber = event.detail.ofNumber || '';
                this.updateRollId();
                this.updateOFStatus();
                // Appliquer automatiquement la baguette magique au changement d'OF
                if (this.ofNumber) {
                    this.fetchNextRollNumber();
                }
            });
            
            // Écouter les changements de numéro de rouleau
            window.eventBus.on(window.eventBus.EVENTS.ROLL_NUMBER_CHANGED, (event) => {
                this.rollNumber = event.detail.rollNumber || '';
                this.updateRollId();
            });
            
            // Écouter les changements de shift
            window.eventBus.on(window.eventBus.EVENTS.SHIFT_SAVED, (event) => {
                this.shiftSaved = true;
                this.shiftId = event.detail.shift?.shift_id || '';
                setTimeout(() => { this.shiftSaved = false; }, window.stickyBarConfig.timeouts.saveNotification);
            });
            
            // Écouter les sauvegardes de rouleau
            window.eventBus.on(window.eventBus.EVENTS.ROLL_SAVED, (event) => {
                this.rollSaved = true;
                setTimeout(() => { this.rollSaved = false; }, window.stickyBarConfig.timeouts.saveNotification);
            });
            
            // Écouter les mises à jour de session
            window.eventBus.on(window.eventBus.EVENTS.SESSION_UPDATED, (event) => {
                if (event.detail.key === 'of' || event.detail.key === 'roll' || event.detail.key === 'shift') {
                    this.loadFromSession();
                }
            });
            
            // Écouter les changements de profil pour récupérer les specs
            window.addEventListener('profile-changed', (event) => {
                if (event.detail && event.detail.profileSpecs) {
                    this.profileSpecs = event.detail.profileSpecs;
                    debug('Profile specs received in sticky-bar:', this.profileSpecs);
                    // Revérifier le statut du grammage avec les nouvelles specs
                    this.checkGrammageStatus();
                }
            });
            
            // Écouter les changements de conformité
            window.eventBus.on(window.eventBus.EVENTS.ROLL_CONFORMITY_CHANGED, (event) => {
                debug('Conformity changed:', event.detail);
                
                // Mettre à jour le statut de conformité et l'état des épaisseurs
                this.rollConformityStatus = event.detail.status;
                this.allThicknessesFilled = event.detail.allThicknessesFilled || false;
                
                debug(`Updated sticky-bar: status=${this.rollConformityStatus}, allFilled=${this.allThicknessesFilled}`);
                
                // Mettre à jour l'ID selon le statut
                this.updateRollId();
            });
            
            // Écouter les changements de shift pour récupérer les données
            window.addEventListener('shift-data-changed', (event) => {
                if (event.detail) {
                    this.operatorId = event.detail.operatorId || '';
                    this.shiftDate = event.detail.date || '';
                    this.vacation = event.detail.vacation || '';
                    this.shiftId = event.detail.shiftId || '';
                }
            });
            
            // Écouter les changements de statut QC
            window.eventBus.on(window.eventBus.EVENTS.QC_STATUS_CHANGED, (event) => {
                if (event.detail && event.detail.status !== undefined) {
                    this.currentQcStatus = event.detail.status;
                    debug('QC status updated:', this.currentQcStatus);
                }
            });
        },
        
        // Mettre à jour l'ID rouleau
        updateRollId() {
            const ofDecoupe = window.sessionData?.of?.ofDecoupe || window.stickyBarConfig.rollId.ofDecoupe;
            this.rollId = window.rollCalculations.generateRollId(
                this.ofNumber,
                this.rollNumber,
                this.rollConformityStatus,
                ofDecoupe
            );
            
            if (this.rollId === '--') {
                this.rollIdExists = null;
                return;
            }
            
            this.rollStatus = this.rollConformityStatus === 'NON_CONFORME' ? 'nok' : 'ok';
            this.checkRollIdExists();
        },
        
        // Vérifier si l'ID rouleau existe en base
        async checkRollIdExists() {
            if (!this.rollId) {
                this.rollIdExists = null;
                return;
            }
            
            this.checkingRollId = true;
            try {
                const response = await fetch(`${window.stickyBarConfig.api.checkRollId}?roll_id=${this.rollId}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                this.rollIdExists = data.exists;
            } catch (error) {
                debug('Erreur vérification ID:', error);
                this.rollIdExists = null;
            } finally {
                this.checkingRollId = false;
            }
        },
        
        // Mettre à jour le statut OF
        updateOFStatus() {
            if (this.ofNumber) {
                this.ofStatus = this.ofNumber;
                
                // Ajouter OF découpe si disponible
                const ofDecoupe = window.sessionData?.of?.ofDecoupe;
                if (ofDecoupe) {
                    this.ofStatus += ` → ${ofDecoupe}`;
                }
                
                // Ajouter le profil si disponible
                const profileName = window.sessionData?.profile?.profileName;
                if (profileName) {
                    this.ofStatus += ` (${profileName})`;
                }
            } else {
                this.ofStatus = window.stickyBarConfig.messages.noOf;
            }
        },
        
        // Récupérer le prochain numéro de rouleau disponible
        async fetchNextRollNumber() {
            if (!this.ofNumber) {
                showNotification('warning', window.stickyBarConfig.messages.noOf);
                return;
            }
            
            try {
                const response = await fetch(`${window.stickyBarConfig.api.nextRollNumber}?of=${this.ofNumber}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                this.rollNumber = data.next_number;
                this.handleRollNumberChange();
                
                showNotification('success', window.stickyBarConfig.messages.nextNumber + data.next_number);
            } catch (error) {
                showNotification('error', window.stickyBarConfig.messages.fetchError);
                debug('Fetch next number error:', error);
            }
        },
        
        // Actions
        async saveAll() {
            showNotification('info', window.stickyBarConfig.messages.savingAll);
            
            try {
                const promises = [];
                
                // Sauvegarder le shift si on a un shiftId
                if (this.shiftId) {
                    const shiftComponent = document.querySelector('[x-data*="shiftForm"]')?._x_dataStack?.[0];
                    if (shiftComponent?.saveShift) {
                        promises.push(shiftComponent.saveShift());
                    }
                }
                
                // Sauvegarder le rouleau si on a un rollId
                if (this.rollId) {
                    promises.push(this.saveRoll());
                }
                
                // Attendre toutes les sauvegardes
                await Promise.all(promises);
                
                showNotification('success', window.stickyBarConfig.messages.saveSuccess);
            } catch (error) {
                showNotification('error', window.stickyBarConfig.messages.saveError);
                debug('Save error:', error);
            }
        },
        
        // Sauvegarder le rouleau
        async saveRoll() {
            if (!this.canSaveRoll) {
                showNotification('warning', this.saveButtonTooltip);
                return;
            }
            
            // Utiliser la modal si disponible
            if (window.modalBuilders && window.modalBuilders.buildRollConfirmation) {
                // Préparer les données pour la modal
                const rollData = {
                    rollId: this.rollId,
                    status: this.rollConformityStatus,
                    length: this.length,
                    netWeight: this.netMass,
                    grammage: this.grammage,
                    defectCount: 0
                };
                
                // Compter les défauts
                const defectsData = window.sessionData?.v3_production?.roll?.defects || {};
                let defectCount = 0;
                for (const cellDefects of Object.values(defectsData)) {
                    defectCount += cellDefects.length;
                }
                rollData.defectCount = defectCount;
                
                // Ajouter les données QC si disponibles
                const qcData = window.sessionData?.v3_production || {};
                if (qcData.qc_micromaire_g || qcData.qc_micromaire_d) {
                    const avgLeft = window.rollCalculations.calculateAverage(qcData.qc_micromaire_g || []);
                    const avgRight = window.rollCalculations.calculateAverage(qcData.qc_micromaire_d || []);
                    if (avgLeft) {
                        rollData.qcMicromaire = avgLeft.toFixed(1);
                        rollData.qcMicromaireUnit = 'μm';
                    } else if (avgRight) {
                        rollData.qcMicromaire = avgRight.toFixed(1);
                        rollData.qcMicromaireUnit = 'μm';
                    }
                }
                
                if (qcData.qc_masse_surfacique_gg || qcData.qc_masse_surfacique_gc || 
                    qcData.qc_masse_surfacique_dc || qcData.qc_masse_surfacique_dd) {
                    const avgMasse = window.rollCalculations.calculateAverage([
                        qcData.qc_masse_surfacique_gg,
                        qcData.qc_masse_surfacique_gc,
                        qcData.qc_masse_surfacique_dc,
                        qcData.qc_masse_surfacique_dd
                    ]);
                    if (avgMasse) {
                        rollData.qcMasseSurf = avgMasse.toFixed(1);
                        rollData.qcMasseSurfUnit = 'g/25cm²';
                    }
                }
                
                // Utiliser le statut QC temps réel
                rollData.qcStatus = this.currentQcStatus || '';
                debug('QC Status for modal:', rollData.qcStatus);
                
                // Construire le contenu de la modal
                const modalConfig = window.modalBuilders.buildRollConfirmation(rollData);
                
                // Ajouter l'action de confirmation
                modalConfig.confirmAction = async () => {
                    // Récupérer le commentaire depuis la modal
                    const modalElement = document.querySelector('[x-data*="confirmModal"]');
                    let comment = '';
                    if (modalElement && modalElement._x_dataStack) {
                        const modalComponent = modalElement._x_dataStack[0];
                        comment = modalComponent.modalConfig.commentValue || '';
                    }
                    await this._performSaveRoll(comment);
                };
                
                // Obtenir la référence au composant modal
                const modalElement = document.querySelector('[x-data*="confirmModal"]');
                if (modalElement && modalElement._x_dataStack) {
                    const modalComponent = modalElement._x_dataStack[0];
                    modalComponent.show(modalConfig);
                    return;
                }
            }
            
            // Si pas de modal, sauvegarder directement
            await this._performSaveRoll();
        },
        
        // Fonction interne pour effectuer la sauvegarde
        async _performSaveRoll(comment = '') {
            
            try {
                showNotification('info', window.stickyBarConfig.messages.savingRoll);
                
                // Préparer les données minimales
                const rollData = {
                    shift_id_str: this.shiftId,
                    tube_mass: parseFloat(this.tubeMass) || null,
                    total_mass: parseFloat(this.totalMass) || null,
                    length: parseFloat(this.length) || null,
                    status: this.rollConformityStatus,
                    comment: comment || ''
                };
                
                // Toujours envoyer le roll_id
                rollData.roll_id = this.rollId;
                
                // Pour CONFORME seulement, envoyer le roll_number (entier)
                if (this.rollConformityStatus === 'CONFORME') {
                    rollData.roll_number = parseInt(this.rollNumber);
                }
                // Pour NON_CONFORME, pas de roll_number (le backend gère)
                
                // L'OF sera extrait automatiquement du roll_id par le backend
                
                // Le backend va récupérer les épaisseurs et défauts depuis la session
                
                debug('Données à envoyer:', rollData);
                
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
                const response = await fetch('/production/api/rolls/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(rollData)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    debug('Erreur API:', error);
                    throw new Error(error.error || error.detail || `HTTP ${response.status}`);
                }
                
                const savedRoll = await response.json();
                debug('Réponse du backend:', savedRoll);
                
                // Appliquer l'état renvoyé par le backend
                if (savedRoll.next_roll_data) {
                    // Si on était en mode découpe et qu'on nous renvoie un OF normal
                    if (this.ofNumber === '9999' && savedRoll.next_roll_data.of_number !== '9999') {
                        // Restaurer l'OF original si disponible
                        const originalOF = window.sessionData?.original_of;
                        if (originalOF) {
                            this.ofNumber = originalOF;
                            window.session.remove('original_of');
                            window.session.remove('original_roll_number');
                        }
                    } else {
                        this.ofNumber = savedRoll.next_roll_data.of_number || this.ofNumber;
                    }
                    
                    this.rollNumber = savedRoll.next_roll_data.roll_number;
                    this.tubeMass = savedRoll.next_roll_data.tube_mass || '';
                    this.nextTubeMass = '';
                    this.totalMass = '';
                    // Récupérer la longueur cible depuis la session
                    const targetLength = window.sessionData?.of?.targetLength;
                    this.length = targetLength ? String(targetLength) : '';
                    this.calculateValues();
                    this.handleRollNumberChange();
                    this.updateOFStatus();
                }
                
                showNotification('success', window.stickyBarConfig.messages.rollSaved.replace('{rollId}', savedRoll.roll_id));
                
                // Émettre l'événement de succès
                window.eventBus.emit(window.eventBus.EVENTS.ROLL_SAVED, { 
                    roll: savedRoll
                });
                
                // Informer les autres composants de se réinitialiser
                window.eventBus.emit(window.eventBus.EVENTS.ROLL_RESET);
                
                return savedRoll;
                
            } catch (error) {
                debug('Erreur sauvegarde rouleau:', error);
                showNotification('error', `Erreur: ${error.message}`);
                throw error;
            }
        },
        
        async exportData() {
            showNotification('info', window.stickyBarConfig.messages.exportPending);
            // Export non implémenté pour l'instant
        },
        
        // Vider toutes les données sauf la partie ordre de fabrication
        clearAllExceptOF() {
            // Confirmation avant de vider
            if (!confirm(window.stickyBarConfig.messages.confirmClear)) {
                return;
            }
            
            // Sauvegarder les données OF actuelles
            const currentOF = {
                ofEnCours: window.sessionData?.of?.ofEnCours || '',
                ofDecoupe: window.sessionData?.of?.ofDecoupe || '',
                targetLength: window.sessionData?.of?.targetLength || 0
            };
            
            // Vider toutes les données en les mettant à null/vide
            const emptyData = {
                // Shift
                shift: {
                    operatorId: '',
                    date: new Date().toISOString().split('T')[0],
                    vacation: '',
                    shiftId: '',
                    startTime: '',
                    machineStartedStart: false,
                    lengthStart: '',
                    endTime: '',
                    machineStartedEnd: false,
                    lengthEnd: '',
                    comments: ''
                },
                // Rouleau
                roll: {
                    defects: {},
                    thicknessValues: {},
                    rattrapages: {}
                },
                // QC - NE PAS réinitialiser car on veut garder les données en cours !
                // qc_micromaire_g: ['', '', ''],
                // qc_micromaire_d: ['', '', ''],
                // qc_masse_surfacique_gg: '',
                // qc_masse_surfacique_gc: '',
                // qc_masse_surfacique_dc: '',
                // qc_masse_surfacique_dd: '',
                // qc_extrait_sec: '',
                // qc_extrait_time: '--:--',
                // qc_loi: false,
                // qc_loi_time: '--:--',
                // qc_status: 'pending',
                // Checklist
                checklist: {
                    items: {},
                    responses: {},
                    comments: {},
                    signature: '',
                    signatureTime: ''
                },
                // Temps perdus
                lost_time_entries: [],
                // Sticky bar - utiliser les vraies clés
                sticky_roll_number: '',
                sticky_tube_mass: '',
                sticky_next_tube_mass: '',
                sticky_total_mass: '',
                sticky_length: currentOF.targetLength ? String(currentOF.targetLength) : '', // Garder la longueur liée à l'OF
                // OF - on garde les valeurs actuelles
                of: currentOF
            };
            
            // Envoyer tout d'un coup
            window.session.patch(emptyData);
            
            // Recharger la page après un court délai pour laisser le temps à la sauvegarde
            setTimeout(() => {
                window.location.reload();
            }, window.stickyBarConfig.timeouts.pageReload);
        },
        
        toggleDebug() {
            const currentDebug = localStorage.getItem('debug') === 'true';
            localStorage.setItem('debug', !currentDebug);
            location.reload();
        },
        
        // Gérer le changement du numéro de rouleau
        handleRollNumberChange() {
            // Ne formater que si le champ n'est pas vide
            if (this.rollNumber && this.rollNumber.toString().trim() !== '') {
                // Formater avec padding si c'est un nombre
                if (!isNaN(this.rollNumber)) {
                    this.rollNumber = this.rollNumber.toString().padStart(3, '0');
                }
            }
            
            window.session.save('sticky_roll_number', this.rollNumber);
            this.updateRollId();
            
            // Émettre l'événement
            window.eventBus.emit(window.eventBus.EVENTS.ROLL_NUMBER_CHANGED, {
                rollNumber: this.rollNumber
            });
        },
        
        // Gérer les changements de données
        handleDataChange() {
            window.session.save('sticky_tube_mass', this.tubeMass);
            window.session.save('sticky_length', this.length);
            window.session.save('sticky_total_mass', this.totalMass);
            window.session.save('sticky_next_tube_mass', this.nextTubeMass);
            
            this.calculateValues();
        },
        
        // Gérer le blur des champs (recalcul et émission d'événements)
        handleFieldBlur() {
            this.calculateValues();
        },
        
        // Helper pour remplir automatiquement TOUT
        fillMassFields() {
            // 1. Remplir les épaisseurs avec rollGridUtils
            if (window.rollGridUtils && window.rollGridUtils.fillRandom) {
                window.rollGridUtils.fillRandom();
            }
            
            // 2. Remplir masse tube si vide
            if (!this.tubeMass) {
                // Masse tube autour de 900g avec variation aléatoire ±50g
                const variation = Math.floor(Math.random() * 101) - 50; // -50 à +50
                this.tubeMass = String(900 + variation);
            }
            
            // 3. Calculer la masse totale pour obtenir un grammage d'environ 80 g/m
            if (this.length) {
                const targetGrammage = 80; // g/m
                const len = parseFloat(this.length);
                const tube = parseFloat(this.tubeMass);
                
                if (!isNaN(len) && !isNaN(tube) && len > 0) {
                    // Masse nette = longueur * grammage cible
                    const netMass = len * targetGrammage;
                    // Masse totale = masse tube + masse nette
                    const totalMass = tube + netMass;
                    // Ajouter une petite variation aléatoire (±5%)
                    const variation = 1 + (Math.random() * 0.1 - 0.05);
                    this.totalMass = String(Math.round(totalMass * variation));
                }
            }
            
            // 4. Remplir masse tube suivante
            if (!this.nextTubeMass) {
                const variation = Math.floor(Math.random() * 101) - 50; // -50 à +50
                this.nextTubeMass = String(900 + variation);
            }
            
            // 5. Remplir les contrôles qualité
            window.eventBus.emit(window.eventBus.EVENTS.FILL_QC_RANDOM);
            
            // 6. Remplir la checklist avec signature - attendre un peu pour que les composants soient chargés
            setTimeout(() => {
                const checklistComponent = document.querySelector('[x-data*="checklist"]');
                if (checklistComponent && checklistComponent._x_dataStack && window.testHelpers && window.testHelpers.fillChecklist) {
                    const checklistData = checklistComponent._x_dataStack[0];
                    window.testHelpers.fillChecklist(checklistData);
                }
            }, window.stickyBarConfig.timeouts.checklistFill);
            
            // Sauvegarder et recalculer
            this.handleDataChange();
            
            showNotification('success', '🎩 Baguette magique : Tout est rempli !');
        },
        
        // Helper pour générer une masse tube suivante
        fillNextTubeMass() {
            // Générer une masse tube autour de 900g avec variation aléatoire ±50g
            const variation = Math.floor(Math.random() * 101) - 50; // -50 à +50
            this.nextTubeMass = String(900 + variation);
            
            // Sauvegarder
            window.session.save('sticky_next_tube_mass', this.nextTubeMass);
            
            showNotification('info', `Masse tube suivante : ${this.nextTubeMass}g`);
        },
        
        // Calculer les valeurs dérivées
        calculateValues() {
            // Calculer la masse nette
            const netMass = window.rollCalculations.calculateNetMass(this.totalMass, this.tubeMass);
            this.netMass = netMass !== null ? netMass.toFixed(0) : '--';
            
            // Calculer le grammage
            if (netMass !== null) {
                const grammage = window.rollCalculations.calculateGrammage(netMass, this.length);
                this.grammage = grammage !== null ? grammage.toFixed(1) : '--';
                debug(`Grammage calc: ${netMass}g / ${this.length}m = ${this.grammage} g/m`);
            } else {
                this.grammage = '--';
            }
            
            // FORCER le recalcul du statut immédiatement et directement
            this.checkGrammageStatus();
            
        },
        
        
        // Vérifier le statut du grammage par rapport aux specs
        checkGrammageStatus() {
            debug(`checkGrammageStatus called: grammage="${this.grammage}", specs=`, this.profileSpecs);
            
            // Si pas de grammage calculé ou pas de specs
            if (this.grammage === '--' || !this.profileSpecs) {
                // Si le statut change, émettre l'événement
                if (this.grammageStatus !== '') {
                    this.grammageStatus = '';
                    window.eventBus.emit(window.eventBus.EVENTS.GRAMMAGE_STATUS_CHANGED, {
                        status: '', 
                        value: null,
                        grammage: this.grammage
                    });
                }
                return;
            }
            
            // Chercher la spec "Masse Surfacique Globale"
            const spec = this.profileSpecs.find(s => s.name === 'Masse Surfacique Globale');
            
            if (!spec) {
                this.grammageStatus = '';
                debug('Spec "Masse Surfacique Globale" non trouvée');
                return;
            }
            
            const value = parseFloat(this.grammage);
            const newStatus = window.rollCalculations.checkGrammageStatus(value, spec);
            
            // Si le statut a changé, émettre un événement
            if (this.grammageStatus !== newStatus) {
                this.grammageStatus = newStatus;
                window.eventBus.emit(window.eventBus.EVENTS.GRAMMAGE_STATUS_CHANGED, {
                    status: newStatus, 
                    value: value,
                    grammage: this.grammage
                });
            }
            
            debug('Grammage status:', this.grammageStatus, 'for value:', value);
        },
        
        // Propriétés calculées pour le bouton de sauvegarde
        get hasRequiredShiftData() {
            return this.operatorId && this.shiftDate && this.vacation;
        },
        
        get hasGrammage() {
            return this.grammage !== '--' && this.grammage !== '';
        },
        
        get canSaveRoll() {
            // Toujours besoin des données du poste et du grammage
            if (!this.hasRequiredShiftData || !this.hasGrammage) {
                return false;
            }
            
            // Si conforme, besoin de toutes les épaisseurs
            if (this.rollConformityStatus === 'CONFORME') {
                debug(`Checking canSaveRoll: allThicknessesFilled=${this.allThicknessesFilled}`);
                return this.allThicknessesFilled;
            }
            
            // Si non conforme, on peut sauver même sans toutes les épaisseurs
            return true;
        },
        
        get saveButtonTooltip() {
            // Si le bouton est actif, pas de tooltip
            if (this.canSaveRoll) {
                return '';
            }
            
            // Sinon, lister ce qui manque
            const missing = [];
            
            if (!this.operatorId) missing.push(window.stickyBarConfig.validationMessages.operatorRequired);
            if (!this.shiftDate) missing.push(window.stickyBarConfig.validationMessages.dateRequired);
            if (!this.vacation) missing.push(window.stickyBarConfig.validationMessages.vacationRequired);
            if (!this.hasGrammage) missing.push(window.stickyBarConfig.validationMessages.grammageRequired);
            
            if (this.rollConformityStatus === 'CONFORME' && !this.allThicknessesFilled) {
                debug(`Tooltip check: conformityStatus=${this.rollConformityStatus}, allThicknessesFilled=${this.allThicknessesFilled}`);
                missing.push(window.stickyBarConfig.validationMessages.thicknessRequired);
            }
            
            debug(`SaveButtonTooltip: ${missing.join(' • ')}`);
            return missing.join(' • ');
        }
    };
}

// Export global pour Alpine
window.stickyBar = stickyBar;