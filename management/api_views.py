from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from production.models import Shift, Roll
from wcm.models import ChecklistResponse
from .models import UserProfile
from .services import StatisticsService, ChecklistService
from .services.report_service import ReportService
from .serializers import (
    ShiftReportSerializer,
    ChecklistReviewSerializer,
    DashboardStatisticsSerializer
)
from .permissions import IsSuperUser


class ShiftReportViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet pour les rapports de shift."""
    queryset = Shift.objects.all()
    serializer_class = ShiftReportSerializer
    permission_classes = [IsSuperUser]
    
    def get_queryset(self):
        """Filtre les shifts avec options de tri."""
        queryset = super().get_queryset()
        
        # Filtrage par date
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Filtrage par opérateur
        operator_id = self.request.query_params.get('operator')
        if operator_id:
            queryset = queryset.filter(operator_id=operator_id)
        
        return queryset.select_related('operator', 'trs').order_by('-date', '-created_at')
    
    @action(detail=True, methods=['get'])
    def comprehensive_report(self, request, pk=None):
        """Récupère le rapport complet d'un shift."""
        try:
            data = ReportService.get_shift_comprehensive_data(pk)
            return Response(data)
        except Shift.DoesNotExist:
            return Response(
                {'error': 'Shift non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Récupère les shifts récents avec KPIs."""
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))
        
        data = ReportService.get_recent_shifts(days=days, limit=limit)
        return Response(data)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def dashboard_statistics(request):
    """API pour les statistiques du dashboard management."""
    mode = request.query_params.get('mode', 'last3')
    date_str = request.query_params.get('date')
    
    # Déterminer la date selon le mode
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    if mode == 'week':
        # Depuis le début de la semaine
        today = timezone.now().date()
        selected_date = today - timedelta(days=today.weekday())
    elif mode == 'custom' and date_str:
        # Date personnalisée (utilisée aussi pour yesterday et today)
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        # Par défaut : aujourd'hui
        selected_date = timezone.now().date()
        mode = 'custom'
    
    stats = StatisticsService.get_dashboard_statistics(selected_date, mode)
    serializer = DashboardStatisticsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def pending_checklists(request):
    """API pour récupérer les checklists en attente."""
    checklists = ChecklistService.get_pending_checklists()
    serializer = ChecklistReviewSerializer(checklists, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def all_checklists(request):
    """API pour récupérer toutes les checklists."""
    days = int(request.query_params.get('days', 7))
    checklists = ChecklistService.get_all_checklists(days=days)
    serializer = ChecklistReviewSerializer(checklists, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def sign_checklist(request, pk):
    """API pour signer une checklist avec le visa management."""
    try:
        visa = request.data.get('visa')
        if not visa:
            return Response(
                {'error': 'Le visa est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        checklist = ChecklistService.add_management_visa(
            checklist_id=pk,
            visa=visa,
            user=request.user
        )
        
        serializer = ChecklistReviewSerializer(checklist)
        return Response(serializer.data)
        
    except ChecklistResponse.DoesNotExist:
        return Response(
            {'error': 'Checklist non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsSuperUser])
def production_trends(request):
    """API pour les tendances de production."""
    days = int(request.query_params.get('days', 7))
    trends = StatisticsService._get_daily_trends(days=days)
    return Response(trends)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def operator_performance(request):
    """API pour la performance des opérateurs."""
    days = int(request.query_params.get('days', 30))
    performance = StatisticsService._get_operator_performance(days=days)
    return Response(performance)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def defects_analysis(request):
    """API pour l'analyse des défauts."""
    days = int(request.query_params.get('days', 30))
    analysis = StatisticsService._get_defects_analysis(days=days)
    return Response(analysis)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def production_alerts(request):
    """API pour les alertes de production."""
    alerts = StatisticsService._get_production_alerts()
    return Response(alerts)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def user_default_visa(request):
    """API pour récupérer le visa par défaut de l'utilisateur connecté."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        return Response({
            'default_visa': profile.default_visa,
            'username': request.user.username
        })
    except UserProfile.DoesNotExist:
        # Créer le profil s'il n'existe pas
        profile = UserProfile.objects.create(user=request.user)
        return Response({
            'default_visa': '',
            'username': request.user.username
        })


@api_view(['GET'])
@permission_classes([IsSuperUser])
def recent_rolls(request):
    """Récupère les derniers rouleaux pour le dashboard management."""
    limit = int(request.GET.get('limit', 50))
    
    # Récupérer tous les rouleaux (pas seulement ceux de la session)
    rolls = Roll.objects.all().select_related('shift__operator').prefetch_related('defects').order_by('-created_at')[:limit]
    
    data = []
    for roll in rolls:
        # Déterminer l'opérateur : depuis le shift, ou depuis shift_id_str
        if roll.shift and roll.shift.operator:
            operator = f"{roll.shift.operator.first_name} {roll.shift.operator.last_name.upper()}"
        elif roll.shift_id_str:
            # Extraire le nom de l'opérateur depuis shift_id_str (format: "DDMMYY_NomPrenom_Vacation")
            parts = roll.shift_id_str.split('_')
            operator = parts[1] if len(parts) > 1 else roll.shift_id_str
        else:
            operator = 'Sans poste'
            
        data.append({
            'id': roll.id,
            'roll_id': roll.roll_id,
            'created_at': roll.created_at,
            'length': float(roll.length) if roll.length else None,
            'operator': operator,
            'is_conform': roll.destination == 'PRODUCTION',
            'avg_thickness_left': float(roll.avg_thickness_left) if roll.avg_thickness_left else None,
            'avg_thickness_right': float(roll.avg_thickness_right) if roll.avg_thickness_right else None,
            'grammage': roll.grammage_calc,
            'shift_id': roll.shift_id_str or (roll.shift.shift_id if roll.shift else None),
            'defects_count': roll.defects.count()
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def roll_details(request, pk):
    """Récupère les détails complets d'un rouleau pour affichage dans la modale."""
    try:
        # Récupérer le rouleau avec toutes ses relations
        roll = Roll.objects.select_related(
            'shift__operator',
            'fabrication_order'
        ).prefetch_related(
            'thickness_measurements',
            'defects__defect_type'
        ).get(pk=pk)
        
        # Déterminer l'opérateur
        if roll.shift and roll.shift.operator:
            operator = f"{roll.shift.operator.first_name} {roll.shift.operator.last_name.upper()}"
        elif roll.shift_id_str:
            parts = roll.shift_id_str.split('_')
            operator = parts[1] if len(parts) > 1 else roll.shift_id_str
        else:
            operator = 'Sans poste'
        
        # Récupérer les spécifications du profil actuel
        from production.models import CurrentProfile
        thickness_spec = None
        current_profile = CurrentProfile.objects.first()
        if current_profile and current_profile.profile:
            thickness_spec = current_profile.profile.profilespecvalue_set.filter(
                spec_item__name='thickness'
            ).first()
        
        # Préparer les données d'épaisseur
        thicknesses = []
        for thickness in roll.thickness_measurements.all():
            thicknesses.append({
                'row': thickness.meter_position,
                'col': thickness.measurement_point,  # Garder GG, GC, GD, DG, DC, DD
                'value': float(thickness.thickness_value),
                'is_nok': not thickness.is_within_tolerance,
                'is_catchup': thickness.is_catchup
            })
        
        # Préparer les données de défauts
        defects = []
        for defect in roll.defects.all():
            defects.append({
                'type': defect.defect_type.name,
                'position': defect.meter_position,
                'side': defect.get_side_position_display() if defect.side_position else '',
                'severity': defect.defect_type.severity,
                'is_blocking': defect.defect_type.severity == 'blocking'
            })
        
        # Construire la réponse
        data = {
            'id': roll.id,
            'roll_id': roll.roll_id,
            'created_at': roll.created_at,
            'status': roll.status or 'CONFORME',
            'destination': roll.destination or 'PRODUCTION',
            'is_conform': roll.destination == 'PRODUCTION',
            
            # Informations générales
            'of_number': roll.fabrication_order.order_number if roll.fabrication_order else None,
            'roll_number': roll.roll_number,
            'operator': operator,
            'shift_id': roll.shift_id_str or (roll.shift.shift_id if roll.shift else None),
            
            # Dimensions et masses
            'length': float(roll.length) if roll.length else None,
            'tube_mass': float(roll.tube_mass) if roll.tube_mass else None,
            'total_mass': float(roll.total_mass) if roll.total_mass else None,
            'net_mass': float(roll.net_mass) if roll.net_mass else None,
            'grammage': roll.grammage_calc,
            
            # Épaisseurs
            'avg_thickness_left': float(roll.avg_thickness_left) if roll.avg_thickness_left else None,
            'avg_thickness_right': float(roll.avg_thickness_right) if roll.avg_thickness_right else None,
            'thicknesses': thicknesses,
            'has_thickness_issues': roll.has_thickness_issues,
            
            # Calculer min et max des épaisseurs
            'min_thickness': min([t['value'] for t in thicknesses]) if thicknesses else None,
            'max_thickness': max([t['value'] for t in thicknesses]) if thicknesses else None,
            
            # Défauts
            'defects': defects,
            'has_blocking_defects': roll.has_blocking_defects,
            
            # Spécifications pour le code couleur
            'thickness_spec': {
                'min': float(thickness_spec.min_value) if thickness_spec else None,
                'max': float(thickness_spec.max_value) if thickness_spec else None,
                'alert_min': float(thickness_spec.alert_min) if thickness_spec and thickness_spec.alert_min else None,
                'alert_max': float(thickness_spec.alert_max) if thickness_spec and thickness_spec.alert_max else None,
            } if thickness_spec else None,
            
            # Commentaire
            'comment': roll.comment
        }
        
        return Response(data)
        
    except Roll.DoesNotExist:
        return Response(
            {'error': 'Rouleau non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsSuperUser])
def shift_details(request, pk):
    """Récupère les détails complets d'un poste pour affichage dans la modale."""
    try:
        # Récupérer le poste avec toutes ses relations
        shift = Shift.objects.select_related(
            'operator'
        ).prefetch_related(
            'rolls__defects',
            'lost_time_entries__reason',
            'quality_controls'
        ).get(pk=pk)
        
        # Calculer les KPIs
        kpis = ReportService._calculate_kpis(shift)
        
        # Préparer la liste des rouleaux
        rolls = []
        for roll in shift.rolls.all().order_by('created_at'):
            rolls.append({
                'id': roll.id,
                'roll_id': roll.roll_id,
                'length': float(roll.length) if roll.length else None,
                'is_conform': roll.destination == 'PRODUCTION',
                'grammage': roll.grammage_calc,
                'defects_count': roll.defects.count(),
                'avg_thickness_left': float(roll.avg_thickness_left) if roll.avg_thickness_left else None,
                'avg_thickness_right': float(roll.avg_thickness_right) if roll.avg_thickness_right else None,
            })
        
        # Préparer les temps perdus
        lost_times = []
        total_lost_time = 0
        for entry in shift.lost_time_entries.all().order_by('-duration'):
            lost_times.append({
                'reason': entry.reason.name,
                'category': entry.reason.category,
                'duration': entry.duration,
                'comment': entry.comment
            })
            total_lost_time += entry.duration
        
        # Préparer les contrôles qualité
        quality_control = None
        if shift.quality_controls.exists():
            qc = shift.quality_controls.first()
            quality_control = {
                'micrometer_left_avg': float(qc.micrometer_left_avg) if qc.micrometer_left_avg else None,
                'micrometer_right_avg': float(qc.micrometer_right_avg) if qc.micrometer_right_avg else None,
                'dry_extract': float(qc.dry_extract) if qc.dry_extract else None,
                'loi_given': qc.loi_given
            }
        
        # Construire la réponse
        data = {
            'id': shift.id,
            'shift_id': shift.shift_id,
            'date': shift.date,
            'vacation': shift.get_vacation_display(),
            
            # Opérateur
            'operator': f"{shift.operator.first_name} {shift.operator.last_name}" if shift.operator else None,
            
            # État machine
            'started_at_beginning': shift.started_at_beginning,
            'started_at_end': shift.started_at_end,
            
            # Horaires
            'start_time': shift.start_time,
            'end_time': shift.end_time,
            
            # Production
            'total_length': float(shift.total_length) if shift.total_length else 0,
            'ok_length': float(shift.ok_length) if shift.ok_length else 0,
            'nok_length': float(shift.nok_length) if shift.nok_length else 0,
            'waste_length': float(shift.raw_waste_length) if shift.raw_waste_length else 0,
            'rolls_count': shift.rolls.count(),
            
            # KPIs
            'kpis': kpis,
            
            # Moyennes épaisseurs
            'avg_thickness_left': float(shift.avg_thickness_left_shift) if shift.avg_thickness_left_shift else None,
            'avg_thickness_right': float(shift.avg_thickness_right_shift) if shift.avg_thickness_right_shift else None,
            'avg_grammage': float(shift.avg_grammage_shift) if shift.avg_grammage_shift else None,
            
            # Détails
            'rolls': rolls,
            'lost_times': lost_times,
            'total_lost_time': total_lost_time,
            'quality_control': quality_control,
            
            # Checklist
            'checklist_signed': False,  # TODO: vérifier si checklist signée
            
            # Commentaires
            'operator_comments': shift.operator_comments,
            'manager_comments': None  # TODO: implémenter les commentaires manager
        }
        
        return Response(data)
        
    except Shift.DoesNotExist:
        return Response(
            {'error': 'Poste non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )