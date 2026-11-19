from requests import models
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import pyLDAvis.gensim_models
from gensim import corpora
from gensim.models import LdaModel, CoherenceModel
import json
import textwrap
from typing import Literal, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import config


load_dotenv()
df_with_prob = pd.read_csv('20250101_20261106沈柏洋LTN_news_seg_topic.csv')
df_with_keywords = pd.read_csv('lda_best_topics_k13_keywords.csv')
client_auth = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

class TopicNamingResult(BaseModel):
    """Structured output schema for LDA topic naming."""

    topic_name: str = Field(description="10字以內的中文主題名稱，需具體且具區辨度")
    description: str = Field(description="100字以內的中文命名原因與主題描述")


def gemini_topic_name(content: str) -> str:
    """Call Gemini API to generate a concise topic name and description."""
    system_prompt = textwrap.dedent("""
        # Background
        你會閱讀到多篇關於台灣縣市長選舉的中文文本以及其主題分類的結果，輸入格式為：(主題)_[主題代表詞(以空格分隔)]_[多篇該主題以||分隔的精選文章]。
        由於資料前處理過程的限制，精選文章的內容並無標點符號，且可能包含些許斷詞碎片。

        # Task
        你的任務是綜合閱讀 LDA 主題代表詞以及多篇代表該主題的完整文章，理解該主題的核心焦點後進行命名與說明：
        1. 給予一個 10 字以內的中文主題名稱。名稱必須具體且具辨識度，並聚焦於該主題特有的事件、人物爭議或政策，避免使用「選舉新聞」、「政治動態」等過於籠統的字眼。
        2. 用 100 字以內的中文說明為何如此命名。
        若代表詞與精選文章的語意略有落差，請以精選文章的實質內容為主、代表詞為輔。
    """).strip()

    response = client_auth.models.generate_content(
        model="gemini-3.8-flash",
        contents=content,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=TopicNamingResult,
        ),
    )
    return response.text


results = []
for topic_num in df_with_prob['topic'].unique():
    tmp_df = df_with_prob[df_with_prob['topic'] == topic_num]
    tmp_df = tmp_df.sort_values(by=['topic_prob'], ascending=False).head(10)
    topic_keywords = df_with_keywords[df_with_keywords['Topic_ID'] == f'主題 {topic_num+1}']

    if topic_keywords.empty:
        continue

    print(topic_keywords)
    tmp_content = (
        f"{topic_keywords['Topic_ID'].iloc[0]}_"
        f"{topic_keywords['Top_Keywords'].iloc[0]}_"
        f"{'||'.join(tmp_df['content'].astype(str).tolist())}"
    )
    result_json = gemini_topic_name(tmp_content)
    print(result_json)
    results.append({
        "topic_id": topic_keywords['Topic_ID'].iloc[0],
        "result": json.loads(result_json),
    })
result_df = pd.DataFrame(results)
result_df.to_csv('gemini_topic_namming_result.csv',encoding='utf-8-sig',index = False)
