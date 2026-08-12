from django.db import models
from django.utils import timezone


class Client(models.Model):
    external_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    payment_deferment = models.IntegerField(null=True, blank=True)
    deferment_days = models.IntegerField(null=True, blank=True)
    secondary_deferment_days = models.IntegerField(null=True, blank=True)
    tin = models.CharField(max_length=32, null=True, blank=True)
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
    deal_datetime = models.DateTimeField(null=True)
    tin = models.CharField(null=True, max_length=32)
    price_type = models.CharField(null=True, max_length=255)
    manager = models.CharField(null=True, max_length=255)
    total_amount = models.DecimalField(null=True, max_digits=12, decimal_places=0)

    def get_status_label(code):
        for key, value in Order.STATUS_CHOICES:
            if key == code:
                return value
        return None


class Texture(models.Model):
    client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.CASCADE, related_name="textures")
    doc_id = models.CharField(max_length=64, unique=True, db_index=True)
    doc_date = models.DateField(null=True, blank=True)
    doc_no = models.CharField(max_length=64, null=True, blank=True)
    doc_type = models.CharField(max_length=32, default="factura")
    doc_status = models.CharField(max_length=64, null=True, blank=True)
    contract_doc_no = models.CharField(max_length=64, null=True, blank=True)
    contract_doc_date = models.DateField(null=True, blank=True)
    tin = models.CharField(max_length=32, null=True, blank=True)
    owner_tin = models.CharField(max_length=32, null=True, blank=True)
    owner_name = models.CharField(max_length=255, null=True, blank=True)
    partner_tin = models.CharField(max_length=32, null=True, blank=True)
    partner_name = models.CharField(max_length=255, null=True, blank=True)
    total_delivery_sum = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_vat_sum = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_delivery_sum_with_vat = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    marked = models.BooleanField(default=False)
    has_vat = models.BooleanField(default=False)
    hasbenefit = models.BooleanField(default=False)
    has_lot = models.BooleanField(default=False)
    is_read = models.IntegerField(default=0)
    is_read_agent = models.IntegerField(default=0)
    commission = models.BooleanField(default=False)
    unilateral = models.BooleanField(default=False)
    raw_data = models.JSONField(default=dict, blank=True)
    is_new_notified = models.BooleanField(default=False)
    last_reminder_sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Счёт-фактура"
        verbose_name_plural = "Счёт-фактуры"

    def __str__(self):
        return f"{self.doc_no or self.doc_id}"

    @classmethod
    def save_or_update_from_payload(cls, payload, client=None):
        if not payload:
            return None

        doc_id = payload.get("docId")
        if not doc_id:
            return None

        doc_date_value = payload.get("docDate")
        contract_doc_date_value = payload.get("contractDocDate")

        defaults = {
            "client": client,
            "doc_date": timezone.datetime.strptime(doc_date_value, "%Y-%m-%d").date() if doc_date_value else None,
            "doc_no": payload.get("docNo"),
            "doc_type": payload.get("docType", "factura"),
            "doc_status": payload.get("docStatus"),
            "contract_doc_no": payload.get("contractDocNo"),
            "contract_doc_date": timezone.datetime.strptime(contract_doc_date_value, "%Y-%m-%d").date() if contract_doc_date_value else None,
            "tin": payload.get("partnerTin") or payload.get("ownerTin"),
            "owner_tin": payload.get("ownerTin"),
            "owner_name": payload.get("ownerName"),
            "partner_tin": payload.get("partnerTin"),
            "partner_name": payload.get("partnerName"),
            "total_delivery_sum": payload.get("totalDeliverySum"),
            "total_vat_sum": payload.get("totalVatSum"),
            "total_delivery_sum_with_vat": payload.get("totalDeliverySumWithVat"),
            "created_at": timezone.datetime.strptime(payload.get("createdAt"), "%Y-%m-%d %H:%M:%S") if payload.get("createdAt") else None,
            "updated_at": timezone.datetime.strptime(payload.get("updatedAt"), "%Y-%m-%d %H:%M:%S") if payload.get("updatedAt") else None,
            "marked": bool(payload.get("marked")),
            "has_vat": bool(payload.get("hasVat")),
            "hasbenefit": bool(payload.get("hasbenefit")),
            "has_lot": bool(payload.get("hasLot")),
            "is_read": payload.get("isRead", 0),
            "is_read_agent": payload.get("isReadAgent", 0),
            "commission": bool(payload.get("commission")),
            "unilateral": bool(payload.get("unilateral"))
        }

        texture, created = cls.objects.get_or_create(doc_id=doc_id, defaults=defaults)
        return texture, created
