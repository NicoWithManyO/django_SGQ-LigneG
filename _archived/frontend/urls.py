from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.index, name='index'),
    path('production-v2/', views.production_v2, name='production-v2'),
]