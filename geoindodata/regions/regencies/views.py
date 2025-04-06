from django.core.paginator import Paginator
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404

from geoindodata.apps.regions.models import Regency


def index(request: HttpRequest) -> HttpResponse:
    regencies = Regency.objects.select_related('province').order_by('regional_code')

    paginator = Paginator(regencies, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Regencies',
        'regencies': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'regions/regencies/index.html', context)


def details(request: HttpRequest, pk: int) -> HttpResponse:
    regency = get_object_or_404(Regency.objects.select_related('province'), pk=pk)

    return render(request, 'regions/regencies/details.html', {'regency': regency})
