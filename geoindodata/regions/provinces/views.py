from django.core.paginator import Paginator
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from geoindodata.apps.regions.models import Province


def index(request: HttpRequest) -> HttpResponse:
    provinces = Province.objects.select_related('geographical_unit').order_by('regional_code')

    paginator = Paginator(provinces, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Provinces',
        'provinces': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'regions/provinces/index.html', context)
