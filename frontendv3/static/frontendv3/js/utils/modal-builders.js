/**
 * Fonctions utilitaires pour construire le contenu des modales de confirmation
 * Approche DRY pour générer le HTML des différents types de confirmations
 */

// Builder pour la confirmation de sauvegarde du shift
function buildShiftConfirmation(shiftData) {
    return {
        title: 'Confirmer la sauvegarde du poste',
        icon: 'bi-clipboard-check',
        question: '', // Pas de question pour éviter la redondance
        confirmText: 'Sauvegarder le poste',
        confirmIcon: 'bi-save',
        confirmClass: 'btn-primary',
        content: buildShiftSummaryHTML(shiftData),
        warning: shiftData.hasIncompleteRolls ? 'Attention : Des rouleaux sont en cours de saisie' : '',
        showComment: true, // Afficher le champ commentaire
        commentValue: shiftData.comments
    };
}

// Builder pour la confirmation de sauvegarde du rouleau
function buildRollConfirmation(rollData) {
    // Déterminer le texte du bouton selon le statut
    let confirmText = 'Sauvegarder le rouleau';
    let confirmClass = 'btn-success';
    
    if (rollData.status === 'NON_CONFORME') {
        confirmText = 'Vers découpe';
        confirmClass = 'btn-warning';
    } else if (rollData.rollId && rollData.rollId !== '--') {
        confirmText = `Sauvegarder ${rollData.rollId}`;
    }
    
    return {
        title: 'Confirmer la sauvegarde du rouleau',
        icon: 'bi-gear-wide-connected',
        showImage: true,
        question: '', // Pas de question car showComment est true
        confirmText: confirmText,
        confirmIcon: 'bi-save',
        confirmClass: confirmClass,
        content: buildRollSummaryHTML(rollData),
        warning: getQCWarning(rollData.qcStatus),
        qcPending: rollData.qcStatus === 'pending',
        showComment: true,
        commentValue: ''
    };
}

// Helpers privés pour construire le HTML
function buildShiftSummaryHTML(data) {
    // Infos de base
    const idPoste = data.shiftId || '--';
    const duration = calculateDuration(data.startTime, data.endTime);
    
    // Calculer les métriques (à adapter selon les données disponibles)
    const rendement = data.rendement || '--';
    const tauxOK = data.tauxOK || '--';
    const longueurOK = data.longueurOK || '--';
    const TO = data.TO || '--';
    
    return `
        <div class="container-fluid">
            <!-- ID Poste -->
            <div class="row g-3 mb-3">
                <div class="col-12 text-start">
                    <label class="text-muted small mb-0">ID Poste</label>
                    <p class="mb-0 text-primary fw-bold">${idPoste}</p>
                </div>
            </div>
            <!-- Humeur de fin de poste -->
            <div class="mb-3 mt-5 pt-4">
                <label class="form-label text-muted small">MoOoOOoOOooOOd de fin de poste :</label>
                <div class="d-flex justify-content-center gap-3">
                    <button type="button" 
                            class="btn rounded-circle d-flex align-items-center justify-content-center p-0" 
                            :class="selectedMood === 'sad' ? 'btn-danger' : 'btn-outline-danger'"
                            style="width: 60px; height: 60px;"
                            @click="selectedMood = selectedMood === 'sad' ? null : 'sad'">
                        <i class="bi bi-emoji-frown" style="font-size: 1.5rem;"></i>
                    </button>
                    <button type="button" 
                            class="btn rounded-circle d-flex align-items-center justify-content-center p-0" 
                            :class="selectedMood === 'neutral' ? 'btn-warning' : 'btn-outline-warning'"
                            style="width: 60px; height: 60px;"
                            @click="selectedMood = selectedMood === 'neutral' ? null : 'neutral'">
                        <i class="bi bi-emoji-neutral" style="font-size: 1.5rem;"></i>
                    </button>
                    <button type="button" 
                            class="btn rounded-circle d-flex align-items-center justify-content-center p-0" 
                            :class="selectedMood === 'happy' ? 'btn-success' : 'btn-outline-success'"
                            style="width: 60px; height: 60px;"
                            @click="selectedMood = selectedMood === 'happy' ? null : 'happy'">
                        <i class="bi bi-emoji-smile" style="font-size: 1.5rem;"></i>
                    </button>
                </div>
                <small class="text-muted d-block text-center mt-2">Information anonyme</small>
            </div>
        </div>
    `;
}

