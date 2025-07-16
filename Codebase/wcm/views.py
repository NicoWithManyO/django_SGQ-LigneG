from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import LostTimeReason


@require_http_methods(["GET"])
def get_lost_time_reasons(request):
    """Retourne la liste des motifs de temps perdu actifs."""
    try:
        reasons = LostTimeReason.objects.filter(is_active=True).order_by('category', 'order', 'name')
        
        reasons_data = []
        for reason in reasons:
            reasons_data.append({
                'id': reason.id,
                'code': reason.code,
                'name': reason.name,
                'category': reason.category,
                'is_planned': reason.is_planned,
                'color': reason.color
            })
        
        return JsonResponse({
            'success': True,
            'reasons': reasons_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
