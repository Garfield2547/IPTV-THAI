# File: scrapers.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re
import time

def setup_driver():
    """ฟังก์ชันสำหรับตั้งค่า Selenium Driver ให้ทำงานเบื้องหลัง"""
    service = Service(executable_path='chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3') # ซ่อน log ที่ไม่จำเป็น
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_one31_schedule():
    """ดึงข้อมูลผังรายการจาก ONE31"""
    URL = "https://www.one31.net/schedule"
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง ONE31...")
    driver = setup_driver()
    scraped_programs = []
    
    try:
        driver.get(URL)
        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            cookie_button.click()
            time.sleep(2)
        except TimeoutException:
            pass # ไม่เจอปุ่มคุกกี้ก็ไม่เป็นไร

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'current-sc-day')))
        html = driver.page_source
        
        soup = BeautifulSoup(html, 'html.parser')
        main_container = soup.find('div', class_='tab-content')
        if main_container:
            program_items = main_container.find_all('p', class_='card-text')
            for item in program_items:
                title_tag = item.find('h2', class_='title')
                time_detail_tag = item.find('div', class_='subtitle-detail-sch')
                if title_tag and time_detail_tag:
                    title = title_tag.text.strip()
                    time_text = time_detail_tag.text.strip()
                    match = re.search(r'เวลา\s*(\d{2}:\d{2})', time_text)
                    if match:
                        scraped_programs.append({"start_time": match.group(1), "title": title})
            print("✅ ดึงข้อมูล ONE31 สำเร็จ")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล ONE31: {e}")
    finally:
        driver.quit()
    return scraped_programs

# In scrapers.py file

# In scrapers.py file

def scrape_mono29_schedule():
    """ดึงข้อมูลผังรายการจาก MONO29 (เวอร์ชันแก้ไข ป้องกันข้อมูลซ้ำซ้อน)"""
    URL = "https://mono29.com/schedule"
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง MONO29...")
    driver = setup_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "pdpa_cookies_btn_accept")))
            print("👍 MONO29: เจอปุ่มคุกกี้แล้ว กำลังจะกด...")
            cookie_button.click()
            time.sleep(2)
        except TimeoutException:
            pass 

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'container-schedule')))
        html = driver.page_source

        soup = BeautifulSoup(html, 'html.parser')
        
        # --- จุดที่แก้ไขสำคัญ ---
        # 1. ค้นหากล่องใหญ่ 'container-schedule' ก่อน
        main_container = soup.find('div', class_='container-schedule')
        
        # 2. จากนั้น ค่อยค้นหากล่องของ 'วันนี้' ที่อยู่ข้างใน ซึ่งมี ID ว่า 'loadContents-1'
        today_schedule_container = main_container.find('div', id='loadContents-2')

        if today_schedule_container:
            program_items = today_schedule_container.find_all('div', class_='programInDisplay')
            for item in program_items:
                try:
                    time_tag = item.find('div', class_='box-time')
                    img_tag = item.find('img')
                    
                    time_str = time_tag.text.strip().replace(' น.', '')
                    title = img_tag['alt'].strip()

                    if time_str and title:
                        scraped_programs.append({"start_time": time_str, "title": title})
                except (AttributeError, KeyError):
                    continue
            print("✅ ดึงข้อมูล MONO29 สำเร็จ (เฉพาะวันนี้)")
        else:
            print("❌ MONO29: ไม่พบ container ของผังรายการวันนี้ (id='loadContents-1')")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล MONO29: {e}")
    finally:
        driver.quit()
    return scraped_programs


# In scrapers.py file, replace the old thairath function with this one

import requests
from bs4 import BeautifulSoup
import json

def scrape_thairath_schedule():
    """ดึงข้อมูลผังรายการจาก Thairath TV (แก้ไข KeyError)"""
    URL = "https://www.thairath.co.th/tv/schedule"
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง Thairath (วิธีใหม่)...")
    scraped_programs = []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            print("❌ Thairath: ไม่พบ script tag '__NEXT_DATA__'")
            return []

        data = json.loads(next_data_script.string)
        
        # --- จุดที่แก้ไข: เปลี่ยนเส้นทางไปยังข้อมูล ---
        schedule_parts = data['props']['initialState']['tv']['data']['items']['schedule'][0]

        for part_name, part_data in schedule_parts.items():
            for item in part_data.get('items', []):
                title = item.get('title')
                start_time = item.get('onAirTime')

                if title and start_time:
                    scraped_programs.append({"start_time": start_time, "title": title})
        
        print("✅ ดึงข้อมูล Thairath สำเร็จ")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล Thairath: {e}")
    
    return scraped_programs

# In scrapers.py file, add this new function at the end

