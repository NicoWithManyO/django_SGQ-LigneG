/**
 * SyncEngine - Moteur de synchronisation avec le backend
 * 
 * Gère la synchronisation robuste des données avec retry automatique et gestion d'erreurs
 */
class SyncEngine {
    constructor(stateManager, api) {
        this.stateManager = stateManager;
        this.api = api || window.apiV2;
        this.syncQueue = [];
        this.syncing = false;
        this.syncTimeout = null;
        this.lastSyncTime = null;
        
        // Configuration
        this.config = {
            batchSize: 10,
            syncDelay: 300, // Délai avant sync (ms)
            retryConfig: {
                maxRetries: 3,
                baseDelay: 1000,
                maxDelay: 30000,
                backoffMultiplier: 2
            },
            priorities: {
                high: 0,
                normal: 1,
                low: 2
            }
        };
        
        // État de synchronisation
        this.syncState = {
            pending: 0,
            syncing: 0,
            succeeded: 0,
            failed: 0,
            lastError: null
        };
        
        // Mapping des chemins vers les clés API
        this.pathMapping = {
            // Shift mappings
            'shift.operatorId': 'operator_id',
            'shift.date': 'shift_date',
            'shift.vacation': 'vacation',
            'shift.startTime': 'shift_form_start_time',
            'shift.endTime': 'shift_form_end_time',
            'shift.machineStartedStart': 'shift_form_machine_started_start',
            'shift.machineStartedEnd': 'shift_form_machine_started_end',
            'shift.lengthStart': 'shift_form_length_start',
            'shift.lengthEnd': 'shift_form_length_end',
            'shift.comment': 'shift_form_comment',
            'shift.id': 'shift_id',
            
            // OF mappings
            'of.targetLength': 'target_length',
            'of.longueurCible': 'target_length',
            'of.enCours': 'of_en_cours',
            'of.decoupe': 'of_decoupe',
            
            // Roll mappings
            'roll.profileId': 'profile_id',
            'roll.targetLength': 'target_length',
            'roll.totalMass': 'total_mass',
            'roll.tubeMass': 'tube_mass',
            'roll.netMass': 'net_mass',
            'roll.grammage': 'grammage',
            'roll.conformity': 'conformity',
            
            // Production/Roll mappings pour la sticky bar
            'production.currentRollNumber': 'current_roll_number',
            'production.currentRollId': 'current_roll_id',
            'production.currentRoll.tubeMass': 'current_roll_tube_mass',
            'production.currentRoll.length': 'current_roll_length',
            'production.currentRoll.totalMass': 'current_roll_total_mass',
            'production.currentRoll.thicknesses': 'current_roll_thicknesses',
            'production.nextTubeWeight': 'next_tube_weight',
            
            // Quality control mappings
            'qc.status': 'qc_status',
            'qc.completedAt': 'qc_completed_at',
            
            // Checklist mappings
            'checklist.signed': 'checklist_signed',
            'checklist.signatureTime': 'checklist_signature_time',
            
            // Lost time mappings
            'lostTime.hasStartupTime': 'has_startup_time',
            
            // Session counter mappings
            'counters.woundLengthOk': 'wound_length_ok',
            'counters.woundLengthNok': 'wound_length_nok',
            'counters.woundLengthTotal': 'wound_length_total',
            
            // Roll mappings - les mesures et défauts sont stockés comme objets
            'roll.measurements': 'roll_measurements',
            'roll.defects': 'roll_defects',
            'roll.thicknessStats': 'roll_thickness_stats',
            'roll.defectCounts': 'roll_defect_counts',
            'roll.conformity': 'roll_conformity'
        };
        
        // S'abonner aux changements d'état
        this._setupStateSubscriptions();
    }
    
    /**
     * Synchroniser un changement avec le backend
     * @param {string} path - Chemin de la donnée
     * @param {*} value - Valeur à synchroniser
     * @param {string} priority - Priorité ('high', 'normal', 'low')
     * @param {boolean} immediate - Si true, synchronise immédiatement sans délai
     */
    async sync(path, value, priority = 'normal', immediate = false) {
        console.log(`📌 SyncEngine.sync called - path: ${path}, value:`, value, `immediate: ${immediate}`);
        const item = {
            id: this._generateId(),
            path,
            value,
            priority,
            retries: 0,
            timestamp: Date.now(),
            status: 'pending'
        };
        
        // Ajouter à la queue
        this.syncQueue.push(item);
        this._sortQueue();
        
        // Mettre à jour les stats
        this.syncState.pending = this.syncQueue.filter(i => i.status === 'pending').length;
        
        // Démarrer la synchronisation avec un délai ou immédiatement
        if (immediate) {
            this._processSyncQueue();
        } else {
            this._scheduleSyncProcess();
        }
    }
    
