import datetime

from django.db import models
from django.db.models import Q, Sum, F

from model_utils import Choices
from thumbnails.fields import ImageField

from geoindodata.apps.demographics.models import Population
from geoindodata.core.utils import FilenameGenerator

from decimal import Decimal
from typing import Optional


class GeographicUnit(models.Model):
    code = models.CharField(max_length=5, unique=True, db_index=True)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Province(models.Model):
    regional_code = models.CharField(max_length=2, unique=True, db_index=True)
    iso_code = models.CharField(max_length=2)
    name = models.CharField(max_length=100)
    geographical_unit = models.ForeignKey(GeographicUnit, on_delete=models.CASCADE, related_name="provinces")

    capital_name = models.CharField(max_length=100, blank=True, null=True)
    capital = models.ForeignKey("Regency", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="province_capitals",
                                help_text="Optional reference if the capital is a regency/city.")

    nickname = models.CharField(max_length=255, blank=True, null=True)
    motto = models.CharField(max_length=255, blank=True, null=True)
    motto_language = models.CharField(max_length=100, blank=True, null=True)
    motto_translation = models.CharField(max_length=255, blank=True, null=True)
    established_date = models.DateField(blank=True, null=True)
    legal_basis = models.CharField(max_length=255, blank=True, null=True)
    anniversary_date = models.DateField(blank=True, null=True)

    flag = ImageField(upload_to=FilenameGenerator(prefix='provinces'), blank=True, null=True)
    coat_of_arms = ImageField(upload_to=FilenameGenerator(prefix='provinces'), blank=True, null=True)

    def __str__(self) -> str:
        return self.name

    def regency_count(self) -> int:
        """Return the number of regencies under this province."""
        return self.regencies.filter(type=Regency.TYPE.kabupaten).count()

    def city_count(self) -> int:
        """Return the number of cities under this province."""
        return self.regencies.filter(type=Regency.TYPE.kota).count()

    def district_count(self) -> int:
        """Return the total number of districts under this province."""
        return sum(regency.districts.count() for regency in self.regencies.all())

    def village_count(self) -> int:
        """Return the total number of villages under this province."""
        return sum(
            district.villages.count()
            for regency in self.regencies.all()
            for district in regency.districts.all()
        )

    def get_area(self, source: str = "gis") -> Decimal:
        """Return the total area of all villages under this province, in square kilometers."""
        total_area = Decimal('0.0')
        for regency in self.regencies.all():
            area = regency.get_area(source)
            if area:
                total_area += area
        return total_area

    def get_population(self, source: str = "bps", year: Optional[int] = None, fetched_at: Optional[str] = None,
                       gender: str = "total") -> int:
        from geoindodata.apps.regions.utils import get_population

        return get_population(self, source, year, fetched_at, gender)

    @property
    def area(self) -> Decimal:
        """Default area (GIS) of the province in square kilometers."""
        return self.get_area()

    @property
    def population(self) -> int:
        """Default population (BPS, most recent) of the province."""
        return self.get_population()

    @property
    def male_population(self) -> int:
        """Default male population (BPS, most recent) of the entity."""
        return self.get_population(gender="male")

    @property
    def female_population(self) -> int:
        """Default female population (BPS, most recent) of the entity."""
        return self.get_population(gender="female")

    @property
    def gender_ratio(self) -> float:
        """Male to female ratio (number of males per 100 females)."""
        females = self.female_population
        if females == 0:
            return 0
        return (self.male_population / females) * 100


class Regency(models.Model):
    regional_code = models.CharField(max_length=4, unique=True, db_index=True)
    sni_code = models.CharField(max_length=3, blank=True, null=True)
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="regencies")

    TYPE = Choices(
        (1, 'kabupaten', 'Kabupaten'),
        (2, 'kota', 'Kota'),
        (3, 'kabupaten_administratif', 'Kabupaten Administratif'),
        (4, 'kota_administratif', 'Kota Administratif')
    )
    type = models.PositiveSmallIntegerField(choices=TYPE)

    capital_name = models.CharField(max_length=100, blank=True, null=True)
    capital = models.ForeignKey("District", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="regency_capitals",
                                help_text="Optional reference if the capital is a district.")

    nickname = models.CharField(max_length=255, blank=True, null=True)
    motto = models.CharField(max_length=255, blank=True, null=True)
    motto_language = models.CharField(max_length=100, blank=True, null=True)
    motto_translation = models.CharField(max_length=255, blank=True, null=True)
    established_date = models.DateField(blank=True, null=True)
    legal_basis = models.CharField(max_length=255, blank=True, null=True)
    anniversary_date = models.DateField(blank=True, null=True)

    vehicle_plate_prefix = models.CharField(
        max_length=2, blank=True, null=True,
        help_text="The optional prefix of the plate number (e.g., 'AB', 'BC', 'CD').")
    vehicle_plate_suffix = models.CharField(max_length=50, blank=True, null=True,
                                            help_text="The optional suffix of the plate number (e.g., 'D', 'V', 'Z').")

    flag = ImageField(upload_to=FilenameGenerator(prefix='regencies'), blank=True, null=True)
    coat_of_arms = ImageField(upload_to=FilenameGenerator(prefix='regencies'), blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.get_type_display()} {self.name}"

    def district_count(self) -> int:
        """Return the total number of districts under this regency."""
        return self.districts.count()

    def village_count(self) -> int:
        """Return the total number of villages under this regency."""
        return sum(district.villages.count() for district in self.districts.all())

    def get_area(self, source: str = "gis") -> Decimal:
        """Return the total area of all villages under this regency, in square kilometers."""
        total_area = Decimal('0.0')
        for district in self.districts.all():
            area = district.get_area(source)
            if area:
                total_area += area
        return total_area

    def get_population(self, source: str = "bps", year: Optional[int] = None, fetched_at: Optional[str] = None,
                       gender: str = "total") -> int:
        from geoindodata.apps.regions.utils import get_population

        return get_population(self, source, year, fetched_at, gender)

    @property
    def area(self) -> Decimal:
        """Default area (GIS) of the province in square kilometers."""
        return self.get_area()

    @property
    def population(self) -> int:
        """Default population (BPS, most recent) of the province."""
        return self.get_population()

    @property
    def male_population(self) -> int:
        """Default male population (BPS, most recent) of the entity."""
        return self.get_population(gender="male")

    @property
    def female_population(self) -> int:
        """Default female population (BPS, most recent) of the entity."""
        return self.get_population(gender="female")

    @property
    def gender_ratio(self) -> float:
        """Male to female ratio (number of males per 100 females)."""
        females = self.female_population
        if females == 0:
            return 0
        return (self.male_population / females) * 100


