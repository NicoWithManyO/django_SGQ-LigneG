from django.urls import path
from . import views

app_name = 'wcm'

urlpatterns = [
    path('api/lost-time-reasons/', views.get_lost_time_reasons, name='get_lost_time_reasons'),
]