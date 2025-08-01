from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Operator, FabricationOrder

class OperatorsAPIView(APIView):
    """API pour récupérer la liste des opérateurs actifs."""
    
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


class FabricationOrdersAPIView(APIView):
    """API pour récupérer la liste des OF."""
    
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
