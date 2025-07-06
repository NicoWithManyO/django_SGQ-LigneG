from django import forms
from django.core.exceptions import ValidationError
from .models import Shift
from core.models import Operator
from datetime import time


class ShiftForm(forms.ModelForm):
    """Formulaire pour la saisie des données de poste."""
    
    # Générer les choix pour opening_time par tranches de 10 minutes avec minutes
    OPENING_TIME_CHOICES = []
    for hour in range(0, 11):  # De 0h à 10h
        for minute in [0, 10, 20, 30, 40, 50]:
            if hour == 0 and minute < 30:  # Min: 00:30
                continue
            if hour == 10 and minute > 0:  # Max: 10:00
                break
            time_obj = time(hour, minute)
            time_str = time_obj.strftime('%H:%M')
            total_minutes = hour * 60 + minute
            display_str = f"{time_str} ({total_minutes} min)"
            OPENING_TIME_CHOICES.append((time_str, display_str))
    
    # Mettre 08:00 en premier
    OPENING_TIME_CHOICES.sort(key=lambda x: (x[0] != '08:00', x[0]))
    
    opening_time = forms.ChoiceField(
        choices=OPENING_TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select fw-bold'}),
        label="Temps d'ouverture",
        help_text="Temps d'ouverture du poste (par tranches de 10 minutes)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Appeler la méthode pour finaliser l'initialisation
        self.finish_init()
    
    class Meta:
        model = Shift
        fields = [
            'date', 'operator', 'vacation',
            'opening_time',
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
            'vacation': forms.Select(attrs={
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
        # Filtrer les opérateurs actifs avec formation terminée
        self.fields['operator'].queryset = Operator.objects.filter(
            is_active=True,
            training_completed=True
        )
        
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
            self.fields['opening_time'].initial = '08:00'
            # Machine toujours démarrée en fin de poste par défaut
            self.fields['started_at_end'].initial = True
            
        # Forcer les valeurs des checkboxes si définies dans les initiales
        if 'started_at_beginning' in self.initial:
            self.fields['started_at_beginning'].initial = self.initial['started_at_beginning']
        if 'started_at_end' in self.initial:
            self.fields['started_at_end'].initial = self.initial['started_at_end']
        
    def clean_opening_time(self):
        """Validation du temps d'ouverture."""
        opening_time_str = self.cleaned_data.get('opening_time')
        if opening_time_str:
            # Convertir la string en objet time pour validation
            from datetime import time
            try:
                hour, minute = map(int, opening_time_str.split(':'))
                opening_time = time(hour, minute)
            except ValueError:
                raise ValidationError("Format d'heure invalide")
            
            min_time = time(0, 30)  # 00:30
            max_time = time(10, 0)  # 10:00
            
            if not (min_time <= opening_time <= max_time):
                raise ValidationError(
                    "Le temps d'ouverture doit être entre 00:30 et 10:00"
                )
            
            # Vérifier que les minutes sont des multiples de 10
            if opening_time.minute % 10 != 0:
                raise ValidationError(
                    "Le temps d'ouverture doit être par tranches de 10 minutes (ex: 06:00, 06:10, 06:20...)"
                )
        
        return opening_time_str
        
    def clean(self):
        """Validation personnalisée du formulaire."""
        cleaned_data = super().clean()
        
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