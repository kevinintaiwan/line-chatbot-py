from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])

# Dictionary to store user selections
user_selections = {}

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

    # Step 1: Initial instructions for drug selection
    if user_input == "1":
        user_selections[user_id] = "1"
        message = TextSendMessage(text="輸入a表示膀胱出血、血尿")
    elif user_input == "2":
        user_selections[user_id] = "2"
        message = TextSendMessage(text="輸入a表示心臟功能異常")
    elif user_input == "3":
        user_selections[user_id] = "3"
        message = TextSendMessage(text="輸入a表示神經肌肉症狀")
    elif user_input == "4":
        user_selections[user_id] = "4"
        message = TextSendMessage(text="輸入a表示口腔、喉嚨痛")

    # Step 2: Detailed information based on 'a' selection
    elif user_input == "a":
        previous_selection = user_selections.get(user_id)

        if previous_selection == "1":
            message = TextSendMessage(
                text="藥物的代謝物排泄至尿液後會引起泌尿道，尤其是膀胱的改變，若出現出血性膀胱炎或血尿等現象，請立即回診就醫\n\n"
                     "平時請喝大量開水，並時常排尿，若醫師無特殊指示，建議於晨間服用，降低對膀胱之副作用"
                emojis=[
                    {
                        "index": 10,  # 插入位置，對應到「喝大量開水」中的「水」之後
                        "productId": "5ac21e6c040ab15980c9b444",
                        "emojiId": "104"
                    }
                ]
            )
        elif previous_selection == "2":
            message = TextSendMessage(
                text="若出現相關症狀，如：胸悶疼痛、呼吸困難、眩暈、心律改變等，請立即就醫，且每三個月需監測心臟功能"
            )
        elif previous_selection == "3":
            message = TextSendMessage(
                text="神經肌肉症狀：包括神經痛、四肢痛、麻木感、肌肉痛、步行困難、知覺異常、運動失調等，孩童最容易感受此副作用，通常一般在治療後 6 週消失，但偶爾會有停止治療後仍持續一段長期間之情形。"
            )
        elif previous_selection == "4":
            message = TextSendMessage(
                text="藥物可能導致口腔、喉嚨痛，若出現此症狀請告知醫護人員，並且避免食用刺激口腔和喉嚨的食物，盡量多喝水"
            )
        else:
            message = TextSendMessage(text="請先選擇藥物，然後再輸入a。")

    # Default instructions if input doesn't match any above
    else:
        message = TextSendMessage(
            text="請輸入以下數字以選擇藥物:\n1. Cyclophosphamide\n2. Doxorubicin\n3. Vincristine\n4. Prednisolone\n\n"
                 "我將為您解析該藥物之副作用與注意事項"
        )

    # Reply to the user
    line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
