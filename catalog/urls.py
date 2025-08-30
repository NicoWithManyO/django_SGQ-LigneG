from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfileTemplateViewSet, QualityDefectTypeViewSet

app_name = 'catalog'

# Créer le router pour les ViewSets
router = DefaultRouter()
router.register(r'profiles', ProfileTemplateViewSet, basename='profile')
router.register(r'defect-types', QualityDefectTypeViewSet, basename='defect-type')

urlpatterns = [
    path('api/', include(router.urls)),
]