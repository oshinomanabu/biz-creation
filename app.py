import streamlit as st
import os
import time
from google import genai

st.set_page_config(page_title="光文社ビジネスクリエーション部", layout="wide")

st.markdown("""
<div style="background-color: #1E293B; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
    <h1 style="color: #F8FAFC; margin: 0; font-size: 28px;">🚀 光文社ビジネスクリエーション部・新事業創出システム</h1>
    <p style="color: #94A3B8; margin-top: 5px; margin-bottom: 0; font-size: 14px;">
        1時間以上の長大な会議音声にも対応。お気持ちの呪縛やコンサルの綺麗事を焼き尽くし、冷徹な議事録と尖った新事業の思想をサルベージします。
    </p>
</div>
""", unsafe_allow_html=True)

left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown("### 🔑 セキュリティ認証")
    user_api_key = st.text_input("ご自身のGemini APIキー (AIzaSy...) を入力してください", type="password")
    
    st.markdown("### 🛠️ 操作・音声ファイルのドロップ")
    uploaded_file = st.file_uploader("会議の録音ファイル（音声）をここにドラッグ＆ドロップしてください", type=["mp3", "m4a", "wav"])

with right_col:
    st.markdown("### 🎯 生成結果（成果物）")
    
    if uploaded_file and user_api_key:
        if left_col.button("議事録・企画案の自動生成を開始", type="primary", use_container_width=True):
            with st.spinner("大容量音声をクラウド間で安全にストリーム転送し、Gemini 1.5 Proで冷徹に解析中..."):
                try:
                    client = genai.Client(api_key=user_api_key)
                    ext = os.path.splitext(uploaded_file.name)[1].lower()
                    temp_filename = f"temp_audio{ext}"
                    with open(temp_filename, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    mime_map = {'.wav': 'audio/wav', '.mp3': 'audio/mp3', '.m4a': 'audio/m4a'}
                    mime_type = mime_map.get(ext, 'audio/mp3')
                    audio_file_ref = client.files.upload(file=temp_filename, config={'mime_type': mime_type})
                    
                    while audio_file_ref.state.name == "PROCESSING":
                        time.sleep(5)
                        audio_file_ref = client.files.get(name=audio_file_ref.name)
                    
                    prompt = """
                    あなたは光文社ビジネスクリエーション部のディレクターとして、高度な論理的知性を持って冷徹に会話を分析する専門家です。
                    添付された音声内容を構造的に分析し、お気持ちの一般論や綺麗事を1文字残さず焼き尽くした【議事録】と、出版社としてのプライドを持った【尖った新事業の企画ドラフト案2つ】を出力してください。

                    ■ 前提条件：
                    ・現在の出版業界は非常に厳しい。既存の「紙」や、失敗に終わった消耗戦のコタツ記事デジタルから完全に脱却する。
                    ・紙、デジタルにとらわれず、イベント、スクールビジネス、終活ビジネス等々の「光文社が手がけなかった」業務を生み出す。
                    ・既存雑誌・書籍と一切関係ないK-POP関係の出版物、グッズ販売、イベント等を行ってきた。
                    ・フィジカルか、AIか、動画か、SNSかを問わず、新たなビジネスイメージを作りたい。
                    ・ただし「出版社がやるビジネス」の矜持を死守。「ラーメン屋」「キャバクラ」は厳禁。海外の最新事例の構造も参照すること。

                    ■ ターゲット層：
                    ・年々高齢化する40～60代女性という既存読者だけでなく、もっと若い世代、男性、オタク層、推し活層、在日外国人その他の「新たなマーケット」を開拓する。

                    ■ 企画におけるNG：
                    ・コンサル的な「お行儀の良い一般論」「誰でも言える綺麗事（絆、おもてなし）」。
                    ・予算を無駄に食う割に、現場を動かせないハコモノ的な大裟な提案。

                    以下のフォーマットを厳格に守って出力すること：
                    ■ 1. 冷徹な議事録（決定事項・争点・Next Actions）
                    ■ 2. 企画案A（タイトル、核心アイデア、コストの引き算、参照すべき海外最新事例、具体的な実行ステップ）
                    ■ 3. 企画案B（同上）
                    """
                    
                    response = client.models.generate_content(model='gemini-1.5-pro', contents=[audio_file_ref, prompt])
                    output_text = response.text
                    
                    st.markdown(output_text)
                    st.download_button("📥 成果物(TXT)をダウンロード", output_text, file_name="output_result.txt", use_container_width=True)
                    
                    client.files.delete(name=audio_file_ref.name)
                    os.remove(temp_filename)
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
    elif uploaded_file and not user_api_key:
        st.warning("左側のエリアに、ご自身のGemini APIキーを入力してください。")
    else:
        st.warning("左側の操作エリアから、音声ファイルをドラッグ＆ドロップしてください。")
