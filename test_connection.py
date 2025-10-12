import requests

# นี่คือ URL สำหรับทดสอบสาธารณะ ใครๆ ก็สามารถเชื่อมต่อได้
TEST_URL = "https://jsonplaceholder.typicode.com/todos/1"

print(f"กำลังลองเชื่อมต่อไปที่: {TEST_URL}")

try:
    response = requests.get(TEST_URL, timeout=10)
    response.raise_for_status() # ตรวจสอบว่ามี error หรือไม่
    data = response.json()

    print("\n✅✅✅ การเชื่อมต่อสำเร็จ! ✅✅✅")
    print("ข้อมูลที่ได้รับ:")
    print(data)

except requests.exceptions.RequestException as e:
    print(f"\n❌❌❌ การเชื่อมต่อล้มเหลว! ❌❌❌")
    print(f"Error: {e}")