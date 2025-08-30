from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from django.db import transaction
from django.conf import settings
from .models import Roll, Shift, CurrentProfile
from .serializers import RollSerializer, ShiftSerializer
from .services import roll_service, shift_service


class CurrentProfileView(APIView):
    """
    API pour gérer le profil actuellement sélectionné.
    GET: Récupère le profil actuel
    POST: Met à jour le profil actuel
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Récupère le profil actuellement sélectionné."""
        try:
            current = CurrentProfile.objects.first()
            if current and current.profile:
                return Response({
                    'profile_id': current.profile.id,
                    'profile_name': current.profile.name,
                    'selected_at': current.selected_at
                })
            return Response({'profile_id': None})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Met à jour le profil actuel."""
        profile_id = request.data.get('profile_id')
        
        try:
            # Récupérer ou créer l'entrée CurrentProfile
            current, created = CurrentProfile.objects.get_or_create(
                defaults={'profile_id': profile_id}
            )
            
            if not created:
                # Mettre à jour si elle existe déjà
                current.profile_id = profile_id
                current.save()
            
            return Response({
                'success': True,
                'profile_id': profile_id
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RollViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des rouleaux.
    
    Endpoints:
    - GET /api/production/rolls/ - Liste des rouleaux de la session
    - POST /api/production/rolls/ - Créer un nouveau rouleau
    - GET /api/production/rolls/{id}/ - Détail d'un rouleau
    """
    
    serializer_class = RollSerializer
    permission_classes = [AllowAny]  # TODO: Ajouter permissions appropriées
    
    def get_queryset(self):
        """Retourne les rouleaux de la session courante."""
        queryset = Roll.objects.all()
        
        # Filtrer par session si disponible
        if self.request.session.session_key:
            queryset = queryset.filter(session_key=self.request.session.session_key)
        
        # Prefetch les relations pour optimiser
        queryset = queryset.prefetch_related(
            'thickness_measurements',
            'defects__defect_type'
        )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['GET'], url_path='next-number')
    def next_number(self, request):
        """
        Récupère le prochain numéro de rouleau disponible pour un OF donné.
        
        Trouve le premier numéro manquant dans la séquence.
        """
        of_number = request.query_params.get('of')
        
        if not of_number:
            return Response(
                {'detail': 'Paramètre OF manquant'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer tous les numéros de rouleaux existants pour cet OF
        existing_rolls = Roll.objects.filter(
            roll_id__startswith=f"{of_number}_"
        ).values_list('roll_id', flat=True)
        
        # Extraire les numéros existants
        existing_numbers = []
        for roll_id in existing_rolls:
            try:
                # Format: OF_NNN
                parts = roll_id.split('_')
                if len(parts) == 2:
                    existing_numbers.append(int(parts[1]))
            except (ValueError, IndexError):
                continue
        
        existing_numbers.sort()
        
        # Trouver le premier numéro manquant
        next_number = 1
        for num in existing_numbers:
            if num == next_number:
                next_number += 1
            elif num > next_number:
                break
        
        # Formater avec 3 chiffres
        formatted_number = str(next_number).zfill(3)
        
        return Response({
            'of_number': of_number,
            'next_number': formatted_number,
            'roll_id': f"{of_number}_{formatted_number}"
        })
    
    @action(detail=False, methods=['GET'], url_path='check-id')
    def check_id(self, request):
        """
        Vérifie si un roll_id existe déjà dans la base de données.
        
        Paramètres:
        - roll_id: L'ID du rouleau à vérifier (format: OF_NumRouleau)
        
        Retourne:
        - exists: True si l'ID existe, False sinon
        """
        roll_id = request.query_params.get('roll_id')
        
        if not roll_id:
            return Response(
                {'detail': 'Paramètre roll_id manquant'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier si le roll_id existe
        exists = Roll.objects.filter(roll_id=roll_id).exists()
        
        return Response({
            'roll_id': roll_id,
            'exists': exists
        })
    
    def create(self, request):
        """
        Crée un nouveau rouleau avec ses mesures.
        
        La logique métier est déléguée au service.
        """
        # Valider les données
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Préparer les données de session
        session_data = {
            'shift_id': serializer.validated_data.get('shift_id_str') or request.session.get('shift_id'),
            'session_key': request.session.session_key,
        }
        
        # Vérifier qu'on a bien un shift_id
        if not session_data['shift_id']:
            return Response(
                {'error': 'Aucun poste actif trouvé dans la session'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ajouter les épaisseurs et défauts depuis la session V3
        v3_roll_data = self._prepare_session_data_v3_roll(request)
        serializer.validated_data['thicknesses'] = v3_roll_data['thicknesses']
        serializer.validated_data['defects'] = v3_roll_data['defects']
        
        try:
            # Créer le rouleau via le service
            roll = roll_service.create_roll_with_measurements(
                serializer.validated_data,
                session_data
            )
            
            # Sérialiser la réponse
            response_serializer = self.get_serializer(roll)
            response_data = response_serializer.data
            
            # Ajouter l'heure de création pour le timer
            response_data['created_at'] = roll.created_at.isoformat()
            
            # Nettoyer la session du rouleau
            self._clean_roll_session(request)
            
            # Préparer les données du prochain rouleau
            next_roll_data = self._prepare_next_roll_data(request, roll)
            response_data['next_roll_data'] = next_roll_data
            
            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            # Log l'erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur création rouleau: {str(e)}", exc_info=True)
            
            return Response(
                {'error': 'Erreur lors de la création du rouleau'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def check_id(self, request):
        """Vérifie si un roll_id existe déjà."""
        roll_id = request.query_params.get('roll_id')
        
        if not roll_id:
            return Response(
                {'error': 'roll_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exists = Roll.objects.filter(roll_id=roll_id).exists()
        
        return Response({
            'exists': exists,
            'roll_id': roll_id
        })
    
    def _prepare_session_data_v3_roll(self, request):
        """
        Prépare les données V3 du rouleau pour le service.
        Mappe les clés V3 vers le format attendu par le backend.
        """
        v3_data = request.session.get('v3_production', {})
        
        # Récupérer les données du rouleau depuis la clé 'roll'
        roll_data = v3_data.get('roll', {})
        thickness_values = roll_data.get('thicknessValues', {})
        rattrapages = roll_data.get('rattrapages', {})
        defects_data = roll_data.get('defects', {})
        
        # Mapper les colonnes aux points de mesure
        COLUMN_TO_POINT = {
            0: 'GG',  # Gauche Gauche
            1: 'GC',  # Gauche Centre
            2: 'GD',  # Gauche Droite
            4: 'DG',  # Droite Gauche
            5: 'DC',  # Droite Centre
            6: 'DD'   # Droite Droite
        }
        
        thicknesses = []
        
        # Traiter les épaisseurs normales
        for key, value in thickness_values.items():
            if value:
                row, col = key.split('-')
                row = int(row)
                col = int(col)
                meter = row + 1  # Le mètre est row + 1
                
                if col in COLUMN_TO_POINT:
                    thicknesses.append({
                        'meter_position': meter,
                        'measurement_point': COLUMN_TO_POINT[col],
                        'thickness_value': float(value),
                        'is_catchup': False,
                        'is_within_tolerance': True  # Sera recalculé par le backend
                    })
        
        # Traiter les rattrapages
        for key, value in rattrapages.items():
            if value:
                row, col = key.split('-')
                row = int(row)
                col = int(col)
                meter = row + 1
                
                if col in COLUMN_TO_POINT:
                    thicknesses.append({
                        'meter_position': meter,
                        'measurement_point': COLUMN_TO_POINT[col],
                        'thickness_value': float(value),
                        'is_catchup': True,
                        'is_within_tolerance': True
                    })
        
        # Mapper les défauts
        defects = []
        
        # Charger les types de défauts pour mapper les noms vers les IDs
        from catalog.models import QualityDefectType
        defect_types_map = {}
        for defect_type in QualityDefectType.objects.filter(is_active=True):
            defect_types_map[defect_type.name] = defect_type.id
        
        # Traiter les défauts par cellule
        for key, defect_names in defects_data.items():
            if defect_names:
                row, col = key.split('-')
                row = int(row)
                col = int(col)
                meter = row + 1
                
                # Déterminer la position sur la laize
                if col < 3:
                    position = 'Gauche'
                elif col > 3:
                    position = 'Droite'
                else:
                    position = 'Centre'
                
                # Convertir col en point de mesure si disponible
                if col in COLUMN_TO_POINT:
                    side_position = COLUMN_TO_POINT[col]
                else:
                    # Pour la colonne centrale (3), utiliser le côté le plus proche
                    side_position = 'GD' if col == 3 else 'DG'
                
                # Ajouter chaque défaut
                for defect_name in defect_names:
                    defect_type_id = defect_types_map.get(defect_name)
                    if defect_type_id:
                        defects.append({
                            'defect_type_id': defect_type_id,
                            'meter_position': meter,
                            'side_position': side_position,
                            'comment': ''
                        })
        
        return {
            'thicknesses': thicknesses,
            'defects': defects
        }
    
    def _clean_roll_session(self, request):
        """Nettoie les données du rouleau après sauvegarde."""
        if 'v3_production' in request.session:
            v3_data = request.session['v3_production']
            
            # Nettoyer uniquement les données du rouleau
            v3_data.pop('roll', None)  # Nettoyer la clé 'roll' au lieu de 'rollGrid'
            
            # Nettoyer les champs sticky bar
            v3_data.pop('sticky_tube_mass', None)
            v3_data.pop('sticky_total_mass', None)
            # Ne pas nettoyer sticky_roll_number ici, on va le mettre à jour dans _prepare_next_roll_data
            
            # Remettre la longueur cible pour le prochain rouleau
            target_length = v3_data.get('of', {}).get('targetLength')
            if target_length:
                v3_data['sticky_length'] = str(target_length)
            else:
                v3_data.pop('sticky_length', None)
            
            # Nettoyer les anciennes valeurs inutiles
            v3_data.pop('original_of', None)
            v3_data.pop('original_roll_number', None)
            v3_data.pop('sticky_roll_id', None)
            
            # Reporter next_tube_mass vers tube_mass
            next_tube = v3_data.pop('sticky_next_tube_mass', None)
            if next_tube:
                v3_data['sticky_tube_mass'] = next_tube
            
            # Nettoyer aussi le commentaire du rouleau
            if 'roll' in v3_data:
                v3_data['roll'].pop('comment', None)
                
            request.session['v3_production'] = v3_data
            request.session.save()
    
    def _prepare_next_roll_data(self, request, saved_roll):
        """Prépare les données pour le prochain rouleau."""
        v3_data = request.session.get('v3_production', {})
        
        # Reporter la masse tube suivante
        next_tube_mass = v3_data.get('sticky_tube_mass', '')
        
        # Debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Préparation prochain rouleau - saved_roll.roll_id: {saved_roll.roll_id}, roll_number: {saved_roll.roll_number}")
        
        # Récupérer le numéro actuel depuis la session
        current_roll_number = v3_data.get('sticky_roll_number', '')
        
        # Si on vient de sauver un CONFORME, on incrémente
        if saved_roll.status == 'CONFORME':
            if current_roll_number and current_roll_number.isdigit():
                current_number = int(current_roll_number)
            else:
                current_number = int(saved_roll.roll_number) if saved_roll.roll_number else 0
            next_roll_number = str(current_number + 1).zfill(3)
            logger.info(f"Rouleau CONFORME sauvé - Incrémentation: {current_number} -> {next_roll_number}")
        else:
            # Si NON CONFORME, on garde le même numéro pour réessayer
            next_roll_number = current_roll_number or '001'
            logger.info(f"Rouleau NON CONFORME sauvé - On garde le numéro: {next_roll_number}")
        
        # L'OF reste celui en cours (pas 9999 même si on vient de sauver un non conforme)
        if saved_roll.fabrication_order and saved_roll.fabrication_order.order_number != '9999':
            of_number = saved_roll.fabrication_order.order_number
        else:
            # Si c'était un 9999, récupérer l'OF en cours depuis la session
            of_number = v3_data.get('of', {}).get('ofEnCours', '')
        
        # Sauvegarder le nouveau numéro dans la session
        v3_data['sticky_roll_number'] = next_roll_number
        request.session['v3_production'] = v3_data
        request.session.save()
        
        return {
            'roll_number': next_roll_number,
            'tube_mass': next_tube_mass,
            'of_number': of_number,
            'shift_id': saved_roll.shift_id_str
        }


class ShiftViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des postes.
    
    Endpoints:
    - GET /api/shifts/ - Liste des postes
    - POST /api/shifts/ - Créer un nouveau poste
    - GET /api/shifts/{id}/ - Détail d'un poste
    """
    
    serializer_class = ShiftSerializer
    permission_classes = [AllowAny]  # TODO: Ajouter permissions appropriées
    
    def get_queryset(self):
        """Retourne les postes."""
        queryset = Shift.objects.all()
        
        # Prefetch les relations pour optimiser
        queryset = queryset.select_related('operator').prefetch_related(
            'lost_time_entries__reason',
            'rolls'
        )
        
        return queryset.order_by('-date', '-created_at')
    
    def perform_update(self, serializer):
        """Mise à jour d'un shift avec recalcul du TRS."""
        shift = serializer.save()
        
        # Recalculer le TRS après la mise à jour
        from wcm.services import calculate_and_create_trs
        calculate_and_create_trs(shift)
    
    @action(detail=False, methods=['get'])
    def last(self, request):
        """
        Récupère le dernier poste enregistré.
        
        Retourne la longueur enroulée en fin de poste (wound_length_end).
        """
        # Récupérer le dernier poste qui a une longueur de fin renseignée
        last_shift = Shift.objects.exclude(
            meter_reading_end__isnull=True
        ).order_by('-created_at').first()
        
        if last_shift:
            # Retourner les données essentielles
            # La baguette magique veut le meter_reading_end du dernier poste
            return Response({
                'shift_id': last_shift.shift_id,
                'date': last_shift.date,
                'wound_length_end': last_shift.meter_reading_end,
                'started_at_end': last_shift.started_at_end,  # Pour savoir si on doit cocher la case
                'operator': f"{last_shift.operator.first_name} {last_shift.operator.last_name}" if last_shift.operator else None,
                'vacation': last_shift.vacation
            })
        else:
            return Response({'detail': 'Aucun poste trouvé'}, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        """
        Crée un nouveau poste avec ses associations.
        
        La logique métier est déléguée au service.
        """
        # Valider les données de base
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Récupérer toutes les données de session nécessaires
        # Utiliser la méthode de mapping V3
        session_data = self._prepare_session_data_v3(request)
        
        # Debug : logger ce qu'on a dans la session
        if settings.DEBUG:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Session data for shift creation: {session_data}")
            logger.info(f"Lost time entries from session: {session_data['lost_time_entries']}")
        
        # Ajouter les données de signature de checklist si présentes
        if session_data['checklist_signature']:
            serializer.validated_data['checklist_signed'] = session_data['checklist_signature']
        if session_data['checklist_signature_time']:
            serializer.validated_data['checklist_signed_time'] = session_data['checklist_signature_time']
        
        try:
            # Créer le poste via le service
            shift = shift_service.create_shift_with_associations(
                serializer.validated_data,
                session_data
            )
            
            # Sérialiser la réponse avec les données calculées
            response_serializer = self.get_serializer(shift)
            response_data = response_serializer.data
            
            # Ajouter des stats supplémentaires
            response_data['roll_count'] = shift.rolls.count()
            response_data['total_lost_time_minutes'] = int(shift.lost_time.total_seconds() / 60) if shift.lost_time else 0
            
            # Préparer la session pour le prochain poste
            next_shift_data = self._prepare_next_shift(request, shift)
            
            # Ajouter les données du prochain poste dans la réponse
            response_data['next_shift_data'] = next_shift_data
            
            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            # Log l'erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur création poste: {str(e)}", exc_info=True)
            
            return Response(
                {'error': f'Erreur lors de la création du poste: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _prepare_next_shift(self, request, saved_shift):
        """Prépare la session pour le prochain poste après sauvegarde."""
        # Utiliser les données du poste sauvé (pas de la session)
        machine_started_end = saved_shift.started_at_end
        meter_reading_end = saved_shift.meter_reading_end
        
        # Nettoyer toute la session
        self._clean_session(request)
        
        # Déterminer la vacation suivante
        vacation_map = {
            'Matin': 'ApresMidi',
            'ApresMidi': 'Nuit',
            'Nuit': 'Matin',
            'Journee': 'Journee'  # Journée reste Journée
        }
        next_vacation = vacation_map.get(saved_shift.vacation, 'Matin')
        
        # Préparer les données du prochain poste
        from datetime import date
        today = date.today()
        
        # Définir les heures par défaut selon la vacation
        default_hours = {
            'Matin': ('04:00', '12:00'),
            'ApresMidi': ('12:00', '20:00'),
            'Nuit': ('20:00', '04:00'),
            'Journee': ('07:30', '15:30')
        }
        
        start_time = default_hours.get(next_vacation, ('', ''))[0]
        end_time = default_hours.get(next_vacation, ('', ''))[1]
        
        # Données du prochain poste
        next_shift_data = {
            'shift_date': today.strftime('%Y-%m-%d'),
            'vacation': next_vacation,
            'start_time': start_time,
            'end_time': end_time,
            'machine_started_start': bool(machine_started_end and meter_reading_end),
            'length_start': str(meter_reading_end) if (machine_started_end and meter_reading_end) else '',
            'machine_started_end': True,
            'operator_id': '',  # Pas d'opérateur
            'comment': ''
        }
        
        # Sauvegarder en session V3 dans la structure shift
        if 'v3_production' not in request.session:
            request.session['v3_production'] = {}
        
        # Initialiser la structure shift si nécessaire
        if 'shift' not in request.session['v3_production']:
            request.session['v3_production']['shift'] = {}
        
        # Mapper les données vers la structure V3
        v3_shift_mapping = {
            'shift_date': 'date',
            'vacation': 'vacation',
            'start_time': 'startTime',
            'end_time': 'endTime',
            'machine_started_start': 'machineStartedStart',
            'length_start': 'lengthStart',
            'machine_started_end': 'machineStartedEnd',
            'operator_id': 'operatorId',
            'comment': 'comments'
        }
        
        # Sauvegarder dans v3_production.shift
        for old_key, new_key in v3_shift_mapping.items():
            if old_key in next_shift_data:
                request.session['v3_production']['shift'][new_key] = next_shift_data[old_key]
        
        # Ajouter les champs manquants
        request.session['v3_production']['shift']['lengthEnd'] = ''
        request.session['v3_production']['shift']['shiftId'] = ''
        
        request.session.save()
        
        # Retourner les données pour la réponse
        return next_shift_data
    
    def _clean_session(self, request):
        """Nettoie les données de session après sauvegarde du poste."""
        # Nettoyer les données V3 qui sont dans request.session['v3_production']
        if 'v3_production' in request.session:
            v3_data = request.session['v3_production']
            
            # Clés à supprimer dans v3_production
            v3_keys_to_remove = [
                'lost_time_entries',      # Temps perdus à réinitialiser
                'checklist',              # Check-list complète
                'checklist_responses',    # Anciennes clés (au cas où)
                'checklist_signature',
                'checklist_signature_time',
                'quality_control',
                'qc_status',
                # Nettoyer aussi les champs QC individuels
                'qc_micromaire_g',
                'qc_micromaire_d',
                'qc_masse_surfacique_gg',
                'qc_masse_surfacique_gc',
                'qc_masse_surfacique_dc',
                'qc_masse_surfacique_dd',
                'qc_extrait_sec',
                'qc_extrait_time',
                'qc_loi',
                'qc_loi_time',
                # Supprimer les données dupliquées du shift
                'shift_date',
                'vacation',
                'start_time',
                'end_time',
                'machine_started_start',
                'machine_started_end',
                'length_start',
                'operator_id',
                'comment',
                # Note: Ne pas nettoyer les données du rouleau en cours
            ]
            
            for key in v3_keys_to_remove:
                v3_data.pop(key, None)
            
            request.session['v3_production'] = v3_data
        
        # Nettoyer TOUTES les clés à la racine de la session sauf v3_production
        # Ces clés viennent de l'ancienne implémentation V1/V2
        root_keys_to_keep = ['v3_production', '_auth_user_id', '_auth_user_backend', '_auth_user_hash']
        
        # Faire une copie des clés pour éviter les problèmes lors de la suppression
        all_keys = list(request.session.keys())
        
        for key in all_keys:
            if key not in root_keys_to_keep:
                request.session.pop(key, None)
        
        request.session.save()
    
    @action(detail=False, methods=['get'])
    def check_id(self, request):
        """Vérifie si un shift_id existe déjà."""
        shift_id = request.query_params.get('shift_id')
        
        if not shift_id:
            return Response(
                {'error': 'shift_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exists = Shift.objects.filter(shift_id=shift_id).exists()
        
        return Response({
            'exists': exists,
            'shift_id': shift_id
        })
    
    @action(detail=False, methods=['get'], url_path='(?P<shift_id>[^/]+)/stats')
    def stats(self, request, shift_id=None):
        """
        Retourne les statistiques de production pour un poste.
        
        Calcule les indicateurs TRS/OEE:
        - Disponibilité (déjà calculée côté frontend)
        - Performance (production réelle vs théorique)
        - Qualité (rouleaux conformes vs total)
        """
        try:
            # Récupérer le shift
            shift = Shift.objects.filter(shift_id=shift_id).first()
            
            if not shift:
                # Si pas de shift sauvegardé, essayer de calculer depuis la session
                from django.db.models import Sum, Count, Q
                from .models import Roll
                
                # Récupérer les rouleaux de la session
                session_key = request.session.session_key
                rolls = Roll.objects.filter(
                    Q(shift_id_str=shift_id) | Q(session_key=session_key)
                )
                
                # Calculer les stats depuis les rouleaux
                stats = rolls.aggregate(
                    total_rolls=Count('id'),
                    conforming_rolls=Count('id', filter=Q(status='CONFORME')),
                    total_length=Sum('length') or 0,
                    conforming_length=Sum('length', filter=Q(status='CONFORME')) or 0
                )
                
                # Données de base
                total_rolls = stats['total_rolls'] or 0
                conforming_rolls = stats['conforming_rolls'] or 0
                total_length = float(stats['total_length'] or 0)
                conforming_length = float(stats['conforming_length'] or 0)
                
            else:
                # Utiliser les données du shift sauvegardé
                rolls = shift.rolls.all()
                total_rolls = rolls.count()
                conforming_rolls = rolls.filter(status='CONFORME').count()
                total_length = float(shift.total_length or 0)
                conforming_length = float(shift.ok_length or 0)
                
                # Ajouter la production enroulée si la machine était en marche
                if shift.started_at_end and shift.meter_reading_end and shift.started_at_beginning and shift.meter_reading_start:
                    # Production = métrage fin - métrage début
                    wound_length = float(shift.meter_reading_end) - float(shift.meter_reading_start)
                    if wound_length > 0:
                        total_length += wound_length
                        # On assume que la production enroulée est conforme
                        conforming_length += wound_length
            
            # Calculer le taux de qualité
            quality_rate = 0
            if total_rolls > 0:
                quality_rate = round((conforming_rolls / total_rolls) * 100, 1)
            
            # Pour la performance, on a besoin de la vitesse théorique et du temps disponible
            # Ces valeurs doivent venir du frontend car elles dépendent du profil et des temps
            
            return Response({
                'shift_id': shift_id,
                'production': {
                    'total_rolls': total_rolls,
                    'conforming_rolls': conforming_rolls,
                    'non_conforming_rolls': total_rolls - conforming_rolls,
                    'total_length': total_length,
                    'conforming_length': conforming_length,
                    'non_conforming_length': total_length - conforming_length,
                },
                'quality_rate': quality_rate,
                'has_data': total_rolls > 0
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur calcul stats shift {shift_id}: {str(e)}", exc_info=True)
            
            return Response(
                {'error': f'Erreur lors du calcul des statistiques: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _prepare_session_data_v3(self, request):
        """
        Prépare les données de session V3 pour le service.
        Mappe les clés V3 vers le format attendu par le backend.
        """
        v3_data = request.session.get('v3_production', {})
        
        # Mapper la checklist V3
        checklist_data = v3_data.get('checklist', {})
        
        # Construire les données QC depuis les champs individuels V3
        quality_control = {}
        
        # Vérifier si on a des données QC
        has_qc_data = any([
            v3_data.get('qc_micromaire_g'),
            v3_data.get('qc_micromaire_d'),
            v3_data.get('qc_masse_surfacique_gg'),
            v3_data.get('qc_masse_surfacique_gc'),
            v3_data.get('qc_masse_surfacique_dc'),
            v3_data.get('qc_masse_surfacique_dd'),
            v3_data.get('qc_extrait_sec'),
            v3_data.get('qc_loi') is not None
        ])
        
        if has_qc_data:
            # Fonction helper pour calculer la moyenne
            def calc_avg(values):
                if not values:
                    return None
                valid_values = [float(v) for v in values if v]
                return sum(valid_values) / len(valid_values) if valid_values else None
            
            # Mapper les données
            quality_control = {
                'micrometry': {
                    'left': v3_data.get('qc_micromaire_g', []),
                    'right': v3_data.get('qc_micromaire_d', []),
                    'averageLeft': calc_avg(v3_data.get('qc_micromaire_g', [])),
                    'averageRight': calc_avg(v3_data.get('qc_micromaire_d', []))
                },
                'surfaceMass': {
                    'leftLeft': v3_data.get('qc_masse_surfacique_gg'),
                    'leftCenter': v3_data.get('qc_masse_surfacique_gc'),
                    'rightCenter': v3_data.get('qc_masse_surfacique_dc'),
                    'rightRight': v3_data.get('qc_masse_surfacique_dd'),
                    'averageLeft': calc_avg([
                        v3_data.get('qc_masse_surfacique_gg'),
                        v3_data.get('qc_masse_surfacique_gc')
                    ]),
                    'averageRight': calc_avg([
                        v3_data.get('qc_masse_surfacique_dc'),
                        v3_data.get('qc_masse_surfacique_dd')
                    ])
                },
                'dryExtract': {
                    'value': v3_data.get('qc_extrait_sec'),
                    'timestamp': v3_data.get('qc_extrait_time'),
                    'sample': v3_data.get('qc_loi'),
                    'loiTimestamp': v3_data.get('qc_loi_time')
                },
                'status': v3_data.get('qc_status', 'pending')
            }
        
        return {
            'session_key': request.session.session_key,
            'checklist_items': checklist_data.get('items', {}),
            'checklist_items_order': checklist_data.get('itemsOrder', []),
            'checklist_responses': checklist_data.get('responses', {}),
            'checklist_comments': checklist_data.get('comments', {}),
            'checklist_signature': checklist_data.get('signature'),
            'checklist_signature_time': checklist_data.get('signatureTime'),
            'quality_control': quality_control,
            'lost_time_entries': v3_data.get('lost_time_entries', []),
        }


# Vues API simples pour la vérification d'unicité
@api_view(['GET'])
def check_roll_id(request):
    """Vérifie si un roll_id existe déjà."""
    roll_id = request.query_params.get('roll_id')
    
    if not roll_id:
        return Response(
            {'error': 'roll_id parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    exists = Roll.objects.filter(roll_id=roll_id).exists()
    
    return Response({
        'exists': exists,
        'roll_id': roll_id
    })


@api_view(['GET'])
def check_shift_id(request):
    """Vérifie si un shift_id existe déjà."""
    shift_id = request.query_params.get('shift_id')
    
    if not shift_id:
        return Response(
            {'error': 'shift_id parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    exists = Shift.objects.filter(shift_id=shift_id).exists()
    
    return Response({
        'exists': exists,
        'shift_id': shift_id
    })