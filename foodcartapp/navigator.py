from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from geopy.distance import great_circle as RADIUS

import logging
import requests

from api_cache.models import APICache
from .models import (
    Restaurant,
    Product,
    RestaurantMenuItem
)


YANDEX_MAPS_API_KEY = settings.YANDEX_MAPS_API_KEY

logging.basicConfig(filename='error.log', level=logging.ERROR)


def fetch_coordinates(address, api_key=YANDEX_MAPS_API_KEY):
    api_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(api_url, params={
        "geocode": address,
        "apikey": api_key,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


def fetch_available_restaurants(order_id):
    restaurants = Restaurant.objects.prefetch_related('menu_items').order_by('name')
    products_in_order = Product.objects.prefetch_related('items').filter(
        Q(items__order__id=order_id)
    ).order_by('name').values_list('id', flat=True)
    menu_items = RestaurantMenuItem.objects.all()

    is_product_in_restaurant = {}
    for restaurant in restaurants:
        is_product_in_restaurant[restaurant.id] = [
                item.availability for item in menu_items.filter(
                    product__in=products_in_order, restaurant=restaurant,
                ).order_by('product__name')
                ]

    restaurants_with_complete_set = [
        restaurant.id for restaurant in restaurants if all(
            is_product_in_restaurant[restaurant.id]
        )
    ]
    return restaurants.filter(id__in=restaurants_with_complete_set)


def fetch_restaurants_distances(restaurants, order):
    try:
        cached_address = APICache.objects.get(address=order.address)
    except ObjectDoesNotExist:
        cached_address = None

    if cached_address:
        order_coords = (cached_address.latitude, cached_address.longitude)

    else:
        if not all([order.latitude, order.longitude]):
            if order.address:
                if order_coords := fetch_coordinates(order.address):
                    latitude, longitude = order_coords
                else:
                    return {}
                order.latitude = latitude
                order.longitude = longitude
                order.save()

                APICache.objects.create(
                    address=order.address,
                    latitude=latitude,
                    longitude=longitude,
                    requested_at=datetime.now()
                )
            else:
                logging.error(
                    f"Coordinates failed: corrupt order address for id {order.id}"
                )
                order_coords = (0, 0)
        else:
            order_coords = (order.latitude, order.longitude)
    restaurants_distances = {}
    for restaurant in restaurants:
        if not all([restaurant.latitude, restaurant.longitude]):
            if restaurant.address:
                if restaurant_coordinates := fetch_coordinates(restaurant.address):
                    latitude, longitude = restaurant_coordinates
                    restaurant.latitude = latitude
                    restaurant.longitude = longitude
                    restaurant.save()
                    restaurant_coords = (latitude, longitude)
                else:
                    logging.error(
                        f"Coordinates failed: haven't received coords {restaurant.name}"
                    )
                    restaurant_coords = (0, 0)
            else:
                logging.error(
                    f"Coordinates failed: corrupt restaurant address for {restaurant.name}"
                )
                restaurant_coords = (0, 0)
        else:
            restaurant_coords = (restaurant.latitude, restaurant.longitude)

        if order_coords or restaurant_coords == (0, 0):
            distance = -999999
        else:
            distance = RADIUS(order_coords, restaurant_coords).km

        restaurants_distances[restaurant] = distance

    restaurants_distances_ordered = dict(
        sorted(restaurants_distances.items(), key=lambda x: x[1])
        )

    return restaurants_distances_ordered
