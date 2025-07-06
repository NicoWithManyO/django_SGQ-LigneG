from django.shortcuts import render
from django.http import JsonResponse
from .models import ThicknessSpecification


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
