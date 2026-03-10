import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "orders.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            package_name TEXT NOT NULL,
            question TEXT,
            amount TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            order_status TEXT NOT NULL,
            tpay_transaction_id TEXT,
            tpay_payment_url TEXT,
            tpay_response_raw TEXT,
            notes TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def create_order(
    customer_name: str,
    customer_email: str,
    package_name: str,
    question: str,
    amount: str,
) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        INSERT INTO orders (
            created_at,
            updated_at,
            customer_name,
            customer_email,
            package_name,
            question,
            amount,
            payment_status,
            order_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now,
            now,
            customer_name,
            customer_email,
            package_name,
            question,
            amount,
            "oczekuje_na_platnosc",
            "nowe",
        ),
    )

    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id


def update_order_payment_data(
    order_id: int,
    tpay_transaction_id: str | None,
    tpay_payment_url: str | None,
    tpay_response_raw: str | None,
) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE orders
        SET
            updated_at = ?,
            tpay_transaction_id = ?,
            tpay_payment_url = ?,
            tpay_response_raw = ?
        WHERE id = ?
        """,
        (
            now,
            tpay_transaction_id,
            tpay_payment_url,
            tpay_response_raw,
            order_id,
        ),
    )

    conn.commit()
    conn.close()


def get_all_orders() -> list[sqlite3.Row]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM orders
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_order_by_id(order_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        """,
        (order_id,),
    )

    row = cursor.fetchone()
    conn.close()
    return row

def get_order_by_transaction_id(tpay_transaction_id: str) -> sqlite3.Row | None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE tpay_transaction_id = ?
        LIMIT 1
        """,
        (tpay_transaction_id,),
    )

    row = cursor.fetchone()
    conn.close()
    return row


def update_payment_status_by_transaction_id(
    tpay_transaction_id: str,
    payment_status: str,
    tpay_response_raw: str | None = None,
) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE orders
        SET
            updated_at = ?,
            payment_status = ?,
            tpay_response_raw = COALESCE(?, tpay_response_raw)
        WHERE tpay_transaction_id = ?
        """,
        (
            now,
            payment_status,
            tpay_response_raw,
            tpay_transaction_id,
        ),
    )

    conn.commit()
    conn.close()

def update_order_payment_status_by_id(
    order_id: int,
    payment_status: str,
    tpay_response_raw: str | None = None,
) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE orders
        SET
            updated_at = ?,
            payment_status = ?,
            tpay_response_raw = COALESCE(?, tpay_response_raw)
        WHERE id = ?
        """,
        (
            now,
            payment_status,
            tpay_response_raw,
            order_id,
        ),
    )

    conn.commit()
    conn.close()

def get_order_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    today_iso = today_start.isoformat()
    week_iso = week_start.isoformat()
    month_iso = month_start.isoformat()

    def count_orders_since(date_from: str) -> int:
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM orders
            WHERE created_at >= ?
            """,
            (date_from,),
        )
        row = cursor.fetchone()
        return row["cnt"] if row else 0

    def sum_paid_since(date_from: str) -> float:
        cursor.execute(
            """
            SELECT COALESCE(SUM(CAST(amount AS REAL)), 0) AS total
            FROM orders
            WHERE created_at >= ?
              AND payment_status = 'oplacone'
            """,
            (date_from,),
        )
        row = cursor.fetchone()
        return float(row["total"]) if row else 0.0

    orders_today = count_orders_since(today_iso)
    orders_week = count_orders_since(week_iso)
    orders_month = count_orders_since(month_iso)

    revenue_today = sum_paid_since(today_iso)
    revenue_week = sum_paid_since(week_iso)
    revenue_month = sum_paid_since(month_iso)

    cursor.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM orders
        WHERE payment_status = 'oplacone'
        """
    )
    paid_count = cursor.fetchone()["cnt"]

    cursor.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM orders
        WHERE order_status = 'zrealizowane'
        """
    )
    done_count = cursor.fetchone()["cnt"]

    cursor.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM orders
        WHERE payment_status = 'oplacone'
          AND order_status != 'zrealizowane'
        """
    )
    queue_count = cursor.fetchone()["cnt"]

    cursor.execute(
        """
        SELECT package_name, COUNT(*) AS cnt
        FROM orders
        GROUP BY package_name
        ORDER BY cnt DESC
        """
    )
    package_breakdown = [
        {"package_name": row["package_name"] or "Brak", "count": row["cnt"]}
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT substr(created_at, 1, 10) AS day,
               COUNT(*) AS orders_count,
               COALESCE(SUM(CASE WHEN payment_status = 'oplacone' THEN CAST(amount AS REAL) ELSE 0 END), 0) AS revenue
        FROM orders
        GROUP BY substr(created_at, 1, 10)
        ORDER BY day ASC
        """
    )
    daily_stats = [
        {
            "day": row["day"],
            "orders_count": row["orders_count"],
            "revenue": float(row["revenue"]),
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        "summary": {
            "orders_today": orders_today,
            "orders_week": orders_week,
            "orders_month": orders_month,
            "paid_count": paid_count,
            "done_count": done_count,
            "queue_count": queue_count,
            "revenue_today": revenue_today,
            "revenue_week": revenue_week,
            "revenue_month": revenue_month,
        },
        "package_breakdown": package_breakdown,
        "daily_stats": daily_stats,
    }


def update_order_status(
    order_id: int,
    payment_status: str | None = None,
    order_status: str | None = None,
    notes: str | None = None,
) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    current_order = get_order_by_id(order_id)
    if current_order is None:
        conn.close()
        return

    now = datetime.utcnow().isoformat()

    new_payment_status = payment_status if payment_status is not None else current_order["payment_status"]
    new_order_status = order_status if order_status is not None else current_order["order_status"]
    new_notes = notes if notes is not None else current_order["notes"]

    cursor.execute(
        """
        UPDATE orders
        SET
            updated_at = ?,
            payment_status = ?,
            order_status = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            now,
            new_payment_status,
            new_order_status,
            new_notes,
            order_id,
        ),
    )

    conn.commit()
    conn.close()

