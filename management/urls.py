from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views, api_views

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'shift-reports', api_views.ShiftReportViewSet, basename='shift-report')

app_name = 'management'

urlpatterns = [
    # Pages de l'interface management
    path('', views.management_dashboard, name='dashboard'),
    path('reports/', views.shift_reports_list, name='reports-list'),
    path('reports/<int:shift_id>/', views.shift_report_detail, name='report-detail'),
    path('checklists/', views.checklist_review_list, name='checklists-list'),
    path('checklists/<int:checklist_id>/', views.checklist_detail, name='checklist-detail'),
    path('statistics/', views.production_statistics, name='statistics'),
    path('exports/', views.exports_list, name='exports'),
    path('control-report/', views.control_report, name='control-report'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/dashboard-stats/', api_views.dashboard_statistics, name='api-dashboard-stats'),
    path('api/checklists/', api_views.all_checklists, name='api-all-checklists'),
    path('api/checklists/pending/', api_views.pending_checklists, name='api-pending-checklists'),
    path('api/checklists/<int:pk>/sign/', api_views.sign_checklist, name='api-sign-checklist'),
    path('api/trends/', api_views.production_trends, name='api-production-trends'),
    path('api/operator-performance/', api_views.operator_performance, name='api-operator-performance'),
    path('api/defects-analysis/', api_views.defects_analysis, name='api-defects-analysis'),
    path('api/alerts/', api_views.production_alerts, name='api-production-alerts'),
    path('api/user-visa/', api_views.user_default_visa, name='api-user-default-visa'),
    path('api/recent-rolls/', api_views.recent_rolls, name='api-recent-rolls'),
    path('api/rolls/<int:pk>/', api_views.roll_details, name='api-roll-details'),
    path('api/shifts/<int:pk>/', api_views.shift_details, name='api-shift-details'),
    path('api/conforming-rolls/', api_views.conforming_rolls_list, name='api-conforming-rolls'),
    path('api/generate-control-report/', api_views.generate_control_report, name='api-generate-control-report'),
]