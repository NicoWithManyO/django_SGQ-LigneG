from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from planification.models import Operator, FabricationOrder
from production.models import CurrentProfile
from catalog.models import ProfileTemplate
from wcm.models import Mode
import json

def production_view(request):
    """Vue principale de production V3"""
    
    # Charger les données de base
    operators = Operator.objects.filter(is_active=True).order_by('last_name', 'first_name')
    fabrication_orders = FabricationOrder.objects.filter(
        terminated=False,
        for_cutting=False
    ).order_by('-order_number')
    cutting_orders = FabricationOrder.objects.filter(
        terminated=False, 
        for_cutting=True
    ).order_by('-order_number')
    
    # Profil actuel
    current_profile = None
    try:
        current_profile_obj = CurrentProfile.objects.first()
        if current_profile_obj and current_profile_obj.profile:
            current_profile = {
                'id': current_profile_obj.profile.id,
                'name': current_profile_obj.profile.name
            }
    except Exception as e:
        pass
    
    # Profils disponibles
    profiles = ProfileTemplate.objects.filter(is_active=True).order_by('name')
    
    # Modes disponibles
    modes = Mode.objects.filter(is_active=True).order_by('name')
    
    # Données de session V3
    session_data = request.session.get('v3_production', {})
    
    # Nettoyer les anciennes clés dupliquées si elles existent
    if 'v3_production' in request.session:
        keys_to_remove = [
            'shift_date', 'vacation', 'start_time', 'end_time',
            'machine_started_start', 'machine_started_end', 
            'length_start', 'operator_id', 'comment'
        ]
        for key in keys_to_remove:
            session_data.pop(key, None)
        request.session['v3_production'] = session_data
        request.session.modified = True
    
    context = {
        'operators': operators,
        'fabrication_orders': fabrication_orders,
        'cutting_orders': cutting_orders,
        'current_profile': current_profile,
        'current_profile_id': current_profile['id'] if current_profile else None,
        'session_data': json.dumps(session_data),
        'operators_json': json.dumps([{
            'id': op.id,  # ID Django pour l'API
            'employee_id': op.employee_id,
            'first_name': op.first_name,
            'last_name': op.last_name,
            'display_name': f"{op.first_name} {op.last_name}"
        } for op in operators]),
        'fabrication_orders_json': json.dumps([{
            'id': of.id,
            'numero': of.order_number,
            'target_length': float(of.target_roll_length) if of.target_roll_length else 0
        } for of in fabrication_orders]),
        'cutting_orders_json': json.dumps([{
            'id': of.id,
            'numero': of.order_number,
            'target_length': float(of.target_roll_length) if of.target_roll_length else 0
        } for of in cutting_orders]),
        'profiles_json': json.dumps([{
            'id': profile.id,
            'name': profile.name,
            'description': profile.description
        } for profile in profiles]),
        'modes_json': json.dumps([{
            'id': mode.id,
            'name': mode.name,
            'is_enabled': mode.is_enabled
        } for mode in modes])
    }
    
    return render(request, 'frontendv3/production.html', context)