from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Operator, FabricationOrder

class OperatorsAPIView(APIView):
    """API pour récupérer et créer des opérateurs."""
    
    def get(self, request):
        """Retourne la liste des opérateurs actifs."""
        operators = Operator.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        data = []
        for op in operators:
            data.append({
                'id': op.id,
                'first_name': op.first_name,
                'last_name': op.last_name,
                'employee_id': op.employee_id,
                'training_completed': op.training_completed,
            })
        
        return Response(data)
    
    def post(self, request):
        """Créer un nouvel opérateur."""
        try:
            # Récupérer les données
            data = request.data
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            
            if not first_name or not last_name:
                return Response({
                    'error': 'Le prénom et le nom sont requis.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Générer l'employee_id
            employee_id = f"{first_name}{last_name.upper()}".replace(' ', '')
            
            # Vérifier si l'opérateur existe déjà
            if Operator.objects.filter(employee_id=employee_id).exists():
                return Response({
                    'error': f'L\'opérateur {employee_id} existe déjà.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer le nouvel opérateur
            new_operator = Operator.objects.create(
                first_name=first_name,
                last_name=last_name,
                training_completed=data.get('training_completed', False),
                is_active=True  # Toujours actif par défaut
            )
            
            return Response({
                'id': new_operator.id,
                'first_name': new_operator.first_name,
                'last_name': new_operator.last_name,
                'employee_id': new_operator.employee_id,
                'training_completed': new_operator.training_completed,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Erreur lors de la création : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FabricationOrdersAPIView(APIView):
    """API pour récupérer et créer des OF."""
    
    def get(self, request):
        """Retourne la liste des OF non terminés."""
        # OF normaux non terminés (exclure ceux de découpe)
        fabrication_orders = FabricationOrder.objects.filter(
            terminated=False, 
            for_cutting=False
        ).order_by('order_number')
        
        # OF de découpe non terminés
        cutting_orders = FabricationOrder.objects.filter(
            terminated=False,
            for_cutting=True
        ).order_by('order_number')
        
        # Formatter les données
        of_data = []
        for of in fabrication_orders:
            of_data.append({
                'id': of.id,
                'order_number': of.order_number,
                'required_length': float(of.required_length) if of.required_length else None,
                'target_roll_length': float(of.target_roll_length) if of.target_roll_length else None,
            })
        
        cutting_data = []
        for of in cutting_orders:
            cutting_data.append({
                'id': of.id,
                'order_number': of.order_number,
            })
        
        return Response({
            'fabrication_orders': of_data,
            'cutting_orders': cutting_data
        })
    
    def post(self, request):
        """Créer un nouvel OF."""
        try:
            # Récupérer les données
            data = request.data
            order_number = data.get('order_number', '').strip()
            
            if not order_number:
                return Response({
                    'error': 'Le numéro d\'OF est requis.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier si l'OF existe déjà
            if FabricationOrder.objects.filter(order_number=order_number).exists():
                return Response({
                    'error': f'L\'OF {order_number} existe déjà.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer le nouvel OF
            new_of = FabricationOrder.objects.create(
                order_number=order_number,
                required_length=data.get('required_length'),
                target_roll_length=data.get('target_roll_length'),
                for_cutting=False,
                terminated=False
            )
            
            return Response({
                'id': new_of.id,
                'order_number': new_of.order_number,
                'required_length': float(new_of.required_length) if new_of.required_length else None,
                'target_roll_length': float(new_of.target_roll_length) if new_of.target_roll_length else None,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Erreur lors de la création : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
