from django.urls import path
from . import views

app_name = 'planification'

urlpatterns = [
    path('api/operators/', views.OperatorsAPIView.as_view(), name='api-operators'),
    path('api/fabrication-orders/', views.FabricationOrdersAPIView.as_view(), name='api-fabrication-orders'),
]