import os
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from db import (
    init_db,
    create_order,
    update_order_payment_data,
    get_all_orders,
    get_order_by_id,
    update_order_payment_status_by_id,
    update_order_status,
    get_order_stats,
    get_order_by_transaction_id,
    update_payment_status_by_transaction_id,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "151884455555556411887641796")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
)

TPAY_CLIENT_ID = os.getenv("TPAY_CLIENT_ID")
TPAY_CLIENT_SECRET = os.getenv("TPAY_CLIENT_SECRET")
TPAY_API_BASE = os.getenv("TPAY_API_BASE", "https://openapi.sandbox.tpay.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
TPAY_WEBHOOK_URL = os.getenv("TPAY_WEBHOOK_URL", "").strip()

ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

init_db()


def is_admin_logged_in() -> bool:
    return bool(session.get("admin_logged_in"))


def require_admin():
    if not is_admin_logged_in():
        return jsonify({"error": "Brak autoryzacji"}), 401
    return None


def map_tpay_status(status: str | None) -> str:
    normalized = str(status or "").lower()

    if normalized in ["paid", "correct", "success", "completed"]:
        return "oplacone"
    if normalized in ["pending", "created"]:
        return "oczekuje_na_platnosc"
    if normalized in ["declined", "failed", "canceled", "cancelled"]:
        return "anulowane"

    return normalized or "nieznany"


def get_tpay_token():
    oauth_url = f"{TPAY_API_BASE}/oauth/auth"

    payload = {
        "client_id": TPAY_CLIENT_ID,
        "client_secret": TPAY_CLIENT_SECRET,
        "grant_type": "client_credentials",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    print("=== TPAY OAUTH DEBUG ===")
    print("TPAY_API_BASE:", TPAY_API_BASE)
    print("TPAY_CLIENT_ID:", TPAY_CLIENT_ID)
    print("TPAY_CLIENT_SECRET exists:", bool(TPAY_CLIENT_SECRET))
    print("TPAY_CLIENT_SECRET length:", len(TPAY_CLIENT_SECRET) if TPAY_CLIENT_SECRET else 0)
    print("OAuth URL:", oauth_url)
    print("OAuth payload keys:", list(payload.keys()))

    response = requests.post(
        oauth_url,
        data=payload,
        headers=headers,
        timeout=30,
    )

    print("OAuth response status:", response.status_code)
    print("OAuth response text:", response.text)

    response.raise_for_status()

    result = response.json()
    access_token = result.get("access_token")

    if not access_token:
        raise Exception(f"Brak access_token w odpowiedzi Tpay: {result}")

    return access_token


def get_tpay_transaction_details(transaction_id: str) -> dict:
    token = get_tpay_token()

    response = requests.get(
        f"{TPAY_API_BASE}/transactions/{transaction_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    print("=== TPAY TRANSACTION DETAILS DEBUG ===")
    print("Transaction ID:", transaction_id)
    print("Details URL:", f"{TPAY_API_BASE}/transactions/{transaction_id}")
    print("Details response status:", response.status_code)
    print("Details response text:", response.text)

    response.raise_for_status()
    return response.json()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "message": "Backend działa"})


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    try:
        data = request.get_json(force=True)
        login = (data.get("login") or "").strip()
        password = (data.get("password") or "").strip()

        if login != ADMIN_LOGIN or password != ADMIN_PASSWORD:
            return jsonify({"error": "Nieprawidłowy login lub hasło"}), 401

        session["admin_logged_in"] = True
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": "Błąd logowania", "details": str(e)}), 500


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_logged_in", None)
    return jsonify({"ok": True})


@app.route("/api/admin/check-auth", methods=["GET"])
def admin_check_auth():
    return jsonify({"authenticated": is_admin_logged_in()})


@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    auth_error = require_admin()
    if auth_error:
        return auth_error

    try:
        stats = get_order_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": "Błąd pobierania statystyk", "details": str(e)}), 500


@app.route("/api/admin/orders", methods=["GET"])
def admin_orders():
    auth_error = require_admin()
    if auth_error:
        return auth_error

    try:
        rows = get_all_orders()

        orders = []
        for row in rows:
            orders.append(
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "customer_name": row["customer_name"],
                    "customer_email": row["customer_email"],
                    "package_name": row["package_name"],
                    "question": row["question"],
                    "amount": row["amount"],
                    "payment_status": row["payment_status"],
                    "order_status": row["order_status"],
                    "tpay_transaction_id": row["tpay_transaction_id"],
                    "tpay_payment_url": row["tpay_payment_url"],
                    "tpay_response_raw": row["tpay_response_raw"],
                    "notes": row["notes"],
                }
            )

        return jsonify({"orders": orders})
    except Exception as e:
        return jsonify({"error": "Błąd pobierania zamówień", "details": str(e)}), 500


