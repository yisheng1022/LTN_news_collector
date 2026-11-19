import json
import re
import requests

session = requests.Session()

# 基礎瀏覽器標頭
base_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://tw.news.yahoo.com/",
}
session.headers.update(base_headers)

# 步驟 1：取得首頁 HTML
target_url = "https://tw.news.yahoo.com/politics/"
res = session.get(target_url)
if res.status_code != 200:
    raise Exception(f"無法存取首頁，狀態碼：{res.status_code}")

html = res.text

# 步驟 2：解析 PRID 與 UUIDs
prid_match = re.search(r'"prid":\s*"([^"]+)"', html)
current_prid = prid_match.group(1) if prid_match else "2gr89ihlelr13"

uuid_match = re.search(r'"uuids":\s*(\[[^\]]+\])', html)
if not uuid_match:
    raise Exception("找不到預載的新聞 UUID 清單！")

all_uuids = json.loads(uuid_match.group(1))
print(f"[成功] 取得 PRID: {current_prid}，預載 UUID 數量: {len(all_uuids)}")

# 關鍵點 1：手動取出前 20 個 UUID，不要一次塞 150 個進去觸發後端超時或記憶體溢出
PAGE_SIZE = 10
current_uuids = all_uuids[:PAGE_SIZE]

# 步驟 3：設定 API 與參數
api_url = "https://tw.news.yahoo.com/_td-news/api/resource"

# 請替換為你瀏覽器有效的 Cookie 與 Crumb
CRUMB = "LYy0oHaTb7j"
COOKIE_STR = (
    "axids=gam=y-Y91TYxpE2uICtPhpyTBKcfkprUeqSwqC~A&dv360=eS1raUlZdU9ORTJ1Ri5kMmIzZG1ySnpPaUJxNl9HczJUZH5B&ydsp=y-v5EfKAFE2uLuyJqo0lLCGAD_cItqnRE6~A&tbla=y-dQc5Z0FE2uLD2uaXWyu4Fn4MRkD0l.x3~A; "
    "A1=d=AQABBEL_gGYCEFOzXmDp_F51xwEIw9iz2CMFEgEBCAHg6moma72qQDIB_eMDAAcIQv-AZtiz2CM&S=AQAAAvRifqvdBNTStuGRcZxmET8; "
    "A3=d=AQABBEL_gGYCEFOzXmDp_F51xwEIw9iz2CMFEgEBCAHg6moma72qQDIB_eMDAAcIQv-AZtiz2CM&S=AQAAAvRifqvdBNTStuGRcZxmET8; "
    "GUC=AQEBCAFq6uBrJkIbWwQF&s=AQAAAJ2ah9XI&g=aumPxA; cmp=t=1793776655&j=0&u=1---;"
)

# 恢復完整必要的 URL 參數（避免 context 檢核失敗）
params = {
    "bkt": "N19TH,election-summary,tw-news-ga-control,tw-newsapp-ga1,news-ga4-control",
    "crumb": CRUMB,
    "device": "desktop",
    "ecma": "modern",
    "feature": "oathPlayer,enableEvPlayer,enableGAMAds,enableGAMEdgeToEdge,videoDocking,enableNewsSearch,enableNewsSearchHistory,enableElectionTopicEntry",
    "intl": "tw",
    "lang": "zh-Hant-TW",
    "partner": "none",
    "prid": current_prid,
    "region": "TW",
    "site": "news",
    "tz": "Asia/Taipei",
    "ver": "2.3.3382",
}

api_headers = {
    "Content-Type": "application/json",
    "Origin": "https://tw.news.yahoo.com",
    "Referer": "https://tw.news.yahoo.com/",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": COOKIE_STR,
}

# 關鍵點 2：保留伺服器邏輯相依欄位，但把 ads 模組乾淨關閉
payload = {
    "requests": {
        "g0": {
            "resource": "ApacStreamService",
            "operation": "read",
            "params": {
                "ui": {
                    "comments": True,
                    "image_quality_override": True,
                    "link_out_allowed": True,
                    "ntk_bypassA3c": True,
                    "pubtime_maxage": 0,
                    "relative_links": True,
                    "show_comment_count": True,
                    "smart_crop": True,
                    "storyline_count": 2,
                    "storyline_min": 2,
                    "summary": True,
                    "thumbnail_size": 100,
                    "view": "mega"
                },
                "category": "LISTID:a9c50387-f6ae-48d3-8d19-6d22ace83050",
                "cgParams": {
                    "overrides": {
                        "lumosStreamInput": {
                            "lumosId": "P13NPolitics",
                            "module": "news"
                        }
                    }
                },
                "forceJpg": True,
                "releasesParams": {
                    "limit": PAGE_SIZE,
                    "offset": 0
                },
                "ncpParams": {
                    "query": {
                        "adsSlotsEnabled": False,  # 關閉廣告插槽
                        "namespace": "abu",
                        "id": "lumos-stream",
                        "configId": "politics",
                        "clientId": "abu-web"
                    },
                    "body": {
                        "gqlVariables": {
                            "lumosStream": {
                                "pagination": {
                                    "nextParams": {
                                        "lumosStreamInput": {
                                            "page": {
                                                "snippetCount": PAGE_SIZE,
                                                "uuids": current_uuids # 只放本次請求的 20 個
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "offnet": {"include_lcp": True},
                "use_content_site": True,
                "useNCP": True,
                "useCG": True,
                "useCGV2": True,
                "pageContext": {
                    "site": "news",
                    "section": "politics",
                    "topic": "default",
                    "pageType": "minihome",
                    "renderTarget": "default"
                },
                "content_type": "section",
                "storeData": {
                    "stream_total": 170,
                    "stream_remaining": 150,
                    "stream_requested": PAGE_SIZE
                }
            }
        }
    },
    "context": {
        "feature": "oathPlayer,enableEvPlayer,enableGAMAds,enableGAMEdgeToEdge,videoDocking,enableNewsSearch,enableNewsSearchHistory,enableElectionTopicEntry",
        "bkt": ["N19TH", "election-summary", "tw-news-ga-control", "tw-newsapp-ga1", "news-ga4-control"],
        "crumb": CRUMB,
        "device": "desktop",
        "intl": "tw",
        "lang": "zh-Hant-TW",
        "partner": "none",
        "prid": current_prid,
        "region": "TW",
        "site": "news",
        "tz": "Asia/Taipei",
        "ver": "2.3.3382",
        "ecma": "modern"
    }
}

# 步驟 4：送出請求
response = session.post(api_url, params=params, json=payload, headers=api_headers)

print("狀態碼:", response.status_code)
if response.status_code == 200:
    data = response.json()
    print(data)
    items = data.get("g0", {}).get("data", {}).get("stream_items", [])
    
    articles = [i for i in items if i.get("type") == "article"]
    print(f"成功取得 {len(articles)} 篇純新聞文章！\n")
    
    for idx, art in enumerate(articles, 1):
        print(f"{idx}. [{art.get('publisher')}] {art.get('title')} {art.get('link')}")
else:
    print(response.text[:500])