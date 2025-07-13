from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django_htmx.http import HttpResponseClientRedirect
import json
from datetime import datetime
from django.db.models import Sum, Q
from .models import Shift, CurrentProd, QualityControl, Roll, RollDefect, RollThickness, LostTimeEntry, MachineParameters
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
                    current_prod = CurrentProd.objects.get(session_key=session_key)
                    quality_data = current_prod.form_data.get('qualityControls', {})
                    
                    # Vérifier si des contrôles qualité existent et sont complets
                    micrometers_left = [v for v in quality_data.get('micrometerLeft', []) if v]
                    micrometers_right = [v for v in quality_data.get('micrometerRight', []) if v]
                    micrometers_filled = (len(micrometers_left) == 3 and len(micrometers_right) == 3)
                    
                    sizing_bath_filled = bool(quality_data.get('sizingBath'))
                    
                    mass_left = [v for v in quality_data.get('surfaceMassLeft', []) if v]
                    mass_right = [v for v in quality_data.get('surfaceMassRight', []) if v]
                    mass_filled = (len(mass_left) == 2 and len(mass_right) == 2)
                    
                    loi_filled = quality_data.get('loiGiven', False)
                    
                    # Vérifier si TOUS les contrôles sont remplis
                    all_quality_filled = micrometers_filled and sizing_bath_filled and mass_filled and loi_filled
                    
                    # VÉRIFIER LA CHECK-LIST
                    checklist_data = current_prod.form_data.get('checklistData', {})
                    checklist_signature = checklist_data.get('signature', '').strip()
                    checklist_signed = bool(checklist_signature)
                    
                except CurrentProd.DoesNotExist:
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
                        current_prod = CurrentProd.objects.get(session_key=session_key)
                        quality_data = current_prod.form_data.get('qualityControls', {})
                        
                        # Créer l'objet QualityControl (on sait qu'ils sont complets)
                        quality_control = QualityControl(shift=shift)
                        
                        # Remplir les valeurs Micronnaire
                        micrometer_left = quality_data.get('micrometerLeft', [])
                        if len(micrometer_left) >= 3:
                            quality_control.micrometer_left_1 = float(micrometer_left[0]) if micrometer_left[0] else None
                            quality_control.micrometer_left_2 = float(micrometer_left[1]) if micrometer_left[1] else None
                            quality_control.micrometer_left_3 = float(micrometer_left[2]) if micrometer_left[2] else None
                        
                        micrometer_right = quality_data.get('micrometerRight', [])
                        if len(micrometer_right) >= 3:
                            quality_control.micrometer_right_1 = float(micrometer_right[0]) if micrometer_right[0] else None
                            quality_control.micrometer_right_2 = float(micrometer_right[1]) if micrometer_right[1] else None
                            quality_control.micrometer_right_3 = float(micrometer_right[2]) if micrometer_right[2] else None
                        
                        # Extrait Sec
                        if quality_data.get('sizingBath'):
                            quality_control.dry_extract = float(quality_data['sizingBath'].replace(',', '.'))
                        
                        # Heure Extrait Sec
                        if quality_data.get('sizingBathTime') and quality_data['sizingBathTime'] != '--':
                            try:
                                quality_control.dry_extract_time = datetime.strptime(quality_data['sizingBathTime'], '%H:%M').time()
                            except:
                                pass
                        
                        # Masses Surfaciques
                        surface_mass_left = quality_data.get('surfaceMassLeft', [])
                        if len(surface_mass_left) >= 2:
                            # GG et GC
                            if surface_mass_left[0]:
                                quality_control.surface_mass_gg = float(surface_mass_left[0].replace(',', '.'))
                            if surface_mass_left[1]:
                                quality_control.surface_mass_gc = float(surface_mass_left[1].replace(',', '.'))
                        
                        surface_mass_right = quality_data.get('surfaceMassRight', [])
                        if len(surface_mass_right) >= 2:
                            # DC et DD
                            if surface_mass_right[0]:
                                quality_control.surface_mass_dc = float(surface_mass_right[0].replace(',', '.'))
                            if surface_mass_right[1]:
                                quality_control.surface_mass_dd = float(surface_mass_right[1].replace(',', '.'))
                        
                        # LOI
                        quality_control.loi_given = quality_data.get('loiGiven', False)
                        if quality_data.get('loiTime') and quality_data['loiTime'] != '--':
                            try:
                                quality_control.loi_time = datetime.strptime(quality_data['loiTime'], '%H:%M').time()
                            except:
                                pass
                        
                        # Opérateur
                        quality_control.created_by = shift.operator
                        
                        # Sauvegarder
                        quality_control.save()
                        print(f"Contrôles qualité sauvegardés pour le shift {shift.shift_id}")
                    
                    except CurrentProd.DoesNotExist:
                        pass
                    
                    # Sauvegarder la check-list
                    if session_key:
                        try:
                            current_prod = CurrentProd.objects.get(session_key=session_key)
                            checklist_data = current_prod.form_data.get('checklistData', {})
                            
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
                        
                        except CurrentProd.DoesNotExist:
                            pass
                    
                    # Sauvegarder les temps d'arrêt
                    if session_key:
                        try:
                            current_prod = CurrentProd.objects.get(session_key=session_key)
                            lost_times = current_prod.form_data.get('lostTimeEntries', [])
                            
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
                                
                        except CurrentProd.DoesNotExist:
                            pass
                
                # Vider seulement les données de fiche de poste (garder OF, lg cible, rouleau)
                session_key = request.session.session_key
                if session_key:
                    try:
                        current_prod = CurrentProd.objects.get(session_key=session_key)
                        form_data = current_prod.form_data
                        
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
                        current_prod.form_data = preserved_data
                        current_prod.save()
                        
                    except CurrentProd.DoesNotExist:
                        pass
                
                # Si requête HTMX, on renvoie un formulaire avec les données préservées
                if request.htmx:
                    from datetime import date
                    initial_data = {'date': date.today()}
                    
                    # Charger les données préservées si elles existent
                    if session_key:
                        try:
                            current_prod = CurrentProd.objects.get(session_key=session_key)
                            preserved = current_prod.form_data
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
                        except CurrentProd.DoesNotExist:
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


