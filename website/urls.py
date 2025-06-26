from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('despre/', views.despre, name='despre'),
    path('servicii/', views.servicii, name='servicii'),
    path('contact/', views.contact, name='contact'),
    path('istoric/', views.istoric_programari, name='istoric'),
    path('consultatii/', views.toate_consultatiile, name='consultatii'),
    path('inregistrare/', views.inregistrare, name='inregistrare'),
    path('ajax/sloturi-disponibile/', views.sloturi_disponibile, name='sloturi_disponibile'),
    path('programare/', views.pagina_programare_interactiva, name='fa_programare'),
    path('ajax/salveaza-programare/', views.salveaza_programare_ajax, name='salveaza_programare_ajax'),
    path('anuleaza-programare/<int:id>/', views.anuleaza_programare, name='anuleaza_programare'),
    path('dashboard-doctor/', views.dashboard_doctor, name='dashboard_doctor'),
    path('secretariat/dashboard/', views.dashboard_secretariat, name='secretariat_dashboard'),
    path('accepta-programare/<int:id>/', views.accepta_programare, name='accepta_programare'),
    path('refuza-programare/<int:id>/', views.refuza_programare, name='refuza_programare'),
    path('consultatie/<int:programare_id>/', views.adauga_consultatie, name='adauga_consultatie'),
    path('programare/<int:programare_id>/consultatie/', views.adauga_consultatie, name='adauga_consultatie'),
    #path('api/interventii/<int:clasa_id>/', views.get_interventii_by_clasa, name='get_interventii_by_clasa'),
    path('interventii/<int:consultatie_id>/', views.vezi_interventie, name='vezi_interventie'),
    path('secretariat/programare-noua/', views.adauga_programare_secretar, name='programare_secretar'),

    #mesagerie
    path('api/chat/<int:programare_id>/', views.lista_mesaje_ajax, name='lista_mesaje_ajax'),
    path('api/chat/<int:programare_id>/trimite/', views.trimite_mesaj_ajax, name='trimite_mesaj_ajax'),

    #calendar-doctori
    path('calendar-doctori/', views.calendar_doctor_view, name='calendar_doctori'),

    #autentificare
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),


    #admin
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/sterge-programare/<int:id>/', views.sterge_programare, name='sterge_programare'),
    path('admin-panel/editeaza-programare/<int:id>/', views.editeaza_programare, name='editeaza_programare'),

    #consultatie
    path('vezi-consultatie/<int:programare_id>/', views.vezi_consultatie, name='vezi_consultatie'),
    path('radiografie/<int:consultatie_id>/', views.vedere_radiografie, name='vedere_radiografie'),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)