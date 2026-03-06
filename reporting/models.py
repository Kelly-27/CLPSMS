from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Profile Model
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

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    description = models.TextField(blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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
    # Requirement 4: Type of Incident Choices
    INCIDENT_TYPES = (
        ('theft', 'Theft / Robbery'),
        ('assault', 'Assault'),
        ('traffic', 'Traffic Accident'),
        ('fraud', 'Fraud'),
        ('homicide', 'Homicide'),
        ('missing', 'Missing Person'),
        ('other', 'Other'),
    )
    ob_number = models.CharField(max_length=50, unique=True, blank=True, help_text="Auto-generated OB Number")
    incident_datetime = models.DateTimeField(help_text="When did the incident occur?")
    location = models.CharField(max_length=255, help_text="Exact location of the incident")
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES, default='other')
    description = models.TextField(help_text="Detailed narrative of the incident")
    reporter_name = models.CharField(max_length=150)
    reporter_id_number = models.CharField(max_length=50, help_text="National ID or Passport Number")
    reporter_phone = models.CharField(max_length=20)
    persons_involved = models.TextField(blank=True, help_text="Names and details of suspects, victims, or witnesses")
    additional_info = models.TextField(blank=True,
                                       help_text="Any extra details, weapon descriptions, vehicle plates, etc.")


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
            ('transferred', 'Transferred to Prison/Court'),
            ('released_free', 'Released without Charge'),
        ]

        related_case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name='suspects')
        first_name = models.CharField(max_length=50)
        last_name = models.CharField(max_length=50)
        id_number = models.CharField(max_length=20, blank=True, null=True, help_text="ID or Passport Number")
        gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
        age = models.PositiveIntegerField(blank=True, null=True)
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