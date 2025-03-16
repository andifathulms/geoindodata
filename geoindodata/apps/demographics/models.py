from django.db import models
from model_utils import Choices


class Population(models.Model):
    village = models.ForeignKey("regions.Village", on_delete=models.CASCADE, related_name="populations")

    SOURCE = Choices(
        (1, 'bps', 'BPS'),
        (2, 'disdukcapil', 'Disdukcapil')
    )
    source = models.PositiveSmallIntegerField(choices=SOURCE)

    year = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Year for BPS data.")
    fetched_at = models.DateField(blank=True, null=True, help_text="Date when Disdukcapil data was fetched.")

    male_count = models.PositiveBigIntegerField(help_text="Male population count.")
    female_count = models.PositiveBigIntegerField(help_text="Female population count.")

    class Meta:
        # Prevent duplicate population entries for the same village, source, and year/date
        unique_together = [
            ('village', 'source', 'year'),
            ('village', 'source', 'fetched_at')
        ]
        indexes = [
            models.Index(fields=['source', 'year']),
            models.Index(fields=['source', 'fetched_at']),
        ]

    def __str__(self) -> str:
        """
        Return a string representation of this Population object.

        The string will include the name of the associated Village, the population value,
        the source of the population data, and the year or date when the data was fetched.

        :return: A string representation of this Population object.
        :rtype: str
        """

        date_info = self.year if self.year else self.fetched_at
        total = self.male_count + self.female_count
        return f"{self.village.name} - {total} ({self.get_source_display()} {date_info})"

    @property
    def total(self) -> int:
        """Return the total population (male + female)."""
        return self.male_count + self.female_count
