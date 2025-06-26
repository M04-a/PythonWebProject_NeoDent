from django import forms
from .models import Doctor, Programare
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from .models import Consultatie, Interventie
from django.forms import inlineformset_factory

class ProgramareForm(forms.Form):
    pacient = forms.ModelChoiceField(
        queryset=User.objects.none(),  # inițial gol
        required=False,
        label="Pacient (doar pentru secretariat)"
    )

    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all())


    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    ora = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # primim userul în view
        super().__init__(*args, **kwargs)

        # Populează ora
        ore_disponibile = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(10, 18)]
        self.fields['ora'].choices = ore_disponibile

        # Dacă e secretar, populăm câmpul pacient
        if user and hasattr(user, 'secretariat'):
            self.fields['pacient'].queryset = User.objects.filter(
                is_staff=False, is_superuser=False
            ).exclude(doctor__isnull=False).exclude(secretariat__isnull=False)
        else:
            self.fields.pop('pacient')

class InregistrareForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label='Prenume', max_length=30)
    last_name = forms.CharField(label='Nume', max_length=30)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def clean_email(self):
        print("=== CLEAN_EMAIL ESTE APELAT ===")
        email = self.cleaned_data.get('email')
        print(f"Email primit: {email}")
        if User.objects.filter(email=email).exists():
            print("EMAIL EXISTĂ DEJA!")
            raise ValidationError('Acest email este deja folosit.')
        return email

class ConsultatieForm(forms.ModelForm):
    class Meta:
        model = Consultatie
        fields = ['dinte', 'tip', 'observatii', 'cost_total', 'nume_medic']
        widgets = {
            'dinte': forms.TextInput(attrs={'class': 'form-control'}),
            'tip': forms.Select(attrs={'class': 'form-select'}),
            'observatii': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cost_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'nume_medic': forms.TextInput(attrs={'class': 'form-control'}),
        }

class InterventieForm(forms.ModelForm):
    class Meta:
        model = Interventie
        fields = ['interventie_catalog']
        widgets = {
            'interventie_catalog': forms.Select(attrs={'class': 'form-control'})
        }

InterventieFormSet = inlineformset_factory(
    Consultatie,
    Interventie,
    form=InterventieForm,
    extra=1,
    can_delete=True
)


class InterventieForm(forms.ModelForm):
    class Meta:
        model = Interventie
        fields = ['interventie_catalog']
        widgets = {
            'interventie_catalog': forms.Select(attrs={'class': 'form-control interventie-select'}),
        }