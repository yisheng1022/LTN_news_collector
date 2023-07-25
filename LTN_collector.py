import requests,datetime,random,time,os,re,json
import pandas as pd
from bs4 import BeautifulSoup as BS

def date_creater(date_start = None,date_end = None):
	if date_start is None:
		datestart = '2021-12-31'
	if date_end is None:
		date_end = datetime.datetime.now().strftime('%Y%m%d')

	date_start = datetime.datetime.strptime(date_start,'%Y%m%d')
	date_end = datetime.datetime.strptime(date_end,'%Y%m%d')
	date_list = []
	while date_start < date_end:
		date_list.append(date_start.strftime('%Y%m%d'))
		date_start += datetime.timedelta(dayss=+1)
	date_list.append(date_end.strftime('%Y%m%d'))
	return date_list

def get_art_cont(cont_type,one_url):
	print(cont_type,one_url)
	cont_res = requests.get(one_url)
	cont_bs = BS(cont_res.text,'html.parser')
	content = ""
	garbage_text = '不用抽 不用搶 現在用APP看新聞 保證天天中獎\u3000\n    點我下載APP\u3000\n    按我看活動辦法'
	if (cont_type == "評論") | (cont_type == "娛樂") | (cont_type == "財經") | (cont_type == "玩咖") | (cont_type == "體育") | (cont_type == "3C") | (cont_type == "時尚") | (cont_type == "財經週報"):
		for a_content in cont_bs.select("div.text p"):
			content = content + a_content.text.replace(garbage_text,"").replace("\n","").replace("\u3000","")
	elif (cont_type == "汽車") | (cont_type == "地產"):
		for a_content in cont_bs.select("div.text.boxTitle p"):
			content = content + a_content.text.replace(garbage_text,"").replace("\n","").replace("\u3000","")
	elif (cont_type == "食譜"):
		for a_content in cont_bs.select("div.text.cookbook.boxTitle p"):
			content = content + a_content.text.replace(garbage_text,"").replace("\n","").replace("\u3000","")
	else:
		for a_content in cont_bs.select("div.text.boxTitle.boxText p"):
			content = content + a_content.text.replace(garbage_text,"").replace("\n","").replace("\u3000","")
	time_l = ""
	if (cont_type == "娛樂"):
		for a_time in cont_bs.select("time.time"):
			time_l = time_l + a_time.text
			time_l = re.sub('[\u4e00-\u9fa5]','',time_l)
			time_l = re.sub('[a-zA-Z]','',time_l)
	else:
		for a_time in cont_bs.select("span.time"):
			time_l = time_l + a_time.text
			time_l = re.sub('[\u4e00-\u9fa5]','',time_l)
			time_l = re.sub('[a-zA-Z]','',time_l)
	time.sleep(random.randint(1,3))
	return content,time_l

# print(get_art_cont("健康","https://health.ltn.com.tw/article/breakingnews/4159454"))
def key_words_search():
	start_date = input("Input start date: ")
	end_date = input("Input end date: ")
	key_words = input("Input the key words: ")
	title_len = 1;page = 0
	while title_len > 0:
		page += 1
		paper_url = "https://search.ltn.com.tw/list?keyword={}&start_time={}&end_time={}&type=all&page={}".format(key_words,start_date,end_date,page)
		page_req = requests.get(paper_url)
		page_bs = BS(page_req.text,'html.parser')
		title_list = [one_title['title'] for one_title in page_bs.select("div.cont a.tit")]
		title_len = len(title_list); print("Page No.", page ," got ",title_len," titles")
		type_list = [one_type.text for one_type in page_bs.select("div.cont i")]
		url_list = [one_url['href'] for one_url in page_bs.select("div.cont a.http")]
		tmp_list = [get_art_cont(a_type,a_url) for a_type,a_url in zip(type_list,url_list)]
		cont_list = [cont[0] for cont in tmp_list]
		date_list = [cont[1] for cont in tmp_list]
		news_dict = {"Title":title_list,"News_Type":type_list,"date":date_list,"content":cont_list,"url":url_list}
		news_pd = pd.DataFrame(news_dict)
		if os.path.isfile(start_date + "_" + end_date + key_words + "LTN_news.csv"):
			news_pd.to_csv(start_date + "_" + end_date + key_words + "LTN_news.csv",index = False,header = False,mode = "a+")
		else:
			news_pd.to_csv(start_date + "_" + end_date + key_words + "LTN_news.csv",index = False,header = True,mode = "w")
		time.sleep(random.randint(5,10))

def usual_news(ban_en,page_set = 25):
	# ban_en = input("Input forum:")
	break_page = 1;start_data = 0
	while break_page < page_set +1:
		print(break_page)
		page_url = "https://news.ltn.com.tw/ajax/breakingnews/{}/{}".format(ban_en,break_page)
		page_req = requests.get(page_url)
		page_json = page_req.json()
		url_list = [];title_list = [];type_list = [];date_list = [];cont_list = []
		# print(page_json["data"]["20"])
		for d in range(start_data,start_data+20):
			if (break_page == 1) :
				str_d = d
			else:
				str_d = str(d)
			url_list.append(page_json["data"][str_d]["url"]);title_list.append(page_json["data"][str_d]["title"]);date_list.append(page_json["data"][str_d]["time"])
			type_list.append(page_json["data"][str_d]["type_cn"]);cont_list.append(get_art_cont(page_json["data"][str_d]["type_cn"],page_json["data"][str_d]["url"])[0])
		break_page += 1;start_data += 20
		# news_dict = {"Title":title_list,"News_Type":type_list,"date":date_list,"content":cont_list,"url":url_list}
		news_pd = pd.DataFrame({"Title":title_list,"News_Type":type_list,"date":date_list,"content":cont_list,"url":url_list})
		if os.path.isfile("LTN_{}.csv".format(ban_en)):
			news_pd.to_csv("LTN_{}.csv".format(ban_en),header = False,index = False,mode = "a+")
		else:
			news_pd.to_csv("LTN_{}.csv".format(ban_en),header = True,index = False,mode = "w")

def clean_dup(f_name):
	# f_name = input("Input file name: ")
	old_df = pd.read_csv(f_name)
	print("Original length:",len(old_df["url"]))
	new_df = old_df.drop_duplicates(subset = ["url"],keep = "last")
	print("New length:",len(new_df["url"]))
	new_df.to_csv(f_name,header = True,index = False,mode = "w")

def date_func(f_name):
	old_df = pd.read_csv(f_name)
	new_d = []
	for things in old_df["date"]:
		if len(things.split(" ")) < 2:
			new_d.append(str(datetime.date.today()).replace("-","/") + " " + things)
		else:
			new_d.append(things)
	old_df["date"] = new_d
	old_df.to_csv(f_name,header = True,index = False, mode = "w")

print("******** LTN News collector ********")
func_in = "2"#input("Function --> 1:Keyword 2:Forums :")
if func_in == "1":
	key_words_search()
elif func_in == "2":
	forum_list = ["life","world","local","politics","society"]
	for one_f in forum_list:
		usual_news(one_f)
		clean_dup("LTN_{}.csv".format(one_f))
		date_func("LTN_{}.csv".format(one_f))
elif func_in == "3":
	print("Access denied")
elif func_in == "4":
	fn = input("File name: ")
	old_df = pd.read_csv(fn)
	new_d = []
	for things in old_df["date"]:
		if len(things.split(" ")) < 2:
			new_d.append(str(datetime.date.today()) + " " + things)
		else:
			new_d.append(things)
	old_df["date"] = new_d
	old_df.to_csv(fn,header = True,index = False, mode = "w")
