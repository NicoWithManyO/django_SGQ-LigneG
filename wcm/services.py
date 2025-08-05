from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

from production.models import CurrentProfile
from .models import TRS


def calculate_and_create_trs(shift, production_totals=None):
    """
    Calcule et crée ou met à jour l'objet TRS pour un shift.
    Réutilise la logique de ReportService mais avec la vraie vitesse du profil.
    
    Args:
        shift: Instance de Shift avec toutes ses données
        production_totals: Dict optionnel avec les totaux de production
                          (total_length, ok_length, nok_length, raw_waste_length)
        
    Returns:
        TRS: L'objet TRS créé ou mis à jour
    """
    # Récupérer le profil actuel
    current_profile = CurrentProfile.objects.first()
    
    if current_profile and current_profile.profile:
        belt_speed = float(current_profile.profile.belt_speed_m_per_minute or 5.0)
        profile_name = current_profile.profile.name
    else:
        belt_speed = 5.0  # Fallback
        profile_name = "Par défaut"
    
    # Calculer le temps d'ouverture
    if shift.start_time and shift.end_time:
        start_datetime = timezone.datetime.combine(shift.date, shift.start_time)
        end_datetime = timezone.datetime.combine(shift.date, shift.end_time)
        
        # Gérer le cas où la fin est le lendemain (vacation Nuit)
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)
        
        opening_time = end_datetime - start_datetime
    else:
        opening_time = timedelta(hours=8)  # 8h par défaut
    
    # Convertir les timings en minutes pour les calculs
    opening_time_minutes = opening_time.total_seconds() / 60
    
    # Temps disponible (déjà calculé dans shift)
    if shift.availability_time:
        available_time_minutes = shift.availability_time.total_seconds() / 60
    else:
        available_time_minutes = opening_time_minutes  # Si pas de temps perdu
    
    # Temps perdu (déjà calculé dans shift)
    if shift.lost_time:
        lost_time_minutes = shift.lost_time.total_seconds() / 60
    else:
        lost_time_minutes = 0
    
    # === CALCUL DES MÉTRIQUES TRS ===
    
    # 1. Disponibilité (%)
    if opening_time_minutes > 0:
        availability = (available_time_minutes / opening_time_minutes) * 100
    else:
        availability = 0
    
    # 2. Performance (%)
    # Utiliser les totaux fournis (qui incluent déjà la production enroulée)
    if production_totals:
        actual_production = float(production_totals.get('total_length', 0))
        ok_length = float(production_totals.get('ok_length', 0))
        nok_length = float(production_totals.get('nok_length', 0))
        raw_waste_length = float(production_totals.get('raw_waste_length', 0))
    else:
        # Fallback: calculer depuis les rouleaux du shift
        from production.models import Roll
        from production.services import shift_service
        rolls = Roll.objects.filter(shift=shift)
        production_totals = shift_service.calculate_production_totals(rolls, shift)
        actual_production = float(production_totals.get('total_length', 0))
        ok_length = float(production_totals.get('ok_length', 0))
        nok_length = float(production_totals.get('nok_length', 0))
        raw_waste_length = float(production_totals.get('raw_waste_length', 0))
    
    if actual_production > 0 and available_time_minutes > 0:
        # Production théorique = temps disponible × vitesse tapis
        theoretical_production = available_time_minutes * belt_speed
        performance = min(100, (actual_production / theoretical_production) * 100)
    else:
        theoretical_production = 0
        performance = 0
    
    # 3. Qualité (%)
    if actual_production > 0:
        quality = (ok_length / actual_production) * 100
    else:
        quality = 0
    
    # 4. TRS (%)
    trs = (availability * performance * quality) / 10000
    
    # Préparer les données TRS
    trs_data = {
        # Temps
        'opening_time': opening_time,
        'availability_time': shift.availability_time or timedelta(0),
        'lost_time': shift.lost_time or timedelta(0),
        # Production
        'total_length': actual_production,
        'ok_length': ok_length,
        'nok_length': nok_length,
        'raw_waste_length': raw_waste_length,
        # Métriques calculées
        'trs_percentage': round(trs, 1),
        'availability_percentage': round(availability, 1),
        'performance_percentage': round(performance, 1),
        'quality_percentage': round(quality, 1),
        'theoretical_production': round(theoretical_production, 2),
        # Profil
        'profile_name': profile_name,
        'belt_speed_m_per_min': belt_speed
    }
    
    # Créer ou mettre à jour l'objet TRS
    trs_obj, created = TRS.objects.update_or_create(
        shift=shift,
        defaults=trs_data
    )
    
    return trs_obj