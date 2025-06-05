import datetime
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from website.forms import ProgramareForm
from website.models import Doctor, Mesaj, Programare
from .forms import InregistrareForm, ProgramareForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from website.forms import ProgramareForm
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime, timedelta, time
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import calendar
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.mail import send_mail
from django.utils.dateparse import parse_date, parse_time
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from website.models import Doctor, Programare
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Programare
import json

@login_required
def lista_mesaje_ajax(request, programare_id):
    programare = get_object_or_404(Programare, id=programare_id)
    if request.user != programare.pacient and request.user != programare.doctor.user:
        return JsonResponse({'error': 'Acces interzis'}, status=403)

    mesaje = programare.mesaje.order_by('data_trimitere')
    lista_mesaje = [{
        'nume_expeditor': msg.expeditor.get_full_name(),
        'text': msg.text,
        'data': msg.data_trimitere.strftime('%Y-%m-%d %H:%M')
    } for msg in mesaje]

    return JsonResponse({'mesaje': lista_mesaje})


@csrf_exempt
@login_required
def trimite_mesaj_ajax(request, programare_id):
    if request.method == 'POST':
        programare = get_object_or_404(Programare, id=programare_id)
        if request.user != programare.pacient and request.user != programare.doctor.user:
            return JsonResponse({'error': 'Acces interzis'}, status=403)

        data = json.loads(request.body)
        text = data.get('text', '').strip()
        if text:
            Mesaj.objects.create( 
                programare=programare,
                expeditor=request.user,
                text=text,
                data_trimitere=timezone.now()
            )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Metodă invalidă'}, status=405)


@login_required
def calendar_doctor_view(request):
    # Obține doctorul asociat utilizatorului
    doctor = get_object_or_404(Doctor, user=request.user)

    # Filtrează programările doctorului
    programari = Programare.objects.filter(doctor=doctor).order_by('data', 'ora')

    context = {
        'programari': programari,
    }
    return render(request, 'calendar.html', context)

@staff_member_required
def dashboard_doctor(request):
    programari = Programare.objects.filter(doctor__user=request.user).order_by('data', 'ora')
    return render(request, 'dashboard.html', {'programari': programari})



@login_required
@csrf_exempt
def salveaza_programare_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            doctor_id = data.get('doctor_id')
            zi = data.get('data')
            ora = data.get('ora')

            if not (doctor_id and zi and ora):
                return JsonResponse({'error': 'Date lipsă'}, status=400)

            doctor = Doctor.objects.get(id=doctor_id)

            # Verificare dacă slotul e deja ocupat
            ocupata = Programare.objects.filter(doctor=doctor, data=zi, ora=ora).exists()
            if ocupata:
                return JsonResponse({'error': 'Slot deja ocupat'}, status=409)

            programare = Programare.objects.create(
                pacient=request.user,
                doctor=doctor,
                data=zi,
                ora=ora,
                status='in_asteptare'
            )

            # Trimite email de confirmare
            send_mail(
                subject='Confirmare programare - Clinica NeoDent',
                message=f"Bună, {request.user.first_name}!\n\nAi fost programat la {doctor.nume_familie} pe data de {zi} la ora {ora}.\n\nVei primi un alt email când programarea este confirmată.\n\nMulțumim!",
                from_email='clinica@domeniu.ro',
                recipient_list=[request.user.email],
                fail_silently=False,
            )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metodă invalidă'}, status=405)
    
@login_required
def pagina_programare_interactiva(request):
    doctori = Doctor.objects.all()
    return render(request, 'fa_programare.html', {'doctori': doctori})

@login_required
def anuleaza_programare(request, id):
    programare = get_object_or_404(Programare, id=id, pacient=request.user)
    programare.delete()
    messages.success(request, "Programarea a fost anulată.")
    return redirect('istoric')

@login_required
def sloturi_disponibile(request):
    doctor_id = request.GET.get('doctor_id')

    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor invalid'}, status=400)

    azi = datetime.today().date()
    zile_disponibile = []

    for zi_offset in range(90):  # până la 3 luni în avans
        zi = azi + timedelta(days=zi_offset)
        if zi.weekday() > 4:
            continue  # doar luni–vineri

        ore_zi = []
        for h in range(10, 18):  # ore între 10:00–17:00
            ora = time(h, 0)
            ocupata = Programare.objects.filter(doctor=doctor, data=zi, ora=ora).exists()
            if not ocupata:
                ore_zi.append(f"{ora.strftime('%H:%M')}")

        if ore_zi:
            ziua_saptamanii = calendar.day_name[zi.weekday()]  # Monday, Tuesday...
            zile_disponibile.append({
                'data': zi.strftime('%Y-%m-%d'),
                'ziua': ziua_saptamanii,
                'ore': ore_zi
            })

    return JsonResponse({'zile': zile_disponibile})

def superuser_required(user):
    return user.is_superuser

