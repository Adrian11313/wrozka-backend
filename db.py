import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json

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
            paid_at TEXT,
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

    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN paid_at TEXT")
    except Exception:
        pass

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS site_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            site_name TEXT,
            site_bio TEXT,
            footer_text TEXT,
            avatar_image_url TEXT,
            hero_image_url TEXT,
            modal_image_url TEXT,
            hero_title TEXT,
            hero_subtitle TEXT,
            modal_title TEXT,
            modal_subtitle TEXT,
            modal_headline TEXT,
            modal_description TEXT,
            modal_form_text TEXT,
            donation_title TEXT,
            donation_description TEXT,
            show_social_links INTEGER NOT NULL DEFAULT 1,
            show_quick_links INTEGER NOT NULL DEFAULT 1,
            show_visual_card INTEGER NOT NULL DEFAULT 1,
            show_packages_section INTEGER NOT NULL DEFAULT 1,
            show_donation_section INTEGER NOT NULL DEFAULT 1,
            show_modal_portal INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS site_social_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            url TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS site_quick_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subtitle TEXT,
            image_url TEXT,
            action_type TEXT NOT NULL,
            action_value TEXT,
            is_highlight INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS site_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price TEXT NOT NULL,
            label TEXT NOT NULL,
            description TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            is_custom_amount INTEGER NOT NULL DEFAULT 0
        )
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS live_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_order_id INTEGER,
            is_visible INTEGER NOT NULL DEFAULT 0,
            read_token INTEGER NOT NULL DEFAULT 0,
            voice_enabled INTEGER NOT NULL DEFAULT 1,
            show_enabled INTEGER NOT NULL DEFAULT 1,
            auto_hide_seconds INTEGER NOT NULL DEFAULT 0,
            hotkey_show TEXT NOT NULL DEFAULT 'F8',
            hotkey_complete TEXT NOT NULL DEFAULT 'F9',
            hotkey_hide TEXT NOT NULL DEFAULT 'F10',
            hotkey_read_again TEXT NOT NULL DEFAULT 'F11',
            updated_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS live_queue_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            enabled INTEGER NOT NULL DEFAULT 1,
            title_text TEXT NOT NULL DEFAULT 'Kolejka',
            subtitle_text TEXT NOT NULL DEFAULT 'Kto jest następny do wróżby?',
            live_badge_text TEXT NOT NULL DEFAULT 'LIVE QUEUE',
            show_live_badge INTEGER NOT NULL DEFAULT 1,
            show_title INTEGER NOT NULL DEFAULT 1,
            show_subtitle INTEGER NOT NULL DEFAULT 1,
            show_queue_count INTEGER NOT NULL DEFAULT 1,
            show_updated_at INTEGER NOT NULL DEFAULT 1,
            show_next_person INTEGER NOT NULL DEFAULT 1,
            show_package_name INTEGER NOT NULL DEFAULT 1,
            show_position_number INTEGER NOT NULL DEFAULT 1,
            max_visible_items INTEGER NOT NULL DEFAULT 2,
            position_top INTEGER NOT NULL DEFAULT 40,
            position_left INTEGER NOT NULL DEFAULT 32,
            overlay_width INTEGER NOT NULL DEFAULT 340,
            title_font_size INTEGER NOT NULL DEFAULT 42,
            subtitle_font_size INTEGER NOT NULL DEFAULT 15,
            next_label_font_size INTEGER NOT NULL DEFAULT 12,
            next_name_font_size INTEGER NOT NULL DEFAULT 36,
            item_name_font_size INTEGER NOT NULL DEFAULT 18,
            item_package_font_size INTEGER NOT NULL DEFAULT 11,
            badge_font_size INTEGER NOT NULL DEFAULT 10,
            line_gap INTEGER NOT NULL DEFAULT 8,
            background_opacity REAL NOT NULL DEFAULT 0.0,
            text_shadow_enabled INTEGER NOT NULL DEFAULT 1,
            accent_color TEXT NOT NULL DEFAULT '#f59e0b',
            title_color TEXT NOT NULL DEFAULT '#fde68a',
            text_color TEXT NOT NULL DEFAULT '#ffffff',
            subtitle_color TEXT NOT NULL DEFAULT '#f5d0fe',
            compact_mode INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT
        )
        """
    )

    ensure_default_site_config(cursor)
    ensure_default_live_state(cursor)
    ensure_default_live_queue_config(cursor)

    conn.commit()
    conn.close()


def ensure_default_site_config(cursor: sqlite3.Cursor) -> None:
    cursor.execute("SELECT COUNT(*) AS cnt FROM site_settings")
    site_settings_count = cursor.fetchone()["cnt"]

    if site_settings_count == 0:
        cursor.execute(
            """
            INSERT INTO site_settings (
                id,
                site_name,
                site_bio,
                footer_text,
                avatar_image_url,
                hero_image_url,
                modal_image_url,
                hero_title,
                hero_subtitle,
                modal_title,
                modal_subtitle,
                modal_headline,
                modal_description,
                modal_form_text,
                donation_title,
                donation_description,
                show_social_links,
                show_quick_links,
                show_visual_card,
                show_packages_section,
                show_donation_section,
                show_modal_portal
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "Kamelia",
                "Duchowa przewodniczka, tarot i odpowiedzi online. Zadaj pytanie, wybierz pakiet i przejdź do płatności.",
                "Wróżka Kamelia • wersja testowa • React + Flask + Tpay",
                "",
                "",
                "",
                "Kamelia zaprasza",
                "Tarot, energia i odpowiedzi dla Ciebie",
                "Portal pytań",
                "Wpisz dane, wybierz pakiet i przejdź do płatności.",
                "Zadaj pytanie",
                "Tarot, energia, relacje i szybka odpowiedź online.",
                "Podaj imię, e-mail, wybierz pakiet i przejdź do płatności Tpay. Możesz też wpisać pytanie do wróżki.",
                "Dowolna wpłata",
                "Jeśli chcesz po prostu wesprzeć Wróżkę Kameliię, wpisz dowolną kwotę i przejdź do płatności.",
                1,
                1,
                1,
                1,
                1,
                1,
            ),
        )

    cursor.execute("SELECT COUNT(*) AS cnt FROM site_social_links")
    social_count = cursor.fetchone()["cnt"]

    if social_count == 0:
        default_social_links = [
            ("TikTok", "https://www.tiktok.com/@wrozka_kamelia", 1, 1),
            ("Instagram", "https://www.instagram.com/wrozka_kamelia", 2, 1),
            ("Facebook", "https://www.facebook.com/Kamelia.Wrozka", 3, 1),
            ("WWW", "https://www.wrozkakamelia.pl/", 4, 1),
        ]

        cursor.executemany(
            """
            INSERT INTO site_social_links (label, url, sort_order, is_active)
            VALUES (?, ?, ?, ?)
            """,
            default_social_links,
        )

    cursor.execute("SELECT COUNT(*) AS cnt FROM site_quick_links")
    quick_links_count = cursor.fetchone()["cnt"]

    if quick_links_count == 0:
        default_quick_links = [
            (
                "PORTAL – zadaj pytanie teraz",
                "Szybka konsultacja i płatność online",
                "",
                "open_modal",
                "portal",
                1,
                1,
                1,
            ),
            (
                "CENNIK – pakiety i zasady",
                "Sprawdź ofertę i wybierz wariant",
                "",
                "scroll_to",
                "pakiety",
                0,
                2,
                1,
            ),
            (
                "Oficjalna strona Kamelii",
                "Pełna oferta i kontakt",
                "",
                "external_url",
                "https://www.wrozkakamelia.pl/",
                0,
                3,
                1,
            ),
            (
                "TikTok",
                "Live i krótkie materiały",
                "",
                "external_url",
                "https://www.tiktok.com/@wrozka_kamelia",
                0,
                4,
                1,
            ),
            (
                "Instagram",
                "Aktualności i kontakt",
                "",
                "external_url",
                "https://www.instagram.com/wrozka_kamelia",
                0,
                5,
                1,
            ),
            (
                "Facebook",
                "Społeczność i informacje",
                "",
                "external_url",
                "https://www.facebook.com/Kamelia.Wrozka",
                0,
                6,
                1,
            ),
        ]

        cursor.executemany(
            """
            INSERT INTO site_quick_links (
                title,
                subtitle,
                image_url,
                action_type,
                action_value,
                is_highlight,
                sort_order,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            default_quick_links,
        )

    cursor.execute("SELECT COUNT(*) AS cnt FROM site_packages")
    packages_count = cursor.fetchone()["cnt"]

    if packages_count == 0:
        default_packages = [
            ("Szybka odpowiedź", "29.00", "29 zł", "Jedno pytanie i szybka odpowiedź.", 1, 1, 0),
            ("Rozkład dnia", "59.00", "59 zł", "Szersza interpretacja i wskazówki.", 2, 1, 0),
            ("Sesja premium", "119.00", "119 zł", "Rozbudowana analiza z priorytetem.", 3, 1, 0),
        ]

        cursor.executemany(
            """
            INSERT INTO site_packages (
                name,
                price,
                label,
                description,
                sort_order,
                is_active,
                is_custom_amount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            default_packages,
        )



def ensure_default_live_state(cursor: sqlite3.Cursor) -> None:
    cursor.execute("SELECT COUNT(*) AS cnt FROM live_state")
    live_state_count = cursor.fetchone()["cnt"]

    if live_state_count == 0:
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO live_state (
                id,
                current_order_id,
                is_visible,
                read_token,
                voice_enabled,
                show_enabled,
                auto_hide_seconds,
                hotkey_show,
                hotkey_complete,
                hotkey_hide,
                hotkey_read_again,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                None,
                0,
                0,
                1,
                1,
                0,
                "F8",
                "F9",
                "F10",
                "F11",
                now,
            ),
        )


