from matplotlib import pyplot as plt
import pandas as pd
from ckiptagger import WS
from collections import Counter
import re

def hot_key_word(df,key_word_list = ['沈伯洋','蔣萬安']):
    for a_keyword in key_word_list:
        df[f'keyword_{a_keyword}_count'] = df['content'].apply(lambda x: str(x).count(a_keyword))
    return df

def pre_processing_data():
    mock_df = pd.read_csv(r'20250101_20261027沈伯洋LTN_news.csv')
    mock_df = mock_df.head(1000)
    mock_df['char_count'] = mock_df['content'].apply(lambda x: len(x))
    mock_df = hot_key_word(mock_df)
    aaa = mock_df['content'].to_list()

    ws = WS("./data")
    ws_result = ws(aaa)

    seg_content_list = []
    for one_content in ws_result:
        tmp_list = []
        for a_word in one_content:
            if re.search(r'[\w]',a_word) and len(a_word)>1:
                tmp_list.append(a_word)
        seg_content_list.append('|'.join(tmp_list))
        
    mock_df['clean_tokens'] = seg_content_list
    mock_df.to_csv('for_cdna_test.csv',index = False,encoding = 'utf-8-sig')
    return mock_df

def cal_tf(df):
    join_content_list = []
    for one_news in df['clean_tokens']:
        join_content_list.extend(one_news.split('|'))
    tf_result = Counter(join_content_list)
    print(tf_result.most_common(15))
    return tf_result.most_common(15)

def draw_tf_result():
    pass
mock_df = pre_processing_data()
tf_dict = cal_tf(mock_df)
most_tf = pd.DataFrame(tf_dict,columns = ['words','counts'])
most_tf.to_csv('most15tf.csv',index = False,encoding = 'utf-8-sig')

