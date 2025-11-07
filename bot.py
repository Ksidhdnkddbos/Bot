import requests
import json
import os

# إعدادات الحساب - غير هذه القيم
DEEPSEEK_EMAIL = "jjkarar76@gmail.com"  # ضع بريدك هنا
DEEPSEEK_PASSWORD = ""      # ضع باسوردك هنا

url = "https://chat.deepseek.com/api/v0/users/login"

payload = {
  "email": DEEPSEEK_EMAIL,
  "mobile": "",
  "password": DEEPSEEK_PASSWORD,
  "area_code": "",
  "device_id": "BZjjj0bMFgmfOaG7HTxCnyfKuigQHdbugwlfXNpJ86vHU8YHnzwO/Ju57nKzG8+Wyllv4orug3+prPpUDoFzlHg==",
  "os": "web"
}

headers = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
    'Content-Type': "application/json",
    'x-client-locale': "en_US",
    'x-app-version': "20241129.1",
    'x-client-version': "1.5.0",
    'x-client-platform': "web",
    'origin': "https://chat.deepseek.com",
    'referer': "https://chat.deepseek.com/sign_in",
}

print("🔐 جاري تسجيل الدخول إلى DeepSeek...")
response = requests.post(url, data=json.dumps(payload), headers=headers)

if response.status_code == 200 and 'token' in response.text:
    hdo = response.json()
    token = hdo['data']['biz_data']['user']['token']
    
    print('✅ تم تسجيل الدخول بنجاح!')
    print(f'🔑 التوكن: {token}')
    
    # حفظ التوكن في متغير بيئة (للاستخدام في Heroku)
    print('\n💾 لإضافة التوكن إلى Heroku، استخدم:')
    print(f'heroku config:set DEEPSEEK_TOKEN={token}')
    
else:
    print('❌ فشل تسجيل الدخول')
    print(f'الخطأ: {response.text}')