def ensure_default_live_queue_config(cursor: sqlite3.Cursor) -> None:
    cursor.execute("SELECT COUNT(*) AS cnt FROM live_queue_config")
    live_queue_config_count = cursor.fetchone()["cnt"]

    if live_queue_config_count == 0:
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO live_queue_config (
                id,
                enabled,
                title_text,
                subtitle_text,
                live_badge_text,
                show_live_badge,
                show_title,
                show_subtitle,
                show_queue_count,
                show_updated_at,
                show_next_person,
                show_package_name,
                show_position_number,
                max_visible_items,
                position_top,
                position_left,
                overlay_width,
                title_font_size,
                subtitle_font_size,
                next_label_font_size,
                next_name_font_size,
                item_name_font_size,
                item_package_font_size,
                badge_font_size,
                line_gap,
                background_opacity,
                text_shadow_enabled,
                accent_color,
                title_color,
                text_color,
                subtitle_color,
                compact_mode,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                1,
                "Kolejka",
                "Kto jest następny do wróżby?",
                "LIVE QUEUE",
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                2,
                40,
                32,
                340,
                42,
                15,
                12,
                36,
                18,
                11,
                10,
                8,
                0.0,
                1,
                "#f59e0b",
                "#fde68a",
                "#ffffff",
                "#f5d0fe",
                1,
                now,
            ),
        )


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [{key: row[key] for key in row.keys()} for row in rows]


