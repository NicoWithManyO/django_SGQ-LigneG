from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from production.models import Shift, Roll, LostTimeEntry
from core.models import MoodCounter, FabricationOrder
from quality.models import DefectType
import json

def dashboard(request):
    """Vue principale du dashboard"""
    return render(request, 'reporting/dashboard.html')

def dashboard_data(request):
    """API pour les données du dashboard"""
    try:
        # Récupérer les 3 derniers postes
        last_shifts = Shift.objects.select_related('operator').order_by('-date', '-end_time')[:3]
        
        # Données des 3 derniers postes
        shifts_data = []
        for shift in last_shifts:
            # Calculer les métriques du poste
            total_length = shift.total_length or 0
            ok_length = shift.ok_length or 0
            nok_length = shift.nok_length or 0
            
            # Temps perdus
            lost_times = shift.lost_time_entries.aggregate(
                total=Sum('duration')
            )['total'] or 0
            
            # Nombre de rouleaux
            rolls_count = shift.rolls.count()
            conformes = shift.rolls.filter(status='CONFORME').count()
            non_conformes = shift.rolls.filter(status='NON_CONFORME').count()
            
            shifts_data.append({
                'id': shift.shift_id,
                'date': shift.date.strftime('%d/%m/%Y'),
                'vacation': shift.vacation,
                'operator': shift.operator.full_name if shift.operator else 'N/A',
                'total_length': total_length,
                'ok_length': ok_length,
                'nok_length': nok_length,
                'lost_time': lost_times,
                'rolls_count': rolls_count,
                'conformes': conformes,
                'non_conformes': non_conformes,
                'trs': calculate_trs(shift),
            })
        
        # Moyennes des 3 postes
        if shifts_data:
            avg_data = {
                'total_length': sum(s['total_length'] for s in shifts_data) / len(shifts_data),
                'ok_length': sum(s['ok_length'] for s in shifts_data) / len(shifts_data),
                'lost_time': sum(s['lost_time'] for s in shifts_data) / len(shifts_data),
                'trs': sum(s['trs'] for s in shifts_data) / len(shifts_data),
            }
        else:
            avg_data = {
                'total_length': 0,
                'ok_length': 0,
                'lost_time': 0,
                'trs': 0,
            }
        
        # Compteurs d'humeur
        mood_counts = MoodCounter.get_all_counts()
        
        # Listing des derniers postes avec plus de détails
        all_shifts = Shift.objects.select_related('operator').order_by('-date', '-end_time')[:20]
        shifts_listing = []
        for shift in all_shifts:
            shifts_listing.append({
                'id': shift.shift_id,
                'date': shift.date.strftime('%d/%m/%Y'),
                'vacation': shift.vacation,
                'operator': shift.operator.full_name if shift.operator else 'N/A',
                'total_length': shift.total_length or 0,
                'trs': calculate_trs(shift),
                'duration': calculate_duration(shift),
            })
        
        # Rouleaux de l'OF en cours
        current_of = None
        rolls_of = []
        
        # Essayer de récupérer l'OF en cours depuis la session
        if request.session.session_key:
            from livesession.models import CurrentSession
            try:
                session = CurrentSession.objects.get(session_key=request.session.session_key)
                of_id = session.session_data.get('current_of')
                if of_id:
                    current_of = FabricationOrder.objects.get(pk=of_id)
            except:
                pass
        
        if current_of:
            rolls = Roll.objects.filter(
                fabrication_order=current_of
            ).order_by('-created_at')[:10]
            
            for roll in rolls:
                rolls_of.append({
                    'id': roll.roll_id,
                    'number': roll.roll_number,
                    'length': roll.length,
                    'status': roll.status,
                    'date': roll.created_at.strftime('%d/%m %H:%M'),
                })
        
        # Métriques défauts (données exemple pour le moment)
        defects_data = {
            'labels': ['Semaine 1', 'Semaine 2', 'Semaine 3', 'Semaine 4'],
            'datasets': [{
                'label': 'Nombre de défauts',
                'data': [12, 19, 8, 15],
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            }]
        }
        
        return JsonResponse({
            'shifts': shifts_data,
            'averages': avg_data,
            'moods': mood_counts,
            'shifts_listing': shifts_listing,
            'rolls_of': rolls_of,
            'current_of': current_of.order_number if current_of else None,
            'defects': defects_data,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def calculate_trs(shift):
    """Calcule le TRS d'un poste"""
    # Temps total en minutes
    total_time = (datetime.combine(shift.date, shift.end_time) - 
                  datetime.combine(shift.date, shift.start_time)).total_seconds() / 60
    
    # Temps perdu
    lost_time = shift.lost_time_entries.aggregate(
        total=Sum('duration')
    )['total'] or 0
    
    # Temps productif
    productive_time = total_time - lost_time
    
    if total_time > 0:
        return round((productive_time / total_time) * 100, 1)
    return 0


def calculate_duration(shift):
    """Calcule la durée d'un poste en heures"""
    duration = (datetime.combine(shift.date, shift.end_time) - 
                datetime.combine(shift.date, shift.start_time)).total_seconds() / 3600
    return round(duration, 1)
