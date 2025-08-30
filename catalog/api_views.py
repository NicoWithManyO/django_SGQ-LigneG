from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ProductProfile, OperatingMode
from .serializers import ProductProfileSerializer, OperatingModeSerializer


class ProductProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les profils de produit."""
    queryset = ProductProfile.objects.all()
    serializer_class = ProductProfileSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Récupérer un profil avec toutes ses relations."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class OperatingModeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les modes de fonctionnement."""
    queryset = OperatingMode.objects.all()
    serializer_class = OperatingModeSerializer