from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ThicknessSpecification, DefectType, RollDefect


def get_thickness_specifications(request):
    """Retourne les spécifications d'épaisseur actives."""
    try:
        spec = ThicknessSpecification.objects.filter(is_active=True).first()
        if spec:
            return JsonResponse({
                'ep_mini': float(spec.ep_mini),
                'ep_mini_alerte': float(spec.ep_mini_alerte),
                'ep_nominale': float(spec.ep_nominale),
                'ep_max_alerte': float(spec.ep_max_alerte),
                'max_nok': spec.max_nok,
            })
        else:
            # Valeurs par défaut si aucune spéc configurée
            return JsonResponse({
                'ep_mini': 3.0,
                'ep_mini_alerte': 3.5,
                'ep_nominale': 4.0,
                'ep_max_alerte': 4.5,
                'max_nok': 4,
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


