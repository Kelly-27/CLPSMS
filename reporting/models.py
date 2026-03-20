from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import hashlib
from datetime import date




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('police_commander', 'Police Commander'),
        ('officer', 'Officer'),
        ('crime_desk', 'Crime Desk Officer'),
    ], default='crime_desk')

    RANK_CHOICES = [
        ('detective', 'Detective'),
        ('corporal', 'Corporal'),
        ('sergeant', 'Sergeant'),
        ('constable', 'Constable'),
    ]
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, blank=True)
    badge_number = models.CharField(max_length=20, unique=True, blank=True)

    phone = models.CharField(max_length=15, blank=True)
    image = models.ImageField(upload_to='officer_images/', blank=True, null=True)

    @property
    def current_status(self):
        today = date.today()
        is_on_leave = self.user.leave_requests.filter(
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        ).exists()

        return "On Leave" if is_on_leave else "Active Duty"

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class EvidenceLedger(models.Model):

    evidence = models.ForeignKey('Evidence', on_delete=models.CASCADE, related_name='ledger_entries')
    action = models.CharField(max_length=100)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()

    previous_hash = models.CharField(max_length=64, blank=True, null=True)
    current_hash = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            last_block = EvidenceLedger.objects.filter(evidence=self.evidence).order_by('-id').first()

            if last_block:
                self.previous_hash = last_block.current_hash
            else:
                self.previous_hash = "GENESIS_BLOCK"

            handler_id = str(self.handled_by.id) if self.handled_by else "None"
            data_to_hash = f"{self.evidence.id}-{self.action}-{handler_id}-{self.details}-{self.previous_hash}"

            self.current_hash = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.evidence} | {self.action} | Hash: {self.current_hash[:10]}..."


class Roster(models.Model):
    officer = models.ForeignKey(User, on_delete=models.CASCADE)
    duty_date = models.DateField()
    shift = models.CharField(max_length=50,
                             choices=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night')])
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_rosters')
    date_assigned = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.officer.username} - {self.duty_date}"


class Case(models.Model):
    INCIDENT_TYPES = (
        ('theft', 'Theft / Robbery'),
        ('assault', 'Assault'),
        ('traffic', 'Traffic Accident'),
        ('fraud', 'Fraud'),
        ('homicide', 'Homicide'),
        ('missing', 'Missing Person'),
        ('other', 'Other'),
    )
    ob_number = models.CharField(max_length=50, unique=True, blank=True,)
    incident_datetime = models.DateTimeField()
    location = models.CharField(max_length=255)
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES, default='other')
    description = models.TextField(max_length=300, help_text="Full description of what occurred")
    reporter_name = models.CharField(max_length=150)
    reporter_id_number = models.CharField(max_length=50,)
    reporter_phone = models.CharField(max_length=20)
    persons_involved = models.TextField(blank=True, help_text="Names and details of suspects, victims, or witnesses")
    additional_info = models.TextField(blank=True,)


    assigned_officers = models.ManyToManyField(User, related_name='investigating_cases', blank=True,
                                               help_text="Officers assigned to this case")

    desk_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='logged_reports')

    date_logged = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('closed', 'Closed')], default='open')

    def save(self, *args, **kwargs):

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.ob_number:
            today = timezone.now()
            self.ob_number = f"OB/{today.strftime('%d/%m/%Y')}/{self.pk}"
            self.save(update_fields=['ob_number'])

    def __str__(self):
        return f"{self.ob_number} - {self.get_incident_type_display()}"


class ArrestedPerson(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    STATUS_CHOICES = [
        ('in_custody', 'In Custody'),
        ('released_bail', 'Released on Bail'),
        ('transferred', 'Transferred to Prison'),
        ('released_free', 'Released without Charge'),
    ]

    related_case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name='suspects')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    id_number = models.CharField(max_length=20, blank=True, null=True,)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_arrested = models.DateTimeField(auto_now_add=True)
    offense = models.CharField(max_length=200, help_text="Specific reason for arrest")
    cell_number = models.CharField(max_length=10, blank=True, null=True, help_text="Holding cell assignment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_custody')
    arresting_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='arrests_made')

    def __str__(self):
        if self.related_case:
            return f"{self.first_name} {self.last_name} - {self.related_case.ob_number}"
        return f"{self.first_name} {self.last_name} - (Pending Case)"

class Evidence(models.Model):
    STATUS_CHOICES = [
        ('in_locker', 'In Locker'),
        ('at_lab', 'At the Lab'),
        ('in_court', 'Presented in Court'),
        ('released', 'Released to Owner'),
        ('destroyed', 'Destroyed'),
    ]

    item_name = models.CharField(max_length=200)
    description = models.TextField(help_text="Detailed description of the item and its condition.")

    related_case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='evidence_items')
    logging_officer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='logged_evidence')

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='in_locker')
    storage_location = models.CharField(max_length=100,)
    image = models.ImageField(upload_to='evidence_photos/', null=True, blank=True)

    date_logged = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.related_case:
            return f"{self.item_name} - {self.related_case.ob_number}"
        return f"{self.item_name} - (Pending Case)"


