import datetime
import calendar
import json
import os
from django.http import HttpResponse, Http404
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date, parse_time
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from website.forms import ProgramareForm
from website.models import Doctor, Mesaj, Programare
from .forms import InregistrareForm, ProgramareForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from website.forms import ProgramareForm
from datetime import datetime, timedelta, time
from django.http import JsonResponse
from django.utils import timezone
from .models import Programare, Consultatie, Interventie
from .forms import ConsultatieForm, InterventieFormSet
from .models import InterventieCatalog
from .models import ClasaInterventie, InterventieCatalog
import logging
logger = logging.getLogger(__name__)



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
    doctor = get_object_or_404(Doctor, user=request.user)
    programari = Programare.objects.filter(doctor=doctor)
    pacient_nume = request.GET.get('pacient')
    status = request.GET.get('status')
    data_de_la = request.GET.get('data_de_la')
    data_pana_la = request.GET.get('data_pana_la')
    ora_de_la = request.GET.get('ora_de_la')
    ora_pana_la = request.GET.get('ora_pana_la')

    if pacient_nume:
        programari = programari.filter(
            Q(pacient__first_name__icontains=pacient_nume) |
            Q(pacient__last_name__icontains=pacient_nume) |
            Q(pacient__username__icontains=pacient_nume)
        )

    if status:
        programari = programari.filter(status=status)

    if data_de_la:
        try:
            programari = programari.filter(data__gte=datetime.strptime(data_de_la, '%Y-%m-%d').date())
        except ValueError:
            pass

    if data_pana_la:
        try:
            programari = programari.filter(data__lte=datetime.strptime(data_pana_la, '%Y-%m-%d').date())
        except ValueError:
            pass

    if ora_de_la:
        try:
            programari = programari.filter(ora__gte=datetime.strptime(ora_de_la, '%H:%M').time())
        except ValueError:
            pass

    if ora_pana_la:
        try:
            programari = programari.filter(ora__lte=datetime.strptime(ora_pana_la, '%H:%M').time())
        except ValueError:
            pass


    programari = programari.order_by('-creat_la')

    context = {
        'programari': programari,
        'pacient_filtru': pacient_nume,
        'status_filtru': status,
        'data_de_la': data_de_la,
        'data_pana_la': data_pana_la,
        'ora_de_la': ora_de_la,
        'ora_pana_la': ora_pana_la,
    }

    return render(request, 'calendar.html', context)


@staff_member_required
def dashboard_doctor(request):
    status_filtru = request.GET.get('status', '') 
    pacient_cautare = request.GET.get('pacient', '').strip()
    data_de_la = request.GET.get('data_de_la')
    data_pana_la = request.GET.get('data_pana_la')
    
    programari = Programare.objects.filter(doctor__user=request.user)
    
    if status_filtru:
        programari = programari.filter(status=status_filtru)
    
    if pacient_cautare:
        programari = programari.filter(
            Q(pacient__first_name__icontains=pacient_cautare) |
            Q(pacient__last_name__icontains=pacient_cautare) |
            Q(pacient__username__icontains=pacient_cautare)
        )
  
    if data_de_la:
        programari = programari.filter(data__gte=data_de_la)
    
   
    if data_pana_la:
        programari = programari.filter(data__lte=data_pana_la)
    

    programari = programari.order_by('-creat_la')
    
    return render(request, 'dashboard.html', {
        'programari': programari,
        'status_filtru': status_filtru,
        'pacient_cautare': pacient_cautare,
        'data_de_la': data_de_la,
        'data_pana_la': data_pana_la,
    })


