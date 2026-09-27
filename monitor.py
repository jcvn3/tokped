import os
import smtplib
from email.message import EmailMessage

from playwright.sync_api import sync_playwright

PRODUCT_URL = "https://www.tokopedia.com/bassaudiobdg/kinera-celest-wyvern-black-edition-10mm-dynamic-driver-in-ear-monitor-earphones-with-mic-1731753518101660852"
TARGET_VARIANT = "STD with Mic"  # monitored variant


def send_email():
    email_user = os.environ["EMAIL_USER"]
    email_app_password = os.environ["EMAIL_APP_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]

    message = EmailMessage()
    message["Subject"] = f"🔔 Tokopedia Ready Stock: {TARGET_VARIANT}"
    message["From"] = email_user
    message["To"] = email_to
    message.set_content(
        f"Varian {TARGET_VARIANT} pada produk Kinera Celest Wyvern BLACK EDITION "
        "terdeteksi tersedia.\n\n"
        f"Link produk:\n{PRODUCT_URL}\n\n"
        "Segera cek Tokopedia karena stok dapat berubah."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_app_password)
        smtp.send_message(message)

    print("📧 Email notifikasi berhasil dikirim.")


def check_stock():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-http2",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        try:
            page = browser.new_page(
                viewport={"width": 1366, "height": 768},
                locale="id-ID",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
            )

            print("Membuka halaman Tokopedia...")
            page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            # Tunggu halaman selesai memuat dan elemen varian muncul.
            page.wait_for_timeout(5000)

            print("Halaman:", page.title())

            variant = page.get_by_text(
                TARGET_VARIANT,
                exact=True
            ).first

            if variant.count() == 0:
                raise RuntimeError(
                    f"Varian '{TARGET_VARIANT}' tidak ditemukan."
                )

            print(f"Memilih varian: {TARGET_VARIANT}")
            variant.click()
            page.wait_for_timeout(2000)

            body_text = page.locator("body").inner_text()

            print("\n===== HASIL PEMERIKSAAN =====")

            sold_out_messages = [
                "Stok: Habis",
                "Stok varian ini habis",
                "Stok Habis",
            ]

            is_sold_out = any(
                message in body_text for message in sold_out_messages
            )

            if is_sold_out:
                print(f"❌ {TARGET_VARIANT}: STOK HABIS")
            else:
                print(f"✅ {TARGET_VARIANT}: TERSEDIA")
                send_email()

            print("=============================\n")

        finally:
            browser.close()


if __name__ == "__main__":
    check_stock()
