import datetime

from django.utils import timezone


def make_due(days_offset: int) -> datetime.datetime:
    d = datetime.date.today() + datetime.timedelta(days=days_offset)
    return timezone.make_aware(datetime.datetime.combine(d, datetime.time(9, 0)))
