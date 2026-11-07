import pandas as pd
import requests
from bs4 import BeautifulSoup as BS
import json
import time
import os
import random

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

def udn_vote(page = 1,skip = 0,end = False):
    news_list = []
    empty_count = 1
    while not end:
        vote_url = f'https://udn.com/vote2026/ajax/realtime?count=99999&skip={skip}&page={page}'
        print(vote_url)
        vote_json = requests.get(vote_url).text
        vote_data = json.loads(vote_json)
        end = vote_data.get('end', True)
        news_data = vote_data.get('lists', [])
        if len(news_data) == 0:
            empty_count += 1
            if empty_count > 3:
                break

        for one_vote_news in news_data:
            # print(one_vote_news['url'])
            news_url = 'https://udn.com' + one_vote_news.get('url', '')
            record = {
                'url': news_url,
                'title': one_vote_news.get('title'),
                'date': one_vote_news.get('time', {}).get('date').split(' ')[0],
                'pub_time': one_vote_news.get('time', {}).get('date').split(' ')[1],
                'content': get_vote_news(news_url),
            }
            news_list.append(record)
        page += 1
        skip += 12
        df = pd.DataFrame(news_list)
        if os.path.isfile("Udn_vote.csv"):
            df.to_csv("Udn_vote.csv",header = False,index = False,mode = "a+")
        else:
            df.to_csv("Udn_vote.csv",header = True,index = False,mode = "w")
        time.sleep(random.randint(1,3))

def udn_normal_main(cate_id, news_type = 'cate_latest_news', sub_id = '', channelID = 2, totalRecNo = 2000, fetch_content = True):
    end = False
    page = 0
    news_records = []
    
    while not end:
        json_url = f'https://udn.com/api/more?page={page}&channelId={channelID}&type={news_type}&cate_id={cate_id}&sub_id={sub_id}&totalRecNo={totalRecNo}'
        # print(json_url)
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
        df = pd.DataFrame(news_records)
        if os.path.isfile("Udn_{}.csv".format(cate_id)):
            df.to_csv("Udn_{}.csv".format(cate_id),header = False,index = False,mode = "a+")
        else:
            df.to_csv("Udn_{}.csv".format(cate_id),header = True,index = False,mode = "w")
        page += 1


def main():
    choice = input("請選擇(1:一般新聞,2:投票新聞):")
    if choice == '1':
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
        udn_normal_main(cate_id, news_type, sub_id, fetch_content)
    elif choice == '2':
        udn_vote(page = 450, skip = 5388)

main()





#要聞_最新(totalRecNo可改)
# https://udn.com/api/more?page=70&channelId=2&type=cate_latest_news&cate_id=6638&totalRecNo=2000
# https://udn.com/api/more?page=2&channelId=2&type=cate_latest_news&cate_id=7225&totalRecNo=966
