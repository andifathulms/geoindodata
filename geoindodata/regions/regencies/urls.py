from django.urls import path

from . import views


app_name = "regencies"

urlpatterns = [
    path('', views.index, name="index"),
    path('<int:pk>/', views.details, name="details")
]