@user_passes_test(superuser_required)
def admin_panel(request):
    programari = Programare.objects.all()
    utilizatori = User.objects.all()
    return render(request, 'admin_panel.html', {'programari': programari, 'utilizatori': utilizatori})

@user_passes_test(superuser_required)
def sterge_programare(request, id):
    programare = get_object_or_404(Programare, id=id)
    programare.delete()
    return redirect('admin_panel')

@user_passes_test(superuser_required)
def editeaza_programare(request, id):
    programare = get_object_or_404(Programare, id=id)
    if request.method == 'POST':
        form = ProgramareForm(request.POST, instance=programare)
        if form.is_valid():
            form.save()
            return redirect('admin_panel')
    else:
        form = ProgramareForm(instance=programare)
    return render(request, 'editeaza_programare.html', {'form': form, 'programare': programare})

@login_required
def istoric_programari(request):
    programari = Programare.objects.filter(pacient=request.user).order_by('-data', '-ora')
    return render(request, 'istoric.html', {'programari': programari})

@login_required
def fa_programare(request):
    mesaj = None
    if request.method == 'POST':
        form = ProgramareForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            serviciu = form.cleaned_data['serviciu']
            data = form.cleaned_data['data']
            ora = form.cleaned_data['ora']

            # Verificare: zi lucrătoare (luni–vineri)
            if data.weekday() > 4:
                mesaj = "Poți face programări doar de luni până vineri."
            else:
                # Verificare dacă slotul e deja ocupat pentru acel doctor
                ocupata = Programare.objects.filter(doctor=doctor, data=data, ora=ora).exists()
                if ocupata:
                    mesaj = "Această oră este deja rezervată."
                else:
                    # Creează programarea
                    Programare.objects.create(
                        pacient=request.user,
                        doctor=doctor,
                        serviciu=serviciu,
                        data=data,
                        ora=ora,
                        status='in_asteptare'
                    )
                    return redirect('istoric')
    else:
        form = ProgramareForm()

    return render(request, 'fa_programare.html', {'form': form, 'mesaj': mesaj})

@login_required
def istoric(request):
    programari = Programare.objects.filter(pacient=request.user).order_by('-data', '-ora')
    return render(request, 'istoric.html', {'programari': programari})

def inregistrare(request):
    if request.method == 'POST':
        form = InregistrareForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Trimite email
            send_mail(
                'Bun venit la Clinica NeoDent!',
                'Contul tău a fost creat cu succes. Ne bucurăm că ești cu noi!',
                'clinica@domeniu.ro',
                [user.email],
                fail_silently=False,
            )

            messages.success(request, 'Contul tău a fost creat cu succes!')
            return redirect('home')
    else:
        form = InregistrareForm()

    return render(request, 'inregistrare.html', {'form': form})

def home(request):
    return render(request, "home.html")

def despre(request):
    return render(request, 'despre.html')

def servicii(request):
    return render(request, 'servicii.html')

def contact(request):
    return render(request, 'contact.html')


#SECRETARIAT
def este_secretar(user):
    return hasattr(user, 'secretariat')

@user_passes_test(este_secretar)
def dashboard_secretariat(request):
    status_filtru = request.GET.get('status')
    
    if status_filtru:
        programari = Programare.objects.filter(status=status_filtru).order_by('-data', '-ora')
    else:
        programari = Programare.objects.all().order_by('-data', '-ora')

    return render(request, 'dashboard.html', {
        'programari': programari,
        'status_filtru': status_filtru
    })

@user_passes_test(este_secretar)
def refuza_programare(request, id):
    programare = get_object_or_404(Programare, id=id)

    programare.status = 'anulata'
    programare.save()

    # Trimitere email pacient
    send_mail(
        'Programarea ta a fost respinsă',
        f'Bună, {programare.pacient.first_name}!\n\nNe pare rău, dar programarea ta din {programare.data} la ora {programare.ora} cu {programare.doctor.user.get_full_name()} a fost respinsă.\n\nTe rugăm să încerci o altă dată.',
        'clinica@domeniu.ro',
        [programare.pacient.email],
        fail_silently=False,
    )

    messages.info(request, "Programarea a fost respinsă.")
    return redirect('secretariat_dashboard')

@user_passes_test(este_secretar)
def accepta_programare(request, id):
    programare = get_object_or_404(Programare, id=id)
    programare.status = 'confirmata'
    programare.save()

    # Trimite email de confirmare pacientului
    send_mail(
        'Programarea ta a fost confirmată!',
        f'Bună, {programare.pacient.first_name}!\n\nProgramarea ta din {programare.data} la ora {programare.ora} cu {programare.doctor.nume_familie} a fost confirmată.\n\nTe așteptăm!',
        'clinica@domeniu.ro',
        [programare.pacient.email],
        fail_silently=False,
    )

    messages.success(request, "Programarea a fost confirmată.")
    return redirect('dashboard_doctor')

#comentariu