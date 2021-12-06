from flask import Flask,request,abort
from linebot import LineBotApi,WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent,TextMessage,TextSendMessage,LocationMessage, flex_message
from linebot.exceptions import LineBotApiError
from linebot.models import PostbackTemplateAction,CarouselColumn,CarouselTemplate,FollowEvent,LocationMessage,MessageEvent,TemplateSendMessage,TextMessage,TextSendMessage,UnfollowEvent,URITemplateAction,AudioSendMessage,VideoSendMessage,FlexSendMessage,QuickReply,QuickReplyButton,MessageAction,PostbackEvent,PostbackAction
import json
import requests
import time
import os

app=Flask(__name__)
#環境変数の取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
line_bot_api=LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler=WebhookHandler(YOUR_CHANNEL_SECRET)


def analyze_shadowban_data(data, account_name):
    is_touketsu = is_touketsu = is_searchsuggestban = is_searchban = is_ghostban = None # 初期化
    marubatsu = lambda x: "○" if x else "×" # バンされている場合(True)は○、されていない場合(False)は×
    try:
        is_exists = data.get("profile").get("exists") is True
    except:
        pass
    if is_exists is False:
        return f"@{account_name} does not exists!"

    try:
        is_touketsu = marubatsu(data.get("profile").get("protected") is True)
        if is_touketsu == "○":
            return "このアカウントは非公開アカウントです。\nシャドウBANチェックはできません。"
    except:
        pass

    try:
        is_ghostban = marubatsu(data.get("tests").get("ghost").get("ban") is True)
    except:
        pass

    try:
        is_searchban = marubatsu(data.get("tests").get("search") is False)
    except:
        pass

    try:
        is_searchsuggestban = marubatsu(data.get("tests").get("typeahead") is False)
    except:
        pass
    mess = f"BANされている場合は○が表示されます。\n@{account_name} \nSuspend：{is_touketsu} \nSearchSuggestBan：{is_searchsuggestban} \nSearchBan:{is_searchban} \nGhostBan:{is_ghostban}"
    return mess

def check_shadowban(username):
    username = username.replace("@", "").replace("＠", "") # @マーク(全角、半角)を削除
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}
    url = "https://shadowban.hmpf.club/" + username
    try_max = 5 # サイトから取得する最大試行回数
    time_sleep = 10 # 取得に失敗した場合の待機時間
    for i in range(try_max):
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return analyze_shadowban_data(res.json(), username)
        if i == try_max - 1:
            return None
        time.sleep(time_sleep*(i+1))

#テスト用
@app.route("/")
def hello_world():
  return "cheer up!!2"

@app.route("/callback",methods=["POST"])
def callback():
    signature=request.headers["X-Line-Signature"]

    body=request.get_data(as_text=True)
    app.logger.info("Request body"+body)

    try:
        handler.handle(body,signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent,message=TextMessage)
def handle_message(event):
    #入力された文字を取得
    text_in = event.message.text

    if "チェック" in text_in:
        text_in = text_in.replace(" ", "").replace("　", "").replace("チェック", "")
        mess = check_shadowban(text_in)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=mess))
    else:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=event.message.text))

if __name__=="__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0",port=port)