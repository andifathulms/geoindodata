from django.contrib import admin

from .models import GeographicUnit, Province, Regency, District, Village

admin.site.register(GeographicUnit)
admin.site.register(Province)
admin.site.register(Regency)
admin.site.register(District)
admin.site.register(Village)
