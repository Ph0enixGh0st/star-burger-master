# Generated by Django 4.2.1 on 2023-06-01 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0045_order_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('unprocessed', 'Не обработан'), ('en-route', 'В доставке'), ('completed', 'Выполнен')], db_index=True, default='unprocessed', max_length=15, verbose_name='Статус заказа'),
        ),
    ]
