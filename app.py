import streamlit as st
import os
import time
from google import genai

# 背景色を黒、およびコンテンツ幅を中央に調律
st.set_page_config(page_title="Kobunsha BIZ-CREA", layout="centered")

# CSSによる客観的なデザイン・配置の強制上書き
st.markdown("""
<style>
    /* 1. 地色を黒に固定 */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #090D16 !important;
        color: #E2E8F0 !important;
    }
    
    /* 2. タイトルの拡大、絵文字のパージ、説明文の配置 */
    .brand-container {
        margin-top: 40px;
        margin-bottom: 30px;
        text-align: left;
    }
    .brand-title {
        font-size: 42px; /* サイズの大幅拡大 */
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
        line-height: 1.2;
    }
    .brand-desc {
        font-size: 14px;
        color: #94A3B8;
        margin-top: 12px;
        line-height: 1.6;
    }
    
    /* 3. 横長を拒絶し、ドロップスペースを特大の四角いボックスへ変更 */
    [data-testid="stFileUploader"] {
        background-color: #111827 !important;
        border: 2px dashed #334155 !important;
        border-radius: 8px !important;
        padding: 60px 40px !important; /* 縦の幅を大幅に広げて四角形化 */
        text-align: center !important;
    }
    [data-testid="stFileUploader"] section {
        width: 100% !important;
    }
    
    /* ボタンおよびテキストエリアの構成要素 */
    .stButton>button {
        background-color: #FFFFFF !important;
        color: #090D16 !important;
        font-weight: 700 !important;
        padding: 14px 20px !important;
        border-radius: 6px !important;
        border: none !important;
        margin-top: 10px;
    }
    .download-zone>div>button {
        background-color: #10B981 !important;
        color: white !important;
    }
    
    #MainMenu, footer, header { visibility: hidden !important; }
    .stDeployButton { display:none !important; }
</style>
""", unsafe_allow_html=True)

if "site_title" not in st.session_state:
    st.session_state["site_title"] = "Kobunsha BIZ-CREA"
if "site_desc" not in st.session_state:
    st.session_state["site_desc"] = "1時間以上の長大な会議音声にも対応。会議や打ち合わせの議事録と新事業の企画案ドラフトを出力します。"
if "prompt_pre" not in st.session_state:
    st.session_state["prompt_pre"] = "・現在の出版業界は非常に厳しい。既存の「紙」や、失敗に終わった消耗戦のコタツ記事デジタルから完全に脱却する。\n・紙、デジタルにとらわれず、イベント、スクールビジネス、終活ビジネス等々の「光文社が手がけなかった」新規事業を生み出す。\n・既存雑誌・書籍と一切関係ないK-POP関係の出版物、グッズ販売、イベント等を行ってきた。\n・フィジカルか、AIか、動画か、SNSかを問わず、新たなビジネスイメージを作りたい。\n・もちろん、書籍やIPといった出版社の事業も大切。\n・ただし「出版社がやるビジネス」のイメージを守る。ラーメン屋やキャバクラを経営してどうする？\n・海外の最新事例の構造も参照すること。"
if "prompt_target" not in st.session_state:
    st.session_state["prompt_target"] = "・年々高齢化する40～60代女性という光文社女性誌の既存読者だけでなく、もっと若い世代、男性、オタク層、推し活層、在日外国人その他の「新たなマーケット」を開拓する。"
if "prompt_ng" not in st.session_state:
    st.session_state["prompt_ng"] = "・コンサル的な「お行儀の良い一般論」「誰でも言える綺麗事（絆、おもおてなし）」。\n・予算を無駄に食う割に、現場を動かせないハコモノ的な大袈裟な提案。"

def update_title(): st.session_state["site_title"] = st.session_state["k1"]
def update_desc(): st.session_state["site_desc"] = st.session_state["k2"]
def update_pre(): st.session_state["prompt_pre"] = st.session_state["k3"]
def update_target(): st.session_state["prompt_target"] = st.session_state["k4"]
def update_ng(): st.session_state["prompt_ng"] = st.session_state["k5"]

query_params = st.query_params
is_admin = False
if "admin" in query_params:
    param_val = query_params["admin"]
    if isinstance(param_val, list):
        is_admin = len(param_val) > 0 and param_val == "true"
    else:
        is_admin = param_val == "true"