@app.route("/api/admin/orders/<int:order_id>/sync-payment", methods=["POST"])
def sync_order_payment(order_id: int):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    try:
        order = get_order_by_id(order_id)
        if order is None:
            return jsonify({"error": "Nie znaleziono zamówienia"}), 404

        transaction_id = order["tpay_transaction_id"]
        if not transaction_id:
            return jsonify({"error": "To zamówienie nie ma transaction_id"}), 400

        result = get_tpay_transaction_details(transaction_id)

        raw_status = (
            result.get("payments", {}).get("status")
            or result.get("status")
            or ""
        )
        local_status = map_tpay_status(raw_status)

        update_order_payment_status_by_id(
            order_id=order_id,
            payment_status=local_status,
            tpay_response_raw=str(result),
        )

        return jsonify(
            {
                "ok": True,
                "order_id": order_id,
                "tpay_status": raw_status,
                "local_status": local_status,
                "result": result,
            }
        )

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Błąd połączenia z Tpay", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Błąd synchronizacji statusu", "details": str(e)}), 500


@app.route("/api/admin/orders/<int:order_id>/complete", methods=["POST"])
def complete_order(order_id: int):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    try:
        order = get_order_by_id(order_id)
        if order is None:
            return jsonify({"error": "Nie znaleziono zamówienia"}), 404

        update_order_status(
            order_id=order_id,
            order_status="zrealizowane",
        )

        return jsonify(
            {
                "ok": True,
                "order_id": order_id,
                "order_status": "zrealizowane",
            }
        )
    except Exception as e:
        return jsonify({"error": "Błąd oznaczania zamówienia", "details": str(e)}), 500


@app.route("/api/admin/orders/<int:order_id>/notes", methods=["POST"])
def update_order_notes(order_id: int):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    try:
        order = get_order_by_id(order_id)
        if order is None:
            return jsonify({"error": "Nie znaleziono zamówienia"}), 404

        data = request.get_json(force=True)
        notes = (data.get("notes") or "").strip()

        update_order_status(
            order_id=order_id,
            notes=notes,
        )

        return jsonify({"ok": True, "order_id": order_id, "notes": notes})
    except Exception as e:
        return jsonify({"error": "Błąd zapisu notatek", "details": str(e)}), 500


