# File: debug_ch7.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

def setup_driver():
    """ฟังก์ชันสำหรับตั้งค่า Selenium Driver ให้ทำงานเบื้องหลัง"""
    service = Service(executable_path='chromedriver.exe')
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # ปิด headless ชั่วคราวเพื่อให้เห็นการทำงาน
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3') # ซ่อน log ที่ไม่จำเป็น
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def export_ch7_html():
    URL = "https://www.ch7.com/schedule.html"

    driver = setup_driver()
    print("🤖 กำลังเปิดเว็บ CH7 Schedule...")

    try:
        driver.get(URL)

        # เว็บช่อง 7 อาจมีคุกกี้ หรือโหลดช้า
        print("...กำลังรอหน้าเว็บโหลดข้อมูล (5 วินาที)...")
        time.sleep(5) 

        # เลื่อนหน้าจอลงเพื่อให้แน่ใจว่าโหลดครบ
        print("...กำลังเลื่อนหน้าจอลง...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3) # รอ 3 วินาทีหลัง scroll

        html_content = driver.page_source
        print("✅ ดึงโค้ด HTML ทั้งหน้าสำเร็จ")

        with open("ch7_page_source.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ บันทึกโค้ด HTML ลงในไฟล์ 'ch7_page_source.html' เรียบร้อยแล้ว")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    export_ch7_html()