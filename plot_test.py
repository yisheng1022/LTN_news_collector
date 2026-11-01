import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

ltn_df = pd.read_csv(r'E:\vpy\LTN\LTN_news_collector\20250101_20261027沈伯洋LTN_news.csv')
udn_df = pd.read_csv(r'Udn_vote_drop.csv')
print('Udn before drop:',len(udn_df))
udn_df.drop_duplicates(inplace=True,keep='first')
print('Udn after drop:',len(udn_df))
udn_df = udn_df[udn_df['content'].str.contains('沈伯洋',na=False)]
udn_df.to_csv('Udn_vote_沈伯洋.csv',index = False,encoding = 'utf-8-sig')

ltn_df.dropna(subset = ["date"],inplace = True)
ltn_df['day'] = ltn_df['date'].apply(lambda x: str(x).split(' ')[0])
day_count_df = ltn_df['day'].value_counts()
day_count_df.sort_index(inplace = True)
day_count_df.index = pd.to_datetime(day_count_df.index)

udn_df.dropna(subset = ["date"],inplace = True)
udn_df['day'] = udn_df['date'].apply(lambda x: str(x).split(' ')[0])
udn_count_df = udn_df['day'].value_counts()
udn_count_df.sort_index(inplace = True)
udn_count_df.index = pd.to_datetime(udn_count_df.index)

# 合併兩者日期並填補缺失值為 0，確保兩邊日期同步對齊
merged_df = pd.DataFrame({'LTN': day_count_df, 'Udn': udn_count_df}).fillna(0)

# 設定長條寬度（以「天」為單位，0.35 天約 8.4 小時）
width = 0.35
offset = pd.Timedelta(days=width / 2)

fig, ax = plt.subplots(figsize=(15, 10))
ax.bar(merged_df.index - offset, merged_df['LTN'], label='LTN', width=width)
ax.bar(merged_df.index + offset, merged_df['Udn'], label='Udn', width=width)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.tick_params(axis='x', rotation=90, labelsize=8)
ax.set_title('沈伯洋新聞數量')
ax.grid(True, axis='x', linestyle='--', color='gray', alpha=0.5)
ax.legend()
plt.tight_layout()
plt.show()

