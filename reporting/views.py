from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, Evidence, InventoryItem, DutyRoster
from django.contrib.auth.views import LoginView
from .forms import OfficerCreationForm, EvidenceForm, InventoryItemForm, DutyRosterForm
from .models import Case
from .forms import CaseForm
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import date
from django.conf import settings
from .models import Case, ArrestedPerson
from .forms import CaseForm, ArrestedPersonForm
import os
from django.db.models import Q

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        try:
            role = self.request.user.profile.role
        except Profile.DoesNotExist:
            role = 'crime_desk'
        if role == 'police_commander':
            return '/police-commander-dashboard/'
        elif role == 'officer':
            return '/officer-dashboard/'
        else:
            return '/reporting-desk/'

@login_required
def reporting_desk(request):
    print_case_id = request.session.pop('print_case_id', None)
    return render(request, 'maindesk.html', {'print_case_id': print_case_id})

@login_required
def police_commander_dashboard(request):
    if not request.user.profile.role == 'police_commander':
        return redirect('reporting_desk')

    return render(request, 'police_commander_dashboard.html')

@login_required
def add_officer(request):
    if not request.user.profile.role == 'police_commander':
        return redirect('police_commander_dashboard')

    if request.method == 'POST':
        form = OfficerCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Officer added successfully!')
            return redirect('police_commander_dashboard')
        else:
            print(form.errors)
    else:
        form = OfficerCreationForm()
    return render(request, 'add_officer.html', {'form': form})


from django.contrib.auth.forms import SetPasswordForm


@login_required
def set_report_desk_password(request):
    if not request.user.profile.role == 'police_commander':
        return redirect('police_commander_dashboard')

    report_desk_user = User.objects.filter(profile__role='crime_desk').first()
    if not report_desk_user:
        messages.error(request,
                       "No Report Desk account exists yet! Please use 'Add Officer' to create one with the Crime Desk role.")
        return redirect('police_commander_dashboard')

    if request.method == 'POST':
        form = SetPasswordForm(user=report_desk_user, data=request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Password successfully updated for the Report Desk!")
            return redirect('police_commander_dashboard')
    else:
        form = SetPasswordForm(user=report_desk_user)

    return render(request, 'set_password.html', {'form': form, 'desk_user': report_desk_user})


@login_required
def view_officers(request):
    allowed_roles = ['police_commander', 'crime_desk']

    if request.user.profile.role not in allowed_roles:
        return redirect('reporting_desk')
    officers = User.objects.all()

    return render(request, 'view_officers.html', {'officers': officers})

@login_required
def view_cases(request):
    if request.user.profile.role not in ['police_commander', 'crime_desk']:
        messages.error(request, "You do not have permission to view the cases list.")
        return redirect('reporting_desk')
    query = request.GET.get('q', '')
    if query:
        cases = Case.objects.filter(
            Q(ob_number__icontains=query) |
            Q(incident_type__icontains=query) |
            Q(description__icontains=query)
        ).order_by('-date_logged')
    else:
        cases = Case.objects.all().order_by('-date_logged')

    return render(request, 'view_cases.html', {'cases': cases, 'query': query})

@login_required
def view_inmates(request):
    if not request.user.profile.role == 'police_commander':
        return redirect('police_commander_dashboard')

    inmates = ArrestedPerson.objects.all()
    return render(request, 'view_inmates.html', {'inmates': inmates})

@login_required
@login_required
def view_inventory(request):
    if not request.user.profile.role == 'police_commander':
        return redirect('police_commander_dashboard')

    query = request.GET.get('q', '')

    if query:
        inventory = InventoryItem.objects.filter(
            Q(item_name__icontains=query) |
            Q(category__icontains=query) |
            Q(serial_number__icontains=query)
        ).order_by('-date_added')
    else:
        inventory = InventoryItem.objects.all().order_by('-date_added')

    return render(request, 'view_inventory.html', {'inventory': inventory, 'query': query})

@login_required
def delete_officer(request, user_id):
    if not request.user.profile.role == 'police_commander':
        return redirect('police_commander_dashboard')
    user_to_delete = get_object_or_404(User, id=user_id)

    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('view_officers')

    if request.method == 'POST':
        user_to_delete.delete()
        messages.success(request, "Officer deleted successfully.")

    return redirect('view_officers')


@login_required
def report_case(request):
    if request.user.profile.role not in ['crime_desk', 'police_commander']:
        messages.error(request, "You do not have permission to log new cases.")
        return redirect('reporting_desk')

    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            new_case = form.save()
            request.session['print_case_id'] = new_case.id
            messages.success(request, f"Case logged successfully! OB Number: {new_case.ob_number}")
            return redirect('reporting_desk')
    else:
        form = CaseForm()

    return render(request, 'report_case.html', {'form': form})


def link_callback(uri, rel):
    if uri.startswith('/static/'):
        file_name = uri.replace('/static/', '')
        path = os.path.join(settings.BASE_DIR, 'static', file_name)
        if not os.path.isfile(path):
            print(f"\n🚨 ALERT: Django looked for the image but could NOT find it at: {path}\n")
        else:
            print(f"\n✅ SUCCESS: Django found the image perfectly at: {path}\n")

        return path
    return uri


@login_required
def generate_case_pdf(request, case_id):
    case = get_object_or_404(Case, id=case_id)

    template_path = 'case_pdf.html'
    context = {'case': case}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{case.ob_number}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)

    if pisa_status.err:
        return HttpResponse('We had some errors generating your PDF <pre>' + html + '</pre>')
    return response


@login_required
def officer_dashboard(request):
    if request.user.profile.role != 'officer':
        return redirect('reporting_desk')

    assigned_cases = Case.objects.filter(assigned_officers=request.user).order_by('-date_logged')

    upcoming_shifts = DutyRoster.objects.filter(
        officer=request.user
    ).order_by('-shift_date', 'shift_time')

    context = {
        'assigned_cases': assigned_cases,
        'upcoming_shifts': upcoming_shifts,
    }

    return render(request, 'officer_dashboard.html', context)

@login_required
def close_case(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    if request.user in case.assigned_officers.all() or request.user.profile.role == 'police_commander':
        case.status = 'closed'
        case.save()
        messages.success(request, f"Case {case.ob_number} has been marked as Closed.")
    else:
        messages.error(request, "Action Denied: You are not assigned to this case.")
    if request.user.profile.role == 'officer':
        return redirect('officer_dashboard')
    else:
        return redirect('view_cases')


@login_required
def delete_case(request, case_id):
    if request.user.profile.role != 'police_commander':
        messages.error(request, "Security Violation: Only the Police Commander can delete official records.")
        return redirect('reporting_desk')

    case = get_object_or_404(Case, id=case_id)

    if request.method == 'POST':
        ob_number = case.ob_number
        case.delete()
        messages.success(request, f"Case {ob_number} has been permanently deleted from the system.")

    return redirect('view_cases')


@login_required
def book_suspect(request):
    if request.user.profile.role not in ['officer', 'police_commander', 'crime_desk']:
        messages.error(request, "You do not have permission to book suspects.")
        return redirect('reporting_desk')

    if request.method == 'POST':
        form = ArrestedPersonForm(request.POST)
        if form.is_valid():
            suspect = form.save(commit=False)
            suspect.arresting_officer = request.user
            suspect.save()
            if suspect.related_case:
                msg = f"Suspect {suspect.first_name} {suspect.last_name} has been officially booked and linked to {suspect.related_case.ob_number}."
            else:
                msg = f"Suspect {suspect.first_name} {suspect.last_name} has been officially booked (Pending Case Assignment)."

            messages.success(request, msg)

            # Smart Redirect
            if request.user.profile.role == 'officer':
                return redirect('officer_dashboard')
            else:
                return redirect('reporting_desk')
    else:
        form = ArrestedPersonForm()

    return render(request, 'book_suspect.html', {'form': form})


@login_required
def view_inmates(request):
    if request.user.profile.role not in ['officer', 'police_commander', 'crime_desk']:
        messages.error(request, "You do not have permission to view the custody ledger.")
        return redirect('reporting_desk')
    inmates = ArrestedPerson.objects.all().order_by('-date_arrested')

    return render(request, 'view_inmates.html', {'inmates': inmates})


@login_required
def update_inmate_status(request, inmate_id):
    # Security check: Only authorized roles can change custody status
    if request.user.profile.role not in ['officer', 'police_commander', 'crime_desk']:
        messages.error(request, "Permission denied: You cannot alter custody records.")
        return redirect('reporting_desk')

    inmate = get_object_or_404(ArrestedPerson, id=inmate_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        # Security validation to ensure they only send a valid status code
        valid_statuses = dict(ArrestedPerson.STATUS_CHOICES).keys()
        if new_status in valid_statuses:
            inmate.status = new_status
            inmate.save()
            messages.success(request,
                             f"Status for {inmate.first_name} {inmate.last_name} successfully updated to '{inmate.get_status_display()}'.")
        else:
            messages.error(request, "System Error: Invalid status code provided.")

    return redirect('view_inmates')


@login_required
def commander_dashboard(request):
    if request.user.profile.role != 'police_commander':
        messages.error(request, "Access Denied: Commander clearance required.")
        return redirect('reporting_desk')

    return render(request, 'police_commander_dashboard.html')


@login_required
def add_evidence(request):
    if request.user.profile.role not in ['officer', 'police_commander', 'crime_desk']:
        messages.error(request, "Permission Denied: You cannot access the evidence locker.")
        return redirect('reporting_desk')

    if request.method == 'POST':
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            evidence = form.save(commit=False)
            evidence.save()
            if evidence.related_case:
                msg = f"Evidence '{evidence.item_name}' securely logged to Case {evidence.related_case.ob_number}."
            else:
                msg = f"Evidence '{evidence.item_name}' securely logged (Pending Case)."

            messages.success(request, msg)
            if request.user.profile.role == 'officer':
                return redirect('officer_dashboard')
            else:
                return redirect('reporting_desk')
    else:
        form = EvidenceForm()

    return render(request, 'add_evidence.html', {'form': form})


@login_required
def view_evidence(request):
    if request.user.profile.role not in ['officer', 'police_commander', 'crime_desk']:
        messages.error(request, "Permission Denied: You cannot view the evidence locker.")
        return redirect('reporting_desk')

    query = request.GET.get('q', '')

    if query:
        evidence_items = Evidence.objects.filter(
            Q(item_name__icontains=query) |
            Q(storage_location__icontains=query) |
            Q(description__icontains=query) |
            Q(related_case__ob_number__icontains=query)
        ).order_by('-date_logged')
    else:
        evidence_items = Evidence.objects.all().order_by('-date_logged')

    return render(request, 'view_evidence.html', {'evidence_items': evidence_items, 'query': query})
@login_required
def view_inventory(request):
    # Only allow Commanders and Officers to see the inventory
    if request.user.profile.role not in ['police_commander', 'officer']:
        messages.error(request, "Access Denied: You do not have clearance to view station assets.")
        return redirect('reporting_desk')

    # Get all items, newest updates first
    items = InventoryItem.objects.all().order_by('-last_updated')
    return render(request, 'view_inventory.html', {'items': items})

@login_required
def add_inventory_item(request):
    # Restrict adding items to Commanders
    if request.user.profile.role != 'police_commander':
        messages.error(request, "Permission Denied: Only the Commander can add inventory.")
        return redirect('view_inventory')

    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Inventory updated: {item.item_name} has been added to the store.")
            return redirect('view_inventory')
    else:
        form = InventoryItemForm()

    return render(request, 'add_inventory_item.html', {'form': form})

@login_required
def update_inventory_item(request, item_id):
    if request.user.profile.role != 'police_commander':
        messages.error(request, "Permission Denied: Only the Commander can update inventory.")
        return redirect('view_inventory')
    item = get_object_or_404(InventoryItem, id=item_id)

    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            updated_item = form.save()
            messages.success(request, f"Success: {updated_item.item_name} has been updated.")
            return redirect('view_inventory')
    else:
        form = InventoryItemForm(instance=item)

    return render(request, 'update_inventory_item.html', {'form': form, 'item': item})

@login_required
def view_rosters(request):
    shifts = DutyRoster.objects.all()
    return render(request, 'view_rosters.html', {'shifts': shifts})

@login_required
def add_roster(request):
    if request.user.profile.role != 'police_commander':
        messages.error(request, "Permission Denied: Only the Commander can assign shifts.")
        return redirect('view_rosters')

    if request.method == 'POST':
        form = DutyRosterForm(request.POST)
        if form.is_valid():
            shift = form.save()
            messages.success(request, f"Shift assigned: {shift.officer.username} scheduled for {shift.get_shift_time_display()}.")
            return redirect('view_rosters')
    else:
        form = DutyRosterForm()

    return render(request, 'add_roster.html', {'form': form})