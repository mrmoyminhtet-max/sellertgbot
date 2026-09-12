import requests

# 1. Telegram Trigger မှ ရလာသော data ကို လက်ခံခြင်း
input_data = _input.all()[0].json
message = input_data.get("message", {})
chat_id = message.get("chat", {}).get("id")

if not chat_id:
    # Chat ID မပါလာပါက ထွက်မည်
    return [{"json": {"error": "Chat ID not found"}}]

photos = message.get("photo", [])
if not photos:
    return [{
        "json": {
            "chat_id": chat_id, 
            "text": "ကျေးဇူးပြု၍ ပစ္စည်းပုံ (Product ID ပါသောပုံ) ကို ပို့ပေးပါရှင်။"
        }
    }]

# အကောင်းဆုံး Resolution ရှိသော ပုံဖိုင်ကို ရယူခြင်း
best_photo = photos[-1]
file_id = best_photo.get("file_id")

# 2. Telegram API မှတဆင့် ပုံဖိုင် လမ်းကြောင်း (file_path) ကို တောင်းခံခြင်း
BOT_TOKEN = "8619835808:AAEaMKGnxq3T0NogMJ6G_o5l5Q99_-JBYA0"
file_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
file_res = requests.get(file_info_url).json()

if not file_res.get("ok"):
    return [{"json": {"chat_id": chat_id, "text": "ပုံကို ဖတ်ရှု၍ မရပါ။"}}]

file_path = file_res["result"]["file_path"]
image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

# 3. Gemini Vision API ကိုသုံး၍ ပုံထဲမှ Product ID ကို ဖတ်ယူခြင်း (OCR)
GEMINI_API_KEY = "AQ.Ab8RN6JUbFRpotafThZqme8ISvKHeyEi51NXiAEBO2l5zZwR-g"
gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

payload = {
    "contents": [{
        "parts": [
            {"text": "Extract only the Product ID visible in this image (e.g., jeans-lee-001). Return only the ID text, with no extra spaces or words."},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(requests.get(image_url).content).decode("utf-8")
                }
            }
        ]
    }]
}

headers = {"Content-Type": "application/json"}
gemini_res = requests.post(gemini_url, json=payload, headers=headers).json()

try:
    product_id = gemini_res["candidates"][0]["content"]["parts"][0]["text"].strip()
except Exception:
    product_id = ""

if not product_id:
    return [{
        "json": {
            "chat_id": chat_id, 
            "text": "ပုံထဲမှ Product ID ကို ရှာမတွေ့ပါ။ ကျေးဇူးပြု၍ ထပ်ကြိုးစားပါ။"
        }
    }]

# 4. ထွက်လာသော Product ID ဖြင့် Supabase တွင် စစ်ဆေးရန် အချက်အလက်များ ပြန်ထုတ်ပေးခြင်း
# (ဤနေရာတွင် Supabase Node သို့မဟုတ် requests ဖြင့် Supabase REST API ကို ဆက်လက်ခေါ်ယူနိုင်ပါသည်)
output_result = {
    "chat_id": chat_id,
    "product_id": product_id,
    "text": f"ရှာတွေ့သော Product ID: {product_id}\nSupabase Database ထဲတွင် ဆက်လက်စစ်ဆေးနေပါပြီ..."
}

return [{"json": output_result}]
