from app.services import *
from config import SMARTUP_API_URL, SMARTUP_PASSWORD, SMARTUP_USERNAME


class ApiMethods:
    clients_list = "b/anor/mr/person/legal_person_list:table"
    reconciliation_act_report = "b/anor/rep/mkr/reconciliation_acts:run"
    orders_list = "b/trade/tdeal/order/order_list:table"


class SmartUpApiClient:
    def __init__(self, url):
        self.api_url = f"{SMARTUP_API_URL}/{url}"
        self.username = SMARTUP_USERNAME
        self.password = SMARTUP_PASSWORD

    def get_clients(self):
        result = []
        offset = 0
        while True:
            data = {
                "p": {
                    "column": [
                        "name",
                        "person_id",
                        "main_phone"
                    ],
                    "filter": [
                        "state",
                        "=",
                        "A"
                    ],
                    "sort": [],
                    "offset": offset,
                    "limit": 200
                },
                "d": {
                    "is_filial": "N"
                }
            }
            response = requests.post(
                self.api_url,
                json=data,
                auth=(self.username, self.password)
            )
            response = response.json()
            result.extend(response.get("data", []))
            count = response.get("count")
            offset += 200
            if offset >= count:
                break
        return result

    def reconciliation_act_report(self, client_id, start_date: date, end_date: date):
        params = {
            "rt": "xlsx",
            "begin_date": start_date.strftime("%d.%m.%Y"),
            "end_date": end_date.strftime("%d.%m.%Y"),
            "reconciliation_date": date.today().strftime("%d.%m.%Y"),
            "person_id": client_id,
            "act_type": "A",
            "with_consignment": "",
            "is_detail": "",
            "-project_code": "trade",
            "-project_hash": "01",
            "-lang_code": "ru"
        }

        response = requests.get(
            self.api_url,
            params=params,
            auth=(self.username, self.password)
        )
        # download file from response
        file_path = f"files/reconciliation_acts/reconciliation_act_{client_id}_{datetime.now().timestamp()}.xlsx"
        with open(f"{file_path}", "wb") as f:
            f.write(response.content)
        return file_path

    def get_orders(self):
        data = {
            "p": {
                "column": [
                    "deal_id",
                    "subfilial_name",
                    "room_name",
                    "person_id",
                    "person_name",
                    "delivery_date",
                    "tin",
                    "price_type_names",
                    "robot_name",
                    "deal_time",
                    "total_amount",
                    "status",
                ],
                "filter": [
                    "source_table",
                    "=",
                    [
                        "MDEAL_HEADERS",
                        "MVT_VISIT_HEADERS"
                    ]
                ],
                "sort": [
                    "-deal_time"
                ],
                "offset": 0
            }
        }
        response = requests.post(
            self.api_url,
            json=data,
            auth=(self.username, self.password)
        )
        response = response.json()
        return response.get("data", [])
