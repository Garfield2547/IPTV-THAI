# File: scrapers.py
# --- เพิ่ม import นี้เข้ามา ---
import undetected_chromedriver as uc
# -------------------------
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

# --- วางฟังก์ชันใหม่นี้ไว้ใต้ setup_driver() เดิม ---

def setup_undetected_driver():
    """ฟังก์ชันสำหรับตั้งค่า undetected-chromedriver ให้ทำงานเบื้องหลัง"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    driver = uc.Chrome(options=options, use_subprocess=True)
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

# --- แทนที่ฟังก์ชัน scrape_amarin_schedule() เดิมด้วยโค้ดนี้ ---

def scrape_amarin_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง Amarin TV HD จาก TrueID (เวอร์ชันหลบการตรวจจับและอัปเดต Selector)
    """
    URL = "https://tv.trueid.net/th-th/live/amarintv-hd"
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง Amarin TV (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        # จัดการปุ่มคุกกี้
        try:
            print("...กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...กำลังรอให้ผังรายการของ TrueID โหลด...")
        # --- จุดแก้ไขที่ 1: เปลี่ยนมาใช้ data-testid ที่คุณหาเจอในการรอ ---
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # --- จุดแก้ไขที่ 2: ใช้ selector ใหม่ในการค้นหาข้อมูล ---
        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ Amarin (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        # ค้นหารายการทั้งหมดจาก class ที่ถูกต้อง
        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                # ค้นหาเวลาและชื่อรายการจาก class ที่ถูกต้อง
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    # กรองเอาเฉพาะรายการที่มีเวลาจริงๆ (ไม่ใช่คำว่า Live)
                    if ':' in time_str: 
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล Amarin TV (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล Amarin TV (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

#
# --- วางฟังก์ชันใหม่นี้ต่อท้ายไฟล์ scrapers.py ---
#

def scrape_ch7_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง 7HD จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/ch7-hd"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง 7HD (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[7HD] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [7HD] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [7HD] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[7HD] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ 7HD (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล 7HD (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล 7HD (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_Workpoint_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง Workpoint จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/workpointtv"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง Workpoint (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[Workpoint] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [Workpoint] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [Workpoint] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[Workpoint] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ Workpoint (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล Workpoint (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล Workpoint (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_PPTV_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง PPTV จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/pptv-hd"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง PPTV (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[PPTV] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [PPTV] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [PPTV] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[PPTV] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ PPTV (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล PPTV (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล PPTV (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_True24_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง True24 จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/true4u"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง True24 (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[True24] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [True24] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [True24] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[True24] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ True24 (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล True24 (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล True24 (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_GMM25_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง GMM25 จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/gmm25"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง GMM25 (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[GMM25] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [GMM25] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [GMM25] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[GMM25] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ GMM25 (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล GMM25 (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล GMM25 (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_TOPNew_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง TOP New จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/tid-top-news"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง TOP New (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[TOP New] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [TOP New] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [TOP New] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[TOP New] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ TOP New (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล TOP New (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล TOP New (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_TPBS_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง TPBS จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/thaipbs"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง TPBS (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[TPBS] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [TPBS] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [TPBS] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[TPBS] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ TPBS (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล TPBS (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล TPBS (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_8SD_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง 8SD จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/ch8"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง 8SD (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[8SD] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [8SD] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [8SD] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[8SD] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ 8SD (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล 8SD (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล 8SD (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_Nation_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง Nation จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/nationtv"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง Nation (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[Nation] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [Nation] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [Nation] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[Nation] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ Nation (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล Nation (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล Nation (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_Boomerang_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง Boomerang จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/boomerang-hd"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง Boomerang (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[Boomerang] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [Boomerang] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [Boomerang] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[Boomerang] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ Boomerang (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล Boomerang (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล Boomerang (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_MCOT_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง MCOT จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/9mcot-hd"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง MCOT (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[MCOT] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [MCOT] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [MCOT] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[MCOT] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ MCOT (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล MCOT (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล MCOT (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_TNN_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง TNN จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/tnn16"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง TNN (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[TNN] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [TNN] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [TNN] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[TNN] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ TNN (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล TNN (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล TNN (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_5HD_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง 5HD จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/ch5"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง 5HD (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[5HD] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [5HD] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [5HD] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[5HD] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ 5HD (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล 5HD (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล 5HD (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

def scrape_JKN18_schedule():
    """
    ดึงข้อมูลผังรายการของช่อง JKN18 จาก TrueID (เวอร์ชันหลบการตรวจจับ)
    """
    # --- จุดที่แก้ไข 1: เปลี่ยน URL เป็นของช่อง 7HD ---
    URL = "https://tv.trueid.net/th-th/live/jkn18"
    # --- จุดที่แก้ไข 2: เปลี่ยนข้อความ Log ต่างๆ ---
    print("🕵️  กำลังเริ่มดึงข้อมูลช่อง JKN18 (จาก TrueID - undetected)...")
    driver = setup_undetected_driver()
    scraped_programs = []

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        try:
            print("...[JKN18] กำลังค้นหาปุ่มคุกกี้...")
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ยอมรับ']")))
            cookie_button.click()
            print("👍 [JKN18] กดปุ่มยอมรับคุกกี้แล้ว")
            time.sleep(2)
        except Exception:
            print("🤔 [JKN18] ไม่พบปุ่มคุกกี้ หรืออาจเคยกดไปแล้ว")
        
        print("...[JKN18] กำลังรอให้ผังรายการของ TrueID โหลด...")
        program_container_selector = "div[data-testid='all-items-programTv']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, program_container_selector)))
        
        time.sleep(3) 

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        program_container = soup.select_one(program_container_selector)
        
        if not program_container:
            print("❌ JKN18 (TrueID): ไม่พบกรอบข้อมูลผังรายการ (data-testid)")
            return []

        program_items = program_container.select("div[class*='style__ProgramItems-sc-']")

        for item in program_items:
            try:
                time_tag = item.select_one("span[class*='style__ProgramShowTime-sc-']")
                title_tag = item.select_one("span[class*='style__ProgramName-sc-']")
                
                if time_tag and title_tag:
                    time_str = time_tag.text.strip()
                    if ':' in time_str:
                        scraped_programs.append({
                            "start_time": time_str, 
                            "title": title_tag.text.strip()
                        })
            except AttributeError:
                continue
                
        print("✅ ดึงข้อมูล JKN18 (จาก TrueID) สำเร็จ!")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดขณะดึงข้อมูล JKN18 (จาก TrueID): {e}")
    finally:
        driver.quit()
        
    return scraped_programs

# สามารถเพิ่มฟังก์ชัน scrape_...() สำหรับช่องอื่นๆ ต่อท้ายไฟล์นี้ได้เรื่อยๆ