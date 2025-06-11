from django.contrib import admin
from .models import Programare, Secretariat
from .models import Doctor, Serviciu
from django.contrib import admin
from .models import Mesaj
from .models import ClasaInterventie, InterventieCatalog
from .models import Consultatie, Interventie

admin.site.register(Consultatie)
admin.site.register(Interventie)
admin.site.register(ClasaInterventie)
admin.site.register(InterventieCatalog)
admin.site.register(Doctor)
admin.site.register(Serviciu)
admin.site.register(Programare)
admin.site.register(Secretariat)

@admin.register(Mesaj)
class MesajAdmin(admin.ModelAdmin):
    list_display = ('expeditor', 'programare', 'data_trimitere')
    search_fields = ('expeditor__username', 'text')
    list_filter = ('data_trimitere',)
