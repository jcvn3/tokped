from playwright.sync_api import sync_playwright
import time

PRODUCT_URL = "https://www.tokopedia.com/bassaudiobdg/kinera-celest-wyvern-black-edition-10mm-dynamic-driver-in-ear-monitor-earphones-with-mic-1731753518101660852"

TARGET_VARIANT = "STD with Mic"


def check_stock():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={"width": 1366, "height": 768},
            locale="id-ID"
        )

        print("Membuka halaman Tokopedia...")
        page.goto(
            PRODUCT_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        # Tunggu halaman selesai memuat
        page.wait_for_timeout(5000)

        print("Halaman:", page.title())

        # Cari dan klik varian target
        variant = page.get_by_text(
            TARGET_VARIANT,
            exact=True
        ).first

        if variant.count() > 0:
            print(f"Memilih varian: {TARGET_VARIANT}")
            variant.click()
            page.wait_for_timeout(2000)
        else:
            print(f"Varian '{TARGET_VARIANT}' tidak ditemukan.")
            browser.close()
            return

        # Ambil seluruh teks halaman
        text = page.locator("body").inner_text()

        print("\n===== HASIL PEMERIKSAAN =====")

        if "Stok Habis" in text:
            print(f"❌ {TARGET_VARIANT}: STOK HABIS")
        else:
            print(f"✅ {TARGET_VARIANT}: KEMUNGKINAN TERSEDIA")

        print("=============================\n")

        browser.close()


if __name__ == "__main__":
    check_stock()