@login_required
@csrf_exempt
def salveaza_programare_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            doctor_id = data.get('doctor_id')
            zi = data.get('data')
            ora = data.get('ora')
            pacient_id = data.get('pacient_id')

            if not (doctor_id and zi and ora):
                return JsonResponse({'error': 'Date lipsă'}, status=400)

            doctor = Doctor.objects.get(id=doctor_id)
            
            if pacient_id:
                pacient = User.objects.get(id=pacient_id)
            else:
                pacient = request.user

            if Programare.objects.filter(doctor=doctor, data=zi, ora=ora).exists():
                return JsonResponse({'error': 'Slot deja ocupat'}, status=409)

            programare = Programare.objects.create(
                pacient=pacient,
                doctor=doctor,
                data=zi,
                ora=ora,
                status='in_asteptare'
            )

            send_mail(
                subject='Confirmare programare - Clinica NeoDent',
                message=f"Bună, {pacient.first_name}!\n\nAi fost programat la {doctor.nume_familie} pe data de {zi} la ora {ora}.\n\nVei primi un alt email când programarea este confirmată.\n\nMulțumim!",
                from_email='clinica@domeniu.ro',
                recipient_list=[pacient.email],
                fail_silently=False,
            )

            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'error': 'Pacientul nu a fost găsit'}, status=404)
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Doctorul nu a fost găsit'}, status=404)
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

    for zi_offset in range(90):   
        zi = azi + timedelta(days=zi_offset)
        if zi.weekday() > 4:
            continue  

        ore_zi = []
        for h in range(10, 18):  
            ora = time(h, 0)
            ocupata = Programare.objects.filter(doctor=doctor, data=zi, ora=ora).exists()
            if not ocupata:
                ore_zi.append(f"{ora.strftime('%H:%M')}")

        if ore_zi:
            ziua_saptamanii = calendar.day_name[zi.weekday()]  
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
    programari = Programare.objects.filter(pacient=request.user)
    doctori = Doctor.objects.filter(programare__pacient=request.user).distinct().order_by('nume_familie', 'prenume')


    doctor_id = request.GET.get('doctor')
    if doctor_id:
        programari = programari.filter(doctor_id=doctor_id)

    data_de_la = request.GET.get('data_de_la')
    if data_de_la:
        try:
            data_de_la = datetime.strptime(data_de_la, '%Y-%m-%d').date()
            programari = programari.filter(data__gte=data_de_la)
        except ValueError:
            pass

    data_pana_la = request.GET.get('data_pana_la')
    if data_pana_la:
        try:
            data_pana_la = datetime.strptime(data_pana_la, '%Y-%m-%d').date()
            programari = programari.filter(data__lte=data_pana_la)
        except ValueError:
            pass

    status = request.GET.get('status')
    if status:
        programari = programari.filter(status=status)

    sort_by = request.GET.get('sort', 'creat_desc')  

    if sort_by == 'data_desc':
        programari = programari.order_by('-data', '-ora')
    elif sort_by == 'data_asc':
        programari = programari.order_by('data', 'ora')
    elif sort_by == 'creat_asc':
        programari = programari.order_by('creat_la', 'id')
    else:  
        programari = programari.order_by('-creat_la', '-id')

    context = {
        'programari': programari,
        'doctori': doctori,
        'sort_by': sort_by,
    }

    return render(request, 'istoric.html', context)


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
            if hasattr(request.user, 'secretariat'):
                pacient = form.cleaned_data['pacient'] 
            else:
                pacient = request.user
            if data.weekday() > 4:
                mesaj = "Poți face programări doar de luni până vineri."
            else:
                ocupata = Programare.objects.filter(doctor=doctor, data=data, ora=ora).exists()
                if ocupata:
                    mesaj = "Această oră este deja rezervată."
                else:
                    Programare.objects.create(
                        pacient=pacient,
                        doctor=doctor,
                        serviciu=serviciu,
                        data=data,
                        ora=ora,
                        status='in_asteptare'
                    )
                    return redirect('istoric')
    else:
         form = ProgramareForm(user=request.user)

    return render(request, 'fa_programare.html', {'form': form, 'mesaj': mesaj})

