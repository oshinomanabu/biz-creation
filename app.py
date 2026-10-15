import streamlit as st
import os
import time
from google import genai

st.set_page_config(page_title="光文社ビジネスクリエーション部", layout="wide")

query_params = st.query_params
is_admin = False
if "admin" in query_params:
    param_val = query_params["admin"]
    if isinstance(param_val, list):
        is_admin = len(param_val) > 0 and param_val == "true"
    else:
        is_admin = param_val == "true"

if "title_val" not in st.session_state:
    st.session_state["title_val"] = "Kobunsha BIZ-CREA"
if "desc_val" not in st.session_state:
    st.session_state["desc_val"] = "1時間以上の長大な会議音声にも対応。会議や打ち合わせの議事録と新事業の企画案ドラフトを出力します。"
if "pre_val" not in st.session_state:
    st.session_state["pre_val"] = "・現在の出版業界は非常に厳しい。既存の「紙」や、失敗に終わった消耗戦のコタツ記事デジタルから完全に脱却する。\n・紙、デジタルにとらわれず、イベント、スクールビジネス、終活ビジネス等々の「光文社が手がけなかった」新規事業を生み出す。\n・既存雑誌・書籍と一切関係ないK-POP関係の出版物、グッズ販売、イベント等を行ってきた。\n・フィジカルか、AIか、動画か、SNSかを問わず、新たなビジネスイメージを作りたい。\n・もちろん、書籍やIPといった出版社の事業も大切。\n・ただし「出版社がやるビジネス」のイメージを守る。ラーメン屋やキャバクラを経営してどうする？\n・海外の最新事例の構造も参照すること。"
if "target_val" not in st.session_state:
    st.session_state["target_val"] = "・年々高齢化する40～60代女性という光文社女性誌の既存読者だけでなく、もっと若い世代、男性、オタク層、推し活層、在日外国人その他の「新たなマーケット」を開拓する。"
if "ng_val" not in st.session_state:
    st.session_state["ng_val"] = "・コンサル的な「お行儀の良い一般論」「誰でも言える綺麗事（絆、おもてなし）」。\n・予算を無駄に食う割に、現場を動かせないハコモノ的な大裟な提案。"

def sync_title(): st.session_state["title_val"] = st.session_state["k1"]
def sync_desc(): st.session_state["desc_val"] = st.session_state["k2"]
def sync_pre(): st.session_state["pre_val"] = st.session_state["k3"]
def sync_target(): st.session_state["target_val"] = st.session_state["k4"]
def sync_ng(): st.session_state["ng_val"] = st.session_state["k5"]

if is_admin:
    left_col, right_col = st.columns(2, gap="large")
else:
    left_spacer, center_box, right_spacer = st.columns(3)
    right_col = center_box

if is_admin:
    with left_col:
        st.markdown("### 🛠️ 【管理者専用】サイト文言・前提条件の自由編集")
        st.text_input("⚙️ システムのメインタイトル", value=st.session_state["title_val"], key="k1", on_change=sync_title)
        st.text_area("⚙️ システムの説明文", value=st.session_state["desc_val"], key="k2", height=70, on_change=sync_desc)
        st.markdown("---")
        st.markdown("### 🎯 戦略文脈（プロンプト）の書き換え")
        st.text_area("■ 前提条件", value=st.session_state["pre_val"], key="k3", height=220, on_change=sync_pre)
        st.text_area("■ 狙うべきターゲット層", value=st.session_state["target_val"], key="k4", height=100, on_change=sync_target)
        st.text_area("■ 排除すべきNG項目", value=st.session_state["ng_val"], key="k5", height=100, on_change=sync_ng)
        st.markdown("---")

with right_col:
    # font-size を 42px へ拡大、ロケットなしの構成
    st.markdown(f"""
    <div style="background-color: #1E293B; padding: 25px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #334155;">
        <h1 style="color: #F8FAFC; margin: 0; font-size: 42px; font-weight: 700;">{st.session_state["title_val"]}</h1>
        <p style="color: #94A3B8; margin-top: 14px; margin-bottom: 0; font-size: 14px; line-height: 1.6;">{st.session_state["desc_val"]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("会議の録音ファイル（音声）をここにドラッグ＆ドロップしてください", type=["mp3", "m4a", "wav"], label_visibility="collapsed")
    
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
                {st.session_state["pre_val"]}

                ■ ターゲット層：
                {st.session_state["target_val"]}

                ■ 企画におけるNG：
                {st.session_state["ng_val"]}

                以下のフォーマットを厳格に守って出力すること：
                ■ 1. 冷徹な議事録（決定事項・争点・Next Actions）
                ■ 2. 企画案A（タイトル、核心アイデア、コストの引き算、参照すべき海外最新事例、具体的な実行ステップ）
                ■ 3. 企画案B（同上）
                """
                
                response = client.models.generate_content(model='gemini-3.8-flash', contents=[audio_file_ref, prompt])
                output_text = response.text
                
                status_placeholder.empty()
                st.success("✅ 解析が完了しました。成果物(TXT)をダウンロードしてください。")
                
                st.download_button(
                    label="📥 成果物(TXT)をダウンロードする",
                    data=output_text,
                    file_name="光文社ビジクリ部_議事録_企画案.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                st.markdown("### 🎯 成果物プレビュー")
                st.text(output_text)
                
                client.files.delete(name=audio_file_ref.name)
                os.remove(temp_filename)
            except Exception as e:
                status_placeholder.empty()
                st.error(f"エラーが発生しました: {e}")
