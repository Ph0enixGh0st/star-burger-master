from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from geopy.distance import great_circle as RADIUS

import requests

from api_cache.models import APICache
from .models import (
    Restaurant,
    Product,
    RestaurantMenuItem
)


YANDEX_MAPS_API_KEY = settings.YANDEX_MAPS_API_KEY

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
    restaurants = Restaurant.objects.prefetch_related(
        'menu_items'
        ).order_by('name')
    products = Product.objects.prefetch_related('items')
    products_in_order = products.filter(
        items__order=order_id,
        ).order_by('name').values_list('id')
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
            if order_coords:=fetch_coordinates(order.address):
                latitude, longitude = order_coords
            else:
                return {}
            order.latitude = latitude
            order.longitude = longitude
            order.save()

            print('ORDER ADRESS models.foodcartapp CHECK #1: ', order.address)

            APICache.objects.create(
                address=order.address,
                latitude=latitude,
                longitude=longitude,
                requested_at=datetime.now()
            )
            print('Created new api_cache address: ', APICache.objects.filter(address=order.address))

        else:
            order_coords = (order.latitude, order.longitude)
    restaurants_distances = {}
    for restaurant in restaurants:
        if not all([restaurant.latitude, restaurant.longitude]):
            if restaurant_coordinates:=fetch_coordinates(restaurant.address):
                latitude, longitude = restaurant_coordinates
                restaurant.latitude = latitude
                restaurant.longitude = longitude
                restaurant.save()
                restaurant_coords = (latitude, longitude)
            else:
                continue
        else:
            restaurant_coords = (restaurant.latitude, restaurant.longitude)

        distance = RADIUS(order_coords, restaurant_coords).km
        restaurants_distances[restaurant] = distance

    restaurants_distances_ordered = dict(
        sorted(restaurants_distances.items(), key=lambda x: x[1])
        )

    return restaurants_distances_ordered
