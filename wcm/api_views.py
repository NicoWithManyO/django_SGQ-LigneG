from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Sum
from catalog.models import WcmLostTimeReason, WcmChecklistTemplate
from .models import LostTimeEntry, Mode, MoodCounter
from .serializers import (
    WcmLostTimeReasonSerializer, 
    LostTimeEntrySerializer, 
    ModeSerializer,
    MoodCounterSerializer,
    MoodCounterIncrementSerializer
)


class WcmLostTimeReasonViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les motifs de temps perdu (lecture seule)"""
    queryset = WcmLostTimeReason.objects.filter(is_active=True)
    serializer_class = WcmLostTimeReasonSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Retourner les motifs actifs triés"""
        return super().get_queryset().order_by('category', 'order', 'name')


class LostTimeEntryViewSet(viewsets.ModelViewSet):
    """ViewSet pour les entrées de temps perdu"""
    serializer_class = LostTimeEntrySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Retourner les entrées de la session courante"""
        queryset = LostTimeEntry.objects.all()
        
        # Filtrer par session courante
        if self.request.session.session_key:
            queryset = queryset.filter(
                session_key=self.request.session.session_key
            )
        
        return queryset.select_related('reason').order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtenir les statistiques de temps perdu de la session"""
        entries = self.get_queryset()
        
        # Calculer le temps total
        total_duration = entries.aggregate(
            total=Sum('duration')
        )['total'] or 0
        
        # Compter les arrêts
        count = entries.count()
        
        # Grouper par catégorie
        by_category = entries.values(
            'reason__category', 'reason__name'
        ).annotate(
            duration_sum=Sum('duration')
        ).order_by('-duration_sum')
        
        return Response({
            'total_duration': total_duration,
            'count': count,
            'by_category': list(by_category)
        })


@api_view(['GET'])
def checklist_template_default(request):
    """Retourner le template de checklist par défaut"""
    try:
        # Chercher le template par défaut
        template = WcmChecklistTemplate.objects.filter(is_default=True).first()
        
        if not template:
            # Si pas de template par défaut, prendre le premier actif
            template = WcmChecklistTemplate.objects.filter(is_active=True).first()
        
        if template:
            # Retourner les items du template
            items = []
            # Récupérer les items via la relation through
            template_items = template.wcmchecklisttemplateitem_set.select_related('item').order_by('order')
            
            for template_item in template_items:
                # On récupère uniquement ce qui existe vraiment
                items.append({
                    'id': template_item.item.id,
                    'text': template_item.item.text,
                    'category': template_item.item.category,
                    'is_required': template_item.is_required,
                    'order': template_item.order
                })
            
            return Response({
                'id': template.id,
                'name': template.name,
                'items': items
            })
        
        # Aucun template trouvé - retourner une réponse vide mais valide
        return Response({
            'id': None,
            'name': 'Aucun template',
            'items': []
        })
        
    except Exception as e:
        print(f"Erreur checklist-template-default: {e}")
        import traceback
        traceback.print_exc()
        # Retourner une réponse vide plutôt qu'une erreur 500
        return Response({
            'id': None,
            'name': 'Erreur',
            'items': []
        })


class ModeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les modes de fonctionnement (lecture seule)"""
    queryset = Mode.objects.filter(is_active=True)
    serializer_class = ModeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Retourner les modes actifs"""
        return super().get_queryset().order_by('name')
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Activer/désactiver un mode."""
        mode = self.get_object()
        mode.is_enabled = not mode.is_enabled
        mode.save()
        
        return Response({
            'id': mode.id,
            'name': mode.name,
            'is_enabled': mode.is_enabled
        })


@api_view(['POST'])
def increment_mood_counter(request):
    """Incrémenter le compteur d'humeur."""
    serializer = MoodCounterIncrementSerializer(data=request.data)
    
    if serializer.is_valid():
        mood_type = serializer.validated_data['mood']
        
        # Trouver ou créer le compteur pour ce type d'humeur
        mood_counter, created = MoodCounter.objects.get_or_create(
            mood_type=mood_type,
            defaults={'count': 0}
        )
        
        # Incrémenter le compteur
        mood_counter.count += 1
        mood_counter.save()
        
        # Retourner les données du compteur mis à jour
        response_serializer = MoodCounterSerializer(mood_counter)
        
        return Response({
            'success': True,
            'message': f'Mood counter for {mood_type} incremented successfully',
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def reset_mood_counters(request):
    """Reset tous les compteurs d'humeur."""
    # Seuls les superusers peuvent reset
    if not request.user.is_authenticated or not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'Permission refusée. Seuls les administrateurs peuvent reset les compteurs.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Utiliser la méthode du modèle pour reset
        reset_time = MoodCounter.reset_all_counters()
        
        # Convertir en heure locale pour l'affichage
        from django.utils import timezone
        local_reset_time = timezone.localtime(reset_time)
        
        return Response({
            'success': True,
            'message': 'Tous les compteurs ont été remis à zéro',
            'reset_time': local_reset_time.strftime('%d/%m/%Y %H:%M')
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur lors du reset : {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)