@require_http_methods(["POST"])
def shift_save_field(request, shift_id):
    """Sauvegarde d'un champ spécifique via HTMX."""
    shift = get_object_or_404(Shift, pk=shift_id)
    field_name = request.POST.get('field_name')
    field_value = request.POST.get('field_value')
    
    if hasattr(shift, field_name):
        try:
            # Conversion du type selon le champ
            field = shift._meta.get_field(field_name)
            
            if field.get_internal_type() == 'DecimalField':
                field_value = float(field_value) if field_value else 0
            elif field.get_internal_type() == 'DurationField':
                # Traitement spécial pour les durées
                pass
            
            setattr(shift, field_name, field_value)
            shift.save()
            
            return HttpResponse(f'<span class="text-success">✓ Sauvegardé</span>')
        except Exception as e:
            return HttpResponse(f'<span class="text-danger">Erreur: {str(e)}</span>')
    
    return HttpResponse('<span class="text-danger">Champ invalide</span>')


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


@require_POST
def auto_save_form(request):
    """Auto-sauvegarde des données du formulaire."""
    try:
        # Récupérer les données JSON
        data = json.loads(request.body)
        
        # Utiliser la session key pour identifier la saisie
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        # Créer ou mettre à jour l'enregistrement
        current_prod, created = CurrentProd.objects.get_or_create(
            session_key=session_key,
            defaults={'form_data': data}
        )
        
        if not created:
            current_prod.form_data = data
            current_prod.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Données sauvegardées',
            'timestamp': current_prod.updated_at.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur de sauvegarde: {str(e)}'
        }, status=500)


