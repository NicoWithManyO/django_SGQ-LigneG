/**
 * Composant Alpine.js pour le contrôle qualité (QC)
 * Gère les mesures de micromaire et masse surfacique
 */
window.qualityControl = function() {
    return {
        // État du contrôle qualité
        qcStatus: 'pending', // pending, ok, nok
        
        // Mesures Micromaire
        micromaireG: ['', '', ''], // 3 valeurs
        micromaireD: ['', '', ''], // 3 valeurs
        
        // Masse Surfacique
        masseSurfaciqueGG: '',
        masseSurfaciqueGC: '',
        masseSurfaciqueDC: '',
        masseSurfaciqueDD: '',
        
        // Extrait Sec et LOI
        extraitSec: '',
        extraitTime: '--:--',
        loi: false,
        loiTime: '--:--',
        
        // Moyennes calculées
        moyenneMicromaireG: '--',
        moyenneMicromaireD: '--',
        moyenneMasseSurfaciqueG: '--',
        moyenneMasseSurfaciqueD: '--',
        
        // Moyennes globales pour affichage header
        moyenneGlobaleMicromaire: '--',
        moyenneGlobaleMasseSurf: '--',
        
        // Session
        saveTimeout: null,
        
        // Specs du profil
        profileSpecs: null,
        qcBadgeStatus: 'pending', // pending, passed, nok
        
        // Unités
        micromaireUnit: 'mlAir/min',
        masseSurfUnit: 'g/25cm²',
        extraitSecUnit: '%',
        
        // Vérifier si une valeur individuelle est NOK
        isValueNOK(value, type, position = null) {
            if (!value || !this.profileSpecs) return false;
            
            const val = parseFloat(value);
            if (isNaN(val)) return false;
            
            let spec = null;
            if (type === 'micromaire') {
                spec = this.profileSpecs.find(s => s.name === 'Micronaire');
            } else if (type === 'masse_surfacique') {
                spec = this.profileSpecs.find(s => s.name === 'Masse Surfacique');
            } else if (type === 'extrait_sec') {
                spec = this.profileSpecs.find(s => s.name === 'Extrait Sec');
            }
            
            if (!spec) return false;
            
            return val < spec.value_min || val > spec.value_max;
        },
        
        init() {
            // Charger depuis la session
            this.loadFromSession();
            
            // Écouter les changements de profil
            window.addEventListener('profile-changed', (event) => {
                if (event.detail && event.detail.profileSpecs) {
                    this.profileSpecs = event.detail.profileSpecs;
                    // Mettre à jour les unités depuis les specs
                    const specMicromaire = this.profileSpecs.find(s => s.name === 'micromaire_g' || s.name === 'micromaire' || s.name === 'Micronaire');
                    const specMasseSurf = this.profileSpecs.find(s => s.name === 'masse_surfacique' || s.name === 'Masse Surfacique');
                    const specExtraitSec = this.profileSpecs.find(s => s.name === 'extrait_sec' || s.name === 'Extrait Sec');
                    
                    if (specMicromaire && specMicromaire.unit) this.micromaireUnit = specMicromaire.unit;
                    if (specMasseSurf && specMasseSurf.unit) this.masseSurfUnit = specMasseSurf.unit;
                    if (specExtraitSec && specExtraitSec.unit) this.extraitSecUnit = specExtraitSec.unit;
                    
                    this.checkQCStatus(); // Recalculer avec les nouvelles specs
                    this.updateGlobalAverages(); // Mettre à jour les moyennes avec les nouvelles unités
                }
            });
            
            // Vérifier le statut initial
            this.checkQCStatus();
            this.updateGlobalAverages();
            
            // Watchers pour calcul automatique des moyennes
            this.$watch('micromaireG', () => {
                this.moyenneMicromaireG = this.calculateAverage(this.micromaireG);
                this.updateGlobalAverages();
                this.checkQCStatus();
                this.autoSave();
            });
            
            this.$watch('micromaireD', () => {
                this.moyenneMicromaireD = this.calculateAverage(this.micromaireD);
                this.updateGlobalAverages();
                this.checkQCStatus();
                this.autoSave();
            });
            
            // Watchers pour masse surfacique
            this.$watch('masseSurfaciqueGG', () => {
                this.moyenneMasseSurfaciqueG = this.calculateAverageMasse('G');
                this.updateGlobalAverages();
                this.checkQCStatus();
                this.autoSave();
            });
            this.$watch('masseSurfaciqueGC', () => {
                this.moyenneMasseSurfaciqueG = this.calculateAverageMasse('G');
                this.updateGlobalAverages();
                this.checkQCStatus();
                this.autoSave();
            });
            this.$watch('masseSurfaciqueDC', () => {
                this.moyenneMasseSurfaciqueD = this.calculateAverageMasse('D');
                this.updateGlobalAverages();
                this.checkQCStatus();
                this.autoSave();
            });
            this.$watch('masseSurfaciqueDD', () => {
                this.moyenneMasseSurfaciqueD = this.calculateAverageMasse('D');
                this.updateGlobalAverages();
                this.checkQCStatus();
                this.autoSave();
            });
            
            // Watchers pour extrait sec et LOI
            this.$watch('extraitSec', () => {
                this.updateGlobalAverages();
                this.checkQCStatus();
                this.autoSave();
            });
            this.$watch('extraitTime', () => this.autoSave());
            this.$watch('loi', () => {
                this.checkQCStatus();
                this.autoSave();
            });
            this.$watch('loiTime', () => this.autoSave());
            
            // Écouter les changements de rouleau
            window.addEventListener('new-roll', () => {
                this.resetQC();
            });
        },
        
        // Chargement depuis la session
        loadFromSession() {
            // Charger depuis sessionData
            if (window.sessionData) {
                if (window.sessionData.qc_micromaire_g) this.micromaireG = window.sessionData.qc_micromaire_g;
                if (window.sessionData.qc_micromaire_d) this.micromaireD = window.sessionData.qc_micromaire_d;
                if (window.sessionData.qc_masse_surfacique_gg) this.masseSurfaciqueGG = window.sessionData.qc_masse_surfacique_gg;
                if (window.sessionData.qc_masse_surfacique_gc) this.masseSurfaciqueGC = window.sessionData.qc_masse_surfacique_gc;
                if (window.sessionData.qc_masse_surfacique_dc) this.masseSurfaciqueDC = window.sessionData.qc_masse_surfacique_dc;
                if (window.sessionData.qc_masse_surfacique_dd) this.masseSurfaciqueDD = window.sessionData.qc_masse_surfacique_dd;
                if (window.sessionData.qc_extrait_sec) this.extraitSec = window.sessionData.qc_extrait_sec;
                if (window.sessionData.qc_extrait_time) this.extraitTime = window.sessionData.qc_extrait_time;
                if (window.sessionData.qc_loi !== undefined) this.loi = window.sessionData.qc_loi;
                if (window.sessionData.qc_loi_time) this.loiTime = window.sessionData.qc_loi_time;
                if (window.sessionData.qc_status) this.qcStatus = window.sessionData.qc_status;
                
                // Recalculer les moyennes
                this.moyenneMicromaireG = this.calculateAverage(this.micromaireG);
                this.moyenneMicromaireD = this.calculateAverage(this.micromaireD);
                this.moyenneMasseSurfaciqueG = this.calculateAverageMasse('G');
                this.moyenneMasseSurfaciqueD = this.calculateAverageMasse('D');
            }
        },
        
        // Sauvegarde automatique
        autoSave() {
            // Sauvegarder chaque champ individuellement
            window.session.save('qc_micromaire_g', this.micromaireG);
            window.session.save('qc_micromaire_d', this.micromaireD);
            window.session.save('qc_masse_surfacique_gg', this.masseSurfaciqueGG);
            window.session.save('qc_masse_surfacique_gc', this.masseSurfaciqueGC);
            window.session.save('qc_masse_surfacique_dc', this.masseSurfaciqueDC);
            window.session.save('qc_masse_surfacique_dd', this.masseSurfaciqueDD);
            window.session.save('qc_extrait_sec', this.extraitSec);
            window.session.save('qc_extrait_time', this.extraitTime);
            window.session.save('qc_loi', this.loi);
            window.session.save('qc_loi_time', this.loiTime);
            window.session.save('qc_status', this.qcStatus);
        },
        
        // Calcul de moyenne
        calculateAverage(values) {
            const nums = values.filter(v => v && !isNaN(parseFloat(v))).map(v => parseFloat(v));
            if (nums.length === 0) return '--';
            const avg = nums.reduce((a, b) => a + b, 0) / nums.length;
            return avg.toFixed(2);
        },
        
        // Calcul moyenne masse surfacique
        calculateAverageMasse(side) {
            let values = [];
            if (side === 'G') {
                if (this.masseSurfaciqueGG) values.push(parseFloat(this.masseSurfaciqueGG));
                if (this.masseSurfaciqueGC) values.push(parseFloat(this.masseSurfaciqueGC));
            } else {
                if (this.masseSurfaciqueDC) values.push(parseFloat(this.masseSurfaciqueDC));
                if (this.masseSurfaciqueDD) values.push(parseFloat(this.masseSurfaciqueDD));
            }
            
            if (values.length === 0) return '--';
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            return avg.toFixed(4);
        },
        
        
        // Vérification du statut QC
        checkQCStatus() {
            // Si pas de specs, on reste en pending
            if (!this.profileSpecs) {
                this.qcBadgeStatus = 'pending';
                window.dispatchEvent(new CustomEvent('qc-badge-changed', { 
                    detail: { status: this.qcBadgeStatus }
                }));
                return;
            }
            
            // Compter les mesures remplies
            const micromaireGFilled = this.micromaireG.filter(v => v).length;
            const micromaireDFilled = this.micromaireD.filter(v => v).length;
            const masseSurfFilled = [
                this.masseSurfaciqueGG,
                this.masseSurfaciqueGC,
                this.masseSurfaciqueDC,
                this.masseSurfaciqueDD
            ].filter(v => v).length;
            
            // Si aucune mesure, on est en pending
            if (micromaireGFilled === 0 && micromaireDFilled === 0 && masseSurfFilled === 0) {
                this.qcBadgeStatus = 'pending';
                window.dispatchEvent(new CustomEvent('qc-badge-changed', { 
                    detail: { status: this.qcBadgeStatus }
                }));
                return;
            }
            
            // Vérifier les moyennes contre les specs
            let hasFailure = false;
            let allComplete = true;
            
            // Récupérer la spec Micronaire (une seule pour G et D)
            const specMicromaire = this.profileSpecs.find(s => s.name === 'Micronaire');
            const specMasseSurf = this.profileSpecs.find(s => s.name === 'Masse Surfacique');
            const specExtraitSec = this.profileSpecs.find(s => s.name === 'Extrait Sec');
            
            // Vérifier Micromaire G
            if (micromaireGFilled >= 3) {
                const avgG = parseFloat(this.moyenneMicromaireG);
                if (specMicromaire && !isNaN(avgG)) {
                    if (avgG < specMicromaire.value_min || avgG > specMicromaire.value_max) {
                        hasFailure = true;
                    }
                }
            } else {
                allComplete = false;
            }
            
            // Vérifier Micromaire D
            if (micromaireDFilled >= 3) {
                const avgD = parseFloat(this.moyenneMicromaireD);
                if (specMicromaire && !isNaN(avgD)) {
                    if (avgD < specMicromaire.value_min || avgD > specMicromaire.value_max) {
                        hasFailure = true;
                    }
                }
            } else {
                allComplete = false;
            }
            
            // Vérifier Masse Surfacique
            if (masseSurfFilled === 4) {
                const avgG = parseFloat(this.moyenneMasseSurfaciqueG);
                const avgD = parseFloat(this.moyenneMasseSurfaciqueD);
                if (specMasseSurf) {
                    if (!isNaN(avgG) && (avgG < specMasseSurf.value_min || avgG > specMasseSurf.value_max)) {
                        hasFailure = true;
                    }
                    if (!isNaN(avgD) && (avgD < specMasseSurf.value_min || avgD > specMasseSurf.value_max)) {
                        hasFailure = true;
                    }
                }
            } else {
                allComplete = false;
            }
            
            // Vérifier Extrait Sec
            if (this.extraitSec) {
                const val = parseFloat(this.extraitSec);
                if (specExtraitSec && !isNaN(val)) {
                    if (val < specExtraitSec.value_min || val > specExtraitSec.value_max) {
                        hasFailure = true;
                    }
                }
            } else {
                allComplete = false;
            }
            
            // Vérifier LOI
            if (!this.loi) {
                allComplete = false;
            }
            
            // Déterminer le statut final
            if (hasFailure) {
                this.qcBadgeStatus = 'nok';
            } else if (allComplete) {
                this.qcBadgeStatus = 'passed';
            } else {
                this.qcBadgeStatus = 'pending';
            }
            
            // Maintenir l'ancien qcStatus pour compatibilité
            this.qcStatus = hasFailure ? 'nok' : (allComplete ? 'ok' : 'pending');
            
            // Émettre les événements
            this.$dispatch('qc-status-changed', { status: this.qcStatus });
            window.dispatchEvent(new CustomEvent('qc-badge-changed', { 
                detail: { status: this.qcBadgeStatus }
            }));
        },
        
        // Mettre à jour les moyennes globales
        updateGlobalAverages() {
            // Calculer moyenne globale micromaire
            if (this.moyenneMicromaireG !== '--' && this.moyenneMicromaireD !== '--') {
                const avgG = parseFloat(this.moyenneMicromaireG);
                const avgD = parseFloat(this.moyenneMicromaireD);
                if (!isNaN(avgG) && !isNaN(avgD)) {
                    this.moyenneGlobaleMicromaire = ((avgG + avgD) / 2).toFixed(2);
                } else {
                    this.moyenneGlobaleMicromaire = '--';
                }
            } else {
                this.moyenneGlobaleMicromaire = '--';
            }
            
            // Calculer moyenne globale masse surfacique
            if (this.moyenneMasseSurfaciqueG !== '--' && this.moyenneMasseSurfaciqueD !== '--') {
                const avgG = parseFloat(this.moyenneMasseSurfaciqueG);
                const avgD = parseFloat(this.moyenneMasseSurfaciqueD);
                if (!isNaN(avgG) && !isNaN(avgD)) {
                    this.moyenneGlobaleMasseSurf = ((avgG + avgD) / 2).toFixed(4);
                } else {
                    this.moyenneGlobaleMasseSurf = '--';
                }
            } else {
                this.moyenneGlobaleMasseSurf = '--';
            }
            
            // Émettre l'événement avec les moyennes et unités
            window.dispatchEvent(new CustomEvent('qc-averages-changed', { 
                detail: { 
                    micromaire: this.moyenneGlobaleMicromaire,
                    micromaireUnit: this.micromaireUnit,
                    masseSurf: this.moyenneGlobaleMasseSurf,
                    masseSurfUnit: this.masseSurfUnit,
                    extraitSec: this.extraitSec || '--',
                    extraitSecUnit: this.extraitSecUnit
                }
            }));
        },
        
        // Validation numérique
        handleNumericInput(event, index = null, field = null) {
            const value = event.target.value;
            const numericValue = value.replace(/[^0-9.,]/g, '').replace(',', '.');
            
            if (index !== null && field) {
                // Pour les arrays (micromaire)
                this[field][index] = numericValue;
            } else {
                event.target.value = numericValue;
            }
        },
        
        // Reset du QC
        resetQC() {
            this.micromaireG = ['', '', ''];
            this.micromaireD = ['', '', ''];
            this.masseSurfaciqueGG = '';
            this.masseSurfaciqueGC = '';
            this.masseSurfaciqueDC = '';
            this.masseSurfaciqueDD = '';
            this.extraitSec = '';
            this.extraitTime = '--:--';
            this.loi = false;
            this.loiTime = '--:--';
            this.qcStatus = 'pending';
            this.qcBadgeStatus = 'pending';
            this.moyenneMicromaireG = '--';
            this.moyenneMicromaireD = '--';
            this.moyenneMasseSurfaciqueG = '--';
            this.moyenneMasseSurfaciqueD = '--';
        },
        
        // Obtenir les données pour sauvegarde
        getQCData() {
            return {
                micromaire_g: this.micromaireG.filter(v => v),
                micromaire_d: this.micromaireD.filter(v => v),
                masse_surfacique_gg: this.masseSurfaciqueGG ? parseFloat(this.masseSurfaciqueGG) : null,
                masse_surfacique_gc: this.masseSurfaciqueGC ? parseFloat(this.masseSurfaciqueGC) : null,
                masse_surfacique_dc: this.masseSurfaciqueDC ? parseFloat(this.masseSurfaciqueDC) : null,
                masse_surfacique_dd: this.masseSurfaciqueDD ? parseFloat(this.masseSurfaciqueDD) : null,
                extrait_sec: this.extraitSec ? parseFloat(this.extraitSec) : null,
                loi: this.loi,
                status: this.qcStatus
            };
        }
    };
};