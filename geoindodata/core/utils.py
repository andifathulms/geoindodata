import os
import shortuuid

from django.template.defaultfilters import slugify
from django.utils import timezone


class FilenameGenerator(object):
    """
    Utility class to handle generation of file upload path
    """
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def __call__(self, instance: object, filename: str) -> str:
        today = timezone.localdate()

        filepath = os.path.basename(filename)
        filename, extension = os.path.splitext(filepath)
        filename = slugify(shortuuid.uuid()[:10])

        path = "/".join([
            self.prefix,
            today.strftime('%Y/%m/%d'),
            filename + extension
        ])
        return path


try:
    from django.utils.deconstruct import deconstructible
    FilenameGenerator = deconstructible(FilenameGenerator)  # type: ignore
except ImportError:
    pass
