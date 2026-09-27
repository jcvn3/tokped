import os
import re
import smtplib
from email.message import EmailMessage

from playwright.sync_api import sync_playwright

PRODUCT_URL = "https://www.tokopedia.com/bassaudiobdg/kinera-celest-wyvern-black-edition-10mm-dynamic-driver-in-ear-monitor-earphones-with-mic-1731753518101660852"
VARIANTS = ["Type-C with Mic", "STD with Mic", "PRO with Boom Mic"]
NOTIFY_VARIANT = "STD with Mic"


def send_email(stock=None, test=False):
    email_user = os.environ["EMAIL_USER"]
    email_app_password = os.environ["EMAIL_APP_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]

    message = EmailMessage()

    if test:
        message["Subject"] = "🧪 TEST - Tokopedia Stock Monitor"
        message.set_content(
            "Ini adalah email TEST dari Tokopedia Stock Monitor.\n\n"
            "Jika email ini masuk, berarti konfigurasi EMAIL_USER, "
            "EMAIL_APP_PASSWORD, EMAIL_TO, dan pengiriman SMTP Gmail "
            "berfungsi dengan baik."
        )
    else:
        stock_text = f"{stock} pcs" if stock is not None else "jumlah tidak terdeteksi"
        message["Subject"] = f"🔔 Tokopedia Ready Stock: {NOTIFY_VARIANT}"
        message.set_content(
            f"Varian {NOTIFY_VARIANT} pada produk Kinera Celest Wyvern BLACK EDITION "
            "terdeteksi tersedia.\n\n"
            f"Perkiraan stok yang terdeteksi: {stock_text}\n\n"
            f"Link produk:\n{PRODUCT_URL}\n\n"
            "Segera cek Tokopedia karena stok dapat berubah."
        )

    message["From"] = email_user
    message["To"] = email_to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_app_password)
        smtp.send_message(message)

    if test:
        print("🧪 Email TEST berhasil dikirim.")
    else:
        print("📧 Email notifikasi berhasil dikirim.")


def get_stock_from_page(body_text):
    # Tokopedia dapat menampilkan jumlah stok seperti "Stok: 3".
    # Jika tidak ada angka, kembalikan None.
    patterns = [
        r"Stok\s*:\s*(\d+)\b",
        r"Stok\s+tersisa\s*(\d+)\b",
        r"tersisa\s*(\d+)\s*(?:buah|pcs|produk)?",
    ]

    for pattern in patterns:
        match = re.search(pattern, body_text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


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
                    results[variant_name] = {
                        "status": "VARIAN TIDAK DITEMUKAN",
                        "stock": None,
                    }
                    print(f"⚠️ {variant_name}: tidak ditemukan")
                    continue

                variant.click()
                page.wait_for_timeout(1500)

                body_text = page.locator("body").inner_text()
                stock = get_stock_from_page(body_text)
                is_sold_out = any(
                    message in body_text
                    for message in sold_out_messages
                )

                if is_sold_out:
                    status = "STOK HABIS"
                    stock = 0
                elif stock is not None:
                    status = "TERSEDIA"
                else:
                    status = "TERSEDIA"

                results[variant_name] = {
                    "status": status,
                    "stock": stock,
                }

            print("\n===== HASIL PEMERIKSAAN =====")

            for variant_name, result in results.items():
                status = result["status"]
                stock = result["stock"]

                if status == "STOK HABIS":
                    icon = "❌"
                elif status == "TERSEDIA":
                    icon = "✅"
                else:
                    icon = "⚠️"

                stock_text = (
                    f" | stok: {stock} pcs"
                    if stock is not None
                    else " | stok: tidak terdeteksi"
                )
                print(f"{icon} {variant_name}: {status}{stock_text}")

            notify_result = results.get(NOTIFY_VARIANT, {})

            if notify_result.get("status") == "TERSEDIA":
                send_email(stock=notify_result.get("stock"))
            else:
                print(
                    f"📧 Email tidak dikirim karena "
                    f"{NOTIFY_VARIANT} belum tersedia."
                )

            print("=============================\n")

        finally:
            browser.close()


if __name__ == "__main__":
    if os.getenv("TEST_EMAIL", "").lower() == "true":
        send_email(test=True)
    else:
        check_stock()
