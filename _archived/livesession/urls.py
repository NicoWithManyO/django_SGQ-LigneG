from django.urls import path
from .views import SessionAPIView, CheckShiftIdAPIView, CheckShiftDuplicateAPIView

app_name = 'livesession'

urlpatterns = [
    path('api/session/', SessionAPIView.as_view(), name='session-api'),
    path('api/check-shift-id/', CheckShiftIdAPIView.as_view(), name='check-shift-id'),
    path('api/check-shift-duplicate/', CheckShiftDuplicateAPIView.as_view(), name='check-shift-duplicate'),
]