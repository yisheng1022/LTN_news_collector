import os
import json
from typing import Literal, Optional
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import config

load_dotenv()

# ==========================================
# 步驟 1：定義強型別 JSON 輸出結構（Schema）
# ==========================================
class PersonSentimentLabel(BaseModel):
    score: float = Field(
        ..., 
        description="對該人物的評價連續分數，範圍為 0.0 到 10.0 的浮點數。5.0 為嚴格客觀中立。"
    )
    sentiment: Literal["正面", "中立", "負面"] = Field(
        ...,
        description="新聞對該人物的總體評價傾向：分數 > 5.5 為正面，4.5 <= 分數 <= 5.5 為中立，< 4.5 為負面。"
    )
    relevance: Literal["核心主角", "次要提及", "背景路過"] = Field(
        ...,
        description="該人物在本文中的重要性。主要討論對象為核心主角；提供回應或意見為次要提及；僅出現在與會或名單中為背景路過。"
    )
    analysis_reason: str = Field(
        ..., 
        description="簡短 1~2 句話說明評分依據，指出媒體框架如何描繪該人物（如：報導角度、批評或讚賞來源、攻防平衡狀況）。"
    )
    key_quote: str = Field(
        ..., 
        description="從原始繁體中文新聞中，摘錄最能佐證此分數的核心原文字句（150字以內，不可自行改寫）。"
    )


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """
    取得 Gemini Client 實例。優先使用傳入的 key，次之從環境變數 (.env) 讀取，最後檢查 config.py。
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or getattr(config, "GEMINI_API_KEY", "")
    if not key:
        raise ValueError(
            "❌ 尚未設定 GEMINI_API_KEY！\n"
            "請確認已在 .env 檔案中設定 GEMINI_API_KEY=您的Key，或在 config.py 中填入。"
        )
    return genai.Client(api_key=key)


# ==========================================
# 步驟 2：核心標註函數設計
# ==========================================
def analyze_person_sentiment(
    article_content: str, 
    selected_person: str = "沈伯洋",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> Optional[dict]:
    """
    呼叫 Gemini API 評估新聞對特定人物的正負面評價、聲量向度與重要度。
    """
    # 決定使用的模型（優先參數，次之 config.py 設定）
    target_model = model_name or getattr(config, "GEMINI_MODEL", "gemini-3.8-flash")
    print(f"🚀 正在使用 {target_model} 模型進行標註...",end="\r")

    # 針對 0.0 ~ 10.0 連續變數特化的系統 Prompt
    system_prompt = f"""
    # Role
    你是一位專精於政治傳播學、媒體框架（Media Framing）與計算輿情分析的資深研究員。
    你的任務是客觀、精確地評估台灣新聞媒體報導中，針對目標人物【{selected_person}】的評價傾向（Sentiment / Stance）與形象塑造。

    # Core Analysis Principles (核心判斷原則，避免誤判)
    1. 【鎖定目標人物，非新聞事件】：區分「事件本身的性質」與「對{selected_person}的評價」。
       - 例如：若新聞報導{selected_person}遭受對手抹黑、司法提告或境外攻擊，但報導角度在於揭露攻擊方的惡意行為、或是報導{selected_person}有力澄清反擊，此篇對{selected_person}屬於「中立或正面」，絕非負面。
       - 只有當新聞內容主要是在指控、揭露{selected_person}的不當行為、或大幅引用對手批評且缺乏平衡時，才評為負面。
    2. 【引述攻防與篇幅比重】：
       - 若報導篇幅主要為對手或輿論的批評質疑，且缺乏澄清辯護，判定為「偏負面」。
       - 若報導同時平衡呈現指責與{selected_person}的回應澄清，判定為「中立平衡（約 4.5 ~ 5.5）」。
       - 若報導著重於{selected_person}的政策論述、專業貢獻、勝訴成果或主導議題，判定為「偏正面」。
    3. 【背景路過不扣分】：
       - 若{selected_person}僅在出席名單、聯名提案中被順帶提及，無實質褒貶評價，應判定為「嚴格中立（5.0）」，且相關度為「背景路過」。

    # Scoring Anchors (0.0 到 10.0 刻度定錨標準 - 嚴禁評分漂移)
    - [0.0 ~ 2.0] 極度負面（重大醜聞／強烈批判）
      * 涉及違法弊案、嚴重失職、誠信崩塌、遭遇社會輿論或對手毀滅性質疑。
      * 報導全篇充斥強烈譴責，且幾無平衡或辯護空間。

    - [2.1 ~ 4.4] 偏向負面（質疑批評／爭議焦點）
      * 報導聚焦其失言爭議、政策失誤、被在野/執政對手重砲質疑，負面聲浪明顯大於正面陳述。
      * 關鍵特徵：遭批、引發爭議、失言、被轟、質疑、不滿、指控。

    - [4.5 ~ 5.5] 客觀中立（純事實陳述／正反平衡）
      * 基準點為 5.0。客觀陳述公務行程、記者會發言、法案提出等事實，語氣平實中立，無主觀修辭褒貶。
      * 或正反雙方意見篇幅大致均等呈現。

    - [5.6 ~ 7.9] 偏向正面（肯定支持／表現良好）
      * 政策獲得支持、揭弊有成、有力回擊對手質疑、展現專業度、獲得支持者或同僚肯定。
      * 關鍵特徵：力挺、肯定、專業、反擊、澄清、主導、斬獲成果。

    - [8.0 ~ 10.0] 極度正面（卓越貢獻／高度讚譽）
      * 獲得重大殊榮、民意大幅力挺、卓越政績、被塑造為典範人物或重要英雄形象。

    # Task Requirements
    1. 評定精確到小數點後一位的連續分數（例如 4.0、7.5）。
    2. 依據分數嚴格對應情感分類（正面／中立／負面）。
    3. 評定人物在本文的角色重要度（核心主角／次要提及／背景路過）。
    4. 摘錄最能佐證該分數的 1~2 句【原始繁體中文】新聞段落（150字以內，嚴禁腦補改寫）。
    """

    try:
        client = get_gemini_client(api_key=api_key)
        response = client.models.generate_content(
            model=target_model,
            contents=article_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=PersonSentimentLabel,
                temperature=getattr(config, "ANNOTATION_TEMPERATURE", 0.1),
            ),
        )
        
        if hasattr(response, "text") and response.text:
            return json.loads(response.text)
        return None
        
    except Exception as e:
        print(f"❌ 標註過程發生錯誤: {e}")
        return None


# ==========================================
# 步驟 3：測試執行
# ==========================================
if __name__ == "__main__":
    target_person = "沈伯洋"
    csv_file = "Udn_vote_drop.csv"
    
    if os.path.exists(csv_file):
        print(f"📂 正在讀取資料集: {csv_file}")
        df = pd.read_csv(csv_file)
        print(f"總筆數: {len(df)}")
        df.dropna(subset=['date', 'content'], inplace=True)
        df.reset_index(drop=True, inplace=True)
        print(f"去除空值後筆數: {len(df)}")
        df = df.sample(n=1000,random_state=99)
        print(f"抽樣 {len(df)} 筆資料，開始標註...")
        
        # 套用標註函數
        df[['sentiment_score', 'sentiment_label', 'relevance', 'analysis_reason', 'key_quote']] = df['content'].apply(
            lambda x: pd.Series(analyze_person_sentiment(x, target_person))
        )
        
        # 儲存結果
        output_file = f"gemini_tagged_data_Udn_{target_person}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 標註完成！結果已儲存至 {output_file}")
        print(df.head())

        # 取第一篇測試
        # sample_article = df.iloc[0]["content"] if "content" in df.columns else ""
        # print(f"\n🚀 正在測試標註第一篇新聞（目標人物：{target_person}）...")
        # result = analyze_person_sentiment(sample_article, selected_person=target_person)
        
        # if result:
        #     print("\n📊 --- 標註成果 ---")
        #     print(f"1. 好感度連續分數 (Score)   : {result.get('score')} / 10.0")
        #     print(f"2. 聲量向度 (Sentiment)     : {result.get('sentiment')}")
        #     print(f"3. 角色重要度 (Relevance)   : {result.get('relevance')}")
        #     print(f"4. 評判原因 (Reason)        : {result.get('analysis_reason')}")
        #     print(f"5. 核心佐證引文 (Key Quote) : {result.get('key_quote')}")
    else:
        print(f"⚠️ 找不到檔案: {csv_file}，請確認檔案路徑。")
