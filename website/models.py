from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

    
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nume_familie = models.CharField(max_length=100)
    prenume = models.CharField(max_length=100)
    specializare = models.CharField(max_length=100)
    email = models.EmailField()
    telefon = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.prenume} {self.nume_familie} ({self.specializare})"

class Mesaj(models.Model):
    programare = models.ForeignKey('Programare', on_delete=models.CASCADE, related_name='mesaje')
    expeditor = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    data_trimitere = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.expeditor.username}: {self.text[:30]}"


class Secretariat(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nume_familie = models.CharField(max_length=100)
    prenume = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return f"{self.prenume} {self.nume_familie}"

class Programare(models.Model):
    pacient = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    data = models.DateField()
    creat_la = models.DateTimeField(auto_now_add=True)
    ora = models.TimeField()
    mesaj = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('in_asteptare', 'În așteptare'),
        ('confirmata', 'Confirmată'),
        ('anulata', 'Anulată'),
        ('efectuata', 'Efectuată'),
    ])

    def __str__(self):
        return f"{self.pacient.username} – {self.data} {self.ora}"

class Consultatie(models.Model):
    programare = models.OneToOneField(Programare, on_delete=models.CASCADE)
    dinte = models.CharField(max_length=50)
    tip = models.CharField(
        max_length=50,
        choices=[
            ('initiala', 'Consultație inițială'),
            ('control', 'Control post-tratament'),
            ('urgenta', 'Urgență')
        ]
    )
    observatii = models.TextField(blank=True)
    cost_total = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    nume_medic = models.CharField(max_length=255)
    radiografie = models.ImageField(
        upload_to='radiografii/%Y/%m/', 
        blank=True, 
        null=True,
        help_text="Radiografie dentară (format: JPG, PNG, max 5MB)"
    )
    
    data_creata = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultație pentru {self.programare.pacient.last_name} {self.programare.pacient.first_name} – {self.programare.data}"

    def delete(self, *args, **kwargs):
        if self.radiografie:
            self.radiografie.delete()
        super().delete(*args, **kwargs)


class ClasaInterventie(models.Model):
    nume = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nume

class InterventieCatalog(models.Model):
    clasa = models.ForeignKey(ClasaInterventie, on_delete=models.CASCADE, related_name='interventii')
    denumire = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.clasa.nume} – {self.denumire} ({self.cost} lei)"


class Interventie(models.Model):
    consultatie = models.ForeignKey(Consultatie, on_delete=models.CASCADE, related_name='interventii')
    interventie_catalog = models.ForeignKey(InterventieCatalog, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return str(self.interventie_catalog)

