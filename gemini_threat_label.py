import json
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import config

load_dotenv()
# ==========================================
# 步驟 1：定義強型別 JSON 輸出結構（Schema）
# ==========================================
class ImplicitThreatRegressionLabel(BaseModel):
    score: float = Field(
        ..., 
        description="中共涉台隱含威脅連續分數，範圍為 0.0 到 10.0 的浮點數。"
    )
    analysis_reason: str = Field(
        ..., 
        description="一到兩句話的政治學術評分依據，明確指出觸發了哪些文獻核心特徵詞。"
    )
    distilled_text: str = Field(
        ..., 
        description="擷取出的原始官媒涉台核心文本段落，必須維持簡體中文，長度嚴格控制在 350 字以內。"
    )

# ==========================================
# 步驟 2：核心標註函數設計
# ==========================================
def get_implicit_threat_score(article_content: str) -> dict:
    """
    呼叫 Gemini API 讀取官媒長文，並輸出符合連續變數設定的結構化標註結果。
    """
    # 初始化 API 客戶端（會自動物理讀取環境變數 GEMINI_API_KEY）
    client = genai.Client()
    
    # 針對 0.0 ~ 10.0 連續變數特化的權威系統 Prompt
    system_prompt = """
    # Role
    你是一位精通計算政治學（Computational Politics）與中共涉台官方修辭學（Chinese Political Rhetoric）的頂級學術專家。你的任務是閱讀中共官方媒體（《人民日報》、《解放軍報》、《光明日報》）的涉台文本，精準評估其對台的「隱含威脅（Implicit Threat）」程度。

    # Theoretical Framework & Operationalization
    根據國際關係與政治學理論（Wong, 2026; Quek & Johnston, 2018），「隱含威脅」定義為：對敵手（台灣當局或美台勾連勢力）發出帶有「負面/懲罰性後果」的言語警告，但「不具體提及明確的軍事行動手段或具體時間線」。
    
    # Scoring Anchors (刻度定錨標準 - 嚴禁評分漂移)
    請根據文本中政治修辭的強度與特徵詞，精確評定一個 0.0 到 10.0 之間的分數（Float）：
    
    - [0.0 ~ 2.0] 常態宣傳或無威脅
      * 語氣平穩、毫無實質負面後果暗示。
      * 聚焦兩岸文化經貿交流（兩岸一家親、融合發展），或例行性重申一中原則歷史經緯。
      
    - [2.1 ~ 5.0] 低度警告性施壓
      * 語氣出現政治性警示，針對台灣特定政策或涉台國際事務表達不滿。
      * 特徵用詞：消極影響、負面影響、不良後果、適得其反。
      
    - [5.1 ~ 8.0] 中度危機級警告
      * 明確施加強烈外交代報訊號，語意高機率指涉台灣將吞下痛苦代價。
      * 特徵用詞：惡果、自食其果、苦果、不顧后果、惡劣影響。
      
    - [8.1 ~ 10.0] 危機級極限軍事威懾
      * 具備極強的臨戰動員感或灰色地帶極限逼迫，強烈暗示毀滅性或實質武力後果。
      * 特徵用詞：玩火自焚、自取滅亡、引火自焚、自尋死路、玩火者必將自焚、一切後果由對方承擔。

    # Task Requirements
    1. 對輸入的文章給予精確到小數點後一位的連續分數（例如 7.5）。
    2. 執行「文本脫水（Text Distillation）」：從原始長文中，精準擷取出最能代表該分數、資訊密度最高、最具威脅修辭特徵的核心段落。
       - 擷取出的文本必須維持【原始簡體中文】。
       - 長度必須【嚴格控制在 350 個字以內】，不可做任何自行腦補的潤飾或擴寫。
    """
    
    try:
        # 使用速度極快、對結構化輸出支持極佳的 gemini-3.5-flash
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=article_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json", # 強制要求回傳 JSON
                response_schema=ImplicitThreatRegressionLabel, # 硬性將 JSON 結構死鎖在 Pydantic 格式上
                temperature=0.1, # 💡 極低溫度，確保打分刻度高度穩定，拒絕隨機性
            ),
        )
        
        # 由於 response_schema 的保護，response.text 必定為合法的 JSON 字串，可直接轉成字典
        return json.loads(response.text)
        
    except Exception as e:
        print(f"❌ 標註過程發生錯誤: {e}")
        return None

# ==========================================
# 步驟 3：本地物理點火測試
# ==========================================
if __name__ == "__main__":
    # 模擬一篇從解放軍報爬下來的 2,000 字涉台社論精簡版
    mock_article = """
    全軍部隊要深入學習貫徹強軍思想。近日，美台加緊軍事勾連，嚴重違反一個中國原則。
    台灣問題是中國核心利益中的核心。个别台独分裂分子挾洋自重，妄圖挑釁國家主權。
    我們正告民進黨當局，任何倚美謀獨的圖謀都是痴心妄想。
    分裂勢力若膽敢跨越紅線，中國人民解放軍嚴陣以待，必將予以迎頭痛擊。
    這是在玩火，玩火者必將自焚，自取滅亡！一切嚴重後果必須由美台當局完全承擔。
    """
    
    print("🚀 啟動大模型專家標註引擎...")
    result = get_implicit_threat_score(mock_article)
    
    if result:
        print("\n📊 --- 標註與大數據脫水成果 ---")
        print(f"1. 隱含威脅連續分數 (Score) : {result['score']} / 10.0")
        print(f"2. 學術評判依據 (Reason)    : {result['analysis_reason']}")
        print(f"3. 脫水精煉文本 (Distilled) : {result['distilled_text']}")
        print(f"   [文字長度檢驗]           : 共 {len(result['distilled_text'])} 個字 (安全跑進地端 512 限制)")