@login_required
def adauga_programare_secretar(request):
    if not hasattr(request.user, 'secretariat'):
        return redirect('home')
    
    doctori = Doctor.objects.all()
    mesaj = None
    
    if request.method == 'POST':
        print("=== DEBUG START ===")
        print(f"POST data: {request.POST}")
        
        form = ProgramareForm(request.POST, user=request.user)
        print(f"Form is valid: {form.is_valid()}")
        
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        
        if form.is_valid():
            print("Form is valid, processing...")
            doctor = form.cleaned_data['doctor']
            data = form.cleaned_data['data']
            ora = form.cleaned_data['ora']
            
            # Verifică toate posibilitățile
            pacient_from_cleaned = form.cleaned_data.get('pacient')
            pacient_from_post = request.POST.get('pacient')
            
            print(f"pacient_from_cleaned: '{pacient_from_cleaned}' (type: {type(pacient_from_cleaned)})")
            print(f"pacient_from_post: '{pacient_from_post}' (type: {type(pacient_from_post)})")
            
            # Verificare strictă
            if not pacient_from_cleaned:
                print("STOP: Pacient nu este selectat!")
                mesaj = "Trebuie să selectezi un pacient."
                # FORȚEAZĂ să nu continue
            else:
                print(f"Pacient selectat: {pacient_from_cleaned}")
                
                if data.weekday() > 4:
                    mesaj = "Poți face programări doar de luni până vineri."
                    print("STOP: Weekend")
                elif Programare.objects.filter(doctor=doctor, data=data, ora=ora).exists():
                    mesaj = "Această oră este deja rezervată."
                    print("STOP: Ora rezervată")
                else:
                    print("Creating programare...")
                    programare = Programare.objects.create(
                        pacient=pacient_from_cleaned,
                        doctor=doctor,
                        data=data,
                        ora=ora,
                        status='in_asteptare'
                    )
                    print(f"Programare created with pacient: {programare.pacient}")
                    print(f"Programare ID: {programare.id}")
                    return redirect('secretariat_dashboard')
        
        print("=== DEBUG END ===")
    else:
        form = ProgramareForm(user=request.user)
    
    pacienti = User.objects.exclude(is_superuser=True)\
                          .exclude(secretariat__isnull=False)\
                          .exclude(doctor__isnull=False)
    
    return render(request, 'programare_sec.html', {
        'form': form,
        'mesaj': mesaj,
        'pacienti': pacienti,
        'doctori': doctori,
    })

