"""
Services métier pour les calculs réutilisables
"""
from datetime import datetime, timedelta
from decimal import Decimal


class MetricsCalculator:
    """Service pour calculer les métriques de production"""
    
    @staticmethod
    def calculate_to(start_time, end_time):
        """
        Calcule le Temps d'Ouverture (TO) en minutes
        
        Args:
            start_time: Heure de début (string, time object ou datetime)
            end_time: Heure de fin (string, time object ou datetime)
            
        Returns:
            int: Temps en minutes
        """
        if not start_time or not end_time:
            return 0
            
        # Normaliser en string HH:MM
        if hasattr(start_time, 'strftime'):
            start_str = start_time.strftime('%H:%M')
        else:
            start_str = str(start_time)[:5]
            
        if hasattr(end_time, 'strftime'):
            end_str = end_time.strftime('%H:%M')
        else:
            end_str = str(end_time)[:5]
        
        # Parser
        start = datetime.strptime(start_str, '%H:%M')
        end = datetime.strptime(end_str, '%H:%M')
        
        # Gérer le passage minuit
        if end < start:
            end += timedelta(days=1)
            
        return int((end - start).total_seconds() / 60)
    
    @staticmethod
    def calculate_tp(lost_times):
        """
        Calcule le Temps Perdu (TP) total
        
        Args:
            lost_times: Liste des temps perdus [{duration: int, reason: str}, ...]
            
        Returns:
            int: Temps perdu total en minutes
        """
        if not lost_times:
            return 0
        return sum(lt.get('duration', 0) for lt in lost_times)
    
    @staticmethod
    def calculate_td(to_minutes, tp_minutes):
        """
        Calcule le Temps Disponible (TD)
        
        Args:
            to_minutes: Temps d'ouverture en minutes
            tp_minutes: Temps perdu en minutes
            
        Returns:
            int: Temps disponible en minutes
        """
        return max(0, to_minutes - tp_minutes)
    
    @staticmethod
    def calculate_length_lost(tp_minutes, belt_speed_m_per_minute):
        """
        Calcule la longueur perdue
        
        Args:
            tp_minutes: Temps perdu en minutes
            belt_speed_m_per_minute: Vitesse du tapis en m/min
            
        Returns:
            float: Longueur perdue en mètres
        """
        if not tp_minutes or not belt_speed_m_per_minute:
            return 0
        return tp_minutes * float(belt_speed_m_per_minute)
    
    @staticmethod
    def calculate_trs(length_ok, target_length):
        """
        Calcule le TRS (Taux de Rendement Synthétique)
        
        Args:
            length_ok: Longueur produite OK en mètres
            target_length: Longueur cible en mètres
            
        Returns:
            float: TRS en pourcentage
        """
        if not target_length or target_length == 0:
            return 0
        return round((float(length_ok) / float(target_length)) * 100, 1)
    
    @staticmethod
    def format_minutes_to_hours(minutes):
        """
        Formate des minutes en heures:minutes
        
        Args:
            minutes: Nombre de minutes
            
        Returns:
            str: Format "Xh00" ou "Xmin"
        """
        if not minutes:
            return '--'
        
        hours = minutes // 60
        mins = minutes % 60
        
        if hours == 0:
            return f"{mins}min"
        elif mins == 0:
            return f"{hours}h"
        else:
            return f"{hours}h{mins:02d}"


class ShiftMetricsService:
    """Service complet pour les métriques d'un poste"""
    
    def __init__(self, shift_data, session_key=None):
        self.shift_data = shift_data
        self.session_key = session_key
        self.calculator = MetricsCalculator()
    
    def get_all_metrics(self):
        """Calcule toutes les métriques du poste"""
        # TO
        to = self.calculator.calculate_to(
            self.shift_data.get('start_time'),
            self.shift_data.get('end_time')
        )
        
        # TP
        tp = self.calculator.calculate_tp(
            self.shift_data.get('lost_times', [])
        )
        
        # TD
        td = self.calculator.calculate_td(to, tp)
        
        # Récupérer la vitesse du tapis depuis la session
        belt_speed = 0
        if self.session_key:
            from .models import CurrentSession
            session = CurrentSession.objects.filter(
                session_key=self.session_key
            ).first()
            if session and session.session_data.get('selected_profile'):
                # TODO: Récupérer la vitesse depuis le profil sélectionné
                # Pour l'instant on laisse à 0
                pass
        
        # Longueur perdue = TP × vitesse tapis
        length_lost = 0
        if tp > 0 and belt_speed > 0:
            length_lost = tp * belt_speed
        
        # Longueur enroulable = TD × vitesse tapis
        length_enroulable = 0
        if td > 0 and belt_speed > 0:
            length_enroulable = td * belt_speed
        
        # TRS (nécessite la longueur OK et cible)
        trs = 0
        if self.session_key:
            # À implémenter selon votre logique
            pass
        
        return {
            'to': to,
            'to_formatted': self.calculator.format_minutes_to_hours(to),
            'tp': tp,
            'tp_formatted': self.calculator.format_minutes_to_hours(tp),
            'td': td,
            'td_formatted': self.calculator.format_minutes_to_hours(td),
            'length_lost': round(length_lost),
            'length_lost_formatted': f"{round(length_lost)}m" if length_lost else "--",
            'length_enroulable': round(length_enroulable),
            'length_enroulable_formatted': f"{round(length_enroulable)}m" if length_enroulable else "--",
            'belt_speed': belt_speed,
            'trs': trs,
            'trs_formatted': f"{trs}%" if trs else "--"
        }