from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    WcmLostTimeReasonViewSet, 
    LostTimeEntryViewSet, 
    ModeViewSet, 
    checklist_template_default,
    increment_mood_counter,
    reset_mood_counters
)

# Créer le router pour l'API
router = DefaultRouter()
router.register(r'lost-time-reasons', WcmLostTimeReasonViewSet)
router.register(r'lost-time-entries', LostTimeEntryViewSet, basename='losttimeentry')
router.register(r'modes', ModeViewSet)

app_name = 'wcm'
urlpatterns = [
    path('api/', include(router.urls)),
    path('api/checklist-template-default/', checklist_template_default, name='checklist-template-default'),
    path('api/mood-counter/increment/', increment_mood_counter, name='mood-counter-increment'),
    path('api/mood-counter/reset/', reset_mood_counters, name='mood-counter-reset'),
]