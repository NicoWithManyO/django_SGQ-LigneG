from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import LiveQualityControl
import json


@require_http_methods(["POST"])
def save_quality_control(request):
    """Sauvegarde un contrôle qualité et calcule les moyennes"""
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    try:
        data = json.loads(request.body)
        field_name = data.get('field')
        value = data.get('value')
        
        # Obtenir ou créer le brouillon de contrôles qualité
        quality_control, created = LiveQualityControl.objects.get_or_create(
            session_key=session_key,
            defaults={'quality_data': {}}
        )
        
        # Cas spécial : effacer tout
        if field_name == 'clear_all' and value:
            quality_control.delete()
            return JsonResponse({
                'success': True,
                'quality_data': {}
            })
        
        # Cas spécial : batch update
        if field_name == 'batch_update' and isinstance(value, dict):
            # Mettre à jour tous les champs d'un coup
            for key, val in value.items():
                if key in ['micronnaire_left_1', 'micronnaire_left_2', 'micronnaire_left_3']:
                    if 'micronnaire_left' not in quality_control.quality_data:
                        quality_control.quality_data['micronnaire_left'] = [None, None, None]
                    index = int(key.split('_')[-1]) - 1
                    quality_control.quality_data['micronnaire_left'][index] = float(val) if val else None
                elif key in ['micronnaire_right_1', 'micronnaire_right_2', 'micronnaire_right_3']:
                    if 'micronnaire_right' not in quality_control.quality_data:
                        quality_control.quality_data['micronnaire_right'] = [None, None, None]
                    index = int(key.split('_')[-1]) - 1
                    quality_control.quality_data['micronnaire_right'][index] = float(val) if val else None
                elif key in ['surface_mass_gg', 'surface_mass_gc', 'surface_mass_dc', 'surface_mass_dd']:
                    quality_control.quality_data[key] = float(val) if val else None
                elif key == 'extrait_sec':
                    quality_control.quality_data[key] = float(val) if val else None
                    if val:
                        from datetime import datetime
                        quality_control.quality_data['extrait_sec_time'] = datetime.now().strftime('%H:%M')
                elif key == 'loi_given':
                    quality_control.quality_data[key] = val == 'true' if isinstance(val, str) else bool(val)
                    if quality_control.quality_data[key]:
                        from datetime import datetime
                        quality_control.quality_data['loi_time'] = datetime.now().strftime('%H:%M')
            
            # Calculer toutes les moyennes
            # Micronnaire gauche
            values = [v for v in quality_control.quality_data.get('micronnaire_left', []) if v is not None]
            quality_control.quality_data['micronnaire_left_avg'] = round(sum(values) / len(values), 2) if values else None
            
            # Micronnaire droit
            values = [v for v in quality_control.quality_data.get('micronnaire_right', []) if v is not None]
            quality_control.quality_data['micronnaire_right_avg'] = round(sum(values) / len(values), 2) if values else None
            
            # Masses surfaciques gauche
            gg = quality_control.quality_data.get('surface_mass_gg')
            gc = quality_control.quality_data.get('surface_mass_gc')
            left_values = [v for v in [gg, gc] if v is not None]
            quality_control.quality_data['surface_mass_left_avg'] = round(sum(left_values) / len(left_values), 4) if left_values else None
            
            # Masses surfaciques droite
            dc = quality_control.quality_data.get('surface_mass_dc')
            dd = quality_control.quality_data.get('surface_mass_dd')
            right_values = [v for v in [dc, dd] if v is not None]
            quality_control.quality_data['surface_mass_right_avg'] = round(sum(right_values) / len(right_values), 4) if right_values else None
            
            quality_control.save()
            return JsonResponse({
                'success': True,
                'quality_data': quality_control.quality_data
            })
        
        # Mettre à jour le champ
        if field_name in ['micronnaire_left_1', 'micronnaire_left_2', 'micronnaire_left_3']:
            # Gérer les tableaux de micronnaire gauche
            if 'micronnaire_left' not in quality_control.quality_data:
                quality_control.quality_data['micronnaire_left'] = [None, None, None]
            index = int(field_name.split('_')[-1]) - 1
            quality_control.quality_data['micronnaire_left'][index] = float(value) if value else None
            
            # Calculer la moyenne
            values = [v for v in quality_control.quality_data['micronnaire_left'] if v is not None]
            if values:
                quality_control.quality_data['micronnaire_left_avg'] = round(sum(values) / len(values), 2)
            else:
                quality_control.quality_data['micronnaire_left_avg'] = None
                
        elif field_name in ['micronnaire_right_1', 'micronnaire_right_2', 'micronnaire_right_3']:
            # Gérer les tableaux de micronnaire droit
            if 'micronnaire_right' not in quality_control.quality_data:
                quality_control.quality_data['micronnaire_right'] = [None, None, None]
            index = int(field_name.split('_')[-1]) - 1
            quality_control.quality_data['micronnaire_right'][index] = float(value) if value else None
            
            # Calculer la moyenne
            values = [v for v in quality_control.quality_data['micronnaire_right'] if v is not None]
            if values:
                quality_control.quality_data['micronnaire_right_avg'] = round(sum(values) / len(values), 2)
            else:
                quality_control.quality_data['micronnaire_right_avg'] = None
                
        elif field_name in ['surface_mass_gg', 'surface_mass_gc', 'surface_mass_dc', 'surface_mass_dd']:
            # Stocker les masses surfaciques
            quality_control.quality_data[field_name] = float(value) if value else None
            
            # Calculer les moyennes gauche et droite
            # Moyenne gauche (GG et GC)
            gg = quality_control.quality_data.get('surface_mass_gg')
            gc = quality_control.quality_data.get('surface_mass_gc')
            left_values = [v for v in [gg, gc] if v is not None]
            if left_values:
                quality_control.quality_data['surface_mass_left_avg'] = round(sum(left_values) / len(left_values), 4)
            else:
                quality_control.quality_data['surface_mass_left_avg'] = None
                
            # Moyenne droite (DC et DD)
            dc = quality_control.quality_data.get('surface_mass_dc')
            dd = quality_control.quality_data.get('surface_mass_dd')
            right_values = [v for v in [dc, dd] if v is not None]
            if right_values:
                quality_control.quality_data['surface_mass_right_avg'] = round(sum(right_values) / len(right_values), 4)
            else:
                quality_control.quality_data['surface_mass_right_avg'] = None
                
        elif field_name == 'extrait_sec':
            # Stocker l'extrait sec et mettre à jour l'heure
            quality_control.quality_data[field_name] = float(value) if value else None
            if value:
                from datetime import datetime
                quality_control.quality_data['extrait_sec_time'] = datetime.now().strftime('%H:%M')
            else:
                # Si vidé, supprimer l'heure
                quality_control.quality_data['extrait_sec_time'] = None
                
        elif field_name == 'loi_given':
            # Stocker le statut LOI et mettre à jour l'heure
            quality_control.quality_data[field_name] = value == 'true' if isinstance(value, str) else bool(value)
            if quality_control.quality_data[field_name]:
                from datetime import datetime
                quality_control.quality_data['loi_time'] = datetime.now().strftime('%H:%M')
            else:
                # Si désactivé, supprimer l'heure
                quality_control.quality_data['loi_time'] = None
                
        else:
            # Autres champs simples
            quality_control.quality_data[field_name] = value
        
        quality_control.save()
        
        return JsonResponse({
            'success': True,
            'quality_data': quality_control.quality_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_http_methods(["GET"])
def get_quality_control(request):
    """Récupère les contrôles qualité sauvegardés"""
    # S'assurer qu'on a une session
    if not request.session.session_key:
        return JsonResponse({'success': True, 'quality_data': {}})
    
    session_key = request.session.session_key
    
    try:
        quality_control = LiveQualityControl.objects.filter(session_key=session_key).first()
        
        if quality_control:
            return JsonResponse({
                'success': True,
                'quality_data': quality_control.quality_data
            })
        else:
            return JsonResponse({
                'success': True,
                'quality_data': {}
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })