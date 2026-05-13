import os
import time
import requests
from dotenv import load_dotenv

try:
    import keyboard
except ImportError:
    print("Brak biblioteki keyboard. Zainstaluj:")
    print("pip install keyboard")
    raise


load_dotenv()

API_BASE = os.getenv("LIVE_API_BASE", "https://wrozka-backend.onrender.com").strip()
ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "admin").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123").strip()

session = requests.Session()


def login_admin() -> bool:
    try:
        response = session.post(
            f"{API_BASE}/api/admin/login",
            json={
                "login": ADMIN_LOGIN,
                "password": ADMIN_PASSWORD,
            },
            timeout=20,
        )

        if response.status_code != 200:
            print("Błąd logowania:", response.status_code, response.text)
            return False

        print("Zalogowano do backendu.")
        return True

    except Exception as exc:
        print("Błąd połączenia przy logowaniu:", exc)
        return False


def post_action(label: str, endpoint: str) -> None:
    try:
        response = session.post(
            f"{API_BASE}{endpoint}",
            timeout=20,
        )

        if response.status_code == 401:
            print("Sesja wygasła. Loguję ponownie...")
            if login_admin():
                response = session.post(
                    f"{API_BASE}{endpoint}",
                    timeout=20,
                )

        if response.ok:
            print(f"{label}: OK")
        else:
            print(f"{label}: BŁĄD {response.status_code} - {response.text}")

    except Exception as exc:
        print(f"{label}: błąd połączenia:", exc)


def show_next_question() -> None:
    post_action(
        "F8 Pokaż następne pytanie",
        "/api/admin/live-question/show-next",
    )


def complete_current_question() -> None:
    post_action(
        "F9 Zakończ i zrealizuj",
        "/api/admin/live-question/complete-current",
    )


def hide_question() -> None:
    post_action(
        "F10 Ukryj pytanie",
        "/api/admin/live-question/hide",
    )


def read_again() -> None:
    post_action(
        "F11 Czytaj ponownie",
        "/api/admin/live-question/read-again",
    )


def main() -> None:
    print("=== Wróżka Kamelia | Pilot live hotkeys ===")
    print("API:", API_BASE)
    print("")
    print("F8  = pokaż następne pytanie")
    print("F9  = zakończ i oznacz jako zrealizowane")
    print("F10 = ukryj pytanie")
    print("F11 = czytaj ponownie")
    print("ESC = zamknij pilota")
    print("")

    if not login_admin():
        print("Nie udało się zalogować. Sprawdź ADMIN_LOGIN / ADMIN_PASSWORD / API_BASE.")
        return

    keyboard.add_hotkey("F8", show_next_question)
    keyboard.add_hotkey("F9", complete_current_question)
    keyboard.add_hotkey("F10", hide_question)
    keyboard.add_hotkey("F11", read_again)

    print("Pilot działa. Możesz przejść do OBS/TikTok Studio.")
    print("Nie zamykaj tego okna podczas live.")
    print("")

    keyboard.wait("esc")
    print("Zamykam pilota live.")


if __name__ == "__main__":
    main()