def normalize_bool_int(value) -> int:
    return 1 if bool(value) else 0


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
            paid_at,
            customer_name,
            customer_email,
            package_name,
            question,
            amount,
            payment_status,
            order_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now,
            now,
            None,
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

    if payment_status == "oplacone":
        cursor.execute(
            """
            UPDATE orders
            SET
                updated_at = ?,
                payment_status = ?,
                tpay_response_raw = COALESCE(?, tpay_response_raw),
                paid_at = COALESCE(paid_at, ?)
            WHERE tpay_transaction_id = ?
            """,
            (
                now,
                payment_status,
                tpay_response_raw,
                now,
                tpay_transaction_id,
            ),
        )
    else:
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

    if payment_status == "oplacone":
        cursor.execute(
            """
            UPDATE orders
            SET
                updated_at = ?,
                payment_status = ?,
                tpay_response_raw = COALESCE(?, tpay_response_raw),
                paid_at = COALESCE(paid_at, ?)
            WHERE id = ?
            """,
            (
                now,
                payment_status,
                tpay_response_raw,
                now,
                order_id,
            ),
        )
    else:
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
          AND order_status != 'zamkniete'
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
    current_paid_at = current_order["paid_at"]

    if new_payment_status == "oplacone" and not current_paid_at:
        new_paid_at = now
    else:
        new_paid_at = current_paid_at

    cursor.execute(
        """
        UPDATE orders
        SET
            updated_at = ?,
            paid_at = ?,
            payment_status = ?,
            order_status = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            now,
            new_paid_at,
            new_payment_status,
            new_order_status,
            new_notes,
            order_id,
        ),
    )

    conn.commit()
    conn.close()


def get_site_config() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM site_settings WHERE id = 1")
    settings_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT *
        FROM site_social_links
        ORDER BY sort_order ASC, id ASC
        """
    )
    social_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT *
        FROM site_quick_links
        ORDER BY sort_order ASC, id ASC
        """
    )
    quick_link_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT *
        FROM site_packages
        ORDER BY sort_order ASC, id ASC
        """
    )
    package_rows = cursor.fetchall()

    conn.close()

    settings = row_to_dict(settings_row) or {}

    social_links = rows_to_dicts(social_rows)
    quick_links = rows_to_dicts(quick_link_rows)
    packages = rows_to_dicts(package_rows)

    return {
        "settings": settings,
        "social_links": social_links,
        "quick_links": quick_links,
        "packages": packages,
    }


