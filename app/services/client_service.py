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

    for name, external_id in raw_items:
        if external_id in existing_map:
            # Update existing object
            client = existing_map[external_id]
            if client.name != name:   # Update only if changed
                client.name = name
                to_update.append(client)
        else:
            # Prepare new object
            to_create.append(
                Client(external_id=external_id, name=name)
            )

    # Step 3 — Perform bulk operations
    with transaction.atomic():
        if to_create:
            Client.objects.bulk_create(to_create, ignore_conflicts=True)

        if to_update:
            Client.objects.bulk_update(to_update, ["name"])
