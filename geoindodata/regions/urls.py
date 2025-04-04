from django.urls import path, include


app_name = "regions"

urlpatterns = [
    path('geoghrapic-units/', include("geoindodata.regions.geographic_units.urls")),
    path('provinces/', include("geoindodata.regions.provinces.urls")),
    path('regencies/', include("geoindodata.regions.regencies.urls"))
]
