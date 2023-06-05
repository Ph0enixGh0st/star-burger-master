from django.core.validators import MinValueValidator, MaxValueValidator

lng_validator_message = 'Долгота должна быть в диапазоне от -180 до 180'
lng_validators = [
    MinValueValidator(-180, lng_validator_message),
    MaxValueValidator(180, lng_validator_message),
                 ]
lat_validator_message = 'Широта должна быть в диапазоне от -90 до 90'
lat_validators = [
    MinValueValidator(-90, lat_validator_message),
    MaxValueValidator(90, lat_validator_message),
    ]