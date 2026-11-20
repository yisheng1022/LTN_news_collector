from requests import models
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import pyLDAvis
import pyLDAvis.gensim_models
from gensim import corpora
from gensim.models import LdaModel, CoherenceModel

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

def seg_model_choose(method='tagger'):
    if method == 'tagger':
        from ckiptagger import WS, POS, data_utils
        # data_utils.download_data_gdown("./") # gdrive-ckip
        ws = WS("./data")
        pos = POS("./data")
        return ws, pos
    elif method == 'transformers':
        from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
        ws_driver = CkipWordSegmenter(model="bert-tiny", device=0)
        pos_driver = CkipPosTagger(model="bert-tiny", device=0)
        return ws_driver, pos_driver


def seg_function(df, method='transformers', output_file="20250101_20261027沈伯洋LTN_news_seg.csv"):
    df['content'] = df['content'].apply(lambda x: re.sub(r"[a-zA-Z]", '', str(x)))
    df['content'] = df['content'].apply(lambda x: re.sub(r"[^\w\s\u4e00-\u9fa5]", '', str(x)))
    news_list = df['content'].tolist()
    ws, pos = seg_model_choose(method)
    ws_results = ws(news_list)
    pos_results = pos(ws_results)
    
    word_with_pos = []
    for one_ws, one_pos in zip(ws_results, pos_results):
        seg_art = ""
        for i in range(len(one_ws)):
            seg_art += f"{one_ws[i]}_{one_pos[i]} "
        word_with_pos.append(seg_art.strip())
        
    df['seg_content'] = word_with_pos
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 斷詞與標註完成，已存至 {output_file}")
    return df


def prepare_corpus(df, filter_pos_blacklist=('DE', 'SHI', 'WHITESPACE', 'PERIODCATEGORY', 'COMMACATEGORY'), min_len=2):
    process_list = []
    for text in df['seg_content'].dropna():
        cleaned_list = []
        for item in str(text).strip().split():
            if '_' in item:
                parts = item.rsplit('_', 1)
                word, pos = parts[0], parts[1]
                # 過濾指定虛詞詞性與長度過短字詞
                if pos not in filter_pos_blacklist and len(word) >= min_len:
                    cleaned_list.append(word)
        if cleaned_list:
            process_list.append(cleaned_list)

    # 建立詞典
    dictionary = corpora.Dictionary(process_list)
    dictionary.filter_extremes(no_below=2)
    
    # 建立 BoW 語料庫
    corpus = [dictionary.doc2bow(text) for text in process_list]
    
    return dictionary, corpus, process_list


