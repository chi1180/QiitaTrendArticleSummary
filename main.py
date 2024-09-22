import os
import sys

PROJECT_NAME = os.path.dirname(os.path.abspath(__file__)).split("\\")[-1]  # __file__ will be undefined if it's not executed as a file.

import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from time import sleep
driver = webdriver.Chrome()

from line_notify import LineNotify
LINE_NOTIFY_TOKEN = os.environ["LINE_NOTIFY_TOKEN"]
line = LineNotify(LINE_NOTIFY_TOKEN)
message = ""

import google.generativeai as genai
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

import requests
QIITA_TREND_URL = "https://qiita.com"
QIITA_ENDPOINT = 'https://qiita.com/api/v2/items'
QIITA_WRITE_TOKEN = os.environ["QIITA_WRITE_TOKEN"]
headers = {
    "Authorization": "Bearer " + QIITA_WRITE_TOKEN,
    "Content-Type": "application/json"
}
article_data = {
    "title": "Qiita のトレンド記事を要約してまとめたモノ（さぼり）",
    "body": "",
    "private": False,
    "tags": [
        { "name": "Qiita"},
        { "name": "トレンド"},
        { "name": "AI"},
        { "name": "要約"},
    ]
}
qiita_drafted_article_url = ""

def main():
    global qiita_drafted_article_url

    driver.get(QIITA_TREND_URL)
    sleep(4)

    article_links =  [ article_link.get_attribute("href") for article_link in driver.find_elements(By.CLASS_NAME, "style-32d82q")]
    for index, article_link in enumerate(article_links):
        driver.get(article_link)
        sleep(4)
        title = driver.find_element(By.CLASS_NAME, "style-wo2a1i").text
        text = driver.find_element(By.CLASS_NAME, "mdContent-inner").text
        res = model.generate_content("以下の記事はテックブログの内容である。簡潔に要約し、要約した内容の身を出力せよ。\n\n" + text)

        article_data["body"] += f"# [{title}]({article_link})\n\n{res.text}\n\n"
        print(f"No.{index + 1}\n# [{title}]({article_link})\n\n{res.text}\n\n")
    driver.quit()

    res = requests.post(QIITA_ENDPOINT, headers=headers, json=article_data)
    if res.status_code == 201:
        qiita_drafted_article_url = res.json().get("url")
    else:
        sys.exit()

if __name__ == "__main__":
    try:
        main()
        message = f"\n無事に{PROJECT_NAME}の処理が完了しました。投稿された記事は {qiita_drafted_article_url} より確認が可能です。"
    except Exception as e:
        message = f"\n{PROJECT_NAME}の処理の実行中にエラーが発生した模様です。\n\n{str(e)}"
    finally:
        line.send(message)

