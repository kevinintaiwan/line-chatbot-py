from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
from datetime import datetime, timedelta

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])

# 使用字典來儲存使用者選擇和時間戳記
user_states = {}

# 定義藥物資訊
DRUG_INFO = {
    "1": {
        "name": "Cyclophosphamide",
        "prompt": "輸入a表示膀胱出血、血尿",
        "detail_text": "藥物的代謝物排泄至尿液後會引起泌尿道，尤其是膀胱的改變，若出現出血性膀胱炎或血尿等現象，請立即回診就醫\n\n"
                      "平時請喝大量開水，並時常排尿，若醫師無特殊指示，建議於晨間服用，降低對膀胱之副作用",
        "emojis": [{
            "index": 71,
            "productId": "5ac21e6c040ab15980c9b444",
            "emojiId": "104"
        }]
    },
    "2": {
        "name": "Doxorubicin",
        "prompt": "輸入a表示心臟功能異常",
        "detail_text": "若出現相關症狀，如：胸悶疼痛、呼吸困難、眩暈、心律改變等，請立即就醫，且每三個月需監測心臟功能",
        "emojis": []
    },
    "3": {
        "name": "Vincristine",
        "prompt": "輸入a表示神經肌肉症狀",
        "detail_text": "神經肌肉症狀：包括神經痛、四肢痛、麻木感、肌肉痛、步行困難、知覺異常、運動失調等，孩童最容易感受此副作用，"
                      "通常一般在治療後 6 週消失，但偶爾會有停止治療後仍持續一段長期間之情形。",
        "emojis": []
    },
    "4": {
        "name": "Prednisolone",
        "prompt": "輸入a表示口腔、喉嚨痛",
        "detail_text": "藥物可能導致口腔、喉嚨痛，若出現此症狀請告知醫護人員，並且避免食用刺激口腔和喉嚨的食物，盡量多喝水",
        "emojis": []
    }
}

def get_default_message():
    return TextSendMessage(
        text="請輸入以下數字以選擇藥物:\n"
             "1. Cyclophosphamide\n"
             "2. Doxorubicin\n"
             "3. Vincristine\n"
             "4. Prednisolone\n\n"
             "我將為您解析該藥物之副作用與注意事項"
    )

def get_drug_detail_message(drug_info):
    """建立藥物詳細資訊的 TextSendMessage"""
    return TextSendMessage(
        text=drug_info["detail_text"],
        emojis=drug_info["emojis"]
    )

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip()
    current_time = datetime.now()

    # 清理過期的使用者狀態（30分鐘後過期）
    cleanup_expired_states(current_time)

    # 處理使用者輸入
    if user_input in DRUG_INFO:
        # 更新使用者狀態
        user_states[user_id] = {
            "selection": user_input,
            "timestamp": current_time,
            "step": "awaiting_a"
        }
        message = TextSendMessage(text=DRUG_INFO[user_input]["prompt"])
    
    elif user_input.lower() == "a":
        user_state = user_states.get(user_id)
        
        if user_state and user_state["step"] == "awaiting_a":
            # 確認選擇的藥物並返回詳細資訊
            drug_number = user_state["selection"]
            message = get_drug_detail_message(DRUG_INFO[drug_number])
            
            # 清除使用者狀態，讓用戶可以重新選擇藥物
            user_states[user_id] = {
                "selection": None,
                "timestamp": current_time,
                "step": "initial"
            }
        else:
            message = TextSendMessage(text="請先選擇藥物編號(1-4)，再輸入a查看詳細資訊。")
    
    else:
        message = get_default_message()

    line_bot_api.reply_message(event.reply_token, message)

def cleanup_expired_states(current_time):
    """清理過期的使用者狀態（30分鐘後過期）"""
    expired_time = current_time - timedelta(minutes=30)
    expired_users = [
        user_id for user_id, state in user_states.items()
        if state["timestamp"] < expired_time
    ]
    for user_id in expired_users:
        del user_states[user_id]

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)