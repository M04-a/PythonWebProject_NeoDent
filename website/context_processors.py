from website.models import Programare

def ultima_programare(request):
    if not request.user.is_authenticated:
        return {}

    programare = Programare.objects.filter(pacient=request.user).order_by('-data', '-ora').first()
    if not programare:
        return {}

    if request.user == programare.pacient:
        interlocutor = f"{programare.doctor.prenume} {programare.doctor.nume_familie}"
    else:
        interlocutor = f"{programare.pacient.first_name} {programare.pacient.last_name}"

    return {
        'programare': programare,
        'interlocutor': interlocutor
    }
