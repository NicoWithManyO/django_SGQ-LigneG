from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django_htmx.http import HttpResponseClientRedirect
import json
from datetime import datetime
from .models import Shift, CurrentProd, QualityControl, Roll, RollDefect, RollThickness, LostTimeEntry
from .forms import ShiftForm
from core.models import Operator, FabricationOrder
from quality.models import DefectType


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


def prod(request):
    """Vue principale de production."""
    shifts = Shift.objects.select_related('operator').order_by('-date', '-created_at')[:10]
    defect_types = DefectType.objects.filter(is_active=True).order_by('name')
    
    context = {
        'shifts': shifts,
        'defect_types': defect_types,
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
            
            # VÉRIFIER LES CONTRÔLES QUALITÉ AVANT DE SAUVEGARDER LE SHIFT
            session_key = request.session.session_key
            all_quality_filled = False
            
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
                    
                except CurrentProd.DoesNotExist:
                    all_quality_filled = False
            
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
                shift = form.save()
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
                        
                        # Reporter l'état machine de fin vers début pour le poste suivant
                        # D'abord essayer de récupérer depuis les données du formulaire
                        started_at_end = form.cleaned_data.get('started_at_end', False)
                        meter_reading_end = form.cleaned_data.get('meter_reading_end', None)
                        
                        # Si pas dans cleaned_data, essayer depuis form_data (auto-save)
                        if 'started_at_end' in form_data:
                            started_at_end = form_data.get('started_at_end', False)
                        if 'meter_reading_end' in form_data:
                            meter_reading_end = form_data.get('meter_reading_end', None)
                        
                        if started_at_end:
                            preserved_data['started_at_beginning'] = True
                            # Reporter le métrage de fin vers début
                            if meter_reading_end:
                                preserved_data['meter_reading_start'] = str(meter_reading_end)
                            print(f"DEBUG: Machine démarrée en fin, reporté vers début. Métrage: {meter_reading_end}")
                        else:
                            preserved_data['started_at_beginning'] = False
                            preserved_data['meter_reading_start'] = ''
                            print(f"DEBUG: Machine pas démarrée en fin, début mis à False")
                        
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
                        
                        # Machine toujours démarrée en fin par défaut
                        preserved_data['started_at_end'] = True
                        # NE PAS vider le métrage de fin car il sera utilisé comme métrage de début du prochain poste
                        # preserved_data['meter_reading_end'] = ''
                        
                        # Reporter la longueur enroulée en fin vers le début du prochain poste
                        # Si on a un shift qui vient d'être sauvegardé, prendre sa longueur totale
                        if shift and shift.total_length:
                            preserved_data['meter_reading_start'] = str(float(shift.total_length))
                            print(f"DEBUG: Longueur totale du poste reportée: {shift.total_length} m")
                        
                        # IMPORTANT: Vider TOUTES les données de production après sauvegarde du poste
                        preserved_data['lostTimeEntries'] = []
                        preserved_data['totalLostTimeMinutes'] = 0
                        
                        # Vider les données du rouleau
                        preserved_data['currentOrderId'] = ''
                        preserved_data['cuttingOrderId'] = ''
                        preserved_data['targetLength'] = ''
                        preserved_data['rollNumber'] = ''
                        preserved_data['tubeMass'] = ''
                        preserved_data['totalMass'] = ''
                        preserved_data['rollLength'] = ''
                        preserved_data['nextTubeMass'] = ''
                        preserved_data['rollData'] = {}
                        
                        # Vider les contrôles qualité
                        preserved_data['qualityControls'] = {}
                        
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
                            if preserved.get('started_at_beginning'):
                                initial_data['started_at_beginning'] = True
                            if preserved.get('meter_reading_start'):
                                initial_data['meter_reading_start'] = preserved.get('meter_reading_start')
                            if preserved.get('started_at_end'):
                                initial_data['started_at_end'] = True
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
            
            # Format pour non conforme: OFDecoupe_JJMMAA
            from datetime import datetime
            now = datetime.now()
            date_str = now.strftime('%d%m%y')
            roll_id = f"{cutting_order_number}_{date_str}"
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
