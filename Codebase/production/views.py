from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
import json
from datetime import datetime
from django.db.models import Sum, Q
from .models import Shift, QualityControl, Roll, LostTimeEntry, MachineParameters
from .forms import ShiftForm
from core.models import Operator, FabricationOrder, Profile, Mode
from quality.models import DefectType
from wcm.models import ChecklistTemplate, ChecklistItem, ChecklistResponse


def get_last_meter_reading(request):
    """Récupère le métrage du dernier poste."""
    try:
        # Récupérer le dernier shift avec meter_reading_end
        last_shift = Shift.objects.exclude(meter_reading_end__isnull=True).order_by('-date', '-created_at').first()
        
        if last_shift:
            return JsonResponse({
                'success': True,
                'meter_reading': float(last_shift.meter_reading_end),
                'shift_info': f"{last_shift.shift_id}"
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Aucun poste précédent trouvé avec un métrage'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


def get_previous_shift(request):
    """Récupère les données complètes du dernier poste pour affichage."""
    try:
        # Récupérer l'offset depuis la requête (0 = dernier, 1 = avant-dernier, etc.)
        offset = int(request.GET.get('offset', 0))
        
        # Récupérer le shift selon l'offset
        shifts = Shift.objects.select_related('operator').order_by('-date', '-created_at')
        
        if offset >= shifts.count():
            # Si l'offset dépasse le nombre de shifts, retourner None
            return JsonResponse({
                'success': True,
                'shift': None,
                'has_more': False
            })
        
        last_shift = shifts[offset] if offset < shifts.count() else None
        
        if last_shift:
            # Compter les rouleaux produits
            roll_count = Roll.objects.filter(shift=last_shift).count()
            
            # Calculer la production totale
            total_length = 0
            if last_shift.meter_reading_start and last_shift.meter_reading_end:
                total_length = last_shift.meter_reading_end - last_shift.meter_reading_start
            
            # Récupérer les réponses de la checklist
            checklist_data = []
            try:
                checklist_responses = ChecklistResponse.objects.filter(
                    shift=last_shift
                ).select_related('item').order_by('item__order')
                
                for response in checklist_responses:
                    checklist_data.append({
                        'item_name': response.item.text,
                        'response': response.response,
                        'response_display': response.get_response_display()
                    })
            except Exception as e:
                print(f"Erreur checklist: {str(e)}")
            
            # Récupérer les temps d'arrêt
            lost_time_data = []
            try:
                lost_times = LostTimeEntry.objects.filter(shift=last_shift).order_by('created_at')
                for lost_time in lost_times:
                    lost_time_data.append({
                        'motif': lost_time.motif,
                        'duration': lost_time.duration,
                        'comment': lost_time.comment or ''
                    })
            except Exception as e:
                print(f"Erreur temps d'arrêt: {str(e)}")
            
            shift_data = {
                'shift_id': last_shift.shift_id,
                'operator_name': last_shift.operator.full_name if last_shift.operator else '--',
                'date': last_shift.date.strftime('%d/%m/%Y') if last_shift.date else '--',
                'vacation': last_shift.get_vacation_display() if last_shift.vacation else '--',
                'start_time': last_shift.start_time.strftime('%H:%M') if last_shift.start_time else '--',
                'end_time': last_shift.end_time.strftime('%H:%M') if last_shift.end_time else '--',
                'operator_comments': last_shift.operator_comments or '',
                'checklist': checklist_data,
                'checklist_signed': last_shift.checklist_signed or '',
                'checklist_signed_time': last_shift.checklist_signed_time.strftime('%H:%M') if last_shift.checklist_signed_time else '',
                'lost_times': lost_time_data,
                'total_lost_time': int(last_shift.lost_time.total_seconds() / 60) if last_shift.lost_time else 0
            }
            
            # Vérifier s'il y a encore des postes après celui-ci
            has_more = offset + 1 < shifts.count()
            
            return JsonResponse({
                'success': True,
                'shift': shift_data,
                'has_more': has_more,
                'offset': offset
            })
        else:
            return JsonResponse({
                'success': True,
                'shift': None,
                'has_more': False
            })
    except Exception as e:
        print(f"Erreur get_previous_shift: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


def get_profile_parameters(request, profile_id):
    """Récupère les paramètres machine et spécifications d'un profil."""
    try:
        profile = Profile.objects.prefetch_related('specifications').get(pk=profile_id)
        
        response_data = {'success': True}
        
        # Paramètres machine
        if profile.machine_parameters:
            params = profile.machine_parameters
            response_data['parameters'] = {
                'name': params.name,
                'oxygen_primary': float(params.oxygen_primary) if params.oxygen_primary else None,
                'oxygen_secondary': float(params.oxygen_secondary) if params.oxygen_secondary else None,
                'propane_primary': float(params.propane_primary) if params.propane_primary else None,
                'propane_secondary': float(params.propane_secondary) if params.propane_secondary else None,
                'speed_primary': float(params.speed_primary) if params.speed_primary else None,
                'speed_secondary': float(params.speed_secondary) if params.speed_secondary else None,
                'belt_speed': float(params.belt_speed) if params.belt_speed else None,
                'belt_speed_m_per_minute': params.belt_speed_m_per_minute,
            }
        else:
            response_data['parameters'] = None
            
        # Spécifications
        specifications = {}
        for spec in profile.specifications.filter(is_active=True):
            specifications[spec.spec_type] = {
                'name': spec.name,
                'type': spec.get_spec_type_display(),
                'value_min': float(spec.value_min) if spec.value_min else None,
                'value_min_alert': float(spec.value_min_alert) if spec.value_min_alert else None,
                'value_nominal': float(spec.value_nominal) if spec.value_nominal else None,
                'value_max_alert': float(spec.value_max_alert) if spec.value_max_alert else None,
                'value_max': float(spec.value_max) if spec.value_max else None,
                'unit': spec.unit,
                'max_nok': spec.max_nok,
            }
        response_data['specifications'] = specifications
        
        return JsonResponse(response_data)
        
    except Profile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Profil non trouvé'
        })


def prod(request):
    """Vue principale de production."""
    from datetime import datetime, timedelta
    
    # Afficher tous les postes
    shifts = Shift.objects.select_related('operator').order_by('-date', '-created_at')
    
    # Forcer le recalcul des moyennes pour les shifts qui n'en ont pas
    for shift in shifts:
        if shift.avg_thickness_left_shift is None or shift.avg_thickness_right_shift is None or shift.avg_grammage_shift is None:
            shift.calculate_roll_averages()
            shift.save(update_fields=['avg_thickness_left_shift', 'avg_thickness_right_shift', 'avg_grammage_shift'])
    
    defect_types = DefectType.objects.filter(is_active=True).order_by('name')
    
    # Afficher tous les rouleaux
    recent_rolls = Roll.objects.select_related('fabrication_order', 'shift').order_by('-created_at')
    
    # Récupérer le template de check-list par défaut ou le premier actif
    checklist_template = ChecklistTemplate.objects.filter(
        is_active=True
    ).order_by('-is_default', 'name').first()
    
    # Récupérer les items de la check-list
    checklist_items = []
    if checklist_template:
        checklist_items = checklist_template.items.filter(
            is_active=True
        ).order_by('order')
    
    # Récupérer les paramètres machine actifs
    machine_parameters = MachineParameters.objects.filter(is_active=True).order_by('name')
    
    # Récupérer les profils actifs avec leurs paramètres machine
    profiles = Profile.objects.filter(is_active=True).select_related('machine_parameters').order_by('name')
    
    # Récupérer les modes actifs (Permissif en premier)
    modes = Mode.objects.filter(is_active=True).order_by('-name')  # Ordre inverse pour avoir Permissif avant Restrictif
    
    # Créer un formulaire vide pour la fiche de poste
    shift_form = ShiftForm()
    
    context = {
        'shifts': shifts,
        'defect_types': defect_types,
        'recent_rolls': recent_rolls,
        'checklist_template': checklist_template,
        'checklist_items': checklist_items,
        'machine_parameters': machine_parameters,
        'profiles': profiles,
        'modes': modes,
        'shift_form': shift_form,
        'form': shift_form,  # Pour compatibilité avec le template shift_block.html
    }
    return render(request, 'production/prod.html', context)


def shift_block(request, shift_id=None):
    """Vue pour le bloc Poste - création ou modification."""
    print(f"DEBUG: shift_block appelé avec shift_id={shift_id}, method={request.method}")
    shift = None
    if shift_id:
        shift = get_object_or_404(Shift, pk=shift_id)
    
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            
            # VÉRIFIER LES CONTRÔLES QUALITÉ ET LA CHECK-LIST AVANT DE SAUVEGARDER LE SHIFT
            session_key = request.session.session_key
            all_quality_filled = False
            checklist_signed = False
            
            if session_key:
                try:
                    from livesession.models import CurrentSession
                    current_session = CurrentSession.objects.get(session_key=session_key)
                    quality_data = current_session.session_data.get('quality_controls', {})
                    
                    # Vérifier si des contrôles qualité existent et sont complets
                    micrometers_left = [v for v in quality_data.get('micrometer_left', []) if v]
                    micrometers_right = [v for v in quality_data.get('micrometer_right', []) if v]
                    micrometers_filled = (len(micrometers_left) == 3 and len(micrometers_right) == 3)
                    
                    sizing_bath_filled = bool(quality_data.get('sizing_bath'))
                    
                    mass_left = [v for v in quality_data.get('surface_mass_left', []) if v]
                    mass_right = [v for v in quality_data.get('surface_mass_right', []) if v]
                    mass_filled = (len(mass_left) == 2 and len(mass_right) == 2)
                    
                    loi_filled = quality_data.get('loi_given', False)
                    
                    # Vérifier si TOUS les contrôles sont remplis
                    all_quality_filled = micrometers_filled and sizing_bath_filled and mass_filled and loi_filled
                    
                    # VÉRIFIER LA CHECK-LIST
                    checklist_data = current_session.session_data.get('checklist_responses', {})
                    checklist_signature = checklist_data.get('signature', '').strip()
                    checklist_signed = bool(checklist_signature)
                    
                except CurrentSession.DoesNotExist:
                    all_quality_filled = False
                    checklist_signed = False
            
            # BLOQUER LA SAUVEGARDE SI LES CONTRÔLES NE SONT PAS COMPLETS
            if not all_quality_filled:
                error_message = "Tous les contrôles qualité doivent être remplis avant de sauvegarder le poste."
                if request.htmx:
                    # Retourner le formulaire avec une alerte JavaScript
                    context = {
                        'form': form, 
                        'shift': shift, 
                        'is_edit': shift is not None,
                        'show_alert': error_message
                    }
                    return render(request, 'production/blocks/shift_block.html', context)
                else:
                    messages.error(request, error_message)
                    return redirect('production:prod')
            
            # BLOQUER LA SAUVEGARDE SI LA CHECK-LIST N'EST PAS SIGNÉE
            if not checklist_signed:
                error_message = "La check-list doit être complétée et signée avant de sauvegarder le poste."
                if request.htmx:
                    # Retourner le formulaire avec une alerte JavaScript
                    context = {
                        'form': form, 
                        'shift': shift, 
                        'is_edit': shift is not None,
                        'show_alert': error_message
                    }
                    return render(request, 'production/blocks/shift_block.html', context)
                else:
                    messages.error(request, error_message)
                    return redirect('production:prod')
            
            # VÉRIFIER SI LE POSTE EXISTE DÉJÀ
            # Générer le shift_id selon le format du modèle
            date_obj = form.cleaned_data['date']
            operator = form.cleaned_data['operator']
            vacation = form.cleaned_data['vacation']
            
            # Format: JJMMAA_PrenomNom_Vacation
            date_formatted = date_obj.strftime('%d%m%y')
            operator_clean = operator.full_name_no_space
            expected_shift_id = f"{date_formatted}_{operator_clean}_{vacation}"
            
            # Vérifier si c'est une création (pas une édition) et si le shift existe déjà
            if not shift and Shift.objects.filter(shift_id=expected_shift_id).exists():
                error_message = f"Ce poste existe déjà : {expected_shift_id}"
                if request.htmx:
                    # Retourner le formulaire avec une alerte JavaScript
                    context = {
                        'form': form, 
                        'shift': shift, 
                        'is_edit': False,
                        'show_alert': error_message
                    }
                    return render(request, 'production/blocks/shift_block.html', context)
                else:
                    messages.error(request, error_message)
                    return redirect('production:prod')
            
            # SAUVEGARDER LE SHIFT SEULEMENT SI LES CONTRÔLES SONT COMPLETS ET LE POSTE N'EXISTE PAS
            try:
                # D'abord, récupérer les longueurs calculées des rouleaux actuels
                # On utilise la session pour récupérer les rouleaux non encore liés au shift
                total_length = 0
                ok_length = 0
                nok_length = 0
                
                if session_key:
                    # Rouleaux de la session actuelle (pas encore liés au shift)
                    session_rolls = Roll.objects.filter(session_key=session_key, shift__isnull=True)
                    
                    for roll in session_rolls:
                        total_length += float(roll.length or 0)
                        if roll.status == 'CONFORME':
                            ok_length += float(roll.length or 0)
                        elif roll.status == 'NON_CONFORME':
                            nok_length += float(roll.length or 0)
                
                # Ne PAS ajouter le métrage de fin - c'est une lecture de compteur, pas une longueur produite!
                
                # Mettre à jour les valeurs dans le formulaire avant de sauvegarder
                shift = form.save(commit=False)
                shift.total_length = total_length
                shift.ok_length = ok_length
                shift.nok_length = nok_length
                shift.save()
                print(f"DEBUG: Shift saved successfully with ID: {shift.id}, shift_id: {shift.shift_id}")
                
                # Lier les rouleaux orphelins (créés sans shift) à ce shift
                if session_key:
                    orphan_rolls = Roll.objects.filter(
                        session_key=session_key,
                        shift__isnull=True
                    )
                    if orphan_rolls.exists():
                        orphan_rolls.update(shift=shift, shift_id_str=shift.shift_id, session_key=None)
                        print(f"DEBUG: {orphan_rolls.count()} rouleaux orphelins liés au shift {shift.shift_id}")
                        
                        # Recalculer les moyennes du shift maintenant qu'on a lié les rouleaux
                        shift.calculate_roll_averages()
                        
                        # Recalculer aussi les longueurs totales maintenant que les rouleaux sont liés
                        linked_rolls = Roll.objects.filter(shift=shift)
                        total_length = 0
                        ok_length = 0
                        nok_length = 0
                        
                        for roll in linked_rolls:
                            total_length += float(roll.length or 0)
                            if roll.status == 'CONFORME':
                                ok_length += float(roll.length or 0)
                            elif roll.status == 'NON_CONFORME':
                                nok_length += float(roll.length or 0)
                        
                        shift.total_length = total_length
                        shift.ok_length = ok_length
                        shift.nok_length = nok_length
                        
                        shift.save(update_fields=['avg_thickness_left_shift', 'avg_thickness_right_shift', 'avg_grammage_shift', 
                                                'total_length', 'ok_length', 'nok_length'])
                
                # Maintenant sauvegarder les contrôles qualité
                if session_key:
                    try:
                        current_session = CurrentSession.objects.get(session_key=session_key)
                        quality_data = current_session.session_data.get('quality_controls', {})
                        
                        # Créer l'objet QualityControl (on sait qu'ils sont complets)
                        quality_control = QualityControl(shift=shift)
                        
                        # Remplir les valeurs Micronnaire
                        micrometer_left = quality_data.get('micrometer_left', [])
                        if len(micrometer_left) >= 3:
                            quality_control.micrometer_left_1 = float(micrometer_left[0]) if micrometer_left[0] else None
                            quality_control.micrometer_left_2 = float(micrometer_left[1]) if micrometer_left[1] else None
                            quality_control.micrometer_left_3 = float(micrometer_left[2]) if micrometer_left[2] else None
                        
                        micrometer_right = quality_data.get('micrometer_right', [])
                        if len(micrometer_right) >= 3:
                            quality_control.micrometer_right_1 = float(micrometer_right[0]) if micrometer_right[0] else None
                            quality_control.micrometer_right_2 = float(micrometer_right[1]) if micrometer_right[1] else None
                            quality_control.micrometer_right_3 = float(micrometer_right[2]) if micrometer_right[2] else None
                        
                        # Extrait Sec
                        if quality_data.get('sizing_bath'):
                            quality_control.dry_extract = float(quality_data['sizing_bath'].replace(',', '.'))
                        
                        # Heure Extrait Sec
                        if quality_data.get('sizing_bath_time') and quality_data['sizing_bath_time'] != '--':
                            try:
                                quality_control.dry_extract_time = datetime.strptime(quality_data['sizing_bath_time'], '%H:%M').time()
                            except:
                                pass
                        
                        # Masses Surfaciques
                        surface_mass_left = quality_data.get('surface_mass_left', [])
                        if len(surface_mass_left) >= 2:
                            # GG et GC
                            if surface_mass_left[0]:
                                quality_control.surface_mass_gg = float(surface_mass_left[0].replace(',', '.'))
                            if surface_mass_left[1]:
                                quality_control.surface_mass_gc = float(surface_mass_left[1].replace(',', '.'))
                        
                        surface_mass_right = quality_data.get('surface_mass_right', [])
                        if len(surface_mass_right) >= 2:
                            # DC et DD
                            if surface_mass_right[0]:
                                quality_control.surface_mass_dc = float(surface_mass_right[0].replace(',', '.'))
                            if surface_mass_right[1]:
                                quality_control.surface_mass_dd = float(surface_mass_right[1].replace(',', '.'))
                        
                        # LOI
                        quality_control.loi_given = quality_data.get('loi_given', False)
                        if quality_data.get('loi_time') and quality_data['loi_time'] != '--':
                            try:
                                quality_control.loi_time = datetime.strptime(quality_data['loi_time'], '%H:%M').time()
                            except:
                                pass
                        
                        # Opérateur
                        quality_control.created_by = shift.operator
                        
                        # Sauvegarder
                        quality_control.save()
                        print(f"Contrôles qualité sauvegardés pour le shift {shift.shift_id}")
                    
                    except CurrentSession.DoesNotExist:
                        pass
                    
                    # Sauvegarder la check-list
                    if session_key:
                        try:
                            current_session = CurrentSession.objects.get(session_key=session_key)
                            checklist_data = current_session.session_data.get('checklist_responses', {})
                            
                            if checklist_data:
                                # Sauvegarder la signature et l'heure dans le shift
                                signature = checklist_data.get('signature', '').strip()
                                signature_time = checklist_data.get('signatureTime', '')
                                
                                if signature:
                                    shift.checklist_signed = signature
                                    # Parser l'heure si elle est au format HH:MM
                                    if signature_time and signature_time != '--':
                                        try:
                                            shift.checklist_signed_time = datetime.strptime(signature_time, '%H:%M').time()
                                        except:
                                            pass
                                    shift.save(update_fields=['checklist_signed', 'checklist_signed_time'])
                                
                                # Sauvegarder les réponses de la check-list
                                for item_key, response_value in checklist_data.items():
                                    if item_key.startswith('item-') and response_value:
                                        try:
                                            item_id = int(item_key.replace('item-', ''))
                                            item = ChecklistItem.objects.get(id=item_id)
                                            
                                            # Créer ou mettre à jour la réponse
                                            ChecklistResponse.objects.update_or_create(
                                                shift=shift,
                                                item=item,
                                                defaults={'response': response_value}
                                            )
                                        except (ValueError, ChecklistItem.DoesNotExist):
                                            pass
                                
                                print(f"Check-list sauvegardée pour le shift {shift.shift_id}")
                        
                        except CurrentSession.DoesNotExist:
                            pass
                    
                    # Sauvegarder les temps d'arrêt
                    if session_key:
                        try:
                            current_session = CurrentSession.objects.get(session_key=session_key)
                            lost_times = current_session.session_data.get('lost_times', [])
                            
                            for lost_time_data in lost_times:
                                if lost_time_data.get('motif') and lost_time_data.get('minutes'):
                                    lost_time_entry = LostTimeEntry(
                                        shift=shift,
                                        motif=lost_time_data.get('motif', ''),
                                        comment=lost_time_data.get('comment', ''),
                                        duration=int(lost_time_data.get('minutes', 0))
                                    )
                                    lost_time_entry.save()
                                    print(f"Temps d'arrêt sauvegardé: {lost_time_entry.motif} - {lost_time_entry.duration}min")
                            
                            # Lier les temps d'arrêt orphelins (créés sans shift) à ce shift
                            orphan_lost_times = LostTimeEntry.objects.filter(
                                session_key=session_key,
                                shift__isnull=True
                            )
                            if orphan_lost_times.exists():
                                orphan_lost_times.update(shift=shift, session_key=None)
                                print(f"DEBUG: {orphan_lost_times.count()} temps d'arrêt orphelins liés au shift {shift.shift_id}")
                            
                            # Recalculer le temps perdu total du shift maintenant que tous les temps d'arrêt sont liés
                            shift.lost_time = shift.calculate_lost_time()
                            
                            # Recalculer le temps disponible (TD = TO - Temps Perdu)
                            if shift.start_time and shift.end_time:
                                shift.availability_time = shift.opening_time - shift.lost_time
                            
                            shift.save(update_fields=['lost_time', 'availability_time'])
                            print(f"Temps perdu total mis à jour: {shift.lost_time}")
                            print(f"Temps disponible mis à jour: {shift.availability_time}")
                                
                        except CurrentSession.DoesNotExist:
                            pass
                
                # Vider seulement les données de fiche de poste (garder OF, lg cible, rouleau)
                session_key = request.session.session_key
                if session_key:
                    try:
                        current_session = CurrentSession.objects.get(session_key=session_key)
                        form_data = current_session.session_data
                        
                        # Garder seulement les données de production (OF, lg cible, rouleau)
                        # + reporter l'état machine de fin vers début pour le poste suivant
                        preserved_data = {}
                        fields_to_preserve = [
                            'currentOrderId', 'targetLength', 'cuttingOrderId',
                            'rollNumber', 'rollLength', 'tubeMass', 'totalMass', 'nextTubeMass'
                        ]
                        
                        # Préserver les données de production
                        for field in fields_to_preserve:
                            if field in form_data:
                                preserved_data[field] = form_data[field]
                        
                        # Ne pas reporter l'état machine entre les postes
                        
                        # Déterminer la vacation suivante
                        current_vacation = shift.vacation
                        next_vacation = 'Matin'  # Par défaut
                        if current_vacation == 'Matin':
                            next_vacation = 'ApresMidi'
                        elif current_vacation == 'ApresMidi':
                            next_vacation = 'Nuit'
                        elif current_vacation == 'Nuit':
                            next_vacation = 'Matin'
                        
                        preserved_data['vacation'] = next_vacation
                        
                        # Définir les heures par défaut selon la vacation
                        if next_vacation == 'Matin':
                            preserved_data['start_time'] = '04:00'
                            preserved_data['end_time'] = '12:00'
                        elif next_vacation == 'ApresMidi':
                            preserved_data['start_time'] = '12:00'
                            preserved_data['end_time'] = '20:00'
                        elif next_vacation == 'Nuit':
                            preserved_data['start_time'] = '20:00'
                            preserved_data['end_time'] = '04:00'
                        
                        # Préserver la date du jour pour le prochain poste
                        from datetime import date
                        preserved_data['date'] = date.today().strftime('%Y-%m-%d')
                        
                        # Préserver l'opérateur
                        preserved_data['operator'] = form.cleaned_data.get('operator').id if form.cleaned_data.get('operator') else ''
                        
                        # Ne pas prédéfinir l'état machine
                        
                        # IMPORTANT: Vider TOUTES les données de production après sauvegarde du poste
                        preserved_data['lostTimeEntries'] = []
                        preserved_data['totalLostTimeMinutes'] = 0
                        
                        # Vider seulement certaines données du rouleau (garder OF et longueur cible)
                        # preserved_data['currentOrderId'] est déjà préservé
                        # preserved_data['cuttingOrderId'] est déjà préservé
                        # preserved_data['targetLength'] est déjà préservé
                        # preserved_data['rollNumber'] est déjà préservé
                        preserved_data['tubeMass'] = ''
                        preserved_data['totalMass'] = ''
                        preserved_data['rollLength'] = ''
                        # preserved_data['nextTubeMass'] est déjà préservé
                        preserved_data['rollData'] = {}
                        
                        # Vider les contrôles qualité
                        preserved_data['qualityControls'] = {}
                        
                        # Vider la checklist
                        preserved_data['checklistData'] = {}
                        
                        # Vider le statut de conformité
                        preserved_data['conformityStatus'] = {
                            'status': 'CONFORME',
                            'destination': 'DECOUPE'
                        }
                        
                        # Sauvegarder les données préservées
                        current_session.session_data = preserved_data
                        current_session.save()
                        
                    except CurrentSession.DoesNotExist:
                        pass
                
                # Si requête HTMX, on renvoie un formulaire avec les données préservées
                if request.htmx:
                    from datetime import date
                    initial_data = {'date': date.today()}
                    
                    # Charger les données préservées si elles existent
                    if session_key:
                        try:
                            current_session = CurrentSession.objects.get(session_key=session_key)
                            preserved = current_session.session_data
                            # Ajouter les données préservées aux initial_data SAUF la date
                            # Ne pas reporter l'état machine
                            if preserved.get('vacation'):
                                initial_data['vacation'] = preserved.get('vacation')
                            if preserved.get('start_time'):
                                initial_data['start_time'] = preserved.get('start_time')
                            if preserved.get('end_time'):
                                initial_data['end_time'] = preserved.get('end_time')
                            # Charger la date depuis preserved (qui est toujours aujourd'hui après save)
                            if preserved.get('date'):
                                initial_data['date'] = preserved.get('date')
                        except CurrentSession.DoesNotExist:
                            pass
                    
                    new_form = ShiftForm(initial=initial_data)
                    context = {
                        'shift': None, 
                        'form': new_form,
                        'is_edit': False,
                        'save_success': True  # Indiquer que la sauvegarde a réussi
                    }
                    response = render(request, 'production/blocks/shift_block.html', context)
                    response['HX-Trigger'] = 'shiftSaveSuccess'
                    return response
                
                return redirect('production:prod')
            except Exception as e:
                print(f"DEBUG: Exception during save: {str(e)}")
                print(f"DEBUG: Exception type: {type(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Erreur lors de la sauvegarde: {str(e)}")
                if request.htmx:
                    context = {'form': form, 'shift': shift, 'is_edit': shift is not None}
                    return render(request, 'production/blocks/shift_block.html', context)
        else:
            print(f"DEBUG: Form is NOT valid")
            print(f"DEBUG: Form errors: {form.errors}")
            print(f"DEBUG: Form non-field errors: {form.non_field_errors()}")
            # Retourner le formulaire avec les erreurs pour que l'utilisateur les voie
            if request.htmx:
                context = {'form': form, 'shift': shift, 'is_edit': shift is not None}
                return render(request, 'production/blocks/shift_block.html', context)
    else:
        if shift is None:
            # Nouveau formulaire avec date d'aujourd'hui
            from datetime import date
            initial_data = {'date': date.today()}
            form = ShiftForm(initial=initial_data)
        else:
            form = ShiftForm(instance=shift)
    
    context = {
        'form': form,
        'shift': shift,
        'is_edit': shift is not None
    }
    
    # Si requête HTMX, on renvoie juste le bloc
    if request.htmx:
        return render(request, 'production/blocks/shift_block.html', context)
    
    return render(request, 'production/shift_form.html', context)


@require_POST
def operator_create(request):
    """Créer un nouvel opérateur via AJAX."""
    try:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        training_completed = request.POST.get('training_completed') == 'on'
        
        if not first_name or not last_name:
            return JsonResponse({
                'success': False,
                'error': 'Le prénom et le nom sont obligatoires'
            })
        
        # Créer l'opérateur
        operator = Operator.objects.create(
            first_name=first_name,
            last_name=last_name,
            training_completed=training_completed,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'operator': {
                'id': operator.id,
                'full_name': operator.full_name,
                'first_name': operator.first_name,
                'last_name': operator.last_name,
                'training_completed': operator.training_completed
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })











def get_shift_lost_times(request, shift_id):
    """Récupérer les temps d'arrêt d'un shift."""
    try:
        shift = get_object_or_404(Shift, id=shift_id)
        lost_times = shift.lost_time_entries.all().order_by('created_at')
        
        lost_times_data = []
        for lost_time in lost_times:
            lost_times_data.append({
                'motif': lost_time.motif,
                'comment': lost_time.comment,
                'duration': lost_time.duration
            })
        
        return JsonResponse({
            'success': True,
            'lost_times': lost_times_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération des temps d\'arrêt: {str(e)}'
        }, status=500)


def get_previous_shift_meter(request):
    """Récupérer le métrage de fin du poste précédent."""
    try:
        date_str = request.GET.get('date')
        vacation = request.GET.get('vacation')
        
        if not date_str or not vacation:
            return JsonResponse({
                'success': False,
                'error': 'Date et vacation requises'
            }, status=400)
        
        # Convertir la date string en objet date
        from datetime import datetime
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Chercher le shift correspondant
        shift = Shift.objects.filter(
            date=date,
            vacation=vacation,
            started_at_end=True,  # Machine démarrée en fin de poste
            meter_reading_end__isnull=False  # Avec un métrage de fin
        ).first()
        
        if shift:
            return JsonResponse({
                'success': True,
                'meter_reading_end': float(shift.meter_reading_end),
                'shift_id': shift.shift_id
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Pas de poste précédent trouvé avec métrage'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_total_rolled_length(request):
    """Récupère la longueur totale enroulée pour un shift."""
    try:
        shift_id = request.GET.get('shift_id')
        
        # Si pas de shift_id explicite, on est en création de nouveau poste
        # Ne PAS chercher un shift existant car on veut les longueurs de la session actuelle seulement
        # Ignorer les paramètres date/operator/vacation même s'ils sont envoyés
        
        # Calculer les longueurs par statut
        length_ok = 0
        length_nok = 0
        length_dechets = 0
        meter_start_to_subtract = 0
        
        if shift_id:
            # Récupérer les rouleaux du shift
            rolls = Roll.objects.filter(shift_id=shift_id)
            # Longueur OK (status CONFORME et destination PRODUCTION)
            length_ok = float(rolls.filter(status='CONFORME', destination='PRODUCTION').aggregate(total=Sum('length'))['total'] or 0)
            # Longueur NOK (destination DECOUPE)
            length_nok = float(rolls.filter(destination='DECOUPE').aggregate(total=Sum('length'))['total'] or 0)
            # Longueur Déchets (destination DECHETS)
            length_dechets = float(rolls.filter(destination='DECHETS').aggregate(total=Sum('length'))['total'] or 0)
            
            # Récupérer le shift pour avoir le métrage de début
            try:
                shift = Shift.objects.get(id=shift_id)
                if shift.meter_reading_start:
                    meter_start_to_subtract = float(shift.meter_reading_start)
                    
                    # Trouver le premier rouleau du poste pour savoir où soustraire
                    first_roll = rolls.order_by('created_at').first()
                    if first_roll:
                        if first_roll.status == 'CONFORME' and first_roll.destination == 'PRODUCTION':
                            # Soustraire du OK
                            length_ok = max(0, length_ok - meter_start_to_subtract)
                        elif first_roll.destination == 'DECOUPE':
                            # Soustraire du NOK
                            length_nok = max(0, length_nok - meter_start_to_subtract)
                        elif first_roll.destination == 'DECHETS':
                            # Soustraire des déchets
                            length_dechets = max(0, length_dechets - meter_start_to_subtract)
            except Shift.DoesNotExist:
                pass
        else:
            # Si pas de shift, chercher par session
            session_key = request.session.session_key
            if session_key:
                rolls = Roll.objects.filter(session_key=session_key, shift__isnull=True)
                length_ok = float(rolls.filter(status='CONFORME', destination='PRODUCTION').aggregate(total=Sum('length'))['total'] or 0)
                length_nok = float(rolls.filter(destination='DECOUPE').aggregate(total=Sum('length'))['total'] or 0)
                length_dechets = float(rolls.filter(destination='DECHETS').aggregate(total=Sum('length'))['total'] or 0)
        
        # Calculer le total
        total_length = length_ok + length_nok + length_dechets
        
        return JsonResponse({
            'success': True,
            'total_length': float(total_length),
            'length_ok': float(length_ok),
            'length_nok': float(length_nok),
            'length_dechets': float(length_dechets)
        })
        
    except Exception as e:
        import traceback
        print(f"[{datetime.now().strftime('%d/%b/%Y %H:%M:%S')}] ERREUR get_total_rolled_length: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