def save_site_config(
    settings: dict,
    social_links: list[dict],
    quick_links: list[dict],
    packages: list[dict],
) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO site_settings (
            id,
            site_name,
            site_bio,
            footer_text,
            avatar_image_url,
            hero_image_url,
            modal_image_url,
            hero_title,
            hero_subtitle,
            modal_title,
            modal_subtitle,
            modal_headline,
            modal_description,
            modal_form_text,
            donation_title,
            donation_description,
            show_social_links,
            show_quick_links,
            show_visual_card,
            show_packages_section,
            show_donation_section,
            show_modal_portal
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            site_name = excluded.site_name,
            site_bio = excluded.site_bio,
            footer_text = excluded.footer_text,
            avatar_image_url = excluded.avatar_image_url,
            hero_image_url = excluded.hero_image_url,
            modal_image_url = excluded.modal_image_url,
            hero_title = excluded.hero_title,
            hero_subtitle = excluded.hero_subtitle,
            modal_title = excluded.modal_title,
            modal_subtitle = excluded.modal_subtitle,
            modal_headline = excluded.modal_headline,
            modal_description = excluded.modal_description,
            modal_form_text = excluded.modal_form_text,
            donation_title = excluded.donation_title,
            donation_description = excluded.donation_description,
            show_social_links = excluded.show_social_links,
            show_quick_links = excluded.show_quick_links,
            show_visual_card = excluded.show_visual_card,
            show_packages_section = excluded.show_packages_section,
            show_donation_section = excluded.show_donation_section,
            show_modal_portal = excluded.show_modal_portal
        """,
        (
            1,
            settings.get("site_name", ""),
            settings.get("site_bio", ""),
            settings.get("footer_text", ""),
            settings.get("avatar_image_url", ""),
            settings.get("hero_image_url", ""),
            settings.get("modal_image_url", ""),
            settings.get("hero_title", ""),
            settings.get("hero_subtitle", ""),
            settings.get("modal_title", ""),
            settings.get("modal_subtitle", ""),
            settings.get("modal_headline", ""),
            settings.get("modal_description", ""),
            settings.get("modal_form_text", ""),
            settings.get("donation_title", ""),
            settings.get("donation_description", ""),
            normalize_bool_int(settings.get("show_social_links", True)),
            normalize_bool_int(settings.get("show_quick_links", True)),
            normalize_bool_int(settings.get("show_visual_card", True)),
            normalize_bool_int(settings.get("show_packages_section", True)),
            normalize_bool_int(settings.get("show_donation_section", True)),
            normalize_bool_int(settings.get("show_modal_portal", True)),
        ),
    )

    cursor.execute("DELETE FROM site_social_links")
    for item in social_links:
        cursor.execute(
            """
            INSERT INTO site_social_links (
                label,
                url,
                sort_order,
                is_active
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                item.get("label", ""),
                item.get("url", ""),
                int(item.get("sort_order", 0)),
                normalize_bool_int(item.get("is_active", True)),
            ),
        )

    cursor.execute("DELETE FROM site_quick_links")
    for item in quick_links:
        cursor.execute(
            """
            INSERT INTO site_quick_links (
                title,
                subtitle,
                image_url,
                action_type,
                action_value,
                is_highlight,
                sort_order,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("title", ""),
                item.get("subtitle", ""),
                item.get("image_url", ""),
                item.get("action_type", "external_url"),
                item.get("action_value", ""),
                normalize_bool_int(item.get("is_highlight", False)),
                int(item.get("sort_order", 0)),
                normalize_bool_int(item.get("is_active", True)),
            ),
        )

    cursor.execute("DELETE FROM site_packages")
    for item in packages:
        cursor.execute(
            """
            INSERT INTO site_packages (
                name,
                price,
                label,
                description,
                sort_order,
                is_active,
                is_custom_amount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("name", ""),
                item.get("price", ""),
                item.get("label", ""),
                item.get("description", ""),
                int(item.get("sort_order", 0)),
                normalize_bool_int(item.get("is_active", True)),
                normalize_bool_int(item.get("is_custom_amount", False)),
            ),
        )

    conn.commit()
    conn.close()



