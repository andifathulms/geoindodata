from django.core.paginator import Paginator
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from geoindodata.apps.regions.models import GeographicUnit


def index(request: HttpRequest) -> HttpResponse:
    units = GeographicUnit.objects.all().order_by('id')

    paginator = Paginator(units, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Unit Geografis',
        'geographic_units': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'regions/geographic_units/index.html', context)