class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('weapon', 'Weapon'),
        ('vehicle', 'Police Vehicle'),
        ('radio', 'Radio'),
        ('uniform', 'Uniform'),
        ('gear', 'Gear'),
        ('stationery', 'Office Supplies / Stationery'),
        ('other', 'Other Equipment'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available in Store'),
        ('assigned', 'Assigned to Officer'),
        ('maintenance', 'Under Maintenance'),
        ('lost_damaged', 'Lost / Damaged'),
    ]

    item_name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    serial_number = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='available')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_equipment')

    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.serial_number:
            return f"{self.item_name} (SN: {self.serial_number})"
        return f"{self.item_name} (Qty: {self.quantity})"


class DutyRoster(models.Model):
    SHIFT_CHOICES = [
        ('morning', 'Morning Shift (0600 - 1400 hrs)'),
        ('evening', 'Evening Shift (1400 - 2200 hrs)'),
        ('night', 'Night Shift (2200 - 0600 hrs)'),
    ]

    DUTY_CHOICES = [
        ('patrol', 'General Patrol'),
        ('report_desk', 'Report Desk'),
        ('guard', 'Cell Duty'),
        ('respond','Respond to Calls'),
        ('sguard', 'Station Guard'),
        ('traffic', 'Traffic Control'),
        ('investigation', 'Active Investigation'),
        ('reserve', 'Standby'),
    ]

    officer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='duty_shifts')
    shift_date = models.DateField()
    shift_time = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    duty_type = models.CharField(max_length=20, choices=DUTY_CHOICES)

    commander_notes = models.TextField(blank=True, null=True)

    date_assigned = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['officer', 'shift_date', 'shift_time']
        ordering = ['-shift_date', 'shift_time']

    def __str__(self):
        return f"{self.officer.get_full_name() or self.officer.username} - {self.get_shift_time_display()} on {self.shift_date}"

class AuditLog(models.Model):
        user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
        action = models.CharField(max_length=100)
        timestamp = models.DateTimeField(auto_now_add=True)
        ip_address = models.GenericIPAddressField(null=True, blank=True)
        details = models.TextField(blank=True, null=True)

        def __str__(self):
            username = self.user.username if self.user else "System"
            return f"{username} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class LawReference(models.Model):
    """Stores the specific laws officers can select from a dropdown."""
    act_name = models.CharField(max_length=255, help_text="e.g., Penal Code Cap 63, Immigration Act Cap 172")
    section = models.CharField(max_length=100, help_text="e.g., Section 13 (2) (f)")
    offense_name = models.CharField(max_length=255, help_text="e.g., Willfully obstructing an immigration officer")
    default_charge_text = models.TextField(help_text="The formal legal text to auto-fill the charge sheet.")

    def __str__(self):
        return f"{self.act_name} - {self.section}: {self.offense_name}"


class ChargeSheet(models.Model):

    related_case = models.ForeignKey(Case, on_delete=models.SET_NULL, related_name='charge_sheets', null=True, blank=True)
    accused_person = models.ForeignKey(ArrestedPerson, on_delete=models.CASCADE, related_name='charges')
    court_file_no = models.CharField(max_length=100, blank=True, null=True)
    date_to_court = models.DateField(blank=True, null=True)
    law_broken = models.ForeignKey(LawReference, on_delete=models.RESTRICT)
    particulars_of_offense = models.TextField()

    date_of_arrest = models.DateField()
    witnesses = models.TextField(blank=True, null=True,help_text="List witnesses and their nationalities")
    arrested_with_warrant = models.BooleanField(default=False, help_text="Check if arrested with a warrant")
    remanded_or_bailed = models.CharField(max_length=50, choices=[
        ('In Custody', 'In Custody'),
        ('Out on Bail', 'Out on Bail'),
        ('Remanded', 'Remanded')
    ], default='In Custody')


    complainant = models.CharField(max_length=255, default="REPUBLIC OF KENYA")
    police_station = models.CharField(max_length=100, default="Litein Police Station")
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_prepared = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.related_case:
            return f"CHARGE SHEET: {self.accused_person} | OB: {self.related_case.ob_number}"
        return f"CHARGE SHEET: {self.accused_person} | OB: Direct Arrest (No OB)"


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity/Paternity Leave'),
        ('compassionate', 'Compassionate Leave'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Commander Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    officer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(help_text="Provide details for your leave request.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_applied = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.officer.username} - {self.get_leave_type_display()} ({self.status})"


class WantedPerson(models.Model):
    THREAT_LEVELS = [
        ('high', 'High - Armed and Dangerous'),
        ('medium', 'Medium - Proceed with Caution'),
        ('low', 'Low - Standard Apprehension')
    ]

    full_name = models.CharField(max_length=150)
    alias = models.CharField(max_length=100, blank=True, null=True)

    image = models.ImageField(upload_to='wanted_posters/', blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    height = models.CharField(max_length=50, blank=True, null=True)
    threat_level = models.CharField(max_length=20, choices=THREAT_LEVELS, default='medium')
    last_known_location = models.CharField(max_length=255, blank=True, null=True)

    crimes = models.CharField(max_length=255)
    description = models.TextField(help_text="Physical description, scars, tattoos")
    is_active = models.BooleanField(default=True, help_text="Uncheck if captured")
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"WANTED: {self.full_name} - {self.get_threat_level_display()}"