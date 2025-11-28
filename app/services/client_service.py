from app.services import *
from app.models import Client
from django.db import transaction


def update_clients_by_data(data):

    raw_items = data

    # Step 1 — Prepare data from API
    incoming_ids = [item[1] for item in raw_items]

    # Step 2 — Fetch existing clients in one query
    existing_clients = Client.objects.filter(external_id__in=incoming_ids)
    existing_map = {c.external_id: c for c in existing_clients}

    to_create = []
    to_update = []

    for name, external_id, phone, payment_deferment in raw_items:
        if phone:
            # Normalize phone number
            phone = phone.strip()
            phone = phone.replace(" ", "").replace("-", "").replace(
                "(", "").replace(")", "").replace(".", "").replace(",", "").replace(
                    ":", "")
            if "+998998" in phone and len(phone) == 16:
                phone = phone.replace("+998998", "+998")
            phone = phone.replace("+", "")
            if len(phone) == 9:
                phone = "998" + phone
            phone = phone[:12]
            if phone.isdigit():
                phone = "+" + phone
            else:
                phone = None

        if payment_deferment:
            payment_deferment, *args = payment_deferment.split(" ")
            if payment_deferment.isdigit():
                payment_deferment = int(payment_deferment)


        if external_id in existing_map:
            # Update existing object
            client = existing_map[external_id]
            if (
                client.name != name or
                client.phone != phone or
                client.payment_deferment != payment_deferment
            ):
                client.name = name
                client.phone = phone
                client.payment_deferment = payment_deferment
                to_update.append(client)
        else:
            # Prepare new object
            to_create.append(
                Client(external_id=external_id, name=name, phone=phone)
            )

    # Step 3 — Perform bulk operations
    with transaction.atomic():
        if to_create:
            # deal by 500 to avoid too large queries
            for i in range(0, len(to_create), 500):
                Client.objects.bulk_create(
                    to_create[i:i+500], ignore_conflicts=True)

        if to_update:
            # Update existing clients by 500 to avoid too large queries
            for i in range(0, len(to_update), 500):
                Client.objects.bulk_update(
                    to_update[i:i+500], ["name", "phone"])
