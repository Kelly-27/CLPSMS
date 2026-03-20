"""
URL configuration for CLPSMS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from reporting import views
from reporting.views import reporting_desk, CustomLoginView, police_commander_dashboard, add_officer, \
    set_report_desk_password, view_officers, update_evidence_status, apply_leave, approve_leave, reject_leave, \
    add_wanted_person, mark_target_caught
from reporting.views import view_cases, view_inmates, view_rosters, view_inventory, view_evidence
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),

    path('admin/', admin.site.urls),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('reporting-desk/', reporting_desk, name='reporting_desk'),
    path('police-commander-dashboard/', police_commander_dashboard, name='police_commander_dashboard'),
    path('add-officer/', add_officer, name='add_officer'),
    path('set-report-desk-password/', set_report_desk_password, name='set_report_desk_password'),
    path('view-officers/', view_officers, name='view_officers'),
    path('view-cases/', view_cases, name='view_cases'),
    path('view-inmates/', view_inmates, name='view_inmates'),
    path('view-rosters/', view_rosters, name='view_rosters'),
    path('view-inventory/', view_inventory, name='view_inventory'),
    path('view-evidence/', view_evidence, name='view_evidence'),
    path('evidence/<int:evidence_id>/update-status/', update_evidence_status, name='update_evidence_status'),
    path('charge-sheet/<int:charge_id>/pdf/', views.generate_charge_sheet_pdf, name='generate_charge_sheet_pdf'),
    path('apply-leave/', apply_leave, name='apply_leave'),
    path('', include('reporting.urls')),
    path('leave/<int:leave_id>/approve/', approve_leave, name='approve_leave'),
    path('leave/<int:leave_id>/reject/', reject_leave, name='reject_leave'),
    path('add-wanted/', add_wanted_person, name='add_wanted_person'),
    path('wanted/<int:target_id>/caught/', mark_target_caught, name='mark_target_caught'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)