from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django_htmx.http import HttpResponseClientRedirect
import json
from datetime import datetime
from .models import Shift, CurrentProd, QualityControlSeries
from .forms import ShiftForm
from core.models import Operator
from quality.models import DefectType


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
                
                # Maintenant sauvegarder les contrôles qualité
                if session_key:
                    try:
                        current_prod = CurrentProd.objects.get(session_key=session_key)
                        quality_data = current_prod.form_data.get('qualityControls', {})
                        
                        # Créer l'objet QualityControlSeries (on sait qu'ils sont complets)
                        quality_control = QualityControlSeries(shift=shift)
                        
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
                        if hasattr(shift, 'started_at_end') and shift.started_at_end:
                            preserved_data['started_at_beginning'] = True
                            # Reporter le métrage de fin vers début
                            if hasattr(shift, 'meter_reading_end') and shift.meter_reading_end:
                                preserved_data['meter_reading_start'] = str(shift.meter_reading_end)
                            print(f"DEBUG: Machine démarrée en fin, reporté vers début. Métrage: {shift.meter_reading_end}")
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
                        
                        # Garder la date d'aujourd'hui
                        from datetime import date
                        preserved_data['date'] = date.today().strftime('%Y-%m-%d')
                        
                        # Machine toujours démarrée en fin par défaut
                        preserved_data['started_at_end'] = True
                        # Vider le métrage de fin pour le prochain formulaire
                        preserved_data['meter_reading_end'] = ''
                        
                        # Sauvegarder les données préservées
                        current_prod.form_data = preserved_data
                        current_prod.save()
                        
                    except CurrentProd.DoesNotExist:
                        pass
                
                # Si requête HTMX, on renvoie un formulaire vide
                # L'auto-save/restore va restaurer les données appropriées
                if request.htmx:
                    from datetime import date
                    initial_data = {'date': date.today()}
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
        # Ici on vérifierait dans une table Roll si elle existait
        # Pour l'instant on simule une vérification - TEMPORAIRE pour test
        exists = True  # Simuler qu'il existe déjà pour tester l'affichage
        
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
            operator = Operator.objects.get(id=operator_id)
        except Operator.DoesNotExist:
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