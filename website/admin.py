from django.contrib import admin
from .models import Programare, Secretariat
from .models import Doctor
from django.contrib import admin
from .models import Mesaj
from .models import ClasaInterventie, InterventieCatalog
from .models import Consultatie, Interventie


admin.site.register(Consultatie)
admin.site.register(Interventie)
admin.site.register(ClasaInterventie)
admin.site.register(InterventieCatalog)
admin.site.register(Doctor)
admin.site.register(Programare)
admin.site.register(Secretariat)