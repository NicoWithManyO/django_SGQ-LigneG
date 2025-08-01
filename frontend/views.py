from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from planification.models import Operator, FabricationOrder
import json


def index(request):
    return render(request, 'frontend/pages/index.html')


def production_v2(request):
    """Nouvelle page de production avec le système core"""
    from planification.models import FabricationOrder
    
    operators = Operator.objects.filter(is_active=True).order_by('first_name', 'last_name')
    fabrication_orders = FabricationOrder.objects.filter(terminated=False, for_cutting=False).order_by('order_number')
    cutting_orders = FabricationOrder.objects.filter(terminated=False, for_cutting=True).order_by('order_number')
    
    # Données de session complètes pour la persistance
    session_data = {
        'operator_id': request.session.get('operator_id'),
        'shift_date': request.session.get('shift_date', ''),
        'vacation': request.session.get('vacation', ''),
        'shift_id': request.session.get('shift_id', ''),
        # Données de prise de poste
        'machine_started_start': request.session.get('machine_started_start', False),
        'start_time': request.session.get('start_time', ''),
        'length_start': request.session.get('length_start', ''),
        # Données de fin de poste
        'machine_started_end': request.session.get('machine_started_end', False),
        'end_time': request.session.get('end_time', ''),
        'length_end': request.session.get('length_end', ''),
        # Données V2 pour les checkboxes
        'shift_form_machine_started_start': request.session.get('shift_form_machine_started_start', False),
        'shift_form_machine_started_end': request.session.get('shift_form_machine_started_end', False),
        'shift_form_length_start': request.session.get('shift_form_length_start', ''),
        'shift_form_length_end': request.session.get('shift_form_length_end', ''),
        # Commentaire
        'comment': request.session.get('comment', ''),
        # Données OF
        'of_en_cours': request.session.get('of_en_cours', ''),
        'target_length': request.session.get('target_length', ''),
        'of_decoupe': request.session.get('of_decoupe', ''),
        # Données sticky bar
        'roll_number': request.session.get('roll_number', ''),
        'tube_mass': request.session.get('tube_mass', ''),
        'roll_length': request.session.get('roll_length', ''),
        'total_mass': request.session.get('total_mass', ''),
        'next_tube_mass': request.session.get('next_tube_mass', ''),
        # Données profil
        'profile_id': request.session.get('profile_id', ''),
        'modes': request.session.get('modes', []),
        # Données contrôle qualité
        'quality_control': request.session.get('quality_control', {}),
        # Données du rouleau (mesures et défauts)
        'roll_measurements': request.session.get('roll_measurements', {}),
        'roll_defects': request.session.get('roll_defects', {}),
        'roll_thickness_stats': request.session.get('roll_thickness_stats', {}),
        'roll_defect_counts': request.session.get('roll_defect_counts', {}),
        'roll_conformity': request.session.get('roll_conformity', {}),
        
        # Données de la sticky bar
        'current_roll_number': request.session.get('current_roll_number'),
        'current_roll_id': request.session.get('current_roll_id'),
        'current_roll_tube_mass': request.session.get('current_roll_tube_mass'),
        'current_roll_length': request.session.get('current_roll_length'),
        'current_roll_total_mass': request.session.get('current_roll_total_mass'),
        'current_roll_thicknesses': request.session.get('current_roll_thicknesses', {}),
        'next_tube_weight': request.session.get('next_tube_weight'),
        
        # OF data
        'of_en_cours': request.session.get('of_en_cours'),
    }
    
    # Préparer les données des opérateurs pour JS
    operators_data = list(operators.values('id', 'first_name', 'last_name', 'employee_id'))
    
    # Préparer les données des OF pour JS
    fabrication_orders_data = []
    for of in fabrication_orders:
        fabrication_orders_data.append({
            'id': of.id,
            'order_number': of.order_number,
            'required_length': str(int(of.required_length)) if of.required_length else None,
            'target_roll_length': str(of.target_roll_length) if of.target_roll_length else None,
        })
    
    cutting_orders_data = list(cutting_orders.values('id', 'order_number'))
    
    context = {
        'operators': operators,
        'session_data': json.dumps(session_data),
        'operators_json': json.dumps(operators_data),
        'fabrication_orders_json': json.dumps(fabrication_orders_data),
        'cutting_orders_json': json.dumps(cutting_orders_data),
    }
    
    return render(request, 'frontend/pages/production-v2-clean.html', context)


