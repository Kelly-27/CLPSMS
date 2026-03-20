from django.contrib import admin
from .models import LawReference, ChargeSheet
# (Make sure to keep your other models here too, like Case, ArrestedPerson, etc.)

# Register the new models so they show up in the admin panel
admin.site.register(LawReference)
admin.site.register(ChargeSheet)