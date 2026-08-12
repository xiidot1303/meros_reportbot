import requests

from app.services import *
from config import SMARTUP_API_URL, SMARTUP_PASSWORD, SMARTUP_USERNAME


class ApiMethods:
    clients_list = "b/anor/mr/person/legal_person_list:table"
    reconciliation_act_report = "b/anor/rep/mkr/reconciliation_acts:run"
    orders_list = "b/trade/tdeal/order/order_list:table"
    archived_orders_list = "b/trade/tdeal/order/order_history_list:table"
    debts_list = "b/anor/mdeal/order/offset/offset_detail_list:table"
    order_report_template = "b/trade/tdeal/order/order_list:save_report_template"
    order_report_download = "b/anor/rep/mdeal/order_report:run"


class SmartUpApiClient:
    def __init__(self, url):
        self.api_url = f"{SMARTUP_API_URL}/{url}"
        self.username = SMARTUP_USERNAME
        self.password = SMARTUP_PASSWORD

    def save_report_template(self, deal_id):
        response = requests.post(
            f"{SMARTUP_API_URL}/{ApiMethods.order_report_template}",
            json={"deal_id": str(deal_id)},
            auth=(self.username, self.password),
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("report_template_id")

    def download_order_report(self, report_template_id):
        response = requests.get(
            f"{SMARTUP_API_URL}/{ApiMethods.order_report_download}",
            params={"template_id": 41, "report_template_id": report_template_id},
            auth=(self.username, self.password),
        )
        response.raise_for_status()
        return response.content

    def get_clients(self):
        result = []
        offset = 0
        while True:
            data = {
                "p": {
                    "column": [
                        "name",
                        "person_id",
                        "main_phone",
                        "group_name5",
                        "group_name6",
                        "tin",
                    ],
                    "filter": ["state", "=", "A"],
                    "sort": [],
                    "offset": offset,
                    "limit": 200,
                },
                "d": {"is_filial": "N"},
            }
            response = requests.post(
                self.api_url, json=data, auth=(self.username, self.password)
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
            "-lang_code": "ru",
        }

        response = requests.get(
            self.api_url, params=params, auth=(self.username, self.password)
        )
        # download file from response
        os.makedirs("files/reconciliation_acts", exist_ok=True)
        file_path = f"files/reconciliation_acts/reconciliation_act_{client_id}_{datetime.now().timestamp()}.xlsx"
        with open(f"{file_path}", "wb") as f:
            f.write(response.content)
        return file_path

    def get_orders(self):
        result = []
        offset = 0
        while True:
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
                        ["MDEAL_HEADERS", "MVT_VISIT_HEADERS"],
                    ],
                    "sort": ["-deal_time"],
                    "offset": offset,
                    "limit": 200,
                }
            }
            response = requests.post(
                self.api_url, json=data, auth=(self.username, self.password)
            )
            response = response.json()
            result.extend(response.get("data", []))
            count = response.get("count")
            offset += 200
            if offset >= count:
                break
        return result

    def get_archived_orders_by_client(self, client_id, offset=0):
        """Get archived orders list by client. Limit: 10"""
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
                ],
                "filter": ["person_id", "=", [client_id]],
                "sort": ["-deal_time"],
                "offset": offset,
                "limit": 10,
            }
        }

        response = requests.post(
            self.api_url, json=data, auth=(self.username, self.password)
        )
        response = response.json()
        return response.get("data")

    def get_debts_by_client(self, client_id):
        result = []
        offset = 0
        while True:
            data = {
                "p": {
                    "column": [
                        "deal_id",
                        "expiry_date",
                        "debt_amount",
                        "overdue_days",
                        "delivery_number",
                    ],
                    "filter": [
                        "and",
                        [
                            ["base_status", "=", ["A", "-1"]],
                            ["person_id", "=", [client_id]],
                        ],
                    ],
                    "sort": ["-expiry_date"],
                    "offset": offset,
                    "limit": 200,
                },
                "d": {},
            }

            response = requests.post(
                self.api_url, json=data, auth=(self.username, self.password)
            )
            response = response.json()
            rows = response.get("data", [])
            result.extend(rows)

            count = response.get("count", 0)
            offset += 200
            if offset >= count:
                break

        return result
