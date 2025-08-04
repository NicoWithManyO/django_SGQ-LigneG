from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from catalog.models import QualityDefectType, ProfileTemplate, ProfileParamValue
from production.models.current import CurrentProfile
import json

@ensure_csrf_cookie
def session_view(request):
    """Gérer les données de session (GET et PATCH)"""
    if request.method == 'GET':
        return JsonResponse(request.session.get('v3_production', {}))
    
    elif request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            
            # Initialiser si nécessaire
            if 'v3_production' not in request.session:
                request.session['v3_production'] = {}
            
            # Mettre à jour les données (merge)
            for key, value in data.items():
                request.session['v3_production'][key] = value
            
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'updated': data,
                'session': request.session.get('v3_production', {})
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@ensure_csrf_cookie
def save_session(request):
    """Sauvegarder des données dans la session"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return JsonResponse({'error': 'Key required'}, status=400)
        
        # Initialiser si nécessaire
        if 'v3_production' not in request.session:
            request.session['v3_production'] = {}
        
        # Sauvegarder la donnée
        request.session['v3_production'][key] = value
        request.session.modified = True
        
        return JsonResponse({'success': True, 'saved': {key: value}})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def load_session(request):
    """Charger une donnée spécifique de la session"""
    key = request.GET.get('key')
    
    if not key:
        return JsonResponse({'error': 'Key required'}, status=400)
    
    value = request.session.get('v3_production', {}).get(key)
    return JsonResponse({'key': key, 'value': value})

def get_defect_types(request):
    """Récupérer la liste des types de défauts actifs."""
    try:
        defect_types = QualityDefectType.objects.filter(is_active=True).values(
            'id', 'name', 'severity', 'threshold_value'
        )
        
        # Transformer pour le frontend
        defects = []
        for defect in defect_types:
            # Rouge pour bloquant, orange pour non-bloquant
            color = 'danger' if defect['severity'] == 'blocking' else 'warning'
            defects.append({
                'id': defect['id'],
                'name': defect['name'],
                'severity': defect['severity'],
                'threshold': defect['threshold_value'],
                'color': color
            })
        
        return JsonResponse({
            'success': True,
            'defects': list(defects)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_profiles(request):
    """Récupérer la liste des profils actifs."""
    try:
        profiles = ProfileTemplate.objects.filter(is_active=True).values(
            'id', 'name', 'description'
        )
        
        return JsonResponse({
            'success': True,
            'profiles': list(profiles)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@ensure_csrf_cookie
def save_current_profile(request):
    """Sauvegarder le profil actuellement sélectionné."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        profile_id = data.get('profile_id')
        
        if not profile_id:
            # Si pas de profil, effacer le profil actuel
            CurrentProfile.objects.all().delete()
            return JsonResponse({'success': True, 'message': 'Profil actuel effacé'})
        
        # Récupérer le profil
        profile = ProfileTemplate.objects.get(id=profile_id, is_active=True)
        
        # Mettre à jour ou créer le profil actuel
        current_profile, created = CurrentProfile.objects.get_or_create(
            defaults={'profile': profile}
        )
        if not created:
            current_profile.profile = profile
            current_profile.save()
        
        return JsonResponse({
            'success': True,
            'profile': {
                'id': profile.id,
                'name': profile.name,
                'description': profile.description
            }
        })
        
    except ProfileTemplate.DoesNotExist:
        return JsonResponse({'error': 'Profil non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_profile_details(request, profile_id):
    """Récupérer les détails complets d'un profil (paramètres machine et spécifications)."""
    try:
        profile = ProfileTemplate.objects.get(id=profile_id, is_active=True)
        
        # Récupérer les paramètres machine
        params = []
        for param_value in profile.profileparamvalue_set.select_related('param_item').order_by('param_item__order'):
            params.append({
                'id': param_value.id,
                'name': param_value.param_item.name,
                'display_name': param_value.param_item.display_name,
                'category': param_value.param_item.category,
                'unit': param_value.param_item.unit,
                'value': float(param_value.value) if param_value.value else 0,
                'default_value': float(param_value.param_item.default_value) if param_value.param_item.default_value else 0
            })
        
        # Grouper par catégorie
        params_by_category = {
            'fibrage': [p for p in params if p['category'] == 'fibrage'],
            'ensimeuse': [p for p in params if p['category'] == 'ensimeuse'],
            'autre': [p for p in params if p['category'] == 'autre']
        }
        
        # Récupérer les spécifications
        specs = []
        for spec_value in profile.profilespecvalue_set.select_related('spec_item').order_by('spec_item__order'):
            specs.append({
                'id': spec_value.id,
                'name': spec_value.spec_item.name,
                'display_name': spec_value.spec_item.display_name,
                'unit': spec_value.spec_item.unit,
                'value_min': float(spec_value.value_min) if spec_value.value_min else None,
                'value_min_alert': float(spec_value.value_min_alert) if spec_value.value_min_alert else None,
                'value_nominal': float(spec_value.value_nominal) if spec_value.value_nominal else None,
                'value_max_alert': float(spec_value.value_max_alert) if spec_value.value_max_alert else None,
                'value_max': float(spec_value.value_max) if spec_value.value_max else None,
                'is_blocking': spec_value.is_blocking
            })
        
        return JsonResponse({
            'success': True,
            'profile': {
                'id': profile.id,
                'name': profile.name,
                'description': profile.description,
                'oee_target': float(profile.oee_target) if profile.oee_target else None,
                'belt_speed': float(profile.belt_speed_m_per_minute) if profile.belt_speed_m_per_minute else None,
                'parameters': params_by_category,
                'specifications': specs
            }
        })
        
    except ProfileTemplate.DoesNotExist:
        return JsonResponse({'error': 'Profil non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)