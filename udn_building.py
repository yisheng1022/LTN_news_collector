import pandas as pd
import requests
from bs4 import BeautifulSoup as BS
import json

# variable explanation = 
# cate_id = 不同的版位分類(要聞、全球...)
# news_type = 版位下的不同分類(最新、政治、軍事...)
# channelID = 目前看到都是2
# totalRecNo = 設越高，能抓到的文章越多

def get_news_content(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BS(res.text, 'html.parser')
        paragraphs = soup.select('section.article-content__editor p')
        return ''.join([p.text.strip() for p in paragraphs if p.text.strip()])
    except Exception as e:
        print(f"爬取內文失敗 ({url}): {e}")
        return ""

def json_main(cate_id, news_type = 'cate_latest_news', channelID = 2, totalRecNo = 2000, fetch_content = True):
    end = False
    page = 0
    news_records = []
    
    while not end:
        json_url = f'https://udn.com/api/more?page={page}&channelId={channelID}&type={news_type}&cate_id={cate_id}&totalRecNo={totalRecNo}'
        json_req = requests.get(json_url).text
        json_data = json.loads(json_req)
        end = json_data.get('end', True)
        
        for one_news in json_data.get('lists', []):
            news_url = 'https://udn.com' + one_news.get('titleLink', '')
            record = {
                'url': news_url,
                'title': one_news.get('title'),
                'datetime': one_news.get('time', {}).get('date'),
                'category': one_news.get('story_list').split('_')[1].strip(),
                'sub_category': one_news.get('story_list').split('_')[2].strip(),
            }
            if fetch_content:
                record['content'] = get_news_content(news_url)
            news_records.append(record)

        if end:
            break
        print(f'已完成第 {page} 頁的爬取，目前累計 {len(news_records)} 筆')
        page += 1

    df = pd.DataFrame(news_records)
    return df

def main():
    url = 'https://udn.com/news/story/6656/9830973?from=udn-catelistnews_ch2'
    
    print(get_news_content(url))
main()





#要聞_最新(totalRecNo可改)
# https://udn.com/api/more?page=70&channelId=2&type=cate_latest_news&cate_id=6638&totalRecNo=2000
# https://udn.com/api/more?page=2&channelId=2&type=cate_latest_news&cate_id=7225&totalRecNo=966