@app.route("/api/tpay/webhook", methods=["POST"])
def tpay_webhook():
    try:
        raw_body = request.get_data(as_text=True)
        data = request.get_json(silent=True) or {}

        transaction_id = (
            data.get("transactionId")
            or data.get("id")
            or data.get("transaction_id")
        )

        payment_status = (
            data.get("status")
            or data.get("paymentStatus")
            or data.get("payment_status")
        )

        print("=== WEBHOOK TPAY ===")
        print("BODY:", raw_body)
        print("PARSED:", data)
        print("TRANSACTION ID:", transaction_id)
        print("PAYMENT STATUS:", payment_status)

        if not transaction_id:
            return jsonify({"error": "Brak transaction_id w webhooku"}), 400

        if not payment_status:
            return jsonify({"error": "Brak statusu płatności w webhooku"}), 400

        order = get_order_by_transaction_id(transaction_id)
        if order is None:
            return jsonify({"error": "Nie znaleziono zamówienia dla tej transakcji"}), 404

        mapped_status = map_tpay_status(payment_status)
        print("MAPPED STATUS:", mapped_status)

        update_payment_status_by_transaction_id(
            tpay_transaction_id=transaction_id,
            payment_status=mapped_status,
            tpay_response_raw=raw_body,
        )

        return jsonify({"ok": True}), 200

    except Exception as e:
        return jsonify({"error": "Błąd webhooka", "details": str(e)}), 500


@app.route("/api/create-payment", methods=["POST"])
def create_payment():
    try:
        data = request.get_json(force=True)

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        amount = data.get("amount")
        description = (data.get("description") or "Usługa Wróżka Kamelia").strip()
        question = (data.get("question") or "").strip()
        package_name = (data.get("package_name") or "Nieznany pakiet").strip()

        print("=== CREATE PAYMENT INPUT ===")
        print("name:", name)
        print("email:", email)
        print("amount:", amount)
        print("description:", description)
        print("question:", question)
        print("package_name:", package_name)

        if not name:
            return jsonify({"error": "Brak imienia"}), 400

        if len(name) < 3:
            return jsonify({"error": "Imię musi mieć co najmniej 3 znaki"}), 400

        if not email:
            return jsonify({"error": "Brak adresu e-mail"}), 400

        if not amount:
            return jsonify({"error": "Brak kwoty"}), 400

        order_id = create_order(
            customer_name=name,
            customer_email=email,
            package_name=package_name,
            question=question,
            amount=str(amount),
        )

        print("Created local order_id:", order_id)

        token = get_tpay_token()

        callbacks = {
            "payerUrls": {
                "success": f"{FRONTEND_URL}/success",
                "error": f"{FRONTEND_URL}/error",
            }
        }

        if TPAY_WEBHOOK_URL:
            callbacks["notification"] = {
                "url": TPAY_WEBHOOK_URL
            }

        payload = {
            "amount": amount,
            "description": f"Zamówienie #{order_id} | {description}",
            "payer": {
                "name": name,
                "email": email,
            },
            "callbacks": callbacks,
        }

        print("=== TPAY WEBHOOK URL ===", TPAY_WEBHOOK_URL)
        print("=== TPAY CALLBACKS ===", callbacks)
        print("=== TPAY PAYLOAD ===", payload)

        response = requests.post(
            f"{TPAY_API_BASE}/transactions",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        print("=== TPAY CREATE STATUS ===", response.status_code)
        print("=== TPAY CREATE TEXT ===", response.text)

        if response.status_code >= 400:
            return jsonify(
                {
                    "error": "Błąd Tpay",
                    "details": response.text,
                }
            ), response.status_code

        result = response.json()

        print("=== TPAY CREATE RESPONSE ===", result)

        tpay_transaction_id = (
            result.get("transactionId")
            or result.get("id")
            or result.get("title")
        )

        payment_url = result.get("transactionPaymentUrl")

        update_order_payment_data(
            order_id=order_id,
            tpay_transaction_id=tpay_transaction_id,
            tpay_payment_url=payment_url,
            tpay_response_raw=str(result),
        )

        return jsonify(
            {
                "order_id": order_id,
                "payment_url": payment_url,
                "result": result,
            }
        )

    except requests.exceptions.RequestException as e:
        print("=== REQUEST EXCEPTION ===", str(e))
        return jsonify({"error": "Błąd połączenia z Tpay", "details": str(e)}), 500
    except Exception as e:
        print("=== SERVER EXCEPTION ===", str(e))
        return jsonify({"error": "Błąd serwera", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)