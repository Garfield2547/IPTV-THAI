# File: generate_epg.py

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import pytz

# --- ส่วนที่สำคัญที่สุด ---
# นำเข้า "นักสืบ" ที่เราสร้างไว้จากไฟล์ scrapers.py
from scrapers import scrape_one31_schedule, scrape_mono29_schedule, scrape_thairath_schedule, scrape_ch3_schedule, scrape_amarin_schedule, scrape_ch7_schedule, scrape_Workpoint_schedule, scrape_PPTV_schedule, scrape_True24_schedule, scrape_GMM25_schedule, scrape_TOPNew_schedule, scrape_TPBS_schedule, scrape_8SD_schedule, scrape_Nation_schedule, scrape_Boomerang_schedule, scrape_MCOT_schedule, scrape_TNN_schedule,scrape_5HD_schedule,scrape_JKN18_schedule


def create_epg():
    """
    ฟังก์ชันหลักสำหรับสร้างไฟล์ guide.xml
    """
    # 1. กำหนดข้อมูลช่อง และจับคู่กับ "นักสืบ" (ฟังก์ชัน) ที่จะไปหาข้อมูล
    #    *** ถ้าต้องการเพิ่มช่องในอนาคต ก็แค่มาเพิ่มใน list นี้ ***
    channels_to_scrape = [
        {"id": "ONE", "name": "ONE 31 HD", "logo": "...", "scraper": scrape_one31_schedule},
        {"id": "Thairath", "name": "Thairath TV", "logo": "...", "scraper": scrape_thairath_schedule},
        {"id": "MONO29", "name": "MONO29 HD", "logo": "...", "scraper": scrape_mono29_schedule},
        {"id": "3HD", "name": "3 HD", "logo": "...", "scraper": scrape_ch3_schedule},
        #{"id": "Amarin", "name": "Amarin TV HD", "logo": "...", "scraper": scrape_amarin_schedule},
        {"id": "7HD", "name": "7 HD", "logo": "...", "scraper": scrape_ch7_schedule},
        #{"id": "Workpoint", "name": "Workpoint HD", "logo": "...", "scraper": scrape_Workpoint_schedule},
       # {"id": "PPTV", "name": "PPTV HD", "logo": "...", "scraper": scrape_PPTV_schedule},
       # {"id": "True24", "name": "True24 SD", "logo": "...", "scraper": scrape_True24_schedule},
       # {"id": "GMM25", "name": "GMM 25", "logo": "...", "scraper": scrape_GMM25_schedule},
       # {"id": "TOPNew", "name": "TOP New SD", "logo": "...", "scraper": scrape_TOPNew_schedule},
       # {"id": "TPBS", "name": "TPBS HD", "logo": "...", "scraper": scrape_TPBS_schedule},
       # {"id": "8SD", "name": "ช่อง 8 SD", "logo": "...", "scraper": scrape_8SD_schedule},
       # {"id": "Nation", "name": "Nation HD", "logo": "...", "scraper": scrape_Nation_schedule},
       # {"id": "Boomerang", "name": "Boomerang", "logo": "...", "scraper": scrape_Boomerang_schedule},
       # {"id": "MCOT", "name": "MCOT HD", "logo": "...", "scraper": scrape_MCOT_schedule},
       # {"id": "TNN", "name": "TNN SD", "logo": "...", "scraper": scrape_TNN_schedule},
       # {"id": "5HD", "name": "5HD", "logo": "...", "scraper": scrape_5HD_schedule},
       # {"id": "JKN18", "name": "JKN18", "logo": "...", "scraper": scrape_JKN18_schedule},
    ]

    program_data = {}

    # 2. วนลูปสั่งให้นักสืบแต่ละคนไปทำงาน
    for channel in channels_to_scrape:
        channel_id = channel["id"]
        scraper_function = channel["scraper"]
        
        # เรียกใช้ฟังก์ชันดึงข้อมูลของช่องนั้นๆ
        scraped_programs = scraper_function()
        
        if not scraped_programs:
            continue # ถ้าดึงข้อมูลไม่ได้ ก็ข้ามไปช่องถัดไป

        # คำนวณเวลาสิ้นสุด
        for i in range(len(scraped_programs)):
            if i < len(scraped_programs) - 1:
                scraped_programs[i]['end_time'] = scraped_programs[i+1]['start_time']
            else:
                scraped_programs[i]['end_time'] = "24:00"
        
        program_data[channel_id] = scraped_programs

    # 3. เริ่มสร้างไฟล์ XML จากข้อมูลทั้งหมดที่รวบรวมได้
    print("\n📝 กำลังสร้างไฟล์ guide.xml...")
    tz = pytz.timezone("Asia/Bangkok")
    today = datetime.now(tz)
    
    tv_root = ET.Element("tv")

    for chan in channels_to_scrape:
        channel_elem = ET.SubElement(tv_root, "channel", {"id": chan["id"]})
        ET.SubElement(channel_elem, "display-name", {"lang": "th"}).text = chan["name"]
        ET.SubElement(channel_elem, "icon", {"src": chan["logo"]})

    for channel_id, programs in program_data.items():
        for prog in programs:
            try:
                start_h, start_m = map(int, prog['start_time'].split(':'))
                end_h, end_m = (23, 59) if prog['end_time'] == "24:00" else map(int, prog['end_time'].split(':'))

                start_time_obj = today.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                end_time_obj = today.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
                
                time_format = "%Y%m%d%H%M%S %z"

                programme_elem = ET.SubElement(tv_root, "programme", {
                    "start": start_time_obj.strftime(time_format),
                    "stop": end_time_obj.strftime(time_format),
                    "channel": channel_id
                })
                
                ET.SubElement(programme_elem, "title", {"lang": "th"}).text = prog["title"]
                ET.SubElement(programme_elem, "desc", {"lang": "th"}).text = prog.get("description", "-")
            except (ValueError, AttributeError):
                continue

    xml_str = ET.tostring(tv_root, 'utf-8')
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="utf-8")

    with open("guide.xml", "wb") as f:
        f.write(pretty_xml_str)
        
    print("✅✅✅ ไฟล์ guide.xml ถูกสร้างขึ้นเรียบร้อยแล้ว! (มีข้อมูลของ ONE31 และ MONO29)")


# --- จุดเริ่มต้นของโปรแกรม ---
if __name__ == "__main__":
    create_epg()