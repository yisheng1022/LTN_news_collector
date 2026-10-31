# from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger, CkipNerChunker
from ckiptagger import WS, POS, data_utils
import pandas as pd
import re


# Initialize drivers
data_utils.download_data_gdown("./") # gdrive-ckip
ws = WS("./data")
pos = POS("./data")
# ner_driver = CkipNerChunker(model="albert-tiny")
df = pd.read_csv("20250101_20261027沈伯洋LTN_news.csv")

df['content'] = df['content'].apply(lambda x: re.sub(r"[^\w\s\u4e00-\u9fa5]", '', str(x)))
news_list = df['content'].tolist()
ws_results = ws(news_list)
pos_results = pos(ws_results)
word_with_pos = []
for one_ws,one_pos in zip(ws_results,pos_results):
    seg_art = ""
    for i in range(len(one_ws)):
        seg_art += one_ws[i] + '_' + one_pos[i] + ' ' 
    word_with_pos.append(seg_art)
df['seg_content'] = word_with_pos
df.to_csv("20250101_20261027沈伯洋LTN_news_seg.csv",index = False,encoding = 'utf-8-sig')
    