@require_POST
def save_quality_controls(request):
    """Fonction désactivée - les contrôles qualité sont maintenant sauvegardés avec le poste."""
    return JsonResponse({
        'success': False,
        'error': 'Cette fonction est désactivée. Les contrôles qualité sont sauvegardés avec le poste.'
    })


def get_saved_form_data(request):
    """Récupérer les données sauvegardées du formulaire."""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'data': {}})
    
    try:
        current_prod = CurrentProd.objects.get(session_key=session_key)
        return JsonResponse({
            'data': current_prod.form_data,
            'timestamp': current_prod.updated_at.isoformat()
        })
    except CurrentProd.DoesNotExist:
        return JsonResponse({'data': {}})


@require_POST
def clear_saved_form_data(request):
    """Supprimer les données sauvegardées du formulaire."""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'success': True, 'message': 'Rien à supprimer'})
    
    try:
        CurrentProd.objects.filter(session_key=session_key).delete()
        return JsonResponse({
            'success': True,
            'message': 'Données supprimées'
        })
    except CurrentProd.DoesNotExist:
        return JsonResponse({
            'success': True,
            'message': 'Aucune donnée à supprimer'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur de suppression: {str(e)}'
        }, status=500)


def check_roll_id(request):
    """Vérifier si un ID de rouleau existe déjà."""
    roll_id = request.GET.get('roll_id', '').strip()
    if not roll_id:
        return JsonResponse({'exists': False})
    
    try:
        # Vérifier si un rouleau avec cet ID existe déjà
        exists = Roll.objects.filter(roll_id=roll_id).exists()
        
        return JsonResponse({
            'exists': exists,
            'roll_id': roll_id
        })
        
    except Exception as e:
        return JsonResponse({
            'exists': False,
            'error': f'Erreur de vérification: {str(e)}'
        }, status=500)


@require_POST
def check_shift_exists(request):
    """Vérifier si un shift existe déjà en utilisant les données du formulaire."""
    try:
        # Récupérer les données JSON du POST
        data = json.loads(request.body)
        
        # Extraire les données nécessaires
        date_str = data.get('date', '').strip()
        operator_id = data.get('operator', '').strip()
        vacation = data.get('vacation', '').strip()
        
        # Vérifier que toutes les données sont présentes
        if not all([date_str, operator_id, vacation]):
            return JsonResponse({
                'exists': False,
                'error': 'Données manquantes (date, operator, vacation)'
            }, status=400)
        
        # Convertir la date
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'exists': False,
                'error': 'Format de date invalide'
            }, status=400)
        
        # Récupérer l'opérateur
        try:
            if operator_id:
                operator = Operator.objects.get(id=operator_id)
            else:
                return JsonResponse({
                    'exists': False,
                    'error': 'Aucun opérateur sélectionné'
                }, status=400)
        except (Operator.DoesNotExist, ValueError):
            return JsonResponse({
                'exists': False,
                'error': 'Opérateur introuvable'
            }, status=400)
        
        # Générer le shift_id selon le même format que le modèle
        # Format: JJMMAA_PrenomNom_Vacation
        date_formatted = date_obj.strftime('%d%m%y')
        operator_clean = operator.full_name_no_space
        shift_id = f"{date_formatted}_{operator_clean}_{vacation}"
        
        # Vérifier si un shift avec ce shift_id existe déjà
        exists = Shift.objects.filter(shift_id=shift_id).exists()
        
        return JsonResponse({
            'exists': exists,
            'shift_id': shift_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'exists': False,
            'error': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'exists': False,
            'error': f'Erreur de vérification: {str(e)}'
        }, status=500)

