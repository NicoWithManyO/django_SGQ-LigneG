from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import RollViewSet, ShiftViewSet, check_roll_id, check_shift_id, CurrentProfileView

# Router pour les API REST
router = DefaultRouter()
router.register(r'rolls', RollViewSet, basename='roll')
router.register(r'shifts', ShiftViewSet, basename='shift')

app_name = 'production'

urlpatterns = [
    # Vérification d'unicité (doit être avant le router)
    path('api/rolls/check-id/', check_roll_id, name='check-roll-id'),
    path('api/shifts/check-id/', check_shift_id, name='check-shift-id'),
    
    # Current profile API
    path('api/current-profile/', CurrentProfileView.as_view(), name='current-profile'),
    
    # API endpoints
    path('api/', include(router.urls)),
]