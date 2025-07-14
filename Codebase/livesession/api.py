"""
API DRF unifiée pour la gestion de session de production
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.core.serializers.json import DjangoJSONEncoder
from .models import CurrentSession
from .serializers import CurrentSessionSerializer
from production.models import Shift, Roll, LostTimeEntry, QualityControl, RollDefect, RollThickness
from wcm.models import ChecklistResponse
from core.models import MoodCounter
from datetime import datetime, time


class DecimalJSONRenderer(JSONRenderer):
    encoder_class = DjangoJSONEncoder


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def current_session(request):
    """
    API unifiée pour toute la session de production
    
    GET: Récupère l'état complet de la session
    PATCH: Met à jour n'importe quelle partie de la session
    DELETE: Réinitialise la session (après sauvegarde d'un poste)
    """
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    if request.method == 'GET':
        # Récupérer ou créer le draft de session
        draft, created = CurrentSession.objects.get_or_create(
            session_key=session_key,
            defaults={'session_data': {}}
        )
        
        # Utiliser le serializer pour formater la réponse
        serializer = CurrentSessionSerializer(
            instance={'draft': draft},
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        # Récupérer ou créer les objets
        draft, _ = CurrentSession.objects.get_or_create(
            session_key=session_key,
            defaults={'session_data': {}}
        )
        
        # Passer au serializer pour validation et sauvegarde
        serializer = CurrentSessionSerializer(
            instance={'draft': draft},
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(
                {
                    'errors': serializer.errors,
                    'data': serializer.data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    elif request.method == 'DELETE':
        # Réinitialiser seulement le draft (pas l'état persistant)
        CurrentSession.objects.filter(session_key=session_key).delete()
        
        return Response({'message': 'Session réinitialisée'})


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def save_shift(request):
    """
    Sauvegarde le shift en cours et réinitialise intelligemment la session
    
    POST: Crée un nouveau Shift avec toutes les données associées
    Retourne le nouvel état de la session après réinitialisation
    """
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        return Response(
            {'error': 'Aucune session active'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session_key = request.session.session_key
    
    # Récupérer la session courante
    try:
        draft = CurrentSession.objects.get(session_key=session_key)
    except CurrentSession.DoesNotExist:
        return Response(
            {'error': 'Aucune donnée de session trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    session_data = draft.session_data
    
    # Validation des données requises
    required_fields = ['operator', 'date', 'vacation', 'start_time', 'end_time']
    missing_fields = [field for field in required_fields if not session_data.get(field)]
    
    if missing_fields:
        return Response(
            {'error': f'Champs requis manquants: {", ".join(missing_fields)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 1. Créer le Shift
        shift = create_shift_from_session(session_data)
        
        # 2. Associer les temps perdus
        if session_data.get('lost_times'):
            create_lost_time_entries(shift, session_data['lost_times'])
        
        # 3. Associer les contrôles qualité
        if session_data.get('quality_controls'):
            create_quality_controls(shift, session_data['quality_controls'])
        
        # 4. Associer les réponses de checklist
        if session_data.get('checklist_responses'):
            create_checklist_responses(shift, session_data['checklist_responses'])
        
        # 5. Associer les rouleaux déjà sauvegardés au shift
        link_rolls_to_shift(shift, session_key)
        
        # 6. Réinitialiser intelligemment la session
        new_session_data = reset_session_after_save(session_data)
        draft.session_data = new_session_data
        draft.save()
        
        # 7. Retourner le nouvel état complet
        serializer = CurrentSessionSerializer(
            instance={'draft': draft},
            context={'request': request}
        )
        
        return Response({
            'shift_id': shift.shift_id,
            'message': 'Poste enregistré avec succès',
            'session': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la sauvegarde: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def create_shift_from_session(session_data):
    """Crée un objet Shift à partir des données de session"""
    
    # Convertir la date string en objet date
    from datetime import date as date_type
    date_str = session_data['date']
    if isinstance(date_str, str):
        # Format attendu: YYYY-MM-DD
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        date_obj = date_str
    
    # Convertir les heures string en objets time
    start_time_str = session_data['start_time']
    end_time_str = session_data['end_time']
    
    if isinstance(start_time_str, str):
        # Gérer les formats HH:MM ou HH:MM:SS
        try:
            start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            start_time_obj = datetime.strptime(start_time_str, '%H:%M:%S').time()
    else:
        start_time_obj = start_time_str
        
    if isinstance(end_time_str, str):
        # Gérer les formats HH:MM ou HH:MM:SS
        try:
            end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            end_time_obj = datetime.strptime(end_time_str, '%H:%M:%S').time()
    else:
        end_time_obj = end_time_str
    
    shift_data = {
        'operator_id': session_data['operator'],
        'date': date_obj,
        'vacation': session_data['vacation'],
        'start_time': start_time_obj,
        'end_time': end_time_obj,
        'started_at_beginning': session_data.get('started_at_beginning', False),
        'meter_reading_start': session_data.get('meter_reading_start'),
        'started_at_end': session_data.get('started_at_end', False),
        'meter_reading_end': session_data.get('meter_reading_end'),
        'operator_comments': session_data.get('operator_comments', ''),
    }
    
    # Ajouter le shift_id s'il existe dans la session
    if session_data.get('shift_id'):
        shift_data['shift_id'] = session_data['shift_id']
    
    # Ajouter les données de checklist
    if session_data.get('checklist_signature'):
        signature_data = session_data['checklist_signature']
        shift_data['checklist_signed'] = signature_data.get('signature', '')
        if signature_data.get('time'):
            try:
                # Convertir le format ISO en time
                dt = datetime.fromisoformat(signature_data['time'].replace('Z', '+00:00'))
                shift_data['checklist_signed_time'] = dt.time()
            except:
                pass
    
    # Calculer les longueurs totales depuis les métriques
    metrics = session_data.get('metrics', {})
    if metrics:
        # Les longueurs viennent des métriques calculées
        shift_data['total_length'] = metrics.get('length_enroulable', 0) + metrics.get('length_lost', 0)
        # TODO: Calculer ok_length et nok_length depuis les rouleaux
    
    return Shift.objects.create(**shift_data)


def create_lost_time_entries(shift, lost_times):
    """Crée les entrées de temps perdu pour le shift"""
    from wcm.models import LostTimeReason
    
    for entry in lost_times:
        # Récupérer le nom du motif depuis l'ID
        motif_name = "Inconnu"
        if entry.get('reason'):
            try:
                reason = LostTimeReason.objects.get(pk=entry['reason'])
                motif_name = reason.name
            except LostTimeReason.DoesNotExist:
                pass
        
        LostTimeEntry.objects.create(
            shift=shift,
            motif=motif_name,
            duration=entry['duration'],
            comment=entry.get('comment', '')
        )


def create_quality_controls(shift, quality_controls):
    """Crée les contrôles qualité pour le shift"""
    qc_data = {
        'shift': shift,
        'created_by': shift.operator,  # Remplir automatiquement avec l'opérateur du poste
        'micrometer_left_1': quality_controls.get('micronnaire_left_1'),
        'micrometer_left_2': quality_controls.get('micronnaire_left_2'),
        'micrometer_left_3': quality_controls.get('micronnaire_left_3'),
        'micrometer_right_1': quality_controls.get('micronnaire_right_1'),
        'micrometer_right_2': quality_controls.get('micronnaire_right_2'),
        'micrometer_right_3': quality_controls.get('micronnaire_right_3'),
        'dry_extract': quality_controls.get('extrait_sec'),
        'dry_extract_time': quality_controls.get('extrait_sec_time'),
        'surface_mass_gg': quality_controls.get('surface_mass_gg'),
        'surface_mass_gc': quality_controls.get('surface_mass_gc'),
        'surface_mass_dc': quality_controls.get('surface_mass_dc'),
        'surface_mass_dd': quality_controls.get('surface_mass_dd'),
        'loi_given': quality_controls.get('loi_given', False),
        'loi_time': quality_controls.get('loi_time'),
    }
    
    # Retirer les None values
    qc_data = {k: v for k, v in qc_data.items() if v is not None}
    
    if len(qc_data) > 1:  # Plus que juste 'shift'
        QualityControl.objects.create(**qc_data)


def create_checklist_responses(shift, checklist_responses):
    """Crée les réponses de checklist pour le shift"""
    for item_id, response in checklist_responses.items():
        if response in ['ok', 'nok']:  # Ignorer 'na'
            # Extraire l'ID numérique de la chaîne (format: "item-15" ou "item_15")
            numeric_id = item_id.replace('item-', '').replace('item_', '')
            try:
                numeric_id = int(numeric_id)
                ChecklistResponse.objects.create(
                    shift=shift,
                    item_id=numeric_id,
                    response=response
                )
            except ValueError:
                # Si ce n'est pas un nombre valide, on ignore
                continue


def link_rolls_to_shift(shift, session_key):
    """Associe les rouleaux déjà sauvegardés au shift"""
    # Chercher les rouleaux orphelins de cette session
    orphan_rolls = Roll.objects.filter(
        session_key=session_key,
        shift__isnull=True
    )
    
    if orphan_rolls.exists():
        count = orphan_rolls.count()
        # Lier les rouleaux au shift et effacer la session_key
        orphan_rolls.update(shift=shift, shift_id_str=shift.shift_id, session_key=None)
        print(f"Lié {count} rouleaux orphelins au shift {shift.shift_id}")
        
        # Recalculer les moyennes du shift
        shift.calculate_roll_averages()
        
        # Recalculer les longueurs totales
        total_length = 0
        ok_length = 0 
        nok_length = 0
        
        for roll in shift.rolls.all():
            total_length += float(roll.length or 0)
            if roll.status == 'CONFORME':
                ok_length += float(roll.length or 0)
            elif roll.status == 'NON_CONFORME':
                nok_length += float(roll.length or 0)
        
        shift.total_length = total_length
        shift.ok_length = ok_length
        shift.nok_length = nok_length
        
        shift.save(update_fields=['avg_thickness_left_shift', 'avg_thickness_right_shift', 
                                 'avg_grammage_shift', 'total_length', 'ok_length', 'nok_length'])




def reset_session_after_save(current_data):
    """
    Réinitialise intelligemment la session après sauvegarde
    Garde certaines données persistantes
    """
    
    # Champs à conserver
    keep_fields = [
        'current_of', 'cutting_of', 'target_length', 'selected_profile',
        'roll_number', 'active_modes', 'belt_speed'
    ]
    
    # Créer la nouvelle session avec les données à garder
    new_data = {field: current_data.get(field) for field in keep_fields if field in current_data}
    
    # Conserver aussi les infos du rouleau en cours (sticky)
    if current_data.get('current_roll') and current_data['current_roll'].get('info'):
        new_data['current_roll'] = {
            'info': {
                'tube_mass': current_data['current_roll']['info'].get('tube_mass', ''),
                'next_tube_mass': current_data['current_roll']['info'].get('next_tube_mass', ''),
                'total_mass': current_data['current_roll']['info'].get('total_mass', ''),
                'roll_length': current_data['current_roll']['info'].get('roll_length', '')
            }
        }
    
    # Reporter l'état de fin de poste au début du nouveau poste
    if current_data.get('started_at_end'):
        new_data['started_at_beginning'] = True
        new_data['meter_reading_start'] = current_data.get('meter_reading_end')
    else:
        new_data['started_at_beginning'] = False
        new_data['meter_reading_start'] = None
    
    # Calculer la vacation suivante et les heures par défaut
    vacation_map = {
        'Matin': ('ApresMidi', '12:00', '20:00'),
        'ApresMidi': ('Nuit', '20:00', '04:00'),
        'Nuit': ('Matin', '04:00', '12:00'),
        'Journee': ('Matin', '04:00', '12:00')  # Après journée, on revient au matin
    }
    
    current_vacation = current_data.get('vacation')
    next_vacation, default_start, default_end = vacation_map.get(current_vacation, ('Matin', '04:00', '12:00'))
    
    # Mettre la date à aujourd'hui (ou demain si on était en poste de nuit)
    from datetime import date, timedelta
    if current_vacation == 'Nuit':
        # Si on sauve un poste de nuit, on passe au jour suivant
        next_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        next_date = date.today().strftime('%Y-%m-%d')
    
    # Réinitialiser tous les autres champs
    new_data.update({
        'operator': None,
        'date': next_date,  # Date du jour (ou +1 si nuit)
        'vacation': next_vacation,  # Vacation suivante
        'start_time': default_start,  # Heure de début par défaut
        'end_time': default_end,  # Heure de fin par défaut
        'started_at_end': True,  # Par défaut on suppose que la machine continue
        'meter_reading_end': None,
        'lost_times': [],
        'checklist_responses': {},
        'checklist_signature': {},
        'quality_controls': {},
        # current_roll est déjà géré plus haut pour conserver les valeurs sticky
        'operator_comments': '',
        'shift_id': None,
    })
    
    return new_data


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def save_roll(request):
    """
    Sauvegarde un rouleau terminé en base de données
    
    POST: Crée un nouveau Roll avec toutes les données associées
    Attend toutes les données nécessaires dans request.data
    """
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        return Response(
            {'error': 'Aucune session active'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session_key = request.session.session_key
    
    # Récupérer la session courante
    try:
        current_session = CurrentSession.objects.get(session_key=session_key)
    except CurrentSession.DoesNotExist:
        return Response(
            {'error': 'Aucune session active trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Récupérer les données depuis la session (source de vérité)
    session_data = current_session.session_data
    current_roll = session_data.get('current_roll', {})
    
    # Données du rouleau depuis la session
    roll_info = current_roll.get('info', {})
    defects = current_roll.get('defects', [])
    thickness_data = current_roll.get('thickness', {})
    
    # Status et destination depuis la requête (choix utilisateur au moment du save)
    roll_status = request.data.get('status')
    destination = request.data.get('destination')
    
    # Contexte depuis la session
    context = {
        'current_of': session_data.get('current_of'),
        'cutting_of': session_data.get('cutting_of')
    }
    
    # Validation des champs requis
    required_fields = ['roll_number', 'length', 'tube_mass', 'total_mass']
    missing_fields = [field for field in required_fields if not roll_info.get(field)]
    
    if missing_fields:
        return Response(
            {'error': f'Champs requis manquants: {", ".join(missing_fields)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Récupérer le shift_id depuis la session déjà chargée
        shift_id = session_data.get('shift_id')
        
        # 1. Générer l'ID du rouleau
        roll_id = generate_roll_id_from_data(context, roll_info, roll_status)
        
        # 2. Créer le rouleau
        roll = Roll.objects.create(
            roll_id=roll_id,
            session_key=session_key,
            shift_id_str=shift_id,  # Utiliser le shift_id de la session
            fabrication_order_id=context.get('current_of') if roll_status == 'CONFORME' else context.get('cutting_of'),
            roll_number=int(roll_info['roll_number']),
            length=float(roll_info['length']),
            tube_mass=float(roll_info['tube_mass']),
            total_mass=float(roll_info['total_mass']),
            status=roll_status,
            destination=destination,
            comment=roll_info.get('comment', '')
        )
        
        # 3. Ajouter les défauts
        if defects:
            create_roll_defects(roll, defects)
        
        # 4. Ajouter les mesures d'épaisseur
        if thickness_data:
            create_thickness_measurements(roll, thickness_data)
        
        # 5. Calculer les moyennes d'épaisseur et sauvegarder
        roll.calculate_thickness_averages()
        roll.save()
        
        # 6. Mettre à jour l'état de la session
        # Incrémenter le numéro de rouleau SEULEMENT si CONFORME
        if roll_status == 'CONFORME':
            current_session.session_data['roll_number'] = int(roll_info['roll_number']) + 1
        # Si NON CONFORME, on garde le même numéro
        
        # Réinitialiser les données du rouleau actuel
        # Récupérer next_tube_mass depuis current_roll.info (où il est stocké)
        current_roll_info = current_session.session_data.get('current_roll', {}).get('info', {})
        next_tube_mass = current_roll_info.get('next_tube_mass', '')
        
        # Si pas trouvé dans current_roll, essayer au niveau racine (pour compatibilité)
        if not next_tube_mass:
            next_tube_mass = current_session.session_data.get('next_tube_mass', '')
        
        target_length = current_session.session_data.get('target_length', '')  # Récupérer la longueur cible
        
        current_session.session_data['current_roll'] = {
            'info': {
                'roll_number': current_session.session_data.get('roll_number', 1),
                'length': str(target_length) if target_length else '',  # Remettre la longueur cible
                'tube_mass': next_tube_mass,  # Passer la masse du tube suivant
                'total_mass': '',
                'next_tube_mass': '',  # Vider next_tube_mass
                'comment': ''
            },
            'defects': [],
            'thickness': {
                'measurements': [],
                'rattrapage': []
            }
        }
        
        # Effacer next_tube_mass du niveau supérieur aussi
        current_session.session_data['next_tube_mass'] = ''
        
        # 6b. Calculer et mettre à jour les métriques de production
        update_production_metrics(current_session, roll, session_key)
        
        # Sauvegarder la session mise à jour
        current_session.save()
        
        # 7. Retourner l'état complet avec les métriques calculées
        serializer = CurrentSessionSerializer(
            instance={'draft': current_session},
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'roll_id': roll.roll_id,
            'status': roll.status,
            'destination': roll.destination,
            'session': serializer.data  # État complet de la session
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la sauvegarde: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def generate_roll_id_from_data(context, roll_info, status):
    """Génère l'ID du rouleau selon le format approprié à partir des données reçues"""
    if status == 'NON_CONFORME':
        # Format pour non conforme: OFDecoupe_JJMMAA_HHMM
        from datetime import datetime
        from core.models import FabricationOrder
        
        # Récupérer le numéro de l'OF de découpe
        cutting_of_id = context.get('cutting_of')
        of_decoupe_number = 'OFDecoupe'  # Valeur par défaut
        
        if cutting_of_id:
            try:
                cutting_of = FabricationOrder.objects.get(pk=cutting_of_id)
                of_decoupe_number = cutting_of.order_number
            except:
                pass
        
        now = datetime.now()
        date_str = now.strftime('%d%m%y')
        time_str = now.strftime('%H%M')
        return f"{of_decoupe_number}_{date_str}_{time_str}"
    else:
        # Format pour conforme: OF_NumRouleau
        of_number = context.get('current_of')
        roll_number = roll_info['roll_number']
        if of_number:
            # Récupérer l'objet OF pour avoir le numéro
            from core.models import FabricationOrder
            try:
                of = FabricationOrder.objects.get(pk=of_number)
                return f"{of.order_number}_{int(roll_number):03d}"
            except:
                pass
        # Fallback
        return f"OF_TEMP_{int(roll_number):03d}"


def determine_roll_destination(status):
    """Détermine la destination en fonction du statut"""
    if status == 'CONFORME':
        return 'PRODUCTION'
    else:
        return 'DECOUPE'




def create_roll_defects(roll, defects_data):
    """Crée les défauts associés au rouleau"""
    from quality.models import DefectType
    
    for defect_dict in defects_data:
        # Récupérer le type de défaut
        defect_type_id = defect_dict.get('type_id')
        if defect_type_id:
            try:
                defect_type = DefectType.objects.get(pk=defect_type_id)
                defect_name = defect_type.name
            except:
                defect_name = defect_dict.get('defect_name', 'Défaut inconnu')
        else:
            defect_name = defect_dict.get('defect_name', 'Défaut inconnu')
        
        # Mapper les positions
        position_map = {
            'G': 'left',
            'C': 'center', 
            'D': 'right'
        }
        position_side = position_map.get(defect_dict.get('position_side', ''), 'center')
        
        RollDefect.objects.create(
            roll=roll,
            defect_name=defect_name,
            meter_position=defect_dict.get('position_m', 0),
            side_position=position_side
        )


def create_thickness_measurements(roll, thickness_data):
    """Crée les mesures d'épaisseur associées au rouleau"""
    
    # Mesures normales
    for measurement in thickness_data.get('measurements', []):
        RollThickness.objects.create(
            roll=roll,
            meter_position=measurement['position_m'],
            measurement_point=measurement['measurement_point'],
            thickness_value=measurement['thickness_value'],
            is_catchup=False
        )
    
    # Mesures de rattrapage
    for rattrapage in thickness_data.get('rattrapage', []):
        # Enlever le suffixe -R du point de mesure
        point = rattrapage['measurement_point'].replace('-R', '')
        RollThickness.objects.create(
            roll=roll,
            meter_position=rattrapage['position_m'],
            measurement_point=point,
            thickness_value=rattrapage['thickness_value'],
            is_catchup=True
        )


def update_production_metrics(current_session, new_roll, session_key):
    """
    Met à jour les métriques de production après sauvegarde d'un rouleau
    
    Pour le premier rouleau, on soustrait le métrage de début
    """
    from production.models import Roll
    
    # Récupérer tous les rouleaux de cette session
    session_rolls = Roll.objects.filter(session_key=session_key)
    
    # Calculer les longueurs par statut
    total_length = 0
    ok_length = 0
    nok_length = 0
    waste_length = 0
    
    for roll in session_rolls:
        length = float(roll.length or 0)
        total_length += length
        
        if roll.status == 'CONFORME':
            ok_length += length
        elif roll.status == 'NON_CONFORME':
            nok_length += length
        elif roll.destination == 'DECHETS':
            waste_length += length
    
    # Pour le premier rouleau, ajuster avec le métrage de début
    if session_rolls.count() == 1:
        meter_reading_start = current_session.session_data.get('meter_reading_start', 0)
        if meter_reading_start:
            # La production réelle doit soustraire ce qui était déjà enroulé
            adjustment = float(meter_reading_start)
            total_length = max(0, total_length - adjustment)
            # Ajuster selon le statut du premier rouleau
            if new_roll.status == 'CONFORME':
                ok_length = max(0, ok_length - adjustment)
            elif new_roll.status == 'NON_CONFORME':
                nok_length = max(0, nok_length - adjustment)
            elif new_roll.destination == 'DECHETS':
                waste_length = max(0, waste_length - adjustment)
    
    # Mettre à jour la session
    current_session.session_data['total_length'] = total_length
    current_session.session_data['ok_length'] = ok_length
    current_session.session_data['nok_length'] = nok_length
    current_session.session_data['waste_length'] = waste_length


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def check_shift_id(request, shift_id):
    """
    Vérifie si un shift_id existe déjà dans la base de données
    
    GET: Retourne {'exists': True/False}
    """
    exists = Shift.objects.filter(shift_id=shift_id).exists()
    return Response({'exists': exists})


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def check_roll_id(request, roll_id):
    """
    Vérifie si un roll_id existe déjà dans la base de données
    
    GET: Retourne {'exists': True/False}
    """
    exists = Roll.objects.filter(roll_id=roll_id).exists()
    return Response({'exists': exists})


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def clear_production_data(request):
    """
    Vide les données de production de la base de données
    - Rouleaux (Roll, RollDefect, RollThickness)
    - Postes (Shift, LostTimeEntry)
    - Contrôles qualité (QualityControl)
    - Réponses checklist (ChecklistResponse)
    """
    try:
        # Compter avant suppression pour le rapport
        counts = {
            'rolls': Roll.objects.count(),
            'shifts': Shift.objects.count(),
            'quality_controls': QualityControl.objects.count(),
            'checklist_responses': ChecklistResponse.objects.count(),
            'roll_defects': RollDefect.objects.count(),
            'roll_thickness': RollThickness.objects.count(),
            'lost_time_entries': LostTimeEntry.objects.count()
        }
        
        # Supprimer dans l'ordre (à cause des foreign keys)
        RollDefect.objects.all().delete()
        RollThickness.objects.all().delete()
        Roll.objects.all().delete()
        
        LostTimeEntry.objects.all().delete()
        QualityControl.objects.all().delete()
        ChecklistResponse.objects.all().delete()
        Shift.objects.all().delete()
        
        return Response({
            'success': True,
            'message': 'Données de production effacées',
            'deleted_counts': counts
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def increment_mood(request):
    """
    Incrémente le compteur d'humeur
    
    POST: {mood: 'happy'|'unhappy'|'neutral'|'no_response'}
    """
    mood_type = request.data.get('mood', 'no_response')
    
    # Valider la valeur
    valid_moods = ['happy', 'unhappy', 'neutral', 'no_response']
    if mood_type not in valid_moods:
        mood_type = 'no_response'
    
    # Incrémenter le compteur
    counter = MoodCounter.increment(mood_type)
    
    return Response({
        'mood': counter.mood_type,
        'count': counter.count,
        'all_counts': MoodCounter.get_all_counts()
    })