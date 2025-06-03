from django.db import models
from django.contrib.auth.models import User


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


class Serviciu(models.Model):
    nume = models.CharField(max_length=100)
    descriere = models.TextField(blank=True)
    pret = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.nume


class Programare(models.Model):
    pacient = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    serviciu = models.ForeignKey(Serviciu, on_delete=models.SET_NULL, null=True)
    data = models.DateField()
    ora = models.TimeField()
    mesaj = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('in_asteptare', 'În așteptare'),
        ('confirmata', 'Confirmată'),
        ('anulata', 'Anulată'),
        ('efectuata', 'Efectuată'),
    ])
    creat_la = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pacient.username} – {self.data} {self.ora}"
