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
    from livesession.models import CurrentSession
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    # Récupérer la session courante pour les données persistantes
    try:
        current_session = CurrentSession.objects.get(session_key=session_key)
        production_state = current_session.session_data  # Pour compatibilité avec le template
    except CurrentSession.DoesNotExist:
        production_state = None
    
    # Récupérer la session courante
    try:
        current_session = CurrentSession.objects.get(session_key=session_key)
        session_data_json = json.dumps(current_session.session_data)
    except CurrentSession.DoesNotExist:
        current_session = None
        session_data_json = '{}'
    
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
    if production_state and production_state.get('active_modes'):
        active_modes_json = json.dumps(production_state.get('active_modes'))
    
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
        'current_session': current_session,
        'session_data_json': session_data_json,
        'active_productivity_tab': production_state.get('active_productivity_tab', 'temps') if production_state else 'temps',
        'roll_number': production_state.get('roll_number') if production_state else None,
    }
    
    return render(request, 'frontend/production.html', context)

# Vue retirée - à refaire proprement

# Vue retirée - à refaire proprement

# Vue retirée - à refaire proprement

# Vues retirées - à refaire proprement

# Vue retirée - à refaire proprement

# Vue retirée - à refaire proprement

# Vues retirées - à refaire proprement