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
        link_rolls_to_shift(shift, session_data)
        
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
    
    shift_data = {
        'operator_id': session_data['operator'],
        'date': session_data['date'],
        'vacation': session_data['vacation'],
        'start_time': session_data['start_time'],
        'end_time': session_data['end_time'],
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
    for entry in lost_times:
        LostTimeEntry.objects.create(
            shift=shift,
            reason_id=entry['reason'],
            duration=entry['duration'],
            comments=entry.get('comment', '')
        )


def create_quality_controls(shift, quality_controls):
    """Crée les contrôles qualité pour le shift"""
    qc_data = {
        'shift': shift,
        'micronnaire_left_1': quality_controls.get('micronnaire_left_1'),
        'micronnaire_left_2': quality_controls.get('micronnaire_left_2'),
        'micronnaire_left_3': quality_controls.get('micronnaire_left_3'),
        'micronnaire_right_1': quality_controls.get('micronnaire_right_1'),
        'micronnaire_right_2': quality_controls.get('micronnaire_right_2'),
        'micronnaire_right_3': quality_controls.get('micronnaire_right_3'),
        'extrait_sec': quality_controls.get('extrait_sec'),
        'extrait_sec_time': quality_controls.get('extrait_sec_time'),
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
            ChecklistResponse.objects.create(
                shift=shift,
                checklist_item_id=item_id.replace('item_', ''),  # Retirer le préfixe
                response=response
            )


def link_rolls_to_shift(shift, session_data):
    """Associe les rouleaux déjà sauvegardés au shift"""
    # Les rouleaux ont été sauvegardés indépendamment
    # On doit maintenant les lier au shift
    current_of = session_data.get('current_of')
    if current_of:
        # Trouver tous les rouleaux de cet OF sans shift
        Roll.objects.filter(
            fabrication_order_id=current_of,
            shift__isnull=True
        ).update(shift=shift)


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
    
    # Reporter l'état de fin de poste au début du nouveau poste
    if current_data.get('started_at_end'):
        new_data['started_at_beginning'] = True
        new_data['meter_reading_start'] = current_data.get('meter_reading_end')
    else:
        new_data['started_at_beginning'] = False
        new_data['meter_reading_start'] = None
    
    # Réinitialiser tous les autres champs
    new_data.update({
        'operator': None,
        'date': None,
        'vacation': None,
        'start_time': None,
        'end_time': None,
        'started_at_end': False,
        'meter_reading_end': None,
        'lost_times': [],
        'checklist_responses': {},
        'checklist_signature': {},
        'quality_controls': {},
        'current_roll': {},
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
    
    # Récupérer toutes les données depuis la requête
    roll_info = request.data.get('roll_info', {})
    defects = request.data.get('defects', [])
    thickness_data = request.data.get('thickness', {})
    status = request.data.get('status')
    destination = request.data.get('destination')
    context = request.data.get('context', {})
    
    # Validation des champs requis
    required_fields = ['roll_number', 'length', 'tube_mass', 'total_mass']
    missing_fields = [field for field in required_fields if not roll_info.get(field)]
    
    if missing_fields:
        return Response(
            {'error': f'Champs requis manquants: {", ".join(missing_fields)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Récupérer le shift_id depuis la session courante
        shift_id = None
        try:
            current_session = CurrentSession.objects.get(session_key=session_key)
            shift_id = current_session.session_data.get('shift_id')
        except CurrentSession.DoesNotExist:
            pass
        
        # 1. Générer l'ID du rouleau
        roll_id = generate_roll_id_from_data(context, roll_info, status)
        
        # 2. Créer le rouleau
        roll = Roll.objects.create(
            roll_id=roll_id,
            session_key=session_key,
            shift_id_str=shift_id,  # Utiliser le shift_id de la session
            fabrication_order_id=context.get('current_of') if status == 'CONFORME' else context.get('cutting_of'),
            roll_number=int(roll_info['roll_number']),
            length=float(roll_info['length']),
            tube_mass=float(roll_info['tube_mass']),
            total_mass=float(roll_info['total_mass']),
            status=status,
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
        
        # 6. Retourner le succès
        return Response({
            'success': True,
            'roll_id': roll.roll_id,
            'status': roll.status,
            'destination': roll.destination
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
        now = datetime.now()
        date_str = now.strftime('%d%m%y')
        time_str = now.strftime('%H%M')
        return f"OFDecoupe_{date_str}_{time_str}"
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
            position_m=defect_dict.get('position_m', 0),
            position_side=position_side
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


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def check_shift_id(request, shift_id):
    """
    Vérifie si un shift_id existe déjà dans la base de données
    
    GET: Retourne {'exists': True/False}
    """
    exists = Shift.objects.filter(shift_id=shift_id).exists()
    return Response({'exists': exists})