def inregistrare(request):
    if request.method == 'POST':
        form = InregistrareForm(request.POST)
        print(f"Form data: {request.POST}")  # pentru debugging
        print("=== ÎNAINTE DE is_valid() ===")
        result = form.is_valid()
        print(f"=== DUPĂ is_valid() === Rezultat: {result}")
        print(f"Form errors: {form.errors}")
        print(f"Form cleaned_data: {getattr(form, 'cleaned_data', 'NU EXISTĂ')}")
        
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                
                # Trimite email-ul
                send_mail(
                    'Bun venit la Clinica NeoDent!',
                    'Contul tău a fost creat cu succes. Ne bucurăm că ești cu noi!',
                    'clinica@domeniu.ro',
                    [user.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Contul tău a fost creat cu succes!')
                return redirect('home')
                
            except Exception as e:
                logger.error(f"Eroare la crearea contului: {e}")
                messages.error(request, 'A apărut o eroare la crearea contului.')
        else:
            # Afișează erorile de validare
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = InregistrareForm()
    
    return render(request, 'inregistrare.html', {'form': form})

@login_required
def istoric(request):
    programari = Programare.objects.filter(pacient=request.user).order_by('creat_la')
    return render(request, 'istoric.html', {'programari': programari})

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
    programari = Programare.objects.select_related('pacient').all()
    
    status_filtru = request.GET.get('status')
    pacient_id = request.GET.get('pacient')
    data_de_la = request.GET.get('data_de_la')
    data_pana_la = request.GET.get('data_pana_la')
    sort_by = request.GET.get('sort', 'creat_desc')

    if status_filtru:
        programari = programari.filter(status=status_filtru)

    if pacient_id:
        try:
            programari = programari.filter(pacient_id=int(pacient_id))
        except ValueError:
            pass

    if data_de_la:
        try:
            data_de_la = datetime.strptime(data_de_la, '%Y-%m-%d').date()
            programari = programari.filter(data__gte=data_de_la)
        except ValueError:
            pass

    if data_pana_la:
        try:
            data_pana_la = datetime.strptime(data_pana_la, '%Y-%m-%d').date()
            programari = programari.filter(data__lte=data_pana_la)
        except ValueError:
            pass

    if sort_by == 'data_asc':
        programari = programari.order_by('data', 'ora')
    elif sort_by == 'data_desc':
        programari = programari.order_by('-data', '-ora')
    elif sort_by == 'creat_asc':
        programari = programari.order_by('creat_la', 'id')
    else: 
        programari = programari.order_by('-creat_la', '-id')


    pacienti = User.objects.filter(
    programare__isnull=False,
    is_staff=False,
    is_superuser=False
    ).distinct().order_by('first_name', 'last_name')

    return render(request, 'dashboard_secretariat.html', {
        'programari': programari,
        'status_filtru': status_filtru,
        'pacienti': pacienti,
        'sort_by': sort_by,
        'data_de_la': request.GET.get('data_de_la'),
        'data_pana_la': request.GET.get('data_pana_la'),
        'pacient_id': pacient_id,
    })

@user_passes_test(este_secretar)
def refuza_programare(request, id):
    programare = get_object_or_404(Programare, id=id)

    programare.status = 'anulata'
    programare.save()

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


    send_mail(
        'Programarea ta a fost confirmată!',
        f'Bună, {programare.pacient.first_name}!\n\nProgramarea ta din {programare.data} la ora {programare.ora} cu {programare.doctor.nume_familie} a fost confirmată.\n\nTe așteptăm!',
        'clinica@domeniu.ro',
        [programare.pacient.email],
        fail_silently=False,
    )

    messages.success(request, "Programarea a fost confirmată.")
    return redirect('secretariat_dashboard')

#Consultaite
def este_doctor(user):
    return hasattr(user, 'doctor')

def este_secretar(user):
    return hasattr(user, 'secretar')

@user_passes_test(este_doctor)
def adauga_consultatie(request, programare_id):
    programare = get_object_or_404(Programare, id=programare_id)
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, "Nu aveți permisiuni pentru această acțiune.")
        return redirect('lista_programari')
    
    clase_interventii = ClasaInterventie.objects.all()
    consultatii_anterioare = Consultatie.objects.filter(programare__pacient=programare.pacient).exclude(programare=programare).select_related('programare').prefetch_related('interventii__interventie_catalog__clasa').order_by('-programare__data')
    interventii_dict = {}
    for clasa in clase_interventii:
        interventii_dict[str(clasa.id)] = [
            {
                'id': interv.id,
                'denumire': interv.denumire,
                'cost': str(interv.cost)
            }
            for interv in clasa.interventii.all()
        ]
    
    interventii_json = json.dumps(interventii_dict)
    
    if request.method == 'POST':
        dinte = request.POST.get('dinte')
        tip = request.POST.get('tip')
        observatii = request.POST.get('observatii', '')
        cost_total = request.POST.get('cost_total', 0)
        radiografie = request.FILES.get('radiografie')
        if radiografie:
            if radiografie.size > 5 * 1024 * 1024:
                messages.error(request, "Radiografia este prea mare. Dimensiunea maximă este 5MB.")
                return render(request, 'adauga_consultatie.html', context)
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if radiografie.content_type not in allowed_types:
                messages.error(request, "Format invalid. Sunt permise doar JPG și PNG.")
                return render(request, 'adauga_consultatie.html', context)

        consultatie = Consultatie.objects.create(
            programare=programare,
            dinte=dinte,
            tip=tip,
            observatii=observatii,
            cost_total=cost_total,
            nume_medic=f"{doctor.prenume} {doctor.nume_familie}",
            radiografie=radiografie 
        )
        
        form_count = int(request.POST.get('form-TOTAL_FORMS', 0))
        for i in range(form_count):
            interventie_catalog_id = request.POST.get(f'form-{i}-interventie_catalog')
            if interventie_catalog_id and not request.POST.get(f'form-{i}-DELETE'):
                interventie_catalog = get_object_or_404(InterventieCatalog, id=interventie_catalog_id)
                Interventie.objects.create(
                    consultatie=consultatie,
                    interventie_catalog=interventie_catalog
                )
        
        programare.status = 'efectuata'
        programare.save()
        
        messages.success(request, "Consultația a fost salvată cu succes!")
        return redirect('calendar_doctori')
    
    context = {
    'programare': programare,
    'clase_interventii': clase_interventii,
    'interventii_json': interventii_json,
    'pacient_nume': programare.pacient.get_full_name() if programare.pacient else "Necunoscut",
    'doctor_nume': f"{programare.doctor.nume_familie} {programare.doctor.prenume}",
    'consultatii_anterioare': consultatii_anterioare,
    }

    
    return render(request, 'adauga_consultatie.html', context)

@login_required
def vedere_radiografie(request, consultatie_id):
    """View pentru afișarea radiografiei cu control de acces"""
    consultatie = get_object_or_404(Consultatie, id=consultatie_id)
    
    if not (
        hasattr(request.user, 'doctor') or 
        consultatie.programare.pacient.user == request.user
    ):
        raise Http404("Nu aveți permisiuni pentru această radiografie.")
    
    if not consultatie.radiografie:
        raise Http404("Radiografia nu există.")
    
    try:
        with consultatie.radiografie.open('rb') as f:
            response = HttpResponse(f.read(), content_type='image/jpeg')
            response['Content-Disposition'] = f'inline; filename="{consultatie.radiografie.name}"'
            return response
    except FileNotFoundError:
        raise Http404("Fișierul radiografiei nu a fost găsit.")

def vezi_consultatie(request, programare_id):
    consultatie = get_object_or_404(Consultatie, programare_id=programare_id)
    return render(request, 'vezi_consultatie.html', {'consultatie': consultatie})

def vezi_interventie(request, consultatie_id):
    """
    View pentru a vedea detaliile unei consultații cu intervenții
    """
    try:
        consultatie = Consultatie.objects.select_related(
            'programare__doctor__user',
            'programare__pacient'
        ).prefetch_related(
            'interventii__interventie_catalog__clasa'
        ).get(id=consultatie_id)
        
        if not consultatie.interventii.exists():
            messages.warning(request, 'Această consultație nu are intervenții înregistrate.')
            return redirect('consultatii')
        
        cost_total_interventii = sum(
            interventie.interventie_catalog.cost 
            for interventie in consultatie.interventii.all()
            if interventie.interventie_catalog
        )
        
        context = {
            'consultatie': consultatie,
            'cost_total_interventii': cost_total_interventii,
            'numar_interventii': consultatie.interventii.count(),
        }
        
        return render(request, 'vezi_interventie.html', context)
        
    except Consultatie.DoesNotExist:
        messages.error(request, 'Consultația nu a fost găsită.')
        return redirect('consultatii')
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'A apărut o eroare: {str(e)}')

        return redirect('consultatii')
    

