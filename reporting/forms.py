from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile, ArrestedPerson, Evidence, InventoryItem, DutyRoster
from .models import Case


class OfficerCreationForm(UserCreationForm):
    # User fields
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    # Profile fields
    rank = forms.ChoiceField(choices=Profile.RANK_CHOICES, required=True)
    badge_number = forms.CharField(max_length=20, required=True, label="Badge Number (Used as Username)")
    phone = forms.CharField(max_length=15, required=False)
    image = forms.ImageField(required=False)

    role = forms.ChoiceField(
        choices=[('officer', 'Officer'), ('crime_desk', 'Crime Desk Officer')],
        required=True,
        label="Role"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'badge_number', 'rank', 'phone', 'image', 'role', 'password1',
                  'password2']

    def clean_badge_number(self):
        badge = self.cleaned_data.get('badge_number')
        if User.objects.filter(username=badge).exists():
            raise ValidationError("A user with this Badge Number already exists.")
        return badge

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['badge_number']

        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                rank=self.cleaned_data['rank'],
                badge_number=self.cleaned_data['badge_number'],
                phone=self.cleaned_data['phone'],
                image=self.cleaned_data['image'],
                role=self.cleaned_data['role']
            )
        return user


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        exclude = ['ob_number', 'status']

        widgets = {
            'desk_officer': forms.Select(attrs={'class': 'form-select form-select-lg', 'required': True}),

            'incident_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., Litein Main Stage'}),
            'incident_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Full narrative of what occurred...'}),
            'reporter_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'reporter_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID or Passport'}),
            'reporter_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07...'}),
            'persons_involved': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Suspects, Victims, Witnesses...'}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                     'placeholder': 'Stolen items, vehicle plates, weapons used...'}),

            'assigned_officers': forms.SelectMultiple(
                attrs={'class': 'form-select', 'help_text': 'Hold CTRL to select multiple officers'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_officers'].queryset = User.objects.exclude(profile__role='crime_desk')

class ArrestedPersonForm(forms.ModelForm):
    class Meta:
        model = ArrestedPerson
        fields = ['related_case', 'first_name', 'last_name', 'id_number', 'gender', 'age',
                  'phone_number', 'offense', 'cell_number']
        widgets = {
            'related_case': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID / Passport No.'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'offense': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., Theft, Assault...'}),
            'cell_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cell 1, Cell 2, etc.'}),
        }


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ['item_name', 'description', 'related_case', 'status', 'storage_location', 'image', 'logging_officer']
        widgets = {
            'item_name': forms.TextInput(
                attrs={'class': 'form-control form-control-lg', 'placeholder': "e.g., Recovered 9mm Handgun"}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                 'placeholder': "Describe the condition, serial numbers, etc."}),
            'related_case': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'storage_location': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': "e.g., Evidence Locker B-42"}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),

            'logging_officer': forms.Select(attrs={'class': 'form-select form-select-lg', 'required': True}),
        }
class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['item_name', 'category', 'serial_number', 'quantity', 'status', 'assigned_to']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Patrol Radio 04'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional for bulk items'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

class DutyRosterForm(forms.ModelForm):
    class Meta:
        model = DutyRoster
        fields = ['officer', 'shift_date', 'shift_time', 'duty_type', 'commander_notes']
        widgets = {
            'officer': forms.Select(attrs={'class': 'form-select'}),
            'shift_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'shift_time': forms.Select(attrs={'class': 'form-select'}),
            'duty_type': forms.Select(attrs={'class': 'form-select'}),
            'commander_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional instructions (e.g., Patrol Sector 4)'}),
        }