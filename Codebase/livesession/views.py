from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import CurrentProductionState, LiveShift
from core.models import FabricationOrder


@require_http_methods(["POST"])
def update_field(request):
    """Endpoint générique pour mettre à jour un champ"""
    field_name = request.POST.get('field')
    value = request.POST.get('value')
    
    print(f"DEBUG: field_name='{field_name}', value='{value}'")
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    # Obtenir ou créer l'état de production
    state, created = CurrentProductionState.objects.get_or_create(
        session_key=session_key,
        defaults={'user': request.user if request.user.is_authenticated else None}
    )
    
    # Router selon le champ
    if field_name == 'current_of':
        if value:
            state.current_of_id = value
        else:
            state.current_of = None
        state.save()
        return JsonResponse({'status': 'ok', 'message': f'OF en cours mis à jour'})
        
    elif field_name == 'cutting_of':
        if value:
            state.cutting_of_id = value
        else:
            state.cutting_of = None
        state.save()
        return JsonResponse({'status': 'ok', 'message': f'OF découpe mis à jour'})
        
    elif field_name == 'target_length':
        state.target_length = value if value else None
        state.save()
        return JsonResponse({'status': 'ok', 'message': f'Longueur cible mise à jour'})
    
    elif field_name == 'selected_profile':
        if value:
            state.selected_profile_id = value
        else:
            state.selected_profile = None
        state.save()
        return JsonResponse({'status': 'ok', 'message': f'Profil mis à jour'})
    
    elif field_name == 'active_modes':
        import json
        try:
            state.active_modes = json.loads(value) if value else {}
        except json.JSONDecodeError:
            state.active_modes = {}
        state.save()
        return JsonResponse({'status': 'ok', 'message': f'Modes mis à jour'})
    
    elif field_name == 'active_productivity_tab':
        state.active_productivity_tab = value if value else 'temps'
        state.save()
        return JsonResponse({'status': 'ok', 'message': f'Onglet actif mis à jour'})
    
    elif field_name == 'roll_number':
        state.roll_number = int(value) if value and value.isdigit() else None
        state.save()
        return JsonResponse({'status': 'ok', 'message': f'Numéro de rouleau mis à jour'})
    
    # Pour les champs de la sticky bar (rouleaux), on pourrait les mettre dans LiveShift
    elif field_name.startswith('sticky-'):
        # Obtenir ou créer le brouillon
        draft, created = LiveShift.objects.get_or_create(
            session_key=session_key,
            defaults={'shift_data': {}}
        )
        
        # Mettre à jour le champ dans le JSON
        if 'current_roll' not in draft.shift_data:
            draft.shift_data['current_roll'] = {}
        
        # Mapper les champs sticky vers des noms plus clairs
        field_map = {
            'sticky-roll-number': 'number',
            'sticky-tube-mass': 'tube_mass',
            'sticky-roll-length': 'length',
            'sticky-total-mass': 'total_mass',
            'sticky-next-tube-mass': 'next_tube_mass'
        }
        
        if field_name in field_map:
            draft.shift_data['current_roll'][field_map[field_name]] = value
            draft.save()
            return JsonResponse({'status': 'ok', 'message': f'Rouleau mis à jour'})
    
    # Pour les champs du shift
    elif field_name.startswith('shift_'):
        # Obtenir ou créer le brouillon
        draft, created = LiveShift.objects.get_or_create(
            session_key=session_key,
            defaults={'shift_data': {}}
        )
        
        # Extraire le nom du champ
        shift_field = field_name.replace('shift_', '')
        
        # Convertir les booléens
        if value in ['true', 'false']:
            value = value == 'true'
        
        # Mettre à jour le champ dans le JSON
        draft.shift_data[shift_field] = value
        draft.save()
        
        return JsonResponse({'status': 'ok', 'message': f'Champ {shift_field} mis à jour'})
    
    return JsonResponse({'status': 'error', 'message': f'Champ inconnu: {field_name}'})