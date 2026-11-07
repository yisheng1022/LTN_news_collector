import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

ltn_df = pd.read_csv(r'E:\vpy\LTN\LTN_news_collector\20250101_20261027沈伯洋LTN_news_seg_topic.csv')
udn_df = pd.read_csv(r'Udn_vote_drop.csv')
udn_df = udn_df[udn_df['content'].str.contains('沈伯洋',na=False)]
udn_df.to_csv('Udn_vote_沈伯洋.csv',index = False,encoding = 'utf-8-sig')

ltn_df.dropna(subset = ["date"],inplace = True)
ltn_df['day'] = ltn_df['date'].apply(lambda x: str(x).split(' ')[0])
ltn_df['day'] = pd.to_datetime(ltn_df['day'])
ltn_df = ltn_df[ltn_df['day'] >= '2026-01-01']
count_df = ltn_df.groupby(['day', 'topic']).size().unstack(fill_value=0).reset_index()
count_df.set_index("day",inplace = True)
print(count_df.columns)
# 載入主題關鍵字讓標籤更有意義
topic_kw = pd.read_csv('lda_best_topics_k18_keywords.csv')
label_map = {
    i: f"{row['Topic_ID']} ({row['Top_Keywords'].split(',')[0].strip()})"
    for i, row in topic_kw.iterrows()
}
count_df.rename(columns=label_map, inplace=True)

# 7 日移動平均以消除每日高頻雜訊
smooth_df = count_df.rolling(window=7, min_periods=1).mean()

# -------------------------------------------------------------
# 方案一：單張大折線圖（18 種不重複色彩 + 實虛線交替 + X 軸每 14 天）
# -------------------------------------------------------------
import numpy as np

fig, ax = plt.subplots(figsize=(16, 9))

# 使用 Turbo 色盤產生 18 種高對比且不重複的顏色
num_topics = len(smooth_df.columns)
colors = [plt.cm.turbo(i) for i in np.linspace(0, 0.95, num_topics)]
linestyles = ['-', '--'] * 9  # 前後交替實線與虛線，增強辨識度

for idx, col in enumerate(smooth_df.columns):
    ax.plot(
        smooth_df.index, 
        smooth_df[col], 
        label=col, 
        color=colors[idx], 
        linestyle=linestyles[idx],
        linewidth=1.8
    )

# X 軸每 14 天標示一次主要日期，每 7 天打次要刻度
ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.xaxis.set_minor_locator(mdates.DayLocator(interval=7))
ax.tick_params(axis='x', rotation=45, labelsize=9)

ax.set_title('沈伯洋各主題隨時間變化趨勢（7 日移動平均）', fontsize=14, fontweight='bold')
ax.set_xlabel('日期', fontsize=11)
ax.set_ylabel('新聞篇數（7日均值）', fontsize=11)
ax.grid(True, linestyle='--', alpha=0.5)

# 圖例放在圖表右側外部，分成 1 欄排列避免重疊
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9, frameon=True)
plt.tight_layout()
plt.show()

# -------------------------------------------------------------
# 方案二（若依然覺得 18 條線交錯太密）：小多圖（18 個獨立子圖網格，各自獨立不受干擾）
# 若要使用請取消下方註解：
# -------------------------------------------------------------
# fig, axes = plt.subplots(6, 3, figsize=(18, 16), sharex=True, sharey=True)
# axes = axes.flatten()
# for idx, col in enumerate(smooth_df.columns):
#     axes[idx].plot(smooth_df.index, smooth_df[col], color=colors[idx], linewidth=1.6)
#     axes[idx].set_title(col, fontsize=10, fontweight='bold')
#     axes[idx].grid(True, linestyle=':', alpha=0.5)
#     axes[idx].xaxis.set_major_locator(mdates.DayLocator(interval=14))
#     axes[idx].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
# for ax in axes[-3:]:
#     ax.tick_params(axis='x', rotation=45, labelsize=8)
# plt.suptitle('沈伯洋 18 個主題獨立趨勢走勢圖（6x3 網格）', fontsize=15, y=0.995)
# plt.tight_layout()
# plt.show()