def get_live_queue_config() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM live_queue_config WHERE id = 1")
    row = cursor.fetchone()

    conn.close()

    if row is None:
        return {
            "enabled": True,
            "title_text": "Kolejka",
            "subtitle_text": "Kto jest następny do wróżby?",
            "live_badge_text": "LIVE QUEUE",
            "show_live_badge": True,
            "show_title": True,
            "show_subtitle": True,
            "show_queue_count": True,
            "show_updated_at": True,
            "show_next_person": True,
            "show_package_name": True,
            "show_position_number": True,
            "max_visible_items": 2,
            "position_top": 40,
            "position_left": 32,
            "overlay_width": 340,
            "title_font_size": 42,
            "subtitle_font_size": 15,
            "next_label_font_size": 12,
            "next_name_font_size": 36,
            "item_name_font_size": 18,
            "item_package_font_size": 11,
            "badge_font_size": 10,
            "line_gap": 8,
            "background_opacity": 0.0,
            "text_shadow_enabled": True,
            "accent_color": "#f59e0b",
            "title_color": "#fde68a",
            "text_color": "#ffffff",
            "subtitle_color": "#f5d0fe",
            "compact_mode": True,
        }

    return {
        "enabled": bool(row["enabled"]),
        "title_text": row["title_text"],
        "subtitle_text": row["subtitle_text"],
        "live_badge_text": row["live_badge_text"],
        "show_live_badge": bool(row["show_live_badge"]),
        "show_title": bool(row["show_title"]),
        "show_subtitle": bool(row["show_subtitle"]),
        "show_queue_count": bool(row["show_queue_count"]),
        "show_updated_at": bool(row["show_updated_at"]),
        "show_next_person": bool(row["show_next_person"]),
        "show_package_name": bool(row["show_package_name"]),
        "show_position_number": bool(row["show_position_number"]),
        "max_visible_items": row["max_visible_items"],
        "position_top": row["position_top"],
        "position_left": row["position_left"],
        "overlay_width": row["overlay_width"],
        "title_font_size": row["title_font_size"],
        "subtitle_font_size": row["subtitle_font_size"],
        "next_label_font_size": row["next_label_font_size"],
        "next_name_font_size": row["next_name_font_size"],
        "item_name_font_size": row["item_name_font_size"],
        "item_package_font_size": row["item_package_font_size"],
        "badge_font_size": row["badge_font_size"],
        "line_gap": row["line_gap"],
        "background_opacity": float(row["background_opacity"]),
        "text_shadow_enabled": bool(row["text_shadow_enabled"]),
        "accent_color": row["accent_color"],
        "title_color": row["title_color"],
        "text_color": row["text_color"],
        "subtitle_color": row["subtitle_color"],
        "compact_mode": bool(row["compact_mode"]),
        "updated_at": row["updated_at"],
    }