def find_best_lda_by_coherence(
    df,
    topic_range=range(2, 15),
    coherence_type='c_v',
    passes=10,
    random_state=42,
    save_prefix="lda_best"
):
    """
    透過 Coherence Score (主題一致性) 尋找最佳主題數 k，並自動儲存最佳模型與視覺化結果。
    """
    print("📦 正在準備語料庫與詞典...")
    dictionary, corpus, process_list = prepare_corpus(df)
    
    coherence_records = []
    best_score = -1.0
    best_k = None
    best_model = None

    print(f"🔍 開始測試主題數範圍: {list(topic_range)}，評估指標: {coherence_type}")
    print("=" * 60)

    for k in topic_range:
        print(f"⏳ 正在訓練 k={k} 的 LDA 模型...", end="", flush=True)
        model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=k,
            random_state=random_state,
            passes=passes,
            alpha='auto',
            per_word_topics=True
        )

        # 計算 Coherence Score
        coherence_model = CoherenceModel(
            model=model,
            texts=process_list,
            dictionary=dictionary,
            coherence=coherence_type
        )
        score = coherence_model.get_coherence()
        print(f"  Coherence ({coherence_type}): {score:.4f}")

        coherence_records.append({'k': k, 'coherence_score': score, 'model': model})

        if score > best_score:
            best_score = score
            best_k = k
            best_model = model

    print("=" * 60)
    print(f"🏆 最佳主題數為: k = {best_k}，最高 Coherence 分數為: {best_score:.4f}")
    print("\n💾 正在儲存最佳模型與分析報表...")

    # 1. 儲存最佳 LDA 模型與詞典
    model_path = f"{save_prefix}_model_k{best_k}.model"
    dict_path = f"{save_prefix}_dict.dict"
    best_model.save(model_path)
    dictionary.save(dict_path)
    print(f"  [1/5] 最佳模型已儲存: {model_path} / {dict_path}")

    # 2. 儲存主題數評估記錄 CSV
    scores_df = pd.DataFrame([{'k': r['k'], 'coherence_score': r['coherence_score']} for r in coherence_records])
    scores_csv = f"{save_prefix}_coherence_scores.csv"
    scores_df.to_csv(scores_csv, index=False, encoding='utf-8-sig')
    print(f"  [2/5] 各主題分數表已儲存: {scores_csv}")

    # 3. 繪製並儲存 Coherence 趨勢折線圖
    plt.figure(figsize=(10, 6))
    plt.plot(scores_df['k'], scores_df['coherence_score'], marker='o', color='royalblue', linewidth=2)
    plt.axvline(x=best_k, color='red', linestyle='--', label=f'Best k={best_k} (Score={best_score:.4f})')
    plt.title(f"LDA Topic Coherence Evaluation ({coherence_type})", fontsize=14)
    plt.xlabel("Number of Topics (k)", fontsize=12)
    plt.ylabel(f"Coherence Score ({coherence_type})", fontsize=12)
    plt.xticks(list(topic_range))
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    trend_img = f"{save_prefix}_coherence_trend.png"
    plt.savefig(trend_img, dpi=300)
    plt.close()
    print(f"  [3/5] 主題一致性趨勢圖已儲存: {trend_img}")

    # 4. 匯出最佳主題之 Top 關鍵詞表
    topic_keywords = []
    for topic_id in range(best_k):
        top_words = [word for word, _ in best_model.show_topic(topic_id, topn=15)]
        topic_keywords.append({
            'Topic_ID': f"主題 {topic_id + 1}",
            'Top_Keywords': ", ".join(top_words)
        })
    topics_df = pd.DataFrame(topic_keywords)
    topics_csv = f"{save_prefix}_topics_k{best_k}_keywords.csv"
    topics_df.to_csv(topics_csv, index=False, encoding='utf-8-sig')
    print(f"  [4/5] 最佳主題關鍵詞已儲存: {topics_csv}")

    # 5. 產出 pyLDAvis 互動式網頁
    try:
        vis_html = f"{save_prefix}_vis_k{best_k}.html"
        vis = pyLDAvis.gensim_models.prepare(best_model, corpus, dictionary, sort_topics=False)
        pyLDAvis.save_html(vis, vis_html)
        print(f"  [5/5] pyLDAvis 互動可視化網頁已儲存: {vis_html}")
    except Exception as e:
        print(f"  ⚠️ pyLDAvis 匯出失敗: {e}")

    print("\n🎉 全部最佳成果儲存完畢！")
    return best_model, best_k, best_score, scores_df

def predict_topic(model,dictionary,doc_content, with_pos = True):
    filter_pos_blacklist=('DE', 'SHI', 'WHITESPACE', 'PERIODCATEGORY', 'COMMACATEGORY')
    cleaned_list = []

    if with_pos == True:
        for item in str(doc_content).strip().split():
            if '_' in item:
                parts = item.rsplit('_', 1)
                word, pos = parts[0], parts[1]
                if pos not in filter_pos_blacklist and len(word) > 1:
                    cleaned_list.append(word)
    else:
        cleaned_list = doc_content.strip().split()
    
    doc_bow = dictionary.doc2bow(cleaned_list)
    doc_topics = model.get_document_topics(doc_bow, minimum_probability=0)

    main_topic = max(doc_topics, key=lambda x: x[1])
    return main_topic[0], round(float(main_topic[1]),3)

def merge_all_news(file_list,merge_file_name):
    df_list = []
    for one_df in file_list:
        df_list.append(pd.read_csv(one_df))
    all_news_df = pd.concat(df_list,ignore_index=True)
    all_news_df.drop_duplicates(subset=['url'],inplace=True,keep='first')
    all_news_df.to_csv(merge_file_name,index = False, encoding = 'utf-8-sig')


