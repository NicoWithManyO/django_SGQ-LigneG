from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import ProductionDraft
from production.forms import ShiftForm
import json

def production_page(request):
    """Page principale de production"""
    from core.models import Profile, Mode, FabricationOrder
    from wcm.models import ChecklistTemplate
    from livesession.models import CurrentProductionState, LiveShift
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    # Récupérer l'état de production persistant
    try:
        production_state = CurrentProductionState.objects.get(session_key=session_key)
    except CurrentProductionState.DoesNotExist:
        production_state = None
    
    # Récupérer le brouillon du poste
    try:
        live_shift = LiveShift.objects.get(session_key=session_key)
        shift_data_json = json.dumps(live_shift.shift_data)
    except LiveShift.DoesNotExist:
        live_shift = None
        shift_data_json = '{}'
    
    # Créer un formulaire vide pour la fiche de poste
    shift_form = ShiftForm()
    
    # Récupérer les profils et modes pour le bloc productivité
    profiles = Profile.objects.filter(is_active=True).select_related('machine_parameters').order_by('name')
    modes = Mode.objects.filter(is_active=True).order_by('-name')
    
    # Récupérer les OF non terminés
    fabrication_orders = FabricationOrder.objects.filter(terminated=False).order_by('order_number')
    # Séparer les OF normaux et les OF de découpe
    cutting_orders = fabrication_orders.filter(for_cutting=True)
    normal_orders = fabrication_orders.filter(for_cutting=False)
    
    # Récupérer le template de checklist et ses items
    checklist_template = ChecklistTemplate.objects.filter(is_active=True).order_by('-is_default', 'name').first()
    checklist_items = []
    if checklist_template:
        checklist_items = checklist_template.items.filter(is_active=True).order_by('order')
    
    # Convertir les modes actifs en JSON pour JavaScript
    active_modes_json = '{}'
    if production_state and production_state.active_modes:
        active_modes_json = json.dumps(production_state.active_modes)
    
    context = {
        'shift_form': shift_form,
        'form': shift_form,  # Pour compatibilité avec le template shift_block.html
        'profiles': profiles,
        'modes': modes,
        'fabrication_orders': fabrication_orders,
        'normal_orders': normal_orders,
        'cutting_orders': cutting_orders,
        'checklist_items': checklist_items,
        'production_state': production_state,
        'active_modes_json': active_modes_json,
        'live_shift': live_shift,
        'shift_data_json': shift_data_json,
    }
    
    return render(request, 'frontend/production.html', context)

# Vue retirée - à refaire proprement

# Vue retirée - à refaire proprement

# Vue retirée - à refaire proprement

# Vues retirées - à refaire proprement

# Vue retirée - à refaire proprement

# Vue retirée - à refaire proprement

# Vues retirées - à refaire proprement