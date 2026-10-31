import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

ltn_df = pd.read_csv(r'D:\vpy\LTN_news_collector\20250101_20261027沈伯洋LTN_news.csv')
udn_df = pd.read_csv(r'Udn_vote.csv')
print('Udn before drop:',len(udn_df))
udn_df.drop_duplicates(inplace=True,keep='first')
print('Udn after drop:',len(udn_df))
udn_df.to_csv('Udn_vote_drop.csv',index = False,encoding = 'utf-8-sig')

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

fig, ax = plt.subplots(figsize=(15, 10))
ax.plot(day_count_df)
ax.plot(udn_count_df)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.tick_params(axis='x', rotation=90, labelsize=8)
ax.set_title('沈伯洋新聞數量')
ax.grid(True, axis='x', linestyle='--', color='gray', alpha=0.5)
plt.tight_layout()
plt.show()

