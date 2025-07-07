from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
import json
from .models import FabricationOrder

@require_POST
def update_fabrication_order(request):
    """Mettre à jour un ordre de fabrication."""
    try:
        data = json.loads(request.body)
        order_number = data.get('order_number')
        for_cutting = data.get('for_cutting', False)
        
        if not order_number:
            return JsonResponse({'success': False, 'error': 'Numéro d\'ordre requis'})
        
        # Créer ou mettre à jour l'ordre
        order, created = FabricationOrder.objects.get_or_create(
            order_number=order_number,
            defaults={
                'required_length': 0,
                'target_roll_length': 0,
                'for_cutting': for_cutting
            }
        )
        
        if not created:
            order.for_cutting = for_cutting
            order.save()
        
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'for_cutting': order.for_cutting,
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except KeyError as e:
        return JsonResponse({'success': False, 'error': f'Champ requis manquant: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erreur interne: {str(e)}'})


def get_fabrication_orders(request):
    """Récupérer les ordres de fabrication non terminés."""
    orders = FabricationOrder.objects.filter(terminated=False).order_by('-created_at')
    
    # Séparer les OF normaux et les OF découpe
    normal_orders = []
    cutting_orders = []
    
    for order in orders:
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'for_cutting': order.for_cutting,
            'required_length': float(order.required_length),
            'due_date': order.due_date.strftime('%d/%m/%Y') if order.due_date else None,
            'produced_count': 0,  # TODO: calculer depuis les rouleaux produits
            'produced_length': 0  # TODO: calculer depuis les rouleaux produits
        }
        
        if order.for_cutting:
            cutting_orders.append(order_data)
        else:
            normal_orders.append(order_data)
    
    return JsonResponse({
        'normal_orders': normal_orders,
        'cutting_orders': cutting_orders
    })


def check_of_exists(request):
    """Vérifier si un OF existe."""
    order_number = request.GET.get('order_number', '').strip()
    
    if not order_number:
        return JsonResponse({'exists': False, 'error': 'Numéro d\'ordre requis'})
    
    try:
        exists = FabricationOrder.objects.filter(order_number=order_number).exists()
        return JsonResponse({'exists': exists, 'order_number': order_number})
    except Exception as e:
        return JsonResponse({'exists': False, 'error': f'Erreur de vérification: {str(e)}'})


@require_POST
def create_of(request):
    """Créer un nouvel OF."""
    try:
        data = json.loads(request.body)
        order_number = data.get('order_number', '').strip()
        required_length = data.get('required_length', 0)
        target_roll_length = data.get('target_roll_length', 0)
        for_cutting = data.get('for_cutting', False)
        
        if not order_number:
            return JsonResponse({'success': False, 'error': 'Numéro d\'ordre requis'})
        
        # Vérifier si l'OF existe déjà
        if FabricationOrder.objects.filter(order_number=order_number).exists():
            return JsonResponse({'success': False, 'error': f'L\'OF "{order_number}" existe déjà'})
        
        # Créer l'OF
        order = FabricationOrder.objects.create(
            order_number=order_number,
            required_length=required_length,
            target_roll_length=target_roll_length,
            for_cutting=for_cutting
        )
        
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'id': order.id,
            'message': f'OF "{order_number}" créé avec succès'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erreur lors de la création: {str(e)}'})
