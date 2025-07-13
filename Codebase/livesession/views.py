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
    
    # Pour les champs de la sticky bar (rouleaux), on les met dans LiveRoll
    elif field_name.startswith('sticky-'):
        from .models import LiveRoll
        
        # Obtenir ou créer le rouleau actif
        roll, created = LiveRoll.objects.get_or_create(
            session_key=session_key,
            is_active=True,
            defaults={'roll_data': {}}
        )
        
        # Mapper les champs sticky vers des noms plus clairs
        field_map = {
            'sticky-roll-number': 'roll_number',
            'sticky-tube-mass': 'tube_mass',
            'sticky-roll-length': 'length',
            'sticky-total-mass': 'total_mass',
            'sticky-next-tube-mass': 'next_tube_mass'
        }
        
        if field_name in field_map:
            roll.roll_data[field_map[field_name]] = value
            roll.save()
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


@require_http_methods(["GET"])
def get_active_roll(request):
    """Récupère les données du rouleau actif"""
    # S'assurer qu'on a une session
    if not request.session.session_key:
        return JsonResponse({'success': False, 'message': 'Pas de session'})
    
    session_key = request.session.session_key
    
    try:
        from .models import LiveRoll
        active_roll = LiveRoll.objects.filter(
            session_key=session_key,
            is_active=True
        ).first()
        
        if active_roll:
            # Calculer la masse nette et le grammage AVANT le statut
            tube_mass = float(active_roll.roll_data.get('tube_mass', 0) or 0)
            total_mass = float(active_roll.roll_data.get('total_mass', 0) or 0)
            length = float(active_roll.roll_data.get('length', 0) or 0)
            
            net_mass = total_mass - tube_mass if total_mass > tube_mass else 0
            grammage = round(net_mass / length, 2) if length > 0 else 0
            
            active_roll.roll_data['net_mass'] = net_mass
            active_roll.roll_data['grammage'] = grammage
            
            # Recalculer le statut avec le grammage inclus
            roll_data_with_session = active_roll.roll_data.copy()
            roll_data_with_session['session_key'] = session_key
            
            # Calculer le statut
            status = calculate_roll_status(roll_data_with_session)
            active_roll.roll_data['status'] = status
            
            # Sauvegarder les mises à jour
            active_roll.save()
            
            return JsonResponse({
                'success': True,
                'roll_data': active_roll.roll_data
            })
        else:
            return JsonResponse({
                'success': True,
                'roll_data': {
                    'defects': [],
                    'thickness_measurements': []
                }
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def calculate_roll_status(roll_data):
    """Calcule le statut du rouleau basé sur les défauts et épaisseurs"""
    from quality.models import DefectType, Specification
    from datetime import datetime
    
    has_blocking_defect = False
    has_non_blocking_defect = False
    has_critical_thickness = False
    has_alert_thickness = False
    has_thickness_data = False
    has_critical_grammage = False
    
    # Vérifier les défauts
    defects = roll_data.get('defects', [])
    if defects:
        defect_ids = [d.get('type_id') for d in defects if d.get('type_id')]
        defect_types = DefectType.objects.filter(id__in=defect_ids, is_active=True)
        
        for defect_type in defect_types:
            if defect_type.severity == 'blocking':
                has_blocking_defect = True
            elif defect_type.severity == 'non_blocking':
                has_non_blocking_defect = True
    
    # Vérifier les épaisseurs
    thickness_measurements = roll_data.get('thickness_measurements', [])
    thickness_count = 0
    
    if thickness_measurements:
        # Récupérer les specs d'épaisseur actives
        thickness_spec = Specification.objects.filter(
            spec_type='thickness',
            is_active=True
        ).first()
        
        if thickness_spec:
            for measurement in thickness_measurements:
                value = measurement.get('thickness_value')
                if value is not None:
                    thickness_count += 1
                    if thickness_spec.value_min and value < float(thickness_spec.value_min):
                        has_critical_thickness = True
                    elif thickness_spec.value_min_alert and value < float(thickness_spec.value_min_alert):
                        has_alert_thickness = True
                    elif thickness_spec.value_max_alert and value > float(thickness_spec.value_max_alert):
                        has_alert_thickness = True
    
    # Vérifier le grammage
    grammage = roll_data.get('grammage', 0)
    if grammage:
        grammage_spec = Specification.objects.filter(
            spec_type='global_surface_mass',
            is_active=True
        ).first()
        
        if grammage_spec:
            status = grammage_spec.get_status(float(grammage))
            if status in ['critical_low', 'critical_high']:
                has_critical_grammage = True
    
    # Déterminer le statut et l'ID du rouleau
    roll_number = roll_data.get('roll_number', '')
    
    # Récupérer les OF depuis CurrentProductionState via la session
    from .models import CurrentProductionState
    session_key = roll_data.get('session_key')
    current_of = ''
    cutting_of = ''
    
    if session_key:
        try:
            state = CurrentProductionState.objects.get(session_key=session_key)
            current_of = state.current_of.order_number if state.current_of else ''
            cutting_of = state.cutting_of.order_number if state.cutting_of else ''
        except CurrentProductionState.DoesNotExist:
            pass
    
    # Déterminer le statut
    if has_blocking_defect or has_critical_thickness or has_critical_grammage:
        status_code = 'NON_CONFORME'
        label = 'NON CONFORME'
        color = '#ff1744'
    else:
        status_code = 'CONFORME'
        label = 'CONFORME'
        color = '#4caf50' if thickness_count >= 6 else '#6c757d'
    
    # Calculer l'ID du rouleau
    roll_id = '--'
    if roll_number and (current_of or cutting_of):
        if status_code == 'NON_CONFORME':
            # Non conforme : OFDécoupe_DDMM
            now = datetime.now()
            roll_id = f"{cutting_of}_{now.strftime('%d%m')}" if cutting_of else '--'
        else:
            # Conforme : OF_NumRouleau
            roll_id = f"{current_of}_{str(roll_number).zfill(3)}" if current_of else '--'
    
    return {
        'code': status_code,
        'label': label,
        'color': color,
        'roll_id': roll_id,
        'grammage_critical': has_critical_grammage
    }


@require_http_methods(["POST"])
def save_active_roll(request):
    """Sauvegarde les données du rouleau actif"""
    import json
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    try:
        data = json.loads(request.body)
        from .models import LiveRoll
        
        # Obtenir ou créer le rouleau actif
        active_roll, created = LiveRoll.objects.get_or_create(
            session_key=session_key,
            is_active=True,
            defaults={'roll_data': data}
        )
        
        if not created:
            # Fusionner avec les données existantes
            # Pour les listes (thickness_measurements, defects), on remplace complètement
            for key, value in data.items():
                if key in ['thickness_measurements', 'defects']:
                    # Remplacer complètement les listes
                    active_roll.roll_data[key] = value
                else:
                    # Pour les autres champs, mettre à jour normalement
                    active_roll.roll_data[key] = value
        
        # Calculer la masse nette et le grammage AVANT le statut
        tube_mass = float(active_roll.roll_data.get('tube_mass', 0) or 0)
        total_mass = float(active_roll.roll_data.get('total_mass', 0) or 0)
        length = float(active_roll.roll_data.get('length', 0) or 0)
        
        # Masse nette = Masse totale - Masse tube
        net_mass = total_mass - tube_mass if total_mass > tube_mass else 0
        
        # Grammage (g/m²) = Masse nette / Longueur (si longueur > 0)
        grammage = round(net_mass / length, 2) if length > 0 else 0
        
        active_roll.roll_data['net_mass'] = net_mass
        active_roll.roll_data['grammage'] = grammage
        
        # Ajouter la session_key pour le calcul du statut
        roll_data_with_session = active_roll.roll_data.copy()
        roll_data_with_session['session_key'] = session_key
        
        # Calculer et ajouter le statut
        status = calculate_roll_status(roll_data_with_session)
        active_roll.roll_data['status'] = status
        
        active_roll.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Rouleau sauvegardé',
            'status': status,
            'net_mass': net_mass,
            'grammage': grammage,
            'grammage_critical': status.get('grammage_critical', False)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_http_methods(["POST"])
def auto_save_shift(request):
    """Sauvegarde automatique des données du poste (remplace CurrentProd)"""
    import json
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    try:
        data = json.loads(request.body)
        
        # Obtenir ou créer le brouillon de poste
        draft, created = LiveShift.objects.get_or_create(
            session_key=session_key,
            defaults={'shift_data': data}
        )
        
        if not created:
            # Fusionner avec les données existantes
            draft.shift_data.update(data)
            draft.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Données sauvegardées'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_http_methods(["GET"])
def get_saved_data(request):
    """Récupère les données sauvegardées du poste (remplace CurrentProd)"""
    # S'assurer qu'on a une session
    if not request.session.session_key:
        return JsonResponse({'data': {}, 'success': True})
    
    session_key = request.session.session_key
    
    try:
        draft = LiveShift.objects.filter(session_key=session_key).first()
        
        if draft:
            return JsonResponse({
                'data': draft.shift_data,
                'success': True
            })
        else:
            return JsonResponse({
                'data': {},
                'success': True
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_http_methods(["POST"])
def clear_saved_data(request):
    """Efface les données sauvegardées (remplace CurrentProd)"""
    # S'assurer qu'on a une session
    if not request.session.session_key:
        return JsonResponse({'success': True})
    
    session_key = request.session.session_key
    
    try:
        # Supprimer le brouillon de poste
        LiveShift.objects.filter(session_key=session_key).delete()
        
        # Garder certaines données dans CurrentProductionState
        # (OF, profils, etc. restent persistants)
        
        return JsonResponse({
            'success': True,
            'message': 'Données effacées'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })