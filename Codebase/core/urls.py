from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('update-fabrication-order/', views.update_fabrication_order, name='update_fabrication_order'),
    path('get-fabrication-orders/', views.get_fabrication_orders, name='get_fabrication_orders'),
    path('check-of-exists/', views.check_of_exists, name='check_of_exists'),
    path('create-of/', views.create_of, name='create_of'),
]