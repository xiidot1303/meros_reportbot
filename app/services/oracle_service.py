import oracledb
from config import (
    ORACLE_HOST,
    ORACLE_PORT,
    ORACLE_SERVICE_NAME,
    ORACLE_USER,
    ORACLE_PASSWORD,
)


class OracleClient:
    """Direct access to the SmartUp Oracle database (alternative to the SmartUp API)."""

    def __init__(self):
        self.dsn = oracledb.makedsn(
            ORACLE_HOST, ORACLE_PORT, service_name=ORACLE_SERVICE_NAME
        )

    def get_connection(self):
        return oracledb.connect(
            user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=self.dsn
        )

    def execute_query(self, query, params=None):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params or {})
                columns = [col[0].lower() for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_product_prices(self, price_type_ids, warehouse_ids):
        """Price-list rows for the given price types, joined with stock balances.

        Returns one row per (price type, product, card, warehouse) — price
        varies per card, so the card grain is meaningful and must not be
        collapsed, and balances are kept apart per warehouse. Only products
        with a positive balance in that warehouse are included;
        `expiry_date_id` comes back as an Oracle number in YYYYMMDD form.
        """
        price_type_binds = {f"pt{i}": pt for i, pt in enumerate(price_type_ids)}
        warehouse_binds = {f"wh{i}": wh for i, wh in enumerate(warehouse_ids)}
        query = PRODUCT_PRICES_QUERY.format(
            price_type_ids=", ".join(f":{name}" for name in price_type_binds),
            warehouse_ids=", ".join(f":{name}" for name in warehouse_binds),
        )
        binds = {
            **price_type_binds,
            **warehouse_binds,
            "filial_id": PRICE_LIST_FILIAL_ID,
        }
        return self.execute_query(query, binds)

# Prices are per branch; 28939 is the branch this cabinet reports on.
PRICE_LIST_FILIAL_ID = 28939

# One row per (price type, product, card, warehouse). `MKW_DW_INVENTORY_BALANCES`
# holds several rows per product/card/warehouse (one per batch), so balances are
# summed to the product+card+warehouse grain before joining onto the price rows.
# Prices are per branch, not per warehouse, so each price row fans out to one
# row per warehouse that stocks it.
# `MD_PERSONS` and `MKW_CARDS` are LEFT JOINed: a product with no producer set
# still belongs in the price list.
PRODUCT_PRICES_QUERY = """
SELECT P."PRICE_TYPE_ID",
       PT."NAME"              AS "PRICE_TYPE_NAME",
       P."PRODUCT_ID",
       PR."CODE"              AS "PRODUCT_CODE",
       PR."NAME"              AS "PRODUCT_NAME",
       MP."NAME"              AS "MANUFACTURER",
       PR."BOX_QUANT",
       P."CARD_ID",
       C."CARD_CODE",
       P."PRICE",
       B."WAREHOUSE_ID",
       B."TOTAL_QUANT"        AS "QUANT",
       B."EXPIRY_DATE_ID"
  FROM "SMARTUP5X_ERP"."MKF_PRODUCT_PRICES" P
  JOIN (SELECT "PRODUCT_ID",
               "CARD_ID",
               "WAREHOUSE_ID",
               SUM("QUANT")          AS "TOTAL_QUANT",
               MIN("EXPIRY_DATE_ID") AS "EXPIRY_DATE_ID"
          FROM "SMARTUP5X_ERP"."MKW_DW_INVENTORY_BALANCES"
         WHERE "WAREHOUSE_ID" IN ({warehouse_ids})
         GROUP BY "PRODUCT_ID", "CARD_ID", "WAREHOUSE_ID"
        HAVING SUM("QUANT") > 0) B
    ON B."PRODUCT_ID" = P."PRODUCT_ID"
   AND B."CARD_ID"    = P."CARD_ID"
  JOIN "SMARTUP5X_ERP"."MKR_PRICE_TYPES" PT
    ON PT."PRICE_TYPE_ID" = P."PRICE_TYPE_ID"
  JOIN "SMARTUP5X_ERP"."MR_PRODUCTS" PR
    ON PR."PRODUCT_ID" = P."PRODUCT_ID"
  LEFT JOIN "SMARTUP5X_ERP"."MD_PERSONS" MP
    ON MP."PERSON_ID" = PR."PRODUCER_ID"
  LEFT JOIN "SMARTUP5X_ERP"."MKW_CARDS" C
    ON C."CARD_ID" = P."CARD_ID"
 WHERE P."FILIAL_ID" = :filial_id
   AND P."PRICE_TYPE_ID" IN ({price_type_ids})
"""
