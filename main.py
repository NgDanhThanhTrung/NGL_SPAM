import threading
import requests
import time
import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)

# ================= CẤU HÌNH =================
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE" 
API_KEY = "ngdanhthanhtrung"
# ID Telegram của bạn (Bot sẽ gửi thông báo vào đây)
# Bạn có thể lấy ID này bằng cách chat /myid với bot sau khi chạy code này
YOUR_CHAT_ID = "YOUR_PERSONAL_CHAT_ID" 
# ============================================

def send_ngl_request(username, message):
    url = "https://ngl.link/api/submit"
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
    data = {"username": username, "question": message, "deviceId": "0000-0000"}
    try:
        res = requests.post(url, data=data, headers=headers, timeout=5)
        return res.status_code
    except:
        return 500

# Hàm gửi tin nhắn thông báo về Telegram khi xong việc
def notify_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": YOUR_CHAT_ID, "text": msg}
    requests.post(url, json=payload)

def task_background_spam(username, message, count):
    """Xử lý gửi spam và báo cáo khi hoàn tất"""
    success = 0
    for _ in range(count):
        if send_ngl_request(username, message) == 200:
            success += 1
        time.sleep(0.2)
    
    # Gửi thông báo hoàn tất về Telegram
    notify_telegram(f"✅ HOÀN THÀNH NHIỆM VỤ!\n👤 Target: {username}\n🚀 Gửi thành công: {success}/{count}")

# --- PHẦN 1: API CHO PHÍM TẮT ---
@app.route('/api/ngl/', methods=['GET'])
def api_handler():
    user = request.args.get('user')
    content = request.args.get('content')
    count = int(request.args.get('count', 1))
    key = request.args.get('key')

    if key != API_KEY:
        return jsonify({"status": "error", "message": "Sai Key"}), 403

    # Chạy ngầm và trả về kết quả ngay cho Phím tắt
    thread = threading.Thread(target=task_background_spam, args=(user, content, count))
    thread.start()

    return jsonify({"status": "processing", "message": "Đang gửi ngầm, sẽ báo qua Telegram khi xong."})

# --- PHẦN 2: TELEGRAM BOT ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Chào bạn! ID của bạn là: `{chat_id}`\nHãy copy ID này dán vào phần YOUR_CHAT_ID trong code.")

async def ngl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        input_str = " ".join(context.args)
        parts = [p.strip() for p in input_str.split("|")]
        user, content = parts[0], parts[1]
        count = int(parts[2]) if len(parts) > 2 else 1

        # Chạy ngầm và báo cáo
        thread = threading.Thread(target=task_background_spam, args=(user, content, count))
        thread.start()

        await update.message.reply_text(f"🚀 Đã nhận lệnh!\nĐang gửi {count} tin tới {user}. Bot sẽ báo khi xong.")
    except:
        await update.message.reply_text("❌ Sai cú pháp: /ngl user | nội dung | số lần")

def run_telegram_bot():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ngl", ngl_command))
    application.run_polling(close_loop=False)

if __name__ == "__main__":
    threading.Thread(target=run_telegram_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
