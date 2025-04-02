from django.urls import path

from . import views


app_name = "geographic_units"

urlpatterns = [
    path('', views.index, name="index"),
]
