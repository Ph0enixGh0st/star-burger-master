from datetime import datetime

from django.db import models
from django.utils import timezone

from foodcartapp.validators import lat_validators, lng_validators
'''
Хранит адрес места и координаты места на карте
Хранит дату запроса к геокодеру, чтобы знать когда пора обновить данные
unique
'''

class APICache(models.Model):
    id = models.AutoField(
        verbose_name='Номер запроса к API',
        primary_key=True,
        db_index=True
    )
    address = models.CharField(
        verbose_name='Адрес',
        max_length=200,
        db_index=True
    )
    latitude = models.FloatField(
        validators=lat_validators,
        verbose_name='Широта',
        null=True,
        blank=True,
    )
    longitude = models.FloatField(
        validators=lng_validators,
        verbose_name='Долгота',
        null=True,
        blank=True,
    )
    requested_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    class Meta:
        verbose_name = 'Кэшированный адрес'
        verbose_name_plural = 'Кэшированные адреса'

    def __str__(self):
        return f'Адрес: {self.address} // Запрошен: {self.requested_at}'
