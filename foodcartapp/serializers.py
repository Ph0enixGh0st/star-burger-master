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

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = super().create(validated_data)

        order_items = []
        for product_data in products_data:
            product = product_data['product']
            product_quantity = product_data['quantity']
            order_items.append(
                OrderItem(
                    product=product,
                    item_price=product.price,
                    quantity=product_quantity,
                    order=order,
                )
            )
        OrderItem.objects.bulk_create(order_items)
        return order
