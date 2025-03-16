import datetime
from django.db.models import Q, Sum, F, Value, ExpressionWrapper, IntegerField

from geoindodata.apps.regions.models import District, Regency, Province
from geoindodata.apps.demographics.models import Population

from typing import Optional


def get_population(self, source: str = "bps", year: Optional[int] = None, fetched_at: Optional[str] = None,
                   gender: str = "total") -> int:
    """
    Return the total population under this [district/regency/province] from the specified source.

    Parameters:
    - source: "bps" or "disdukcapil"
    - year: Year for BPS data or filter year for disdukcapil data
    - fetched_at: Specific date for disdukcapil data
    - gender: "male", "female", or "total" (default)

    Returns the most recent data if no year/date is specified.
    """

    source_id = dict([(v, k) for k, v in Population.SOURCE_TYPE])[source]

    # Base query depends on the model type
    if isinstance(self, District):
        query = {"source": source_id, "village__district": self}
    elif isinstance(self, Regency):
        query = {"source": source_id, "village__district__regency": self}
    elif isinstance(self, Province):
        query = {"source": source_id, "village__district__regency__province": self}

    # Source-specific filtering
    if source == "bps":
        if year:
            query["year"] = year

            if gender == "male":
                result = Population.objects.filter(**query).aggregate(total=Sum('male_count'))
            elif gender == "female":
                result = Population.objects.filter(**query).aggregate(total=Sum('female_count'))
            else:  # total
                result = Population.objects.filter(**query).aggregate(
                    total=Sum(ExpressionWrapper(F('male_count') + F('female_count'), output_field=IntegerField()))
                )

            return result['total'] or 0
        else:
            # For higher-level entities, when year is not specified,
            # we need to get the latest year that has data
            queryset = Population.objects.filter(source=source_id)

            # Add appropriate filter for the model type
            if isinstance(self, District):
                queryset = queryset.filter(village__district=self)
            elif isinstance(self, Regency):
                queryset = queryset.filter(village__district__regency=self)
            elif isinstance(self, Province):
                queryset = queryset.filter(village__district__regency__province=self)

            latest_year = queryset.order_by('-year').values_list('year', flat=True).first()

            if latest_year:
                query["year"] = latest_year

                if gender == "male":
                    result = Population.objects.filter(**query).aggregate(total=Sum('male_count'))
                elif gender == "female":
                    result = Population.objects.filter(**query).aggregate(total=Sum('female_count'))
                else:  # total
                    result = Population.objects.filter(**query).aggregate(
                        total=Sum(ExpressionWrapper(F('male_count') + F('female_count'), output_field=IntegerField()))
                    )

                return result['total'] or 0
            return 0

    elif source == "disdukcapil":
        if fetched_at:
            # Specific fetched_at date
            query["fetched_at"] = fetched_at

            if gender == "male":
                result = Population.objects.filter(**query).aggregate(total=Sum('male_count'))
            elif gender == "female":
                result = Population.objects.filter(**query).aggregate(total=Sum('female_count'))
            else:  # total
                result = Population.objects.filter(**query).aggregate(
                    total=Sum(ExpressionWrapper(F('male_count') + F('female_count'), output_field=IntegerField()))
                )

            return result['total'] or 0
        elif year:
            # Get data with fetched_at in the specified year
            start_date = datetime.date(year, 1, 1)
            end_date = datetime.date(year, 12, 31)

            base_query = Population.objects.filter(source=source_id)
            if isinstance(self, District):
                base_query = base_query.filter(village__district=self)
            elif isinstance(self, Regency):
                base_query = base_query.filter(village__district__regency=self)
            elif isinstance(self, Province):
                base_query = base_query.filter(village__district__regency__province=self)

            year_query = base_query.filter(
                Q(fetched_at__gte=start_date) & 
                Q(fetched_at__lte=end_date)
            )

            # Get the most recent fetched_at date within that year
            latest_date = year_query.order_by('-fetched_at').values_list('fetched_at', flat=True).first()

            if latest_date:
                date_query = base_query.filter(fetched_at=latest_date)

                if gender == "male":
                    result = date_query.aggregate(total=Sum('male_count'))
                elif gender == "female":
                    result = date_query.aggregate(total=Sum('female_count'))
                else:  # total
                    result = date_query.aggregate(
                        total=Sum(ExpressionWrapper(F('male_count') + F('female_count'), output_field=IntegerField()))
                    )

                return result['total'] or 0
            return 0
        else:
            # Get the most recent data based on fetched_at
            base_query = Population.objects.filter(source=source_id)
            if isinstance(self, District):
                base_query = base_query.filter(village__district=self)
            elif isinstance(self, Regency):
                base_query = base_query.filter(village__district__regency=self)
            elif isinstance(self, Province):
                base_query = base_query.filter(village__district__regency__province=self)

            latest_date = base_query.order_by('-fetched_at').values_list('fetched_at', flat=True).first()

            if latest_date:
                date_query = base_query.filter(fetched_at=latest_date)

                if gender == "male":
                    result = date_query.aggregate(total=Sum('male_count'))
                elif gender == "female":
                    result = date_query.aggregate(total=Sum('female_count'))
                else:  # total
                    result = date_query.aggregate(
                        total=Sum(ExpressionWrapper(F('male_count') + F('female_count'), output_field=IntegerField()))
                    )

                return result['total'] or 0
            return 0

    return 0