function buildRollSummaryHTML(data) {
    const fields = [];
    
    // ID et statut
    fields.push(buildField('ID Rouleau', data.rollId, 'col-6', 'text-primary fw-bold'));
    
    const statusBadge = `<span class="badge ${data.status === 'CONFORME' ? 'bg-success' : 'bg-danger'}">${data.status}</span>`;
    fields.push(buildField('Statut', statusBadge, 'col-6', '', false));
    
    // Métriques principales
    fields.push(buildField('Longueur', `${data.length} m`, 'col-4'));
    fields.push(buildField('Masse nette', `${data.netWeight} kg`, 'col-4'));
    fields.push(buildField('Grammage', `${data.grammage} g/m²`, 'col-4'));
    
    // Contrôle qualité
    if (data.qcMicromaire || data.qcMasseSurf) {
        fields.push('<div class="col-12"><hr class="my-2"></div>');
        fields.push('<div class="col-12"><small class="text-muted">Contrôle Qualité</small></div>');
        
        if (data.qcMicromaire) {
            fields.push(buildField('Micromaire', `${data.qcMicromaire} ${data.qcMicromaireUnit}`, 'col-6'));
        }
        if (data.qcMasseSurf) {
            fields.push(buildField('Masse surf.', `${data.qcMasseSurf} ${data.qcMasseSurfUnit}`, 'col-6'));
        }
    }
    
    // Défauts
    if (data.defectCount > 0) {
        fields.push(buildField('Défauts', `${data.defectCount} défaut(s) déclaré(s)`, 'col-12', 'text-danger'));
    }
    
    return `<div class="row g-3">${fields.join('')}</div>`;
}

// Helper pour construire un champ
function buildField(label, value, colClass = 'col-12', valueClass = 'fw-bold', escapeHtmlFlag = true) {
    const displayValue = escapeHtmlFlag ? escapeHtml(value) : value;
    
    return `
        <div class="${colClass}">
            <label class="text-muted small mb-0">${label}</label>
            <p class="mb-0 ${valueClass}">${displayValue}</p>
        </div>
    `;
}

// Helper pour obtenir le warning QC approprié
function getQCWarning(qcStatus) {
    const warnings = {
        'nok': 'Contrôle qualité NOK - Le rouleau sera marqué non conforme'
    };
    return warnings[qcStatus] || '';
}

// Helper pour calculer la durée entre deux heures
function calculateDuration(startTime, endTime) {
    if (!startTime || !endTime) return '--';
    
    try {
        // Convertir les heures en minutes
        const [startH, startM] = startTime.split(':').map(Number);
        const [endH, endM] = endTime.split(':').map(Number);
        
        let startMinutes = startH * 60 + startM;
        let endMinutes = endH * 60 + endM;
        
        // Si fin < début, on considère que c'est le lendemain
        if (endMinutes < startMinutes) {
            endMinutes += 24 * 60;
        }
        
        const durationMinutes = endMinutes - startMinutes;
        const hours = Math.floor(durationMinutes / 60);
        const minutes = durationMinutes % 60;
        
        return `${hours}h${minutes.toString().padStart(2, '0')}`;
    } catch (e) {
        return '--';
    }
}

// Helper pour formater une date
function formatDate(dateStr) {
    if (!dateStr) return '-';
    
    try {
        const date = new Date(dateStr);
        const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
        return date.toLocaleDateString('fr-FR', options);
    } catch (e) {
        return dateStr;
    }
}

// Helper pour échapper le HTML
function escapeHtml(text) {
    if (!text) return '';
    
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

// Export global
window.modalBuilders = {
    buildShiftConfirmation,
    buildRollConfirmation
};