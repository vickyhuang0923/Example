import uuid
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime

# 初始化 Chrome Driver
service = Service(executable_path="./chromedriver")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# 網站 URL
base_url = "https://www.ptt.cc"
start_page = 38862
pageSum=0
stopSum = 600
start_url = f"{base_url}/bbs/Gossiping/index{start_page}.html"

# 取得現在時間
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 取得網頁內容並解析
def get_soup(url):
    driver.get(url)
    if "over18" in driver.current_url:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "yes"))).click()
    time.sleep(1)  # 等待頁面加載
    page_source = driver.page_source
    return BeautifulSoup(page_source, "html.parser")

# 取得文章列表頁面的所有文章連結
def get_article_links(soup):
    articles = soup.select("div.r-ent div.title a")
    return [a["href"] for a in articles]

# 取得文章內容
def get_article_content(article_url):
    soup = get_soup(f"{base_url}{article_url}")
    titleTag = soup.select_one("meta[property='og:title']")
    title = titleTag["content"] if titleTag else "No Title"
    authorTag = soup.select_one("span.article-meta-value")
    author = authorTag.text if authorTag else "No Author"
    dateTag = soup.select("span.article-meta-value")
    date = dateTag[-1].text if dateTag else "No Date"
    content = soup.select_one("#main-content").text.split("※ 發信站: 批踢踢實業坊(ptt.cc)")[0].strip()
    exclude = soup.select("#main-content div[class^='article-metaline'] span")
    for p in exclude:
      content = content.replace(p.text, '')
    content = re.sub(r'[\r\n\s]', '',content)
    return  {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, content)), #使用uuid3生成唯一ID
        "title": title, 
        "author": author, 
        "date": date,
        "content": content,
        "url": f"{base_url}{article_url}",
        "current_time": get_current_time()
    }

# 爬取所有頁面的文章內容
all_articles = []
current_url = start_url

while True:
    soup = get_soup(current_url)
    article_links = get_article_links(soup)
    for link in article_links:
        try:
            article_content = get_article_content(link)
            if article_content['title'] != "No Title":
                all_articles.append(article_content)
                print(f"已爬取: {article_content['title']}")
        except Exception as e:
            print(f"Error fetching article {link}: {e}")
    # 找到上一頁的連結
    paging = soup.select("div.btn-group.btn-group-paging a")
    prev_page_link = paging[1].get("href") if len(paging) > 1 else None
    if prev_page_link and "index" in prev_page_link:
        pageSum+=1
        current_url = f"{base_url}{prev_page_link}"
    else:
        break
    if pageSum == stopSum:
      break
# 將結果存成 JSON 文件
with open("PTT八卦版內文.json", "w", encoding="utf-8") as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=4)

print(f"共爬取了 {len(all_articles)} 篇文章，已存儲到 PTT八卦版內文.json")
# 共爬取了 11984 篇文章，已存儲到 PTT八卦版內文201-800.json
driver.quit()