def scrape_ch3_schedule():
    """ดึงข้อมูลผังรายการจาก CH3 Plus"""
    URL = "https://ch3plus.com/schedule"
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง 3HD...")
    driver = setup_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        try:
            # รอและกดปุ่มคุกกี้ "ยอมรับทั้งหมด"
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับทั้งหมด']")))
            print("👍 CH3: เจอปุ่มคุกกี้แล้ว กำลังจะกด...")
            cookie_button.click()
            time.sleep(2)
        except TimeoutException:
            pass # ไม่เจอปุ่มคุกกี้ก็ไม่เป็นไร

        # รอให้ตารางผังรายการโหลดเสร็จ
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'schedule-detail')))
        html = driver.page_source

        soup = BeautifulSoup(html, 'html.parser')
        
        # ค้นหาตารางผังรายการ
        schedule_table = soup.find('table', class_='schedule-detail')
        if schedule_table:
            # ค้นหารายการทั้งหมดที่อยู่ใน <tr>
            program_items = schedule_table.find('tbody').find_all('tr')
            for item in program_items:
                try:
                    columns = item.find_all('td')
                    if len(columns) == 2:
                        # เวลาอยู่ในคอลัมน์แรก, ชื่อรายการอยู่ในคอลัมน์ที่สอง
                        time_str = columns[0].text.split('-')[0].strip() # เอาเฉพาะเวลาเริ่ม
                        title = columns[1].text.strip()
                        
                        # ตัด element ที่ไม่ต้องการทิ้ง (เช่น รูปไอคอน)
                        if "ดูได้เฉพาะในประเทศไทย" in title:
                            title = title.replace("ดูได้เฉพาะในประเทศไทย", "").strip()
                        if "ดูได้เฉพาะหน้าจอทีวี" in title:
                            title = title.replace("ดูได้เฉพาะหน้าจอทีวี", "").strip()

                        if time_str and title:
                            scraped_programs.append({"start_time": time_str, "title": title})
                except (AttributeError, IndexError):
                    continue
            print("✅ ดึงข้อมูล 3HD สำเร็จ")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล 3HD: {e}")
    finally:
        driver.quit()
    return scraped_programs

# In scrapers.py file, replace the old amarin function with this one

#def scrape_amarin_schedule():
    """ดึงข้อมูลผังรายการจาก Amarin TV (ใช้วิธีคลิกเพื่อเปิดข้อมูล)"""
    URL = "https://www.amarintv.com/schedule"
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง Amarin TV (Selenium)...")
    driver = setup_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        
        print("...กำลังรอให้ปุ่มควบคุมโหลดเสร็จ...")
        
        # รอจนเจอ "ปุ่ม" ควบคุมของแต่ละช่วงเวลา
        time_section_buttons = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[id^=':r']"))
        )

        print(f"👍เจอปุ่มควบคุม {len(time_section_buttons)} ปุ่ม กำลังคลิกเพื่อเปิดข้อมูล...")
        
        # วนลูปเพื่อคลิกเปิดแต่ละช่วงเวลา
        for button in time_section_buttons:
            try:
                # ใช้ JavaScript คลิกเพื่อความแน่นอน
                driver.execute_script("arguments[0].click();", button)
                time.sleep(1) # รอ 1 วินาทีเพื่อให้ข้อมูลโหลดหลังคลิก
            except Exception:
                continue # ถ้าคลิกไม่ได้ก็ข้ามไป

        # หลังจากคลิกเปิดทั้งหมดแล้ว ค่อยดึงโค้ด HTML ทั้งหน้า
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # ค้นหารายการทั้งหมดในหน้าเว็บ (ตอนนี้ข้อมูลควรจะมาครบทุกช่วงเวลาแล้ว)
        program_items = soup.find_all('a', class_='detail_row__jWZ4z')
        
        if program_items:
            for item in program_items:
                try:
                    time_str = item.find_all('div')[0].text.strip()
                    title = item.find_all('div')[2].text.strip()

                    if time_str and title:
                        scraped_programs.append({"start_time": time_str, "title": title})
                except (AttributeError, IndexError):
                    continue
            print("✅ ดึงข้อมูล Amarin TV สำเร็จ")
        else:
            print("❌ Amarin TV: ไม่พบข้อมูลรายการย่อย")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล Amarin TV: {e}")
    finally:
        driver.quit()
    
    # เรียงลำดับรายการตามเวลาเริ่มต้นก่อนส่งค่ากลับ
    scraped_programs.sort(key=lambda x: x['start_time'])
    return scraped_programs

# In scrapers.py file, replace the old ch7 function with this new one

# def scrape_ch7_schedule():
    """ดึงข้อมูลผังรายการจาก CH7 (ใช้ Selenium และ Class ที่ถูกต้องจากผู้ใช้)"""
    URL = "https://www.ch7.com/schedule.html"
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง 7HD (Selenium)...")
    driver = setup_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        
        try:
            # --- จุดที่แก้ไข 1: รอและกดปุ่มคุกกี้ตาม ID ที่ถูกต้อง ---
            print("...กำลังค้นหาปุ่มยอมรับคุกกี้...")
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "cookie-notice-accept-btn"))
            )
            print("👍 7HD: เจอปุ่มคุกกี้แล้ว กำลังจะกด...")
            # ใช้ Javascript คลิกเพื่อความแน่นอน
            driver.execute_script("arguments[0].click();", cookie_button) 
            time.sleep(2) # รอ 2 วินาทีเพื่อให้ pop-up หายไป
        except TimeoutException:
            print("🤔 7HD: ไม่พบหน้าต่างคุกกี้")

        # --- จุดที่แก้ไข 2: รอจนกว่า 'content-left' ซึ่งเป็นกรอบของรายการจะโหลดเสร็จ ---
        print("...กำลังรอให้ผังรายการของวันนี้โหลดเสร็จ...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "content-left"))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # ค้นหารายการทั้งหมดที่มี class 'content-left'
        program_items = soup.find_all('div', class_='content-left')
        
        for item in program_items:
            try:
                # --- จุดที่แก้ไข 3: ดึงข้อมูลจาก Class ที่ถูกต้อง ---
                time_str = item.find(class_='text-muted').text.strip()
                title = item.find(class_='text-title-schedule-program').text.strip()

                if time_str and title:
                    scraped_programs.append({"start_time": time_str, "title": title})
            except (AttributeError, IndexError):
                continue
        print("✅ ดึงข้อมูล 7HD สำเร็จ")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล 7HD: {e}")
    finally:
        driver.quit()
    
    return scraped_programs
# สามารถเพิ่มฟังก์ชัน scrape_...() สำหรับช่องอื่นๆ ต่อท้ายไฟล์นี้ได้เรื่อยๆ