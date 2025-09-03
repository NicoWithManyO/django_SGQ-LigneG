from django.db.models import Avg, Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from production.models import Shift, Roll
from quality.models import Controls, RollDefect
from wcm.models import LostTimeEntry


class ReportService:
    """Service pour la génération et l'analyse des rapports de production."""
    
    @staticmethod
    def get_shift_comprehensive_data(shift_id):
        """
        Récupère toutes les données d'un shift pour un rapport complet.
        
        Args:
            shift_id: ID du shift
            
        Returns:
            dict: Données complètes du shift avec KPIs calculés
        """
        shift = Shift.objects.select_related(
            'operator',
            'checklist_response'
        ).prefetch_related(
            'rolls',
            'lost_time_entries__reason',
            'quality_controls',
            'rolls__defects__defect_type'
        ).get(pk=shift_id)
        
        return {
            'shift': shift,
            'kpis': ReportService._calculate_kpis(shift),
            'production_stats': ReportService._get_production_statistics(shift),
            'quality_stats': ReportService._get_quality_statistics(shift),
            'defects_summary': ReportService._get_defects_summary(shift),
            'lost_time_summary': ReportService._get_lost_time_summary(shift),
            'rolls_details': ReportService._get_rolls_details(shift),
            'operator_comments': shift.operator_comments
        }
    
    @staticmethod
    def _calculate_kpis(shift):
        """
        Calcule les KPIs principaux du shift.
        
        Returns:
            dict: TRS, disponibilité, performance, qualité
        """
        # Essayer de récupérer le TRS pré-calculé
        if hasattr(shift, 'trs'):
            trs_obj = shift.trs
            return {
                'trs': float(trs_obj.trs_percentage),
                'availability': float(trs_obj.availability_percentage),
                'performance': float(trs_obj.performance_percentage),
                'quality': float(trs_obj.quality_percentage),
                'opening_time': round(trs_obj.opening_time.total_seconds() / 60, 0),
                'available_time': round(trs_obj.availability_time.total_seconds() / 60, 0),
                'lost_time': round(trs_obj.lost_time.total_seconds() / 60, 0)
            }
        
        # Fallback sur le calcul actuel pour les anciens shifts
        # Temps d'ouverture en minutes
        if shift.start_time and shift.end_time:
            start_datetime = timezone.datetime.combine(shift.date, shift.start_time)
            end_datetime = timezone.datetime.combine(shift.date, shift.end_time)
            # Gérer le cas où la fin est le lendemain
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
            opening_time = (end_datetime - start_datetime).total_seconds() / 60
        else:
            opening_time = 480  # 8h par défaut
        
        # Temps disponible
        lost_time_total = shift.lost_time_entries.aggregate(
            total=Sum('duration')
        )['total'] or 0
        available_time = opening_time - lost_time_total
        
        # Disponibilité
        availability = (available_time / opening_time * 100) if opening_time > 0 else 0
        
        # Performance (production réelle vs théorique)
        # Si pas de temps perdu, on considère une performance de 100%
        # Sinon on calcule en fonction de la production
        actual_production = float(shift.total_length or 0)
        if actual_production > 0 and available_time > 0:
            # Calculer une vitesse théorique basée sur les données réelles
            # On considère qu'une bonne performance est de 5m/min
            theoretical_speed = 5  # m/min plus réaliste
            theoretical_production = available_time * theoretical_speed
            performance = min(100, (actual_production / theoretical_production * 100))
        else:
            performance = 0
        
        # Qualité
        ok_length = float(shift.ok_length or 0)
        total_length = float(shift.total_length or 0)
        quality = (ok_length / total_length * 100) if total_length > 0 else 0
        
        # TRS
        trs = (availability * performance * quality) / 10000
        
        return {
            'trs': round(trs, 1),
            'availability': round(availability, 1),
            'performance': round(performance, 1),
            'quality': round(quality, 1),
            'opening_time': round(opening_time, 0),
            'available_time': round(available_time, 0),
            'lost_time': lost_time_total
        }
    
    @staticmethod
    def _get_production_statistics(shift):
        """Statistiques de production du shift."""
        rolls = shift.rolls.all()
        
        return {
            'total_rolls': rolls.count(),
            'conforming_rolls': rolls.filter(status='CONFORME').count(),
            'non_conforming_rolls': rolls.filter(status='NON_CONFORME').count(),
            'total_length': shift.total_length or 0,
            'ok_length': shift.ok_length or 0,
            'nok_length': shift.nok_length or 0,
            'waste_length': shift.raw_waste_length or 0,
            'avg_thickness_left': shift.avg_thickness_left_shift or 0,
            'avg_thickness_right': shift.avg_thickness_right_shift or 0,
            'avg_grammage': shift.avg_grammage_shift or 0
        }
    
    @staticmethod
    def _get_quality_statistics(shift):
        """Statistiques qualité du shift."""
        controls = shift.quality_controls.first()
        
        if not controls:
            return None
            
        return {
            'micrometer_left_avg': controls.micrometer_left_avg,
            'micrometer_right_avg': controls.micrometer_right_avg,
            'dry_extract': controls.dry_extract,
            'surface_mass_left_avg': controls.surface_mass_left_avg,
            'surface_mass_right_avg': controls.surface_mass_right_avg,
            'loi_given': controls.loi_given,
            'is_valid': controls.is_valid
        }
    
    @staticmethod
    def _get_defects_summary(shift):
        """Résumé des défauts par type."""
        defects = RollDefect.objects.filter(
            roll__shift=shift
        ).values(
            'defect_type__name',
            'defect_type__severity'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'total_defects': sum(d['count'] for d in defects),
            'by_type': list(defects),
            'blocking_count': sum(
                d['count'] for d in defects 
                if d['defect_type__severity'] == 'blocking'
            )
        }
    
    @staticmethod
    def _get_lost_time_summary(shift):
        """Résumé des temps perdus par catégorie."""
        lost_times = shift.lost_time_entries.values(
            'reason__category',
            'reason__name'
        ).annotate(
            total_duration=Sum('duration')
        ).order_by('-total_duration')
        
        return {
            'total_duration': sum(lt['total_duration'] for lt in lost_times),
            'by_reason': list(lost_times),
            'count': shift.lost_time_entries.count()
        }
    
    @staticmethod
    def _get_rolls_details(shift):
        """Détails des rouleaux du shift."""
        rolls = shift.rolls.select_related(
            'fabrication_order'
        ).prefetch_related(
            'defects__defect_type'
        ).order_by('created_at')
        
        rolls_data = []
        for roll in rolls:
            rolls_data.append({
                'roll_id': roll.roll_id,
                'roll_number': roll.roll_number,
                'of_number': roll.fabrication_order.order_number if roll.fabrication_order else None,
                'length': roll.length,
                'grammage': roll.grammage_calc,
                'status': roll.status,
                'destination': roll.destination,
                'defects_count': roll.defects.count(),
                'has_blocking_defects': roll.has_blocking_defects,
                'avg_thickness_left': roll.avg_thickness_left,
                'avg_thickness_right': roll.avg_thickness_right
            })
        
        return rolls_data
    
    @staticmethod
    def get_recent_shifts(days=7, limit=10):
        """
        Récupère les shifts récents avec leurs KPIs principaux.
        
        Args:
            days: Nombre de jours à regarder en arrière
            limit: Nombre maximum de shifts à retourner
        """
        since_date = timezone.now().date() - timedelta(days=days)
        
        shifts = Shift.objects.filter(
            date__gte=since_date
        ).select_related(
            'operator',
            'checklist_response'
        ).order_by('-date', '-created_at')[:limit]
        
        shifts_data = []
        for shift in shifts:
            kpis = ReportService._calculate_kpis(shift)
            shifts_data.append({
                'id': shift.id,
                'shift_id': shift.shift_id,
                'date': shift.date,
                'vacation': shift.vacation,
                'operator': f"{shift.operator.first_name} {shift.operator.last_name}" if shift.operator else 'N/A',
                'trs': kpis['trs'],
                'total_length': float(shift.total_length) if shift.total_length else 0,
                'nok_length': float(shift.nok_length) if shift.nok_length else 0,
                'waste_length': float(shift.raw_waste_length) if shift.raw_waste_length else 0,
                'has_comment': bool(shift.operator_comments),
                'started_at_beginning': shift.started_at_beginning,
                'started_at_end': shift.started_at_end,
                'checklist_signed': bool(shift.checklist_response.management_visa) if hasattr(shift, 'checklist_response') else False
            })
        
        return shifts_data