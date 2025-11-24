from django.db import models


class Client(models.Model):
    external_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    tg_id = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("D", "Черновик"),
        ("B#N", "Новый"),
        ("B#E", "В обработке"),
        ("B#W", "В ожидании"),
        ("B#S", "Отгружен"),
        ("B#V", "Доставлен"),
        ("A", "Архив"),
        ("C", "Отменен"),
    ]
    status = models.CharField(null=True, max_length=16, choices=STATUS_CHOICES)
    deal_id = models.CharField(null=True, max_length=32)
    project = models.CharField(null=True, max_length=255)
    client = models.ForeignKey(Client, null=True, on_delete=models.CASCADE)
    delivery_date = models.DateField(null=True)
    tin = models.CharField(null=True, max_length=32)
    price_type = models.CharField(null=True, max_length=64)
    manager = models.CharField(null=True, max_length=255)
    total_amount = models.DecimalField(null=True, max_digits=12, decimal_places=0)

    def get_status_label(code):
        for key, value in Order.STATUS_CHOICES:
            if key == code:
                return value
        return None