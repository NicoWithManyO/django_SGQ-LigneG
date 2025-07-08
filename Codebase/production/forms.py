from django import forms
from django.core.exceptions import ValidationError
from .models import Shift
from core.models import Operator
from datetime import time


class ShiftForm(forms.ModelForm):
    """Formulaire pour la saisie des données de poste."""
    
    # Champs pour les heures de début et fin
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control fw-bold'
        }),
        label="Heure de début",
        help_text="Heure de début du poste",
        required=False
    )
    
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control fw-bold'
        }),
        label="Heure de fin",
        help_text="Heure de fin du poste",
        required=False
    )
    
    # Redéfinir le champ vacation avec placeholder
    vacation = forms.ChoiceField(
        choices=[('', '--')] + list(Shift.VACATION_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select fw-bold'}),
        label="Vacation",
        help_text="Vacation du poste",
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Appeler la méthode pour finaliser l'initialisation
        self.finish_init()
    
    class Meta:
        model = Shift
        fields = [
            'date', 'operator', 'vacation',
            'start_time', 'end_time',
            'started_at_beginning', 'meter_reading_start',
            'started_at_end', 'meter_reading_end',
            'total_length', 'ok_length', 'nok_length',
            'operator_comments'
        ]
        
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control fw-bold'
            }),
            'operator': forms.Select(attrs={
                'class': 'form-select fw-bold'
            }),
            'started_at_beginning': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'meter_reading_start': forms.NumberInput(attrs={
                'class': 'form-control fw-bold',
                'step': '1',
                'min': '0',
                'placeholder': 'Métrage si démarrée'
            }),
            'started_at_end': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'meter_reading_end': forms.NumberInput(attrs={
                'class': 'form-control fw-bold',
                'step': '1',
                'min': '0',
                'placeholder': 'Métrage si démarrée'
            }),
            'total_length': forms.NumberInput(attrs={
                'class': 'form-control fw-bold',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Longueur totale en mètres'
            }),
            'ok_length': forms.NumberInput(attrs={
                'class': 'form-control fw-bold',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Longueur conforme en mètres'
            }),
            'nok_length': forms.NumberInput(attrs={
                'class': 'form-control fw-bold',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Longueur non conforme en mètres'
            }),
            'operator_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Commentaires de l\'opérateur...'
            })
        }
    
    def finish_init(self):
        # Filtrer les opérateurs actifs avec formation terminée et les trier alphabétiquement
        self.fields['operator'].queryset = Operator.objects.filter(
            is_active=True,
            training_completed=True
        ).order_by('first_name')
        
        # Supprimer l'option vide (placeholder) pour le champ operator
        self.fields['operator'].empty_label = '--'
        
        # Rendre certains champs optionnels pour la saisie progressive
        self.fields['meter_reading_start'].required = False
        self.fields['meter_reading_end'].required = False
        self.fields['total_length'].required = False
        self.fields['ok_length'].required = False
        self.fields['nok_length'].required = False
        self.fields['operator_comments'].required = False
        
        # Valeurs par défaut pour nouveau formulaire
        if not self.instance.pk:  # Nouveau formulaire
            from datetime import date
            self.fields['date'].initial = date.today()
            # Machine toujours démarrée en fin de poste par défaut
            self.fields['started_at_end'].initial = True
            
        # Forcer les valeurs des checkboxes si définies dans les initiales
        if 'started_at_beginning' in self.initial:
            self.fields['started_at_beginning'].initial = self.initial['started_at_beginning']
        if 'started_at_end' in self.initial:
            self.fields['started_at_end'].initial = self.initial['started_at_end']
        
        
    def clean(self):
        """Validation personnalisée du formulaire."""
        cleaned_data = super().clean()
        
        # Validation des heures de début et fin
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            # Simuler la durée du poste pour validation
            from datetime import datetime, timedelta
            today = datetime.today().date()
            start_datetime = datetime.combine(today, start_time)
            end_datetime = datetime.combine(today, end_time)
            
            # Si l'heure de fin est avant l'heure de début, c'est que le poste passe minuit
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
            
            duration = end_datetime - start_datetime
            
            # Vérifier que la durée est raisonnable
            if duration > timedelta(hours=24):
                raise ValidationError("La durée du poste ne peut pas dépasser 24 heures.")
            if duration <= timedelta(0):
                raise ValidationError("L'heure de fin doit être après l'heure de début.")
        
        # Validation des longueurs (sans raw_waste_length)
        total = cleaned_data.get('total_length', 0)
        ok = cleaned_data.get('ok_length', 0)
        nok = cleaned_data.get('nok_length', 0)
        
        if total and (ok + nok) > total:
            raise ValidationError(
                "La somme des longueurs OK + NOK ne peut pas dépasser la longueur totale."
            )
        
        # Validation conditionnelle des meter_reading
        started_at_beginning = cleaned_data.get('started_at_beginning', False)
        meter_reading_start = cleaned_data.get('meter_reading_start')
        
        if started_at_beginning and not meter_reading_start:
            raise ValidationError(
                "Le métrage de début est obligatoire si la machine est démarrée en début de poste."
            )
        
        started_at_end = cleaned_data.get('started_at_end', False)
        meter_reading_end = cleaned_data.get('meter_reading_end')
        
        if started_at_end and not meter_reading_end:
            raise ValidationError(
                "Le métrage de fin est obligatoire si la machine est démarrée en fin de poste."
            )
        
        return cleaned_data