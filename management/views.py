from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from production.models import Shift
from .services import ReportService, StatisticsService, ChecklistService
from .decorators import superuser_required


@superuser_required
def management_dashboard(request):
    """Dashboard principal du management avec vue d'ensemble."""
    context = {
        'title': 'Tableau de bord Management',
        'today': timezone.now().date()
    }
    return render(request, 'management/pages/dashboard.html', context)


@superuser_required
def shift_reports_list(request):
    """Liste des rapports de poste."""
    context = {
        'title': 'Rapports de poste'
    }
    return render(request, 'management/pages/reports.html', context)


@superuser_required
def shift_report_detail(request, shift_id):
    """Détail d'un rapport de poste."""
    shift = get_object_or_404(Shift, pk=shift_id)
    report_data = ReportService.get_shift_comprehensive_data(shift_id)
    
    context = {
        'title': f'Rapport {shift.shift_id}',
        'report': report_data
    }
    return render(request, 'management/pages/shift_report.html', context)


@superuser_required
def checklist_review_list(request):
    """Liste des checklists à réviser."""
    # Récupérer le nombre de jours depuis les paramètres GET (par défaut 7)
    days = int(request.GET.get('days', 7))
    
    # Récupérer toutes les checklists
    all_checklists = ChecklistService.get_all_checklists(days=days)
    
    # Séparer les checklists en attente et visées
    pending_checklists = [c for c in all_checklists if not c.management_visa]
    signed_checklists = [c for c in all_checklists if c.management_visa]
    
    context = {
        'title': 'Révision des checklists',
        'pending_checklists': pending_checklists,
        'signed_checklists': signed_checklists,
        'all_checklists': all_checklists,
        'days': days
    }
    return render(request, 'management/pages/checklists.html', context)


@superuser_required
def checklist_detail(request, checklist_id):
    """Détail d'une checklist."""
    checklist_data = ChecklistService.get_checklist_details(checklist_id)
    
    context = {
        'title': f'Checklist {checklist_data["checklist"].shift.shift_id}',
        'checklist_data': checklist_data
    }
    return render(request, 'management/pages/checklist_detail.html', context)


@superuser_required
def production_statistics(request):
    """Statistiques de production avancées."""
    context = {
        'title': 'Statistiques de production'
    }
    return render(request, 'management/pages/statistics.html', context)
