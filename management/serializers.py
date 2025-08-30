from rest_framework import serializers
from production.models import Shift
from wcm.models import ChecklistResponse
from planification.models import Operator


class OperatorSerializer(serializers.ModelSerializer):
    """Serializer pour les opérateurs."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Operator
        fields = ['id', 'employee_id', 'first_name', 'last_name', 'full_name']


class ShiftReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports de shift."""
    operator = OperatorSerializer(read_only=True)
    has_checklist_visa = serializers.SerializerMethodField()
    rolls_count = serializers.IntegerField(source='rolls.count', read_only=True)
    trs = serializers.SerializerMethodField()
    
    class Meta:
        model = Shift
        fields = [
            'id', 'shift_id', 'date', 'vacation',
            'operator', 'start_time', 'end_time',
            'total_length', 'ok_length', 'nok_length',
            'avg_thickness_left_shift', 'avg_thickness_right_shift',
            'avg_grammage_shift', 'has_checklist_visa', 'rolls_count', 'trs'
        ]
    
    def get_has_checklist_visa(self, obj):
        """Vérifie si la checklist a un visa management."""
        if hasattr(obj, 'checklist_response'):
            return bool(obj.checklist_response.management_visa)
        return False
    
    def get_trs(self, obj):
        """Récupère le TRS depuis le modèle TRS associé."""
        if hasattr(obj, 'trs'):
            return float(obj.trs.trs_percentage)
        return None


class ChecklistReviewSerializer(serializers.ModelSerializer):
    """Serializer pour la révision des checklists."""
    shift_id = serializers.CharField(source='shift.shift_id', read_only=True)
    shift_date = serializers.DateField(source='shift.date', read_only=True)
    shift_vacation = serializers.CharField(source='shift.vacation', read_only=True)
    operator_name = serializers.SerializerMethodField()
    nok_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ChecklistResponse
        fields = [
            'id', 'shift_id', 'shift_date', 'shift_vacation',
            'operator_name', 'operator_signature', 'operator_signature_date',
            'management_visa', 'management_visa_date',
            'nok_count', 'completion_rate', 'created_at'
        ]
    
    def get_nok_count(self, obj):
        """Compte le nombre de réponses NOK."""
        return sum(1 for response in obj.responses.values() if response == 'nok')
    
    def get_operator_name(self, obj):
        """Retourne le nom complet de l'opérateur."""
        if obj.operator:
            return f"{obj.operator.first_name} {obj.operator.last_name}"
        return 'N/A'
    
    def get_completion_rate(self, obj):
        """Calcule le taux de complétion."""
        # Une checklist sauvegardée est toujours complète à 100%
        # car elle contient uniquement les items qui étaient actifs au moment du remplissage
        return 100.0


class DashboardStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du dashboard."""
    current_kpis = serializers.DictField()
    daily_trends = serializers.ListField()
    weekly_comparison = serializers.DictField()
    monthly_stats = serializers.DictField()
    operator_performance = serializers.ListField()
    defects_analysis = serializers.DictField()
    alerts = serializers.ListField()
    mood_data = serializers.DictField()