class District(models.Model):
    regional_code = models.CharField(max_length=6, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    regency = models.ForeignKey(Regency, on_delete=models.CASCADE, related_name="districts")

    TYPE = Choices(
        (1, 'kecamatan', 'Kecamatan'),
        (2, 'distrik', 'Distrik')
    )
    type = models.PositiveSmallIntegerField(choices=TYPE)

    capital_name = models.CharField(max_length=100, blank=True, null=True)
    capital = models.ForeignKey("Village", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="district_capitals",
                                help_text="Optional reference if the capital is a village.")

    def __str__(self) -> str:
        return f"{self.name} ({self.get_type_display()})"

    def village_count(self) -> int:
        """Return the total number of villages under this district."""
        return self.villages.count()

    def get_area(self, source: str = "gis") -> Decimal:
        """Return the total area of all villages under this district, in square kilometers,
        calculated from the specified source ('gis' or 'bps')."""
        return sum(village.get_area(source) for village in self.villages.all() if village.get_area(source))

    def get_population(self, source: str = "bps", year: Optional[int] = None, fetched_at: Optional[str] = None,
                       gender: str = "total") -> int:
        from geoindodata.apps.regions.utils import get_population

        return get_population(self, source, year, fetched_at, gender)

    @property
    def area(self) -> Decimal:
        """Default area (GIS) of the province in square kilometers."""
        return self.get_area()

    @property
    def population(self) -> int:
        """Default population (BPS, most recent) of the province."""
        return self.get_population()

    @property
    def male_population(self) -> int:
        """Default male population (BPS, most recent) of the entity."""
        return self.get_population(gender="male")

    @property
    def female_population(self) -> int:
        """Default female population (BPS, most recent) of the entity."""
        return self.get_population(gender="female")

    @property
    def gender_ratio(self) -> float:
        """Male to female ratio (number of males per 100 females)."""
        females = self.female_population
        if females == 0:
            return 0
        return (self.male_population / females) * 100


class Village(models.Model):
    regional_code = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="villages")

    TYPE = Choices(
        (1, 'desa', 'Desa'),
        (2, 'kelurahan', 'Kelurahan')
    )
    type = models.PositiveSmallIntegerField(choices=TYPE)

    gis_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                   help_text="Area in square kilometers from GIS data.")
    bps_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                   help_text="Area in square kilometers from BPS data.")

    def __str__(self) -> str:
        return f"{self.name} ({self.get_type_display()})"

    def get_area(self, source: str = "gis") -> Decimal:
        """Return area from the specified source ('gis' or 'bps')."""
        if source == "gis" and self.gis_area is not None:
            return self.gis_area
        return self.bps_area  # Fallback to BPS if GIS is missing

    def get_population(self, source: str = "bps", year: Optional[int] = None, fetched_at: Optional[str] = None,
                       gender: str = "total") -> int:
        """
        Return the population of this village from the specified source.

        Parameters:
        - source: "bps" or "disdukcapil"
        - year: Year for BPS data or filter year for disdukcapil data
        - fetched_at: Specific date for disdukcapil data
        - gender: "male", "female", or "total" (default)

        Returns the most recent data if no year/date is specified.
        """

        source_id = dict([(v, k) for k, v in Population.SOURCE])[source]
        query = {"source": source_id, "village": self}

        # Determine the field to aggregate based on gender
        if gender == "male":
            value_field = "male_count"
        elif gender == "female":
            value_field = "female_count"
        else:  # total
            value_field = "male_count + female_count"  # We'll use this in the annotation

        # Source-specific filtering
        if source == "bps":
            if year:
                query["year"] = year
                try:
                    record = Population.objects.get(**query)
                    if gender == "male":
                        return record.male_count
                    elif gender == "female":
                        return record.female_count
                    else:
                        return record.male_count + record.female_count
                except Population.DoesNotExist:
                    return 0
                except Population.MultipleObjectsReturned:
                    if gender == "total":
                        result = Population.objects.filter(**query).aggregate(
                            total=Sum(F('male_count') + F('female_count'))
                        )
                    else:
                        result = Population.objects.filter(**query).aggregate(total=Sum(value_field))
                    return result['total'] or 0
            else:
                # Get the latest year's data
                latest = Population.objects.filter(source=source_id, village=self).order_by('-year').first()
                if latest:
                    if gender == "male":
                        return latest.male_count
                    elif gender == "female":
                        return latest.female_count
                    else:
                        return latest.male_count + latest.female_count
                return 0

        elif source == "disdukcapil":
            if fetched_at:
                # Specific fetched_at date
                query["fetched_at"] = fetched_at
                try:
                    record = Population.objects.get(**query)
                    if gender == "male":
                        return record.male_count
                    elif gender == "female":
                        return record.female_count
                    else:
                        return record.male_count + record.female_count
                except Population.DoesNotExist:
                    return 0
                except Population.MultipleObjectsReturned:
                    if gender == "total":
                        result = Population.objects.filter(**query).aggregate(
                            total=Sum(F('male_count') + F('female_count'))
                        )
                    else:
                        result = Population.objects.filter(**query).aggregate(total=Sum(value_field))
                    return result['total'] or 0
            elif year:
                # Get data with fetched_at in the specified year
                start_date = datetime.date(year, 1, 1)
                end_date = datetime.date(year, 12, 31)
                latest = Population.objects.filter(
                    Q(source=source_id) &
                    Q(village=self) &
                    Q(fetched_at__gte=start_date) &
                    Q(fetched_at__lte=end_date)
                ).order_by('-fetched_at').first()

                if latest:
                    if gender == "male":
                        return latest.male_count
                    elif gender == "female":
                        return latest.female_count
                    else:
                        return latest.male_count + latest.female_count
                return 0
            else:
                # Get the most recent data based on fetched_at
                latest = Population.objects.filter(source=source_id, village=self).order_by('-fetched_at').first()
                if latest:
                    if gender == "male":
                        return latest.male_count
                    elif gender == "female":
                        return latest.female_count
                    else:
                        return latest.male_count + latest.female_count
                return 0

        return 0

    @property
    def area(self) -> Decimal:
        """Default area (GIS) of the province in square kilometers."""
        return self.get_area()

    @property
    def population(self) -> int:
        """Default population (BPS, most recent) of the province."""
        return self.get_population()

    @property
    def male_population(self) -> int:
        """Default male population (BPS, most recent) of the entity."""
        return self.get_population(gender="male")

    @property
    def female_population(self) -> int:
        """Default female population (BPS, most recent) of the entity."""
        return self.get_population(gender="female")

    @property
    def gender_ratio(self) -> float:
        """Male to female ratio (number of males per 100 females)."""
        females = self.female_population
        if females == 0:
            return 0
        return (self.male_population / females) * 100
