from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import DefectType, RollDefect, Specification


def get_thickness_specifications(request):
    """Retourne les spécifications d'épaisseur actives."""
    try:
        # Chercher d'abord dans le nouveau modèle Specification
        spec = Specification.objects.filter(spec_type='thickness', is_active=True).first()
        if spec:
            return JsonResponse({
                'name': spec.name,
                'ep_mini': float(spec.value_min) if spec.value_min else 3.0,
                'ep_mini_alerte': float(spec.value_min_alert) if spec.value_min_alert else 3.5,
                'ep_nominale': float(spec.value_nominal) if spec.value_nominal else 4.0,
                'ep_max_alerte': float(spec.value_max_alert) if spec.value_max_alert else 4.5,
                'max_nok': spec.max_nok if spec.max_nok else 4,
                'is_blocking': spec.is_blocking,
            })
        else:
            # Valeurs par défaut si aucune spéc configurée
            return JsonResponse({
                'name': '80gr/m² (défaut)',
                'ep_mini': 3.0,
                'ep_mini_alerte': 3.5,
                'ep_nominale': 4.0,
                'ep_max_alerte': 4.5,
                'max_nok': 4,
                'is_blocking': True,
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def save_roll_defects(request):
    """Sauvegarde les défauts détectés sur un rouleau."""
    try:
        data = json.loads(request.body)
        roll_id = data.get('roll_id')
        defects = data.get('defects', {})
        
        if not roll_id:
            return JsonResponse({'error': 'ID rouleau manquant'}, status=400)
        
        saved_defects = []
        
        # Parcourir les défauts par mètre et position
        for meter_str, positions in defects.items():
            meter = int(meter_str)
            
            for position, defect_name in positions.items():
                if not defect_name or not defect_name.strip():
                    continue
                    
                # Trouver le type de défaut par nom
                try:
                    defect_type = DefectType.objects.get(name=defect_name, is_active=True)
                except DefectType.DoesNotExist:
                    # Ignorer les défauts inconnus
                    continue
                
                # Mapper les positions
                position_mapping = {
                    'left': 'left',
                    'center': 'center', 
                    'right': 'right'
                }
                
                side_position = position_mapping.get(position)
                if not side_position:
                    continue
                
                # Vérifier si le défaut existe déjà
                existing_defect = RollDefect.objects.filter(
                    roll_id=roll_id,
                    meter_position=meter,
                    side_position=side_position,
                    defect_type=defect_type
                ).first()
                
                if not existing_defect:
                    # Créer le nouveau défaut
                    defect = RollDefect.objects.create(
                        roll_id=roll_id,
                        defect_type=defect_type,
                        description=f"Défaut {defect_name} détecté à {meter}m côté {side_position}",
                        meter_position=meter,
                        side_position=side_position
                    )
                    saved_defects.append({
                        'id': defect.id,
                        'type': defect_name,
                        'meter': meter,
                        'position': side_position,
                        'is_blocking': defect.is_blocking
                    })
        
        # Calculer le statut de conformité des défauts (seulement ceux vraiment bloquants)
        blocking_defects_count = RollDefect.objects.filter(
            roll_id=roll_id,
            defect_type__severity='blocking'
        ).count()
        
        return JsonResponse({
            'success': True,
            'saved_defects': saved_defects,
            'blocking_defects_count': blocking_defects_count,
            'message': f'{len(saved_defects)} défauts sauvegardés'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_all_specifications(request):
    """Retourne toutes les spécifications actives pour tous les types."""
    try:
        specs = Specification.objects.filter(is_active=True)
        specs_data = {}
        
        for spec in specs:
            spec_key = f"{spec.spec_type}_{spec.name}"
            specs_data[spec_key] = {
                'spec_type': spec.spec_type,
                'name': spec.name,
                'unit': spec.unit,
                'value_min': float(spec.value_min) if spec.value_min else None,
                'value_min_alert': float(spec.value_min_alert) if spec.value_min_alert else None,
                'value_nominal': float(spec.value_nominal) if spec.value_nominal else None,
                'value_max_alert': float(spec.value_max_alert) if spec.value_max_alert else None,
                'value_max': float(spec.value_max) if spec.value_max else None,
                'is_blocking': spec.is_blocking,
                'max_nok': spec.max_nok,
            }
        
        return JsonResponse(specs_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