if is_admin:
    left_col, right_col = st.columns(2, gap="large")
    with left_col:
        st.markdown("### 🛠️ 【管理者専用】サイト文言・前提条件の自由編集")
        st.text_input("⚙️ システムのメインタイトル", value=st.session_state["site_title"], key="k1", on_change=update_title)
        st.text_area("⚙️ システムの説明文", value=st.session_state["site_desc"], key="k2", height=70, on_change=update_desc)
        st.markdown("---")
        st.text_area("■ 前提条件", value=st.session_state["prompt_pre"], key="k3", height=220, on_change=update_pre)
        st.text_area("■ 狙うべきターゲット層", value=st.session_state["prompt_target"], key="k4", height=100, on_change=update_target)
        st.text_area("■ 排除すべきNG項目", value=st.session_state["prompt_ng"], key="k5", height=100, on_change=update_ng)
        st.markdown("---")
else:
    right_col = st.container()

with right_col:
    # 調律されたメインヘッダー
    st.markdown(f"""
    <div class="brand-container">
        <h1 class="brand-title">{st.session_state["site_title"]}</h1>
        <p class="brand-desc">{st.session_state["site_desc"]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 特大四角形化したアップローダーボックス
    uploaded_file = st.file_uploader("", type=["mp3", "m4a", "wav"], label_visibility="collapsed")
    
    if uploaded_file:
        st.markdown(f"**🟢 検知:** `{uploaded_file.name}` ({uploaded_file.size/1024/1024:.2f} MB)")
        
        if st.button("議事録・新事業企画案の自動生成を開始", type="primary", use_container_width=True):
            status_placeholder = st.empty()
            status_placeholder.markdown("⏳ **大容量音声を転送しながら、Geminiで冷徹に解析中... (1〜3分かかります)**")
            
            try:
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    st.error("認証エラー: GEMINI_API_KEYが登録されていません。")
                    st.stop()
                    
                client = genai.Client(api_key=api_key)
                ext = os.path.splitext(uploaded_file.name).lower()
                temp_filename = f"temp_audio{ext}"
                with open(temp_filename, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                mime_map = {'.wav': 'audio/wav', '.mp3': 'audio/mp3', '.m4a': 'audio/m4a'}
                mime_type = mime_map.get(ext, 'audio/mp3')
                audio_file_ref = client.files.upload(file=temp_filename, config={'mime_type': mime_type})
                
                while audio_file_ref.state.name == "PROCESSING":
                    time.sleep(5)
                    audio_file_ref = client.files.get(name=audio_file_ref.name)
                
                prompt = f"""
                あなたは光文社ビジネスクリエーション部のディレクターとして、高度な論理的知性を持って冷徹に会話を分析する専門家です。
                添付された音声内容を構造的に分析し、お気持ちの一般論や綺麗事を1文字残さず焼き尽くした【議事録】と、出版社としてのプライドを持った【尖った新事業の企画ドラフト案2つ】を出力してください。

                ■ 前提条件：
                {st.session_state["prompt_pre"]}

                ■ ターゲット層：
                {st.session_state["prompt_target"]}

                ■ 企画におけるNG：
                {st.session_state["prompt_ng"]}

                以下のフォーマットを厳格に守って出力すること：
                ■ 1. 冷徹な議事録（決定事項・争点・Next Actions）
                ■ 2. 企画案A（タイトル、核心アイデア、コストの引き算、参照すべき海外最新事例、具体的な実行ステップ）
                ■ 3. 企画案B（同上）
                """
                
                response = client.models.generate_content(model='gemini-3.8-flash', contents=[audio_file_ref, prompt])
                output_text = response.text
                
                status_placeholder.empty()
                st.success("✅ 解析が完了しました。成果物(TXT)をダウンロードしてください。")
                
                st.markdown('<div class="download-btn">', unsafe_allow_html=True)
                st.download_button(
                    label="📥 成果物(TXT)をダウンロードする",
                    data=output_text,
                    file_name="光文社ビジクリ部_議事録_企画案.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("### 🎯 成果物プレビュー")
                st.code(output_text, language="text")
                
                client.files.delete(name=audio_file_ref.name)
                os.remove(temp_filename)
            except Exception as e:
                status_placeholder.empty()
                st.error(f"エラーが発生しました: {e}")
