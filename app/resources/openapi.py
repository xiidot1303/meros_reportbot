"""OpenAPI 3.1 spec for the inbound integration API.

Hand-maintained: the API views are plain Django views, not DRF, so there is
nothing for a schema generator to introspect. When you change a view under
app/views/, update the matching operation here in the same commit.
"""

BASIC_AUTH = [{"basicAuth": []}]


ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "const": "error"},
        "message": {"type": "string"},
    },
    "required": ["status", "message"],
}


def _error(description, message):
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": ERROR_SCHEMA,
                "example": {"status": "error", "message": message},
            }
        },
    }


UNAUTHORIZED = _error("Missing or invalid credentials.", "Unauthorized.")
INVALID_JSON = _error("Malformed JSON or a missing required field.", "Invalid JSON.")


OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "MerosPharm Integration API",
        "version": "1.0.0",
        "summary": "Inbound endpoints for external systems.",
        "description": (
            "Endpoints other MerosPharm systems call to push data into the client "
            "cabinet.\n\n"
            "**Authentication.** Every endpoint uses HTTP Basic against a Django user "
            "created for the calling system. Credentials are issued separately and "
            "travel on every request, so call over HTTPS only.\n\n"
            "**Conventions.** Request and response bodies are JSON. A `200` always "
            "carries `\"status\": \"success\"`; errors carry `\"status\": \"error\"` "
            "and a `message`."
        ),
    },
    "servers": [
        {"url": "/", "description": "This server"},
    ],
    "tags": [
        {
            "name": "Payments",
            "description": (
                "Client payments from the payment system. Received and forwarded to "
                "the client over Telegram — **nothing is stored on this side**."
            ),
        },
        {
            "name": "Orders",
            "description": "Order-related data pushed in from the order system.",
        },
    ],
    "components": {
        "securitySchemes": {
            "basicAuth": {
                "type": "http",
                "scheme": "basic",
                "description": "A Django user account. Ask the MerosPharm team to issue one.",
            }
        },
        "schemas": {
            "PaymentRequest": {
                "type": "object",
                "required": ["doc_id"],
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "maxLength": 64,
                        "description": (
                            "Your identifier for the payment document. Echoed back in "
                            "the response. Required."
                        ),
                        "examples": ["PAY-2026-000123"],
                    },
                    "amount": {
                        "type": ["string", "number", "null"],
                        "description": (
                            "Payment amount. Accepts a number or a string; spaces and a "
                            "comma decimal separator are tolerated "
                            "(`\"1 500 000,55\"` parses fine)."
                        ),
                        "examples": ["1500000.55"],
                    },
                    "datetime": {
                        "type": ["string", "null"],
                        "description": (
                            "When the payment was made. Accepted formats: "
                            "`YYYY-MM-DD HH:MM:SS`, `YYYY-MM-DDTHH:MM:SS`, "
                            "`DD.MM.YYYY HH:MM`, `YYYY-MM-DD`, `DD.MM.YYYY`. "
                            "Naive local time (Asia/Tashkent) — do not send an offset."
                        ),
                        "examples": ["2026-08-19 14:30:00"],
                    },
                    "tin": {
                        "type": ["string", "number", "null"],
                        "maxLength": 32,
                        "description": (
                            "Client INN. **This is the lookup key** — the client is found "
                            "by matching this against their cabinet. Without it nobody is "
                            "notified."
                        ),
                        "examples": ["123456789"],
                    },
                    "purpose": {
                        "type": ["string", "null"],
                        "description": "Payment purpose, shown to the client verbatim.",
                        "examples": ["Оплата за товар по договору №45"],
                    },
                },
            },
            "PaymentResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "const": "success"},
                    "message": {"type": "string"},
                    "doc_id": {"type": "string", "description": "Echo of the id you sent."},
                    "notified": {
                        "type": "integer",
                        "description": (
                            "How many Telegram users actually received the message. "
                            "`0` means no active cabinet matched that TIN — the call "
                            "still succeeded."
                        ),
                    },
                },
            },
            "OrderTransportRequest": {
                "type": "object",
                "required": ["order_id"],
                "properties": {
                    "order_id": {
                        "type": ["string", "number"],
                        "maxLength": 64,
                        "description": (
                            "The order this vehicle is assigned to. **Send the SmartUp "
                            "`deal_id`.** Required. A number is accepted and stored as a "
                            "string."
                        ),
                        "examples": ["D-90210"],
                    },
                    "car_brand": {
                        "type": ["string", "null"],
                        "maxLength": 128,
                        "description": "Manufacturer.",
                        "examples": ["Chevrolet"],
                    },
                    "car_model": {
                        "type": ["string", "null"],
                        "maxLength": 128,
                        "description": "Model.",
                        "examples": ["Labo"],
                    },
                    "car_autonum": {
                        "type": ["string", "null"],
                        "maxLength": 32,
                        "description": "Licence plate, stored verbatim with no reformatting.",
                        "examples": ["01A123BC"],
                    },
                    "firstname": {
                        "type": ["string", "null"],
                        "maxLength": 128,
                        "description": "Driver's first name.",
                        "examples": ["Азиз"],
                    },
                    "lastname": {
                        "type": ["string", "null"],
                        "maxLength": 128,
                        "description": "Driver's last name.",
                        "examples": ["Каримов"],
                    },
                },
            },
            "OrderTransportResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "const": "success"},
                    "message": {
                        "type": "string",
                        "description": "`Transport saved.` on insert, `Transport updated.` on update.",
                    },
                    "transport_id": {
                        "type": "integer",
                        "description": (
                            "Our record id. Stable across updates for the same "
                            "`order_id` — quote it in support requests."
                        ),
                    },
                    "order_id": {"type": "string", "description": "Echo of the id you sent."},
                    "order_matched": {
                        "type": "boolean",
                        "description": (
                            "Whether an order with that id exists on our side. `false` is "
                            "**not** an error — see the endpoint description."
                        ),
                    },
                    "created": {
                        "type": "boolean",
                        "description": "`true` on first save, `false` when an existing record was updated.",
                    },
                },
            },
        },
    },
    "paths": {
        "/api/payments/": {
            "post": {
                "tags": ["Payments"],
                "summary": "Receive a client payment",
                "operationId": "receivePayment",
                "description": (
                    "Notifies the client over Telegram that their payment was received, "
                    "in their own language (uz/ru).\n\n"
                    "The client is located by `tin`, so that field decides whether anyone "
                    "hears about it. A valid call with an unmatched TIN returns `200` with "
                    "`\"notified\": 0`.\n\n"
                    "### Retries\n"
                    "**Nothing is stored**, so this endpoint is *not* idempotent — "
                    "re-posting the same `doc_id` sends the client a second message. Only "
                    "retry when you know the first call failed."
                ),
                "security": BASIC_AUTH,
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PaymentRequest"},
                            "example": {
                                "doc_id": "PAY-2026-000123",
                                "amount": "1500000.55",
                                "datetime": "2026-08-19 14:30:00",
                                "tin": "123456789",
                                "purpose": "Оплата за товар по договору №45",
                            },
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Payment accepted. Check `notified` to see if it reached anyone.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PaymentResponse"},
                                "example": {
                                    "status": "success",
                                    "message": "Payment received.",
                                    "doc_id": "PAY-2026-000123",
                                    "notified": 1,
                                },
                            }
                        },
                    },
                    "400": _error("Malformed JSON, or `doc_id` missing.", "doc_id is required."),
                    "401": UNAUTHORIZED,
                },
            }
        },
        "/api/order-transport/": {
            "post": {
                "tags": ["Orders"],
                "summary": "Assign a vehicle and driver to an order",
                "operationId": "saveOrderTransport",
                "description": (
                    "Records the car and driver assigned to an order.\n\n"
                    "### Retries are safe\n"
                    "The record is keyed on `order_id`: posting the same order twice "
                    "updates the existing row instead of creating a duplicate. This also "
                    "means **one vehicle per order** — a second car for the same "
                    "`order_id` replaces the first. Tell us if an order can legitimately "
                    "carry several vehicles.\n\n"
                    "### Unknown orders are accepted\n"
                    "If the order has not reached us yet — common when the vehicle is "
                    "assigned before the order syncs from SmartUp — the transport is still "
                    "stored and you get `200` with `\"order_matched\": false`. Nothing is "
                    "lost; do not treat it as a failure.\n\n"
                    "If `order_matched` is `false` for orders that definitely exist on "
                    "your side, we are keying on different identifiers — stop and contact "
                    "us rather than working around it.\n\n"
                    "### No client notification\n"
                    "This endpoint only records data. The client is **not** messaged about "
                    "their vehicle. Ask us if you need that."
                ),
                "security": BASIC_AUTH,
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/OrderTransportRequest"},
                            "example": {
                                "order_id": "D-90210",
                                "car_brand": "Chevrolet",
                                "car_model": "Labo",
                                "car_autonum": "01A123BC",
                                "firstname": "Азиз",
                                "lastname": "Каримов",
                            },
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Transport stored (created or updated).",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/OrderTransportResponse"},
                                "example": {
                                    "status": "success",
                                    "message": "Transport saved.",
                                    "transport_id": 1,
                                    "order_id": "D-90210",
                                    "order_matched": True,
                                    "created": True,
                                },
                            }
                        },
                    },
                    "400": _error("Malformed JSON, or `order_id` missing.", "order_id is required."),
                    "401": UNAUTHORIZED,
                },
            }
        },
    },
}
