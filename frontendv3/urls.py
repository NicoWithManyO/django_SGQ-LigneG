from django.urls import path
from . import views, api_views

app_name = 'frontendv3'

urlpatterns = [
    # Page principale de production V3
    path('', views.production_view, name='production'),
    path('production-v3/', views.production_view, name='production-v3'),
    
    # API endpoints
    path('api/session/', api_views.session_view, name='api-session'),
    path('api/session/save/', api_views.save_session, name='api-session-save'),
    path('api/session/load/', api_views.load_session, name='api-session-load'),
    path('api/defect-types/', api_views.get_defect_types, name='api-defect-types'),
    path('api/profiles/', api_views.get_profiles, name='api-profiles'),
    path('api/current-profile/', api_views.save_current_profile, name='api-current-profile'),
    path('api/profiles/<int:profile_id>/', api_views.get_profile_details, name='api-profile-details'),
]