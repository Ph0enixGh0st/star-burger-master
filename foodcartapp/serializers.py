from rest_framework.serializers import ModelSerializer

from .models import Order, OrderItem, Product


class OrderItemSerializer(ModelSerializer):
        class Meta:
            model = OrderItem
            fields = [
                'product',
                'quantity'
            ]

class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(
         many=True,
         allow_empty=False,
         write_only=True
    )

    class Meta:
        model = Order
        fields = [
            'products',
            'id',
            'firstname',
            'lastname',
            'phonenumber',
            'address'
        ]
