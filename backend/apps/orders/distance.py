from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from django.core.exceptions import ValidationError


EARTH_RADIUS_MILES = 3958.7613


def distance_miles(*, origin_latitude, origin_longitude, destination_latitude, destination_longitude) -> Decimal:
    values = tuple(
        float(value)
        for value in (origin_latitude, origin_longitude, destination_latitude, destination_longitude)
    )
    origin_lat, origin_lng, destination_lat, destination_lng = values
    if not -90 <= origin_lat <= 90 or not -90 <= destination_lat <= 90:
        raise ValidationError({"delivery_latitude": "Latitude must be between -90 and 90."})
    if not -180 <= origin_lng <= 180 or not -180 <= destination_lng <= 180:
        raise ValidationError({"delivery_longitude": "Longitude must be between -180 and 180."})

    latitude_delta = radians(destination_lat - origin_lat)
    longitude_delta = radians(destination_lng - origin_lng)
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(origin_lat))
        * cos(radians(destination_lat))
        * sin(longitude_delta / 2) ** 2
    )
    miles = 2 * EARTH_RADIUS_MILES * asin(sqrt(haversine))
    return Decimal(str(miles)).quantize(Decimal("0.001"))
