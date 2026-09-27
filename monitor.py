import os
import smtplib
from email.message import EmailMessage

from playwright.sync_api import sync_playwright

PRODUCT_URL = "https://www.tokopedia.com/bassaudiobdg/kinera-celest-wyvern-black-edition-10mm-dynamic-driver-in-ear-monitor-earphones-with-mic-1731753518101660852"
VARIANTS = ["Type-C with Mic", "STD with Mic", "PRO with Boom Mic"]
NOTIFY_VARIANT = "STD with Mic"


def send_email():
    email_user = os.environ["EMAIL_USER"]
    email_app_password = os.environ["EMAIL_APP_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]

    message = EmailMessage()
    message["Subject"] = f"🔔 Tokopedia Ready Stock: {NOTIFY_VARIANT}"
    message["From"] = email_user
    message["To"] = email_to
    message.set_content(
        f"Varian {NOTIFY_VARIANT} pada produk Kinera Celest Wyvern BLACK EDITION "
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
        browser = p.firefox.launch(headless=True)

        try:
            page = browser.new_page(
                viewport={"width": 1366, "height": 768},
                locale="id-ID",
            )

            print("Membuka halaman Tokopedia dengan Firefox...")
            page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(5000)
            print("Halaman:", page.title())

            sold_out_messages = [
                "Stok: Habis",
                "Stok varian ini habis",
                "Stok Habis",
            ]

            results = {}

            for variant_name in VARIANTS:
                print(f"Memilih varian: {variant_name}")

                variant = page.get_by_text(
                    variant_name,
                    exact=True,
                ).first

                if variant.count() == 0:
                    results[variant_name] = "VARIAN TIDAK DITEMUKAN"
                    print(f"⚠️ {variant_name}: tidak ditemukan")
                    continue

                variant.click()
                page.wait_for_timeout(1500)

                body_text = page.locator("body").inner_text()
                is_sold_out = any(
                    message in body_text
                    for message in sold_out_messages
                )

                results[variant_name] = (
                    "STOK HABIS" if is_sold_out else "TERSEDIA"
                )

            print("\n===== HASIL PEMERIKSAAN =====")

            for variant_name, status in results.items():
                if status == "STOK HABIS":
                    icon = "❌"
                elif status == "TERSEDIA":
                    icon = "✅"
                else:
                    icon = "⚠️"

                print(f"{icon} {variant_name}: {status}")

            if results.get(NOTIFY_VARIANT) == "TERSEDIA":
                send_email()
            else:
                print(
                    f"📧 Email tidak dikirim karena "
                    f"{NOTIFY_VARIANT} belum tersedia."
                )

            print("=============================\n")

        finally:
            browser.close()


if __name__ == "__main__":
    check_stock()
