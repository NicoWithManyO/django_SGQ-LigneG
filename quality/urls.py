from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import QualityDefectTypeViewSet

router = DefaultRouter()
router.register(r'defect-types', QualityDefectTypeViewSet, basename='defect-types')

app_name = 'quality'

urlpatterns = [
    path('api/', include(router.urls)),
]