    /**
     * Synchroniser immédiatement toutes les données en attente
     */
    async syncNow() {
        if (this.syncTimeout) {
            clearTimeout(this.syncTimeout);
            this.syncTimeout = null;
        }
        
        await this._processSyncQueue();
    }
    
    /**
     * Obtenir l'état de synchronisation
     */
    getSyncState() {
        return {
            ...this.syncState,
            queueLength: this.syncQueue.length,
            isSyncing: this.syncing,
            lastSyncTime: this.lastSyncTime
        };
    }
    
    /**
     * Vider la queue de synchronisation
     */
    clearQueue() {
        this.syncQueue = [];
        this.syncState.pending = 0;
        
        if (this.syncTimeout) {
            clearTimeout(this.syncTimeout);
            this.syncTimeout = null;
        }
    }
    
    /**
     * Réessayer les éléments en échec
     */
    retryFailed() {
        const failedItems = this.syncQueue.filter(item => item.status === 'failed');
        
        failedItems.forEach(item => {
            item.status = 'pending';
            item.retries = 0;
        });
        
        this.syncState.failed = 0;
        this.syncState.pending = failedItems.length;
        
        if (failedItems.length > 0) {
            this._scheduleSyncProcess();
        }
    }
    
    // Méthodes privées
    
    _setupStateSubscriptions() {
        // S'abonner aux changements qui nécessitent une synchronisation
        const pathsToSync = Object.keys(this.pathMapping);
        
        // Ajouter aussi la surveillance des chemins imbriqués pour production.currentRoll
        const nestedPaths = [
            'production.currentRoll.tubeMass',
            'production.currentRoll.length',
            'production.currentRoll.totalMass',
            'production.currentRoll.thicknesses'
        ];
        
        nestedPaths.forEach(path => {
            if (!pathsToSync.includes(path)) {
                pathsToSync.push(path);
            }
        });
        
        pathsToSync.forEach(path => {
            // Pour les mesures et défauts de rouleaux, s'abonner avec wildcard
            if (path === 'roll.measurements' || path === 'roll.defects') {
                // S'abonner aux changements sur les sous-chemins (ex: roll.measurements.3-1)
                const wildcardPath = path + '.*';
                const callback = ({ path: fullPath, newValue, source }) => {
                    if (source === 'user') {
                        // Récupérer l'objet complet pour synchroniser
                        const parentValue = this.stateManager.getState(path) || {};
                        this.sync(path, parentValue);
                    }
                };
                this.stateManager.subscribe(wildcardPath, callback);
                
                // S'abonner aussi au chemin racine pour les réinitialisations
                this.stateManager.subscribe(path, (value, oldValue, source) => {
                    if (source === 'user') {
                        this.sync(path, value);
                    }
                });
            } else {
                // Pour les autres chemins, souscription normale
                this.stateManager.subscribe(path, (value, oldValue, source) => {
                    if (source === 'user') {
                        console.log(`🔄 Sync triggered for ${path}:`, value);
                        this.sync(path, value);
                    }
                });
            }
        });
    }
    
    _scheduleSyncProcess() {
        if (this.syncTimeout) {
            clearTimeout(this.syncTimeout);
        }
        
        this.syncTimeout = setTimeout(() => {
            this.syncTimeout = null;
            if (!this.syncing) {
                this._processSyncQueue();
            }
        }, this.config.syncDelay);
    }
    
    async _processSyncQueue() {
        if (this.syncing || this.syncQueue.length === 0) {
            return;
        }
        
        this.syncing = true;
        
        try {
            // Prendre un batch d'éléments à synchroniser
            const batch = this._getNextBatch();
            
            if (batch.length === 0) {
                this.syncing = false;
                return;
            }
            
            // Traiter le batch
            await this._processBatch(batch);
            
            // Continuer s'il reste des éléments
            if (this.syncQueue.filter(i => i.status === 'pending').length > 0) {
                // Petit délai entre les batchs
                setTimeout(() => this._processSyncQueue(), 100);
            }
            
        } finally {
            this.syncing = false;
            this.lastSyncTime = Date.now();
        }
    }
    