def draw_topic_distribute(df):

    import numpy as np
    import matplotlib.dates as mdates
    import ast

    topic_name_df = pd.read_csv('gemini_topic_namming_result.csv')
    topic_name_df['original_topic_num'] = topic_name_df['topic_id'].apply(lambda x: int(x.split(' ')[1].strip())-1)
    topic_name_df = topic_name_df.sort_values('original_topic_num')
    topic_name_df['tmp_chinese_name'] = topic_name_df['result'].apply(lambda x: ast.literal_eval(x)['topic_name'])
    topic_name_df['topic_chinese_name'] = topic_name_df['original_topic_num'].astype(str) + '_' + topic_name_df['tmp_chinese_name']
    topic_dict = dict(zip(topic_name_df['original_topic_num'], topic_name_df['topic_chinese_name']))

    df.dropna(subset = ['date'],ignore_index=True,inplace = True)
    df['pub_date'] = df['date'].apply(lambda x: str(x).split(' ')[0])
    df['pub_time'] = df['date'].apply(lambda x: str(x).split(' ')[1])
    
    df['pub_date'] = pd.to_datetime(df['pub_date'], format = "%Y/%m/%d")
    df = df[df['pub_date'] > '2025-12-31']
    df['topic_name'] = df['topic'].map(topic_dict)
    count_df = df.groupby(['pub_date', 'topic_name']).size().unstack(fill_value=0).asfreq('D', fill_value=0)
    ordered_cols = [c for c in topic_name_df['topic_chinese_name'] if c in count_df.columns]
    count_df = count_df[ordered_cols]

    smooth_df = count_df.rolling(window=7, min_periods=1).mean()

    num_topics = len(count_df.columns)
    colors = [plt.cm.turbo(i) for i in np.linspace(0, 0.95, num_topics)]
    linestyles = ['-', '--']  # 前後交替實線與虛線，增強辨識度

    plot_configs = [
        (count_df, '沈伯洋各主題隨時間變化趨勢（每日原始數據）', '新聞篇數（每日）'),
        (smooth_df, '沈伯洋各主題隨時間變化趨勢（7 日移動平均）', '新聞篇數（7日均值）'),
    ]

    for data_df, title, ylabel in plot_configs:
        fig, ax = plt.subplots(figsize=(16, 9),layout='constrained')

        for idx, col in enumerate(data_df.columns):
            ax.plot(
                data_df.index,
                data_df[col],
                label=col,
                color=colors[idx],
                linestyle=linestyles[idx % 2],
                linewidth=1.8
            )

        ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_minor_locator(mdates.DayLocator(interval=7))
        ax.tick_params(axis='x', rotation=45, labelsize=9)

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('日期', fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8, frameon=True)
        # plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    # file_list = ['20261027_20261106沈伯洋LTN_news.csv','20250101_20261027沈伯洋LTN_news.csv']
    # merge_all_news(file_list,'20250101_20261106沈柏洋LTN_news.csv')
    seg_csv_file = "20250101_20261106沈柏洋LTN_news.csv_seg.csv"
    raw_csv_file = "20250101_20261106沈柏洋LTN_news.csv"

    # # 若已有斷詞檔則直接讀取，避免重複執行費時的斷詞運算
    # if os.path.exists(seg_csv_file):
    #     print(f"📂 偵測到已存在的斷詞資料: {seg_csv_file}，直接載入...")
    #     df = pd.read_csv(seg_csv_file)
    # else:
    #     print(f"📂 讀取原始資料 {raw_csv_file} 並執行斷詞...")
    #     df = pd.read_csv(raw_csv_file)
    #     df = seg_function(df, method='transformers', output_file=seg_csv_file)

    # # 執行 Coherence 評估並自動儲存最佳結果（例如測試主題數 k = 2 到 14）
    # best_model, best_k, best_score, scores_df = find_best_lda_by_coherence(
    #     df=df,
    #     topic_range=range(5, 20),  # 可依需求調整測試的主題數量範圍
    #     coherence_type='c_v',     # 推薦 'c_v' 指標（亦可使用 'u_mass'）
    #     passes=10,
    #     random_state=42,
    #     save_prefix="lda_best"
    # )

    # df = pd.read_csv("20250101_20261106沈柏洋LTN_news.csv_seg.csv")
    # lda_model = LdaModel.load("lda_best_model_k13.model")
    # lda_dictionary =corpora.Dictionary.load("lda_best_dict.dict")
    # df['topic'] = df['seg_content'].apply(lambda x: predict_topic(lda_model,lda_dictionary, x))
    # topic_list = []
    # prob_list = []
    # for one_seg_content in df['seg_content']:
    #     topic_num, prob = predict_topic(lda_model,lda_dictionary,one_seg_content)
    #     topic_list.append(topic_num)
    #     prob_list.append(prob)
    # df['topic'] = topic_list
    # df['topic_prob'] = prob_list
    # print(df['topic'].value_counts())
    # df.to_csv("20250101_20261106沈柏洋LTN_news_seg_topic.csv", index=False,encoding = "utf-8-sig")

    df = pd.read_csv("20250101_20261106沈柏洋LTN_news_seg_topic.csv")
    draw_topic_distribute(df)