def save_live_queue_config(config: dict) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM live_queue_config WHERE id = 1")
    current = cursor.fetchone()

    now = datetime.utcnow().isoformat()

    def current_or_default(key: str, default):
        if current is not None and key in current.keys():
            return current[key]
        return default

    def text_value(key: str, default: str) -> str:
        value = config.get(key, current_or_default(key, default))
        value = str(value or "").strip()
        return value if value else default

    def int_value(key: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
        try:
            value = int(config.get(key, current_or_default(key, default)))
        except Exception:
            value = default

        if minimum is not None:
            value = max(minimum, value)
        if maximum is not None:
            value = min(maximum, value)

        return value

    def float_value(key: str, default: float, minimum: float | None = None, maximum: float | None = None) -> float:
        try:
            value = float(config.get(key, current_or_default(key, default)))
        except Exception:
            value = default

        if minimum is not None:
            value = max(minimum, value)
        if maximum is not None:
            value = min(maximum, value)

        return value

    values = {
        "enabled": normalize_bool_int(config.get("enabled", current_or_default("enabled", True))),
        "title_text": text_value("title_text", "Kolejka"),
        "subtitle_text": text_value("subtitle_text", "Kto jest następny do wróżby?"),
        "live_badge_text": text_value("live_badge_text", "LIVE QUEUE"),
        "show_live_badge": normalize_bool_int(config.get("show_live_badge", current_or_default("show_live_badge", True))),
        "show_title": normalize_bool_int(config.get("show_title", current_or_default("show_title", True))),
        "show_subtitle": normalize_bool_int(config.get("show_subtitle", current_or_default("show_subtitle", True))),
        "show_queue_count": normalize_bool_int(config.get("show_queue_count", current_or_default("show_queue_count", True))),
        "show_updated_at": normalize_bool_int(config.get("show_updated_at", current_or_default("show_updated_at", True))),
        "show_next_person": normalize_bool_int(config.get("show_next_person", current_or_default("show_next_person", True))),
        "show_package_name": normalize_bool_int(config.get("show_package_name", current_or_default("show_package_name", True))),
        "show_position_number": normalize_bool_int(config.get("show_position_number", current_or_default("show_position_number", True))),
        "max_visible_items": int_value("max_visible_items", 2, 0, 10),
        "position_top": int_value("position_top", 40, 0, 1800),
        "position_left": int_value("position_left", 32, 0, 1080),
        "overlay_width": int_value("overlay_width", 340, 180, 1000),
        "title_font_size": int_value("title_font_size", 42, 12, 120),
        "subtitle_font_size": int_value("subtitle_font_size", 15, 8, 60),
        "next_label_font_size": int_value("next_label_font_size", 12, 8, 40),
        "next_name_font_size": int_value("next_name_font_size", 36, 12, 120),
        "item_name_font_size": int_value("item_name_font_size", 18, 8, 80),
        "item_package_font_size": int_value("item_package_font_size", 11, 8, 50),
        "badge_font_size": int_value("badge_font_size", 10, 7, 40),
        "line_gap": int_value("line_gap", 8, 0, 80),
        "background_opacity": float_value("background_opacity", 0.0, 0.0, 1.0),
        "text_shadow_enabled": normalize_bool_int(config.get("text_shadow_enabled", current_or_default("text_shadow_enabled", True))),
        "accent_color": text_value("accent_color", "#f59e0b"),
        "title_color": text_value("title_color", "#fde68a"),
        "text_color": text_value("text_color", "#ffffff"),
        "subtitle_color": text_value("subtitle_color", "#f5d0fe"),
        "compact_mode": normalize_bool_int(config.get("compact_mode", current_or_default("compact_mode", True))),
    }

    cursor.execute(
        """
        INSERT INTO live_queue_config (
            id,
            enabled,
            title_text,
            subtitle_text,
            live_badge_text,
            show_live_badge,
            show_title,
            show_subtitle,
            show_queue_count,
            show_updated_at,
            show_next_person,
            show_package_name,
            show_position_number,
            max_visible_items,
            position_top,
            position_left,
            overlay_width,
            title_font_size,
            subtitle_font_size,
            next_label_font_size,
            next_name_font_size,
            item_name_font_size,
            item_package_font_size,
            badge_font_size,
            line_gap,
            background_opacity,
            text_shadow_enabled,
            accent_color,
            title_color,
            text_color,
            subtitle_color,
            compact_mode,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            enabled = excluded.enabled,
            title_text = excluded.title_text,
            subtitle_text = excluded.subtitle_text,
            live_badge_text = excluded.live_badge_text,
            show_live_badge = excluded.show_live_badge,
            show_title = excluded.show_title,
            show_subtitle = excluded.show_subtitle,
            show_queue_count = excluded.show_queue_count,
            show_updated_at = excluded.show_updated_at,
            show_next_person = excluded.show_next_person,
            show_package_name = excluded.show_package_name,
            show_position_number = excluded.show_position_number,
            max_visible_items = excluded.max_visible_items,
            position_top = excluded.position_top,
            position_left = excluded.position_left,
            overlay_width = excluded.overlay_width,
            title_font_size = excluded.title_font_size,
            subtitle_font_size = excluded.subtitle_font_size,
            next_label_font_size = excluded.next_label_font_size,
            next_name_font_size = excluded.next_name_font_size,
            item_name_font_size = excluded.item_name_font_size,
            item_package_font_size = excluded.item_package_font_size,
            badge_font_size = excluded.badge_font_size,
            line_gap = excluded.line_gap,
            background_opacity = excluded.background_opacity,
            text_shadow_enabled = excluded.text_shadow_enabled,
            accent_color = excluded.accent_color,
            title_color = excluded.title_color,
            text_color = excluded.text_color,
            subtitle_color = excluded.subtitle_color,
            compact_mode = excluded.compact_mode,
            updated_at = excluded.updated_at
        """,
        (
            1,
            values["enabled"],
            values["title_text"],
            values["subtitle_text"],
            values["live_badge_text"],
            values["show_live_badge"],
            values["show_title"],
            values["show_subtitle"],
            values["show_queue_count"],
            values["show_updated_at"],
            values["show_next_person"],
            values["show_package_name"],
            values["show_position_number"],
            values["max_visible_items"],
            values["position_top"],
            values["position_left"],
            values["overlay_width"],
            values["title_font_size"],
            values["subtitle_font_size"],
            values["next_label_font_size"],
            values["next_name_font_size"],
            values["item_name_font_size"],
            values["item_package_font_size"],
            values["badge_font_size"],
            values["line_gap"],
            values["background_opacity"],
            values["text_shadow_enabled"],
            values["accent_color"],
            values["title_color"],
            values["text_color"],
            values["subtitle_color"],
            values["compact_mode"],
            now,
        ),
    )

    conn.commit()
    conn.close()

    return get_live_queue_config()


def get_live_control_config() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM live_state WHERE id = 1")
    row = cursor.fetchone()

    conn.close()

    if row is None:
        return {
            "voice_enabled": True,
            "show_enabled": True,
            "auto_hide_seconds": 0,
            "hotkey_show": "F8",
            "hotkey_complete": "F9",
            "hotkey_hide": "F10",
            "hotkey_read_again": "F11",
        }

    return {
        "voice_enabled": bool(row["voice_enabled"]),
        "show_enabled": bool(row["show_enabled"]),
        "auto_hide_seconds": row["auto_hide_seconds"],
        "hotkey_show": row["hotkey_show"],
        "hotkey_complete": row["hotkey_complete"],
        "hotkey_hide": row["hotkey_hide"],
        "hotkey_read_again": row["hotkey_read_again"],
    }


def save_live_control_config(config: dict) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM live_state WHERE id = 1")
    current = cursor.fetchone()

    now = datetime.utcnow().isoformat()

    voice_enabled = normalize_bool_int(
        config.get("voice_enabled", current["voice_enabled"] if current else True)
    )
    show_enabled = normalize_bool_int(
        config.get("show_enabled", current["show_enabled"] if current else True)
    )
    auto_hide_seconds = int(
        config.get("auto_hide_seconds", current["auto_hide_seconds"] if current else 0)
    )
    hotkey_show = str(
        config.get("hotkey_show", current["hotkey_show"] if current else "F8")
    ).strip() or "F8"
    hotkey_complete = str(
        config.get("hotkey_complete", current["hotkey_complete"] if current else "F9")
    ).strip() or "F9"
    hotkey_hide = str(
        config.get("hotkey_hide", current["hotkey_hide"] if current else "F10")
    ).strip() or "F10"
    hotkey_read_again = str(
        config.get("hotkey_read_again", current["hotkey_read_again"] if current else "F11")
    ).strip() or "F11"

    cursor.execute(
        """
        UPDATE live_state
        SET
            voice_enabled = ?,
            show_enabled = ?,
            auto_hide_seconds = ?,
            hotkey_show = ?,
            hotkey_complete = ?,
            hotkey_hide = ?,
            hotkey_read_again = ?,
            updated_at = ?
        WHERE id = 1
        """,
        (
            voice_enabled,
            show_enabled,
            auto_hide_seconds,
            hotkey_show,
            hotkey_complete,
            hotkey_hide,
            hotkey_read_again,
            now,
        ),
    )

    conn.commit()
    conn.close()

    return get_live_control_config()


def get_live_question_state() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM live_state WHERE id = 1")
    state_row = cursor.fetchone()

    if state_row is None:
        conn.close()
        return {
            "is_visible": False,
            "voice_enabled": True,
            "show_enabled": True,
            "read_token": 0,
            "auto_hide_seconds": 0,
            "current_order": None,
        }

    current_order = None

    if state_row["current_order_id"]:
        cursor.execute(
            """
            SELECT *
            FROM orders
            WHERE id = ?
            """,
            (state_row["current_order_id"],),
        )
        order_row = cursor.fetchone()
        current_order = row_to_dict(order_row)

    result = {
        "is_visible": bool(state_row["is_visible"]),
        "voice_enabled": bool(state_row["voice_enabled"]),
        "show_enabled": bool(state_row["show_enabled"]),
        "read_token": state_row["read_token"],
        "auto_hide_seconds": state_row["auto_hide_seconds"],
        "hotkey_show": state_row["hotkey_show"],
        "hotkey_complete": state_row["hotkey_complete"],
        "hotkey_hide": state_row["hotkey_hide"],
        "hotkey_read_again": state_row["hotkey_read_again"],
        "updated_at": state_row["updated_at"],
        "current_order": current_order,
    }

    conn.close()
    return result


def show_next_live_question() -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE payment_status = 'oplacone'
          AND order_status != 'zrealizowane'
          AND order_status != 'zamkniete'
        ORDER BY COALESCE(paid_at, created_at) ASC, id ASC
        LIMIT 1
        """
    )

    order_row = cursor.fetchone()
    now = datetime.utcnow().isoformat()

    if order_row is None:
        cursor.execute(
            """
            UPDATE live_state
            SET
                current_order_id = NULL,
                is_visible = 0,
                updated_at = ?
            WHERE id = 1
            """,
            (now,),
        )

        conn.commit()
        conn.close()
        return None

    cursor.execute(
        """
        UPDATE live_state
        SET
            current_order_id = ?,
            is_visible = 1,
            read_token = read_token + 1,
            updated_at = ?
        WHERE id = 1
        """,
        (
            order_row["id"],
            now,
        ),
    )

    result = row_to_dict(order_row)

    conn.commit()
    conn.close()
    return result


def hide_live_question() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE live_state
        SET
            is_visible = 0,
            updated_at = ?
        WHERE id = 1
        """,
        (now,),
    )

    conn.commit()
    conn.close()


def read_live_question_again() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE live_state
        SET
            is_visible = 1,
            read_token = read_token + 1,
            updated_at = ?
        WHERE id = 1
        """,
        (now,),
    )

    conn.commit()
    conn.close()


def complete_current_live_question() -> int | None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM live_state WHERE id = 1")
    state_row = cursor.fetchone()

    if state_row is None or not state_row["current_order_id"]:
        conn.close()
        return None

    order_id = int(state_row["current_order_id"])
    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE orders
        SET
            updated_at = ?,
            order_status = 'zrealizowane'
        WHERE id = ?
        """,
        (
            now,
            order_id,
        ),
    )

    cursor.execute(
        """
        UPDATE live_state
        SET
            current_order_id = NULL,
            is_visible = 0,
            updated_at = ?
        WHERE id = 1
        """,
        (now,),
    )

    conn.commit()
    conn.close()

    return order_id