def toate_consultatiile(request):
    consultatii = Consultatie.objects.select_related(
        'programare__doctor__user', 
        'programare__pacient'
    ).prefetch_related('interventii__interventie_catalog__clasa')
    
    doctori = Doctor.objects.select_related('user').all().order_by('nume_familie', 'prenume')
    
    tip_serviciu = request.GET.get('tip_serviciu')
    if tip_serviciu == 'consultatie':
        consultatii = consultatii.filter(interventii__isnull=True)
    elif tip_serviciu == 'interventie':
        consultatii = consultatii.filter(interventii__isnull=False).distinct()
    
    doctor_id = request.GET.get('doctor')
    if doctor_id:
        try:
            doctor_id = int(doctor_id)
            consultatii = consultatii.filter(programare__doctor_id=doctor_id)
        except (ValueError, TypeError):
            pass
    
    pacient_nume = request.GET.get('pacient')
    if pacient_nume:
        pacient_nume = pacient_nume.strip()
        if pacient_nume:
            consultatii = consultatii.filter(
                Q(programare__pacient__first_name__icontains=pacient_nume) |
                Q(programare__pacient__last_name__icontains=pacient_nume) |
                Q(programare__pacient__username__icontains=pacient_nume)
            )
    
    data_de_la = request.GET.get('data_de_la')
    if data_de_la:
        try:
            data_de_la = datetime.strptime(data_de_la, '%Y-%m-%d').date()
            consultatii = consultatii.filter(programare__data__gte=data_de_la)
        except ValueError:
            pass
    
    data_pana_la = request.GET.get('data_pana_la')
    if data_pana_la:
        try:
            data_pana_la = datetime.strptime(data_pana_la, '%Y-%m-%d').date()
            consultatii = consultatii.filter(programare__data__lte=data_pana_la)
        except ValueError:
            pass
    
    status = request.GET.get('status')
    if status and status in ['in_asteptare', 'confirmata', 'anulata', 'efectuata']:
        consultatii = consultatii.filter(programare__status=status)
    
    sort_by = request.GET.get('sort', 'data_desc')
    
    if sort_by == 'data_desc':
        consultatii = consultatii.order_by('-programare__data', '-programare__ora')
    elif sort_by == 'data_asc':
        consultatii = consultatii.order_by('programare__data', 'programare__ora')
    elif sort_by == 'creat_asc':
        consultatii = consultatii.order_by('data_creata', 'id')
    else:  
        consultatii = consultatii.order_by('-data_creata', '-id')
    
    servicii = []
    
    for consultatie in consultatii:
        interventii_lista = list(consultatie.interventii.all())
        tip_serviciu = 'interventie' if interventii_lista else 'consultatie'
        cost_interventii = sum(
            interv.interventie_catalog.cost if interv.interventie_catalog else 0 
            for interv in interventii_lista
        )
        
        servicii.append({
            'id': consultatie.id,
            'tip': tip_serviciu,
            'data': consultatie.programare.data,
            'ora': consultatie.programare.ora,
            'doctor': consultatie.programare.doctor,
            'pacient': consultatie.programare.pacient,
            'status': consultatie.programare.status,
            'creat_la': consultatie.data_creata,
            'programare_id': consultatie.programare.id,
            'consultatie': consultatie,
            'interventii': interventii_lista,
            'cost_total': consultatie.cost_total + cost_interventii,
            'observatii': consultatie.observatii,
            'dinte': consultatie.dinte,
            'tip_consultatie': consultatie.tip,
        })
    total_count = len(servicii)
    consultatii_count = len([s for s in servicii if s['tip'] == 'consultatie'])
    interventii_count = len([s for s in servicii if s['tip'] == 'interventie'])
    consultatii_tab = [s['consultatie'] for s in servicii if s['tip'] == 'consultatie']
    interventii_tab = [s['consultatie'] for s in servicii if s['tip'] == 'interventie']

    
    
    context = {
    'servicii': servicii,
    'doctori': doctori,
    'total_count': total_count,
    'consultatii_count': consultatii_count, 
    'interventii_count': interventii_count,
    'sort_by': sort_by,
    'filtru_tip_serviciu': tip_serviciu,
    'filtru_doctor': doctor_id,
    'filtru_pacient': pacient_nume,
    'filtru_data_de_la': data_de_la,
    'filtru_data_pana_la': data_pana_la,
    'consultatii': consultatii_tab,
    'interventii': interventii_tab,
    }

    
    return render(request, 'consultatii.html', context)