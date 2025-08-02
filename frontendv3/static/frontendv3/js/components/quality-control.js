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
        
        // Session
        saveTimeout: null,
        
        init() {
            // Charger depuis la session
            this.loadFromSession();
            
            // Watchers pour calcul automatique des moyennes
            this.$watch('micromaireG', () => {
                this.moyenneMicromaireG = this.calculateAverage(this.micromaireG);
                this.checkQCStatus();
                this.autoSave();
            });
            
            this.$watch('micromaireD', () => {
                this.moyenneMicromaireD = this.calculateAverage(this.micromaireD);
                this.checkQCStatus();
                this.autoSave();
            });
            
            // Watchers pour masse surfacique
            this.$watch('masseSurfaciqueGG', () => {
                this.moyenneMasseSurfaciqueG = this.calculateAverageMasse('G');
                this.autoSave();
            });
            this.$watch('masseSurfaciqueGC', () => {
                this.moyenneMasseSurfaciqueG = this.calculateAverageMasse('G');
                this.autoSave();
            });
            this.$watch('masseSurfaciqueDC', () => {
                this.moyenneMasseSurfaciqueD = this.calculateAverageMasse('D');
                this.autoSave();
            });
            this.$watch('masseSurfaciqueDD', () => {
                this.moyenneMasseSurfaciqueD = this.calculateAverageMasse('D');
                this.autoSave();
            });
            
            // Watchers pour extrait sec et LOI
            this.$watch('extraitSec', () => this.autoSave());
            this.$watch('extraitTime', () => this.autoSave());
            this.$watch('loi', () => this.autoSave());
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
            // Compter les champs remplis
            const micromaireGFilled = this.micromaireG.filter(v => v).length;
            const micromaireDFilled = this.micromaireD.filter(v => v).length;
            
            // Si au moins une mesure de chaque côté
            if (micromaireGFilled > 0 && micromaireDFilled > 0) {
                this.qcStatus = 'ok';
                // TODO: Vérifier les limites de spécification pour déterminer ok/nok
            } else if (micromaireGFilled + micromaireDFilled > 0) {
                this.qcStatus = 'pending';
            } else {
                this.qcStatus = 'pending';
            }
            
            // Émettre l'événement
            this.$dispatch('qc-status-changed', { status: this.qcStatus });
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