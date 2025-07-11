from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import DefectType, Specification
from production.models import RollDefect


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


# SUPPRIMÉ : Les défauts seront sauvegardés avec le rouleau


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


