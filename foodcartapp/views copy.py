import json

from django.http import JsonResponse
from django.templatetags.static import static

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order, OrderItem

from.serializers import OrderItemSerializer, OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):

    serializer = OrderSerializer(data=request.data)
    print('Serializer: ', serializer)
    serializer.is_valid(raise_exception=True)

    order_positions = serializer.validated_data
    print('ORDER POS_1: ' ,order_positions)
    products = dict(order_positions.pop('products'))
    #order_positions = dict(order_positions)

    print('ORDER POS_2: ' ,order_positions)
    print('Products: ', products)

    '''
    ORDER DESC:  OrderedDict([('firstname', 'Василий'), ('lastname', 'Васильевич'), ('phonenumber', '+79123456789'), ('address', 'Лондон')])
    Products:  [OrderedDict([('product', <Product: Стейкхаус>), ('quantity', 1)])]

    ORDER POS_1:  OrderedDict([('products', [OrderedDict([('product', <Product: Стейкхаус>), ('quantity', 1)])]), ('firstname', 'Василий'), ('lastname', 'Васильевич'), ('phonenumber', '+79123456789'), ('address', 'Лондон')])
    ORDER POS_2:  {'firstname': 'Василий', 'lastname': 'Васильевич', 'phonenumber': '+79123456789', 'address': 'Лондон'}
    Products:  {'product': 'quantity'}

    '''

    order_intake = Order.objects.create(
        firstname=order_positions['firstname'],
        lastname=order_positions['lastname'],
        address=order_positions['address'],
        phonenumber=order_positions['phonenumber']
    )
    products = order_positions['products']

    order_items = []
    for item in products:
        print('item: ', item)
        order_items.append(OrderItem(
            order = order_intake,
            product=Product.objects.get(id=item['product']),
            quantity=int(item['quantity']),
            item_price=int(Product.objects.filter(id=item['product']).values_list('price', flat=True).first())
            )
        )

    OrderItem.objects.bulk_create(order_items)

    return Response(order_positions)
