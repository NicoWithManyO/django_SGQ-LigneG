from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from catalog.models import QualityDefectType
from .serializers import QualityDefectTypeSerializer


class QualityDefectTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les types de défauts qualité."""
    
    queryset = QualityDefectType.objects.filter(is_active=True)
    serializer_class = QualityDefectTypeSerializer
    permission_classes = []  # Pas d'authentification requise pour l'instant
    
    def get_queryset(self):
        """Retourne uniquement les types de défauts actifs."""
        return super().get_queryset().order_by('name')