@require_POST
def save_roll(request):
    """Sauvegarder un rouleau avec ses défauts et mesures d'épaisseur."""
    try:
        # Récupérer les données de la session
        session_key = request.session.session_key
        if not session_key:
            return JsonResponse({
                'success': False,
                'error': 'Session non trouvée'
            }, status=400)
        
        try:
            current_prod = CurrentProd.objects.get(session_key=session_key)
            form_data = current_prod.form_data
        except CurrentProd.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Aucune donnée de production en cours'
            }, status=400)
        
        # Récupérer les données du rouleau
        roll_data = form_data.get('rollData', {})
        roll_number = form_data.get('rollNumber')
        roll_length = form_data.get('rollLength')
        tube_mass = form_data.get('tubeMass')
        total_mass = form_data.get('totalMass')
        
        # Vérifier les données requises
        if not all([roll_number, roll_length, tube_mass, total_mass]):
            return JsonResponse({
                'success': False,
                'error': 'Données du rouleau incomplètes'
            }, status=400)
        
        # Récupérer le shift actuel (le plus récent) si il existe
        operator_id = form_data.get('operator')
        if operator_id and operator_id != '':
            shift = Shift.objects.filter(
                operator__id=operator_id,
                date=form_data.get('date')
            ).order_by('-created_at').first()
        else:
            shift = None
        
        # shift peut être None, ce n'est pas un problème
        
        # Construire l'ID du shift même s'il n'est pas encore sauvegardé
        shift_id_str = None
        if form_data.get('date') and form_data.get('operator') and form_data.get('vacation'):
            try:
                from datetime import datetime
                date_obj = datetime.strptime(form_data.get('date'), '%Y-%m-%d').date()
                date_str = date_obj.strftime('%d%m%y')
                
                # Récupérer l'opérateur pour avoir son nom complet sans espaces
                operator_id = form_data.get('operator')
                if operator_id and operator_id != '':
                    operator = Operator.objects.get(id=operator_id)
                    operator_clean = operator.full_name_no_space
                else:
                    operator_clean = 'UnknownOperator'
                
                vacation = form_data.get('vacation')
                shift_id_str = f"{date_str}_{operator_clean}_{vacation}"
            except Exception as e:
                print(f"Erreur lors de la construction du shift_id_str: {e}")
                pass
        
        # Récupérer l'OF
        of_id = form_data.get('currentOrderId')
        if not of_id or of_id == '':
            return JsonResponse({
                'success': False,
                'error': 'Aucun ordre de fabrication sélectionné'
            }, status=400)
        
        try:
            fabrication_order = FabricationOrder.objects.get(id=of_id)
        except (FabricationOrder.DoesNotExist, ValueError):
            return JsonResponse({
                'success': False,
                'error': 'Ordre de fabrication non trouvé'
            }, status=400)
        
        # Déterminer le statut et la destination basé sur la validation UI
        # Récupérer le statut depuis les données du formulaire (calculé côté client)
        conformity_data = form_data.get('conformityStatus', {})
        status_from_ui = conformity_data.get('status', 'CONFORME')
        
        # Vérifier les défauts bloquants
        defects_data = roll_data.get('defects', {})
        has_blocking_defects = any(defects_data.values())  # Simplifié pour l'instant
        
        # Vérifier les problèmes d'épaisseur
        # TODO: Implémenter la logique de validation des épaisseurs
        has_thickness_issues = False
        
        # Utiliser le statut de l'UI qui a déjà fait la validation
        if status_from_ui == 'NON CONFORME':
            status = 'NON_CONFORME'
            destination = 'DECOUPE'
        else:
            status = 'CONFORME'
            destination = 'PRODUCTION'
        
        # Générer le roll_id selon le statut
        if status == 'NON_CONFORME':
            # Récupérer l'OF de découpe
            cutting_order_id = form_data.get('cuttingOrderId')
            if cutting_order_id and cutting_order_id != '':
                try:
                    cutting_order = FabricationOrder.objects.get(id=cutting_order_id)
                    cutting_order_number = cutting_order.order_number
                except:
                    cutting_order_number = 'OFDecoupe'
            else:
                cutting_order_number = 'OFDecoupe'
            
            # Format pour non conforme: OFDecoupe_JJMMAA_HHMM
            from datetime import datetime
            now = datetime.now()
            date_str = now.strftime('%d%m%y')
            time_str = now.strftime('%H%M')
            roll_id = f"{cutting_order_number}_{date_str}_{time_str}"
        else:
            # Format pour conforme: OF_NumRouleau
            roll_id = f"{fabrication_order.order_number}_{int(roll_number):03d}"
        
        # Créer le rouleau (avec shift si disponible, sinon avec session_key)
        roll = Roll.objects.create(
            roll_id=roll_id,  # Passer l'ID généré
            shift=shift,  # Peut être None
            shift_id_str=shift.shift_id if shift else shift_id_str,  # Utiliser l'ID construit si pas de shift
            session_key=session_key if not shift else None,  # Stocker session_key si pas de shift
            fabrication_order=fabrication_order,
            roll_number=int(roll_number),
            length=float(roll_length),
            tube_mass=float(tube_mass),
            total_mass=float(total_mass),
            status=status,
            destination=destination,
            has_blocking_defects=has_blocking_defects,
            has_thickness_issues=has_thickness_issues
        )
        
        # Sauvegarder les défauts
        defects_data = roll_data.get('defects', {})
        for meter_str, positions in defects_data.items():
            meter = int(meter_str)
            for position, defect_name in positions.items():
                if defect_name and defect_name.strip():
                    RollDefect.objects.create(
                        roll=roll,
                        defect_name=defect_name.strip(),
                        meter_position=meter,
                        side_position=position
                    )
        
        # Sauvegarder les mesures d'épaisseur principales
        thickness_data = roll_data.get('thicknessMeasurements', {})
        for meter_str, measurements in thickness_data.items():
            meter = int(meter_str)
            for point, value in measurements.items():
                if value:
                    RollThickness.objects.create(
                        roll=roll,
                        meter_position=meter,
                        measurement_point=point,
                        thickness_value=float(value),
                        is_catchup=False
                    )
        
        # Sauvegarder les mesures de rattrapage
        catchup_data = roll_data.get('thicknessCatchups', {})
        for meter_str, measurements in catchup_data.items():
            meter = int(meter_str)
            for point, value in measurements.items():
                if value:
                    RollThickness.objects.create(
                        roll=roll,
                        meter_position=meter,
                        measurement_point=point,
                        thickness_value=float(value),
                        is_catchup=True
                    )
        
        # Incrémenter le numéro de rouleau SEULEMENT si le rouleau est CONFORME
        if status == 'CONFORME':
            new_roll_number = int(roll_number) + 1
            current_prod.form_data['rollNumber'] = str(new_roll_number)
        else:
            # Pour un rouleau NON CONFORME, garder le même numéro
            new_roll_number = int(roll_number)
        
        # Nettoyer les données du rouleau mais garder le reste
        current_prod.form_data['rollLength'] = ''
        current_prod.form_data['tubeMass'] = ''
        current_prod.form_data['totalMass'] = ''
        current_prod.form_data['rollData'] = {
            'thicknessMeasurements': {},
            'thicknessCatchups': {},
            'defects': {}
        }
        
        # Sauvegarder les changements
        current_prod.save()
        
        # Recalculer les moyennes du shift si le rouleau a un shift associé
        if roll.shift:
            roll.shift.calculate_roll_averages()
            roll.shift.save(update_fields=['avg_thickness_left_shift', 'avg_thickness_right_shift', 'avg_grammage_shift'])
        
        return JsonResponse({
            'success': True,
            'roll_id': roll.roll_id,
            'new_roll_number': new_roll_number,
            'message': f'Rouleau {roll.roll_id} sauvegardé avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la sauvegarde: {str(e)}'
        }, status=500)


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
