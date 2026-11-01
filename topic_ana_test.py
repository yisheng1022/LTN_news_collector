from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from ckiptagger import WS, POS, data_utils
import pandas as pd
import re
import pyLDAvis.gensim_models
import pyLDAvis
from gensim import corpora
from gensim.models import LdaModel


def seg_model_choose(method = 'tagger'):
    if method == 'tagger':
        # data_utils.download_data_gdown("./") # gdrive-ckip
        ws = WS("./data")
        pos = POS("./data")
        return ws,pos
    elif method == 'transformers':
        ws_driver  = CkipWordSegmenter(model="bert-tiny",device=0)
        pos_driver = CkipPosTagger(model="bert-tiny",device=0)
        return ws_driver,pos_driver

def seg_function(df, method = 'transformers'):
    df['content'] = df['content'].apply(lambda x: re.sub(r"[^\w\s\u4e00-\u9fa5]", '', str(x)))
    news_list = df['content'].tolist()
    ws, pos = seg_model_choose(method)
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
    return df

def LDA_analysis(df,k = 5):
    dictionary = corpora.Dictionary(processed_docs)
    corpus = [dictionary.doc2bow(text) for text in processed_docs]
    num_topics = 2

    lda_model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        random_state=42,       # 固定隨機種子以確保結果可重複
        passes=10,             # 訓練語料庫的迭代次數
        alpha='auto'           # 自動調整文檔-主題分佈的超參數
    )

df = pd.read_csv("20250101_20261027沈伯洋LTN_news.csv")
df = seg_function(df)




