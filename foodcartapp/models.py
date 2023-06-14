from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone

from .validators import lat_validators, lng_validators


class Restaurant(models.Model):
    name = models.CharField(
        'Название',
        max_length=50
    )
    address = models.CharField(
        'Адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'Телефон',
        max_length=50,
        blank=True,
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

    class Meta:
        verbose_name = 'Ресторан'
        verbose_name_plural = 'Рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)

    def with_items_in_order(self, order_id):
        return self.prefetch_related('items').filter(items__order__id=order_id)


class ProductCategory(models.Model):
    name = models.CharField(
        'Название',
        max_length=50
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'Название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='Категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'Картинка'
    )
    special_status = models.BooleanField(
        'Спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'Описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name='Ресторан',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='Продукт',
    )
    availability = models.BooleanField(
        'В продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Пункт меню ресторана'
        verbose_name_plural = 'Пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.Manager):
    def get_total(self):
        return super().get_total().annotate(
            sum=Sum(F('items__item_price') * F('items__quantity'))
        )


class Order(models.Model):
    STATUS_CHOICES = [
        ('unprocessed', 'Не обработан'),
        ('en-route', 'В доставке'),
        ('completed', 'Выполнен'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличными'),
        ('non_cash', 'Электронно'),
     ]

    id = models.AutoField(
        verbose_name='Номер заказа',
        primary_key=True,
        db_index=True)
    firstname = models.CharField(
        verbose_name='Имя',
        max_length=50,
        db_index=True)
    lastname = models.CharField(
        verbose_name='Фамилия',
        max_length=50,
        db_index=True)
    address = models.CharField(
        verbose_name='Адрес',
        max_length=200,
        db_index=True)

    phonenumber = PhoneNumberField(verbose_name='Телефон', region='RU')

    status = models.CharField(
        'Статус заказа',
        max_length=15,
        default='unprocessed',
        choices=STATUS_CHOICES,
        db_index=True
    )
    payment_method = models.CharField(
        'Cпособ оплаты',
        default='cash',
        max_length=100,
        choices=PAYMENT_METHOD_CHOICES,
        db_index=True
    )
    comment = models.TextField(
        'Комментарий',
        max_length=500,
        blank=True,
    )
    registered_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    called_at = models.DateTimeField(
        default=None,
        blank=True,
        null=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        default=None,
        blank=True,
        null=True,
        db_index=True
    )
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='orders',
        verbose_name='Ресторан',
        help_text='Выберите ресторан для исполнения заказа',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
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

    objects = OrderQuerySet()

    class Meta:
        ordering = ['id']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return 'Заказ #: %s, Имя заказчика: %s %s, Телефон: %s' % (self.id, self.firstname, self.lastname, self.phonenumber)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        verbose_name='Заказ',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='items',
        verbose_name='Продукт',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)],
    )
    item_price = models.DecimalField(
        verbose_name='Зафиксированная цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = 'Заказанные позиции'

    def __str__(self):
        return f'{self.order} - {self.product}'
