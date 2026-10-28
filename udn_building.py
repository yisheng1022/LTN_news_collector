import pandas as pd
import requests
from bs4 import BeautifulSoup as BS
import json
import time

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

def get_vote_news(vote_url):
    try:
        res = requests.get(vote_url, timeout=10)
        soup = BS(res.text, 'html.parser')
        paragraphs = soup.select('article.story_article p')
        return ''.join([p.text.strip() for p in paragraphs if p.text.strip()])
    except Exception as e:
        print(f"爬取內文失敗 ({vote_url}): {e}")
        return ""

def json_vote(page = 1, is_more = True):
    news_list = []
    while is_more:
        vote_url = f'https://udn.com/vote2026/ajax/realtime?count=7787&skip=0&page={page}'
        vote_json = requests.get(vote_url).text
        vote_data = json.loads(vote_json)
        is_more = vote_data.get('end', True)
        for one_vote_news in vote_data.get('lists', []):
            print(one_vote_news['url'])
            news_url = 'https://udn.com' + one_vote_news.get('url', '')
            record = {
                'url': news_url,
                'location': one_vote_news.get('location'),
                'date': one_vote_news.get('time', {}).get('date').split(' ')[0],
                'pub_time': one_vote_news.get('time', {}).get('date').split(' ')[1],
                'content': get_vote_news(news_url),
            }
            news_list.append(record)
        page += 1
    df = pd.DataFrame(news_list)
    return df

def json_main(cate_id, news_type = 'cate_latest_news', sub_id = '', channelID = 2, totalRecNo = 2000, fetch_content = True):
    end = False
    page = 0
    news_records = []
    
    while not end:
        json_url = f'https://udn.com/api/more?page={page}&channelId={channelID}&type={news_type}&cate_id={cate_id}&sub_id={sub_id}&totalRecNo={totalRecNo}'
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
    cate_id = input("請輸入版位代碼(6638:要聞,7225:全球,6639:社會):")
    news_type = input("請輸入新聞類別(latest:最新,sub:其他):")
    if news_type == 'latest':
        news_type = 'cate_latest_news'
    elif news_type == 'sub':
        news_type = 'subcate_articles'
        sub_id = input("請輸入次分類代碼(124652:要聞選戰,6656:要聞政治,10930要聞軍事,124061:全球中東戰火,6809全球國際焦點):")

    fetch_content = input("是否需要內文？(y/n)")
    if fetch_content == 'y':
        fetch_content = True
    else:
        fetch_content = False
    json_main(cate_id, news_type, sub_id, fetch_content)

main()
# json_vote()
get_vote_news('https://udn.com/vote2026/story/124652/9838052')





#要聞_最新(totalRecNo可改)
# https://udn.com/api/more?page=70&channelId=2&type=cate_latest_news&cate_id=6638&totalRecNo=2000
# https://udn.com/api/more?page=2&channelId=2&type=cate_latest_news&cate_id=7225&totalRecNo=966
