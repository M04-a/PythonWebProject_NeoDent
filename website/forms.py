from django import forms
from .models import Doctor, Programare, Serviciu
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from .models import Consultatie, Interventie
from django.forms import inlineformset_factory

class InregistrareForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Acest email este deja folosit.')
        return email

class ProgramareForm(forms.Form):
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all())
    serviciu = forms.ModelChoiceField(queryset=Serviciu.objects.all())
    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    ora = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Oferim toate orele posibile inițial: 10:00 - 17:00 (cu pas de 1 oră)
        ore_disponibile = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(10, 18)]
        self.fields['ora'].choices = ore_disponibile

class InregistrareForm(UserCreationForm): # type: ignore
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label='Prenume', max_length=30)
    last_name = forms.CharField(label='Nume', max_length=30)

    class Meta:
        model = User # type: ignore
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

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