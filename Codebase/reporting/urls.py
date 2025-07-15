from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),
]