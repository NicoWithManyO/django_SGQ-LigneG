from django.urls import path
from . import views

app_name = 'quality'

urlpatterns = [
    path('get-thickness-specs/', views.get_thickness_specifications, name='get_thickness_specs'),
]