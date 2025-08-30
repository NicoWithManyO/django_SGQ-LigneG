from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ProfileTemplate, QualityDefectType
from .serializers import ProfileTemplateSerializer, ProfileTemplateListSerializer, QualityDefectTypeSerializer


class ProfileTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour la consultation des profils."""
    queryset = ProfileTemplate.objects.filter(is_active=True).order_by('name')
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Utilise un serializer différent pour la liste et le détail."""
        if self.action == 'list':
            return ProfileTemplateListSerializer
        return ProfileTemplateSerializer
    
    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        """Marquer ce profil comme actif et désactiver les autres."""
        profile = self.get_object()
        
        # Désactiver tous les autres profils
        ProfileTemplate.objects.exclude(pk=profile.pk).update(is_default=False)
        
        # Activer ce profil
        profile.is_default = True
        profile.save()
        
        return Response({'status': 'success', 'message': f'Profile {profile.name} set as active'})


class QualityDefectTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les types de défauts qualité."""
    queryset = QualityDefectType.objects.filter(is_active=True).order_by('name')
    serializer_class = QualityDefectTypeSerializer
    permission_classes = [AllowAny]