    _getNextBatch() {
        const pendingItems = this.syncQueue.filter(i => i.status === 'pending');
        return pendingItems.slice(0, this.config.batchSize);
    }
    
    async _processBatch(batch) {
        // Grouper les éléments par priorité
        const grouped = this._groupBatchData(batch);
        
        // Marquer comme en cours
        batch.forEach(item => {
            item.status = 'syncing';
        });
        this.syncState.syncing = batch.length;
        
        try {
            // Envoyer au backend
            const response = await this.api.saveToSession(grouped);
            
            // Succès - retirer de la queue
            batch.forEach(item => {
                const index = this.syncQueue.indexOf(item);
                if (index > -1) {
                    this.syncQueue.splice(index, 1);
                }
            });
            
            this.syncState.succeeded += batch.length;
            this.syncState.syncing = 0;
            this.syncState.pending = this.syncQueue.filter(i => i.status === 'pending').length;
            this.syncState.lastError = null;
            
            if (window.DEBUG) {
            }
            
        } catch (error) {
            console.error('Sync error:', error);
            
            // Gérer l'échec
            await this._handleBatchError(batch, error);
        }
    }
    
    async _handleBatchError(batch, error) {
        this.syncState.lastError = error.message;
        
        for (const item of batch) {
            item.retries++;
            
            if (item.retries < this.config.retryConfig.maxRetries) {
                // Réessayer plus tard
                item.status = 'pending';
                item.nextRetryTime = Date.now() + this._calculateRetryDelay(item.retries);
                
                if (window.DEBUG) {
                    console.log(`🔄 Will retry ${item.path} (attempt ${item.retries + 1})`);
                }
            } else {
                // Échec définitif
                item.status = 'failed';
                item.error = error.message;
                this.syncState.failed++;
                
                console.error(`❌ Sync failed for ${item.path} after ${item.retries} retries`);
                
                // Notifier l'état
                this.stateManager.setState('sync.error', {
                    path: item.path,
                    error: error.message,
                    timestamp: Date.now()
                }, 'system');
            }
        }
        
        this.syncState.syncing = 0;
        this.syncState.pending = this.syncQueue.filter(i => i.status === 'pending').length;
        
        // Replanifier pour les retry
        if (this.syncState.pending > 0) {
            const nextRetryItem = this.syncQueue
                .filter(i => i.status === 'pending' && i.nextRetryTime)
                .sort((a, b) => a.nextRetryTime - b.nextRetryTime)[0];
            
            if (nextRetryItem) {
                const delay = Math.max(0, nextRetryItem.nextRetryTime - Date.now());
                setTimeout(() => this._processSyncQueue(), delay);
            }
        }
    }
    
    _groupBatchData(batch) {
        const data = {};
        
        batch.forEach(item => {
            const apiKey = this.pathMapping[item.path] || item.path;
            data[apiKey] = item.value;
        });
        
        return data;
    }
    
    _calculateRetryDelay(retryCount) {
        const { baseDelay, maxDelay, backoffMultiplier } = this.config.retryConfig;
        const delay = Math.min(
            baseDelay * Math.pow(backoffMultiplier, retryCount - 1),
            maxDelay
        );
        
        // Ajouter un peu de jitter pour éviter les pics
        const jitter = delay * 0.1 * Math.random();
        
        return Math.floor(delay + jitter);
    }
    
    _sortQueue() {
        this.syncQueue.sort((a, b) => {
            // D'abord par priorité
            const priorityDiff = this.config.priorities[a.priority] - this.config.priorities[b.priority];
            if (priorityDiff !== 0) return priorityDiff;
            
            // Puis par timestamp (FIFO)
            return a.timestamp - b.timestamp;
        });
    }
    
    _generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

// Exposer la classe globalement
window.SyncEngine = SyncEngine;

// L'instance sera créée dans init.js quand tout sera prêt
console.log('✅ SyncEngine class loaded');

// Exposer pour les tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SyncEngine;
}