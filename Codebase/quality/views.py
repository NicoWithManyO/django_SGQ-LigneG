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
        # Récupérer le nom du profil depuis les paramètres de la requête
        profile_name = request.GET.get('profile', None)
        
        # Chercher d'abord dans le nouveau modèle Specification
        if profile_name:
            # Chercher la spécification pour le profil demandé
            spec = Specification.objects.filter(
                spec_type='thickness', 
                name=profile_name,
                is_active=True
            ).first()
        else:
            # Si pas de profil spécifié, prendre la première active
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
        
        # Créer aussi un objet simplifié avec juste le premier de chaque type
        specs_by_type = {}
        
        for spec in specs:
            spec_key = f"{spec.spec_type}_{spec.name}"
            spec_dict = {
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
            specs_data[spec_key] = spec_dict
            
            # Prendre le premier de chaque type pour l'objet simplifié
            if spec.spec_type not in specs_by_type:
                specs_by_type[spec.spec_type] = spec_dict
        
        return JsonResponse({
            'all_specs': specs_data,
            'specifications': specs_by_type  # Format attendu par le JS
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_defect_types(request):
    """Retourne tous les types de défauts actifs."""
    try:
        defect_types = DefectType.objects.filter(is_active=True).order_by('name')
        defect_types_data = []
        
        for defect in defect_types:
            defect_types_data.append({
                'id': defect.id,
                'name': defect.name,
                'severity': defect.severity,
                'threshold_value': defect.threshold_value
            })
        
        return JsonResponse({
            'success': True,
            'defect_types': defect_types_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


