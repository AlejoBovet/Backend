from django.contrib import admin
from .models import Alimento, Dispensa, HistorialAlimentos, Minuta, Users
# Register your models here.

admin.site.register(Alimento)
admin.site.register(Dispensa)
admin.site.register(HistorialAlimentos)
admin.site.register(Minuta)
admin.site.register(Users)
# Compare this snippet from AppMinutIA/Backend/minutia/apirest/admin.py: