import os
import logging
from flask import Flask, request
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Твой chat_id (администратора) - замени на свой
ADMIN_CHAT_ID = "123456789"  # ЗАМЕНИ НА СВОЙ CHAT_ID

# Клавиатура с кнопкой "Поделиться номером"
share_phone_keyboard = {
    "keyboard": [[{
        "text": "📱 Поделиться номером",
        "request_contact": True
    }]],
    "resize_keyboard": True,
    "one_time_keyboard": True
}

# Обычная клавиатура
default_keyboard = {
    "keyboard": [[{"text": "📱 Поделиться номером"}]],
    "resize_keyboard": True
}

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_URL}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    requests.post(url, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        data = request.get_json()
        
        # Проверяем, что это сообщение
        if 'message' not in data:
            return 'ok'
            
        message = data['message']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        username = message['from'].get('username', 'нет')
        first_name = message['from'].get('first_name', '')
        last_name = message['from'].get('last_name', '')
        
        full_name = f"{first_name} {last_name}".strip()

        # Если пользователь отправил контакт
        if 'contact' in message:
            contact = message['contact']
            phone_number = contact['phone_number']
            
            # Проверяем, что контакт принадлежит отправителю
            if contact['user_id'] == user_id:
                # Сообщение пользователю
                send_message(chat_id, "✅ Спасибо! Ваш номер получен.", default_keyboard)
                
                # Сообщение админу (тебе) с номером
                admin_message = (
                    f"📱 <b>Новый номер!</b>\n\n"
                    f"👤 Имя: {full_name}\n"
                    f"📞 Телефон: <code>{phone_number}</code>\n"
                    f"🆔 User ID: {user_id}\n"
                    f"📛 Username: @{username}"
                )
                send_message(ADMIN_CHAT_ID, admin_message)
                
            else:
                send_message(chat_id, "❌ Это не ваш номер телефона.")
            
            return 'ok'

        # Если текстовое сообщение
        if 'text' in message:
            text = message['text']
            
            if text == '/start':
                welcome_text = (
                    "👋 Привет! Я бот для сбора номеров телефонов.\n\n"
                    "Нажми кнопку ниже, чтобы поделиться своим номером:"
                )
                send_message(chat_id, welcome_text, share_phone_keyboard)
            elif 'номер' in text.lower() or '📱' in text:
                send_message(chat_id, "Нажмите кнопку ниже, чтобы поделиться номером:", share_phone_keyboard)
            else:
                send_message(chat_id, "Нажмите кнопку '📱 Поделиться номером'", share_phone_keyboard)

        return 'ok'

@app.route('/')
def set_webhook():
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    response = requests.post(f"{TELEGRAM_URL}/setWebhook", data={'url': webhook_url})
    return f"✅ Бот запущен!<br>Webhook: {webhook_url}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
