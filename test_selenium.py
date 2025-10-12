from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re
import time

def scrape_one31_schedule_selenium():
    URL = "https://www.one31.net/schedule"
    
    try:
        service = Service(executable_path='chromedriver.exe')
        driver = webdriver.Chrome(service=service)
    except Exception as e:
        print(f"❌ เกิดปัญหาในการเปิด ChromeDriver: {e}")
        return None

    print("🤖 Selenium กำลังเปิดเบราว์เซอร์...")
    
    try:
        driver.get(URL)
        
        try:
            cookie_button_wait = WebDriverWait(driver, 10)
            accept_button = cookie_button_wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            print("👍 เจอปุ่มคุกกี้แล้ว กำลังจะกด 'ยอมรับ'...")
            accept_button.click()
            time.sleep(2)
        except TimeoutException:
            print("🤔 ไม่พบหน้าต่างคุกกี้")

        # เรารอ 'ป้ายชื่อห้อง' (current-sc-day) เพื่อให้แน่ใจว่าหน้าเว็บโหลดเสร็จ
        print("...กำลังรอจนกว่าผังรายการจะโหลดเสร็จ (สูงสุด 20 วินาที)...")
        schedule_wait = WebDriverWait(driver, 20)
        schedule_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'current-sc-day')))
        
        print("✅ ผังรายการโหลดเสร็จสมบูรณ์แล้ว!")
        
        html = driver.page_source
        
    finally:
        driver.quit()
        print("🤖 ปิดเบราว์เซอร์แล้ว")

    soup = BeautifulSoup(html, 'html.parser')
    
    # --- จุดที่แก้ไขสำคัญ ---
    # เราจะค้นหาจาก 'กรอบที่ใหญ่กว่า' ที่ชื่อว่า 'tab-content'
    main_container = soup.find('div', class_='tab-content')

    if not main_container:
        print("❌ ไม่พบโครงสร้างหลัก 'tab-content'")
        return []

    # แล้วค่อยค้นหารายการทั้งหมดที่อยู่ในกรอบใหญ่นั้น
    program_items = main_container.find_all('p', class_='card-text')
    
    scraped_programs = []
    for item in program_items:
        try:
            title_tag = item.find('h2', class_='title')
            time_detail_tag = item.find('div', class_='subtitle-detail-sch')

            if not title_tag or not time_detail_tag:
                continue

            title = title_tag.text.strip()
            time_text = time_detail_tag.text.strip()
            
            match = re.search(r'เวลา\s*(\d{2}:\d{2})', time_text)
            if not match:
                continue
                
            time_str = match.group(1)
            
            scraped_programs.append({
                "start_time": time_str, "end_time": "",
                "title": title, "description": ""
            })
        except AttributeError:
            continue
            
    # คำนวณเวลาสิ้นสุด (ใช้ตรรกะเดิม)
    for i in range(len(scraped_programs)):
        if i < len(scraped_programs) - 1:
            scraped_programs[i]['end_time'] = scraped_programs[i+1]['start_time']
        else:
            scraped_programs[i]['end_time'] = "24:00"

    return scraped_programs

if __name__ == "__main__":
    schedule = scrape_one31_schedule_selenium()
    if schedule:
        print("\n🎉🎉🎉 สำเร็จ! 🎉🎉🎉")
        print("--- 📺 ผังรายการช่อง ONE31 ที่ดึงมาได้ ---")
        for prog in schedule:
            print(f"[{prog['start_time']} - {prog['end_time']}] {prog['title']}")
    else:
        print("\n❌❌❌ สคริปต์ทำงานจบ แต่ไม่พบข้อมูลรายการย่อยข้างใน")