import streamlit as st
import os
import time
import random
import tempfile
from google import genai
from google.genai import errors as genai_errors

st.set_page_config(page_title="光文社ビジネスクリエーション部", layout="wide")

# =========================================================
# 503対策の設定
# =========================================================
# 上から順に試す。存在しないモデル(404)は自動で飛ばすので、
# 名前が分からなくても候補を並べておけばよい。
MODEL_CANDIDATES = [
    "gemini-3.6-flash",          # メイン（社内で利用可能と確認済み）
    "gemini-3.6-flash-preview",  # 正式名に -preview が付く場合の保険
    "gemini-3.5-flash",          # 以下、混雑時の代替（存在しなければ自動で飛ばす）
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
]
RETRYABLE_CODES = {429, 500, 503, 504}   # 混雑・一時障害とみなして再試行するコード
MAX_ATTEMPTS_PER_MODEL = 5               # 1モデルあたりの試行回数
BASE_WAIT_SEC = 10                       # 初回の待ち時間（以後倍々）
MAX_WAIT_SEC = 120                       # 1回の待ち時間の上限
FILE_PROCESS_TIMEOUT_SEC = 900           # 音声のサーバー側処理待ちの上限


def wait_with_message(status, seconds, reason):
    """待ち時間を残り秒数つきで表示しながら待つ"""
    end = time.time() + seconds
    while True:
        remain = int(end - time.time())
        if remain <= 0:
            break
        status.markdown(f"⏳ **{reason}。{remain}秒後に再試行します…**（社内向けのため、そのままお待ちください）")
        time.sleep(1)


def upload_with_retry(client, path, mime_type, status):
    """音声アップロード自体も混雑で失敗することがあるので再試行する"""
    last_error = None
    for attempt in range(1, 4):
        try:
            status.markdown(f"⏳ **音声ファイルを転送中…（{attempt}/3回目）**")
            return client.files.upload(file=path, config={"mime_type": mime_type})
        except genai_errors.APIError as e:
            last_error = e
            if e.code not in RETRYABLE_CODES or attempt == 3:
                raise
            wait_with_message(status, BASE_WAIT_SEC * attempt, f"転送が混雑しています（エラー{e.code}）")
    raise last_error


def wait_until_active(client, file_ref, status):
    """サーバー側の音声処理完了を待つ。上限時間とFAILEDを検知する"""
    start = time.time()
    while file_ref.state.name == "PROCESSING":
        elapsed = int(time.time() - start)
        if elapsed > FILE_PROCESS_TIMEOUT_SEC:
            raise TimeoutError("音声ファイルの処理が時間内に終わりませんでした。")
        status.markdown(f"⏳ **音声ファイルを準備中…（{elapsed}秒経過）**")
        time.sleep(5)
        file_ref = client.files.get(name=file_ref.name)
    if file_ref.state.name != "ACTIVE":
        raise RuntimeError(f"音声ファイルの処理に失敗しました（状態: {file_ref.state.name}）")
    return file_ref


def generate_with_retry(client, contents, status):
    """候補モデルを順に試し、混雑時は指数バックオフで再試行する"""
    last_error = None
    for model in MODEL_CANDIDATES:
        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                status.markdown(f"⏳ **{model} で解析中…（{attempt}/{MAX_ATTEMPTS_PER_MODEL}回目・1〜3分かかります）**")
                response = client.models.generate_content(model=model, contents=contents)
                if not response.text:
                    raise RuntimeError("Geminiから空の応答が返りました。")
                return response.text, model
            except genai_errors.APIError as e:
                last_error = e
                if e.code == 404:
                    # このモデル名は存在しない → 待たずに次の候補へ
                    break
                if e.code not in RETRYABLE_CODES:
                    # 音声形式の不備など、再試行しても直らないエラー
                    raise
                if attempt == MAX_ATTEMPTS_PER_MODEL:
                    # このモデルは諦めて次の候補へ
                    break
                wait = min(MAX_WAIT_SEC, BASE_WAIT_SEC * (2 ** (attempt - 1))) + random.uniform(0, 3)
                wait_with_message(status, wait, f"{model} が混雑しています（エラー{e.code}）")
    if last_error is not None:
        raise last_error
    raise RuntimeError("利用可能なモデルが見つかりませんでした。")


# =========================================================
# ここから下は元の画面構成のまま
# =========================================================
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

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                st.error("認証エラー: GEMINI_API_KEYが登録されていません。")
                st.stop()

            client = genai.Client(api_key=api_key)
            temp_path = None
            audio_file_ref = None

            try:
                ext = os.path.splitext(uploaded_file.name)[1].lower()

                # 利用者ごとに別名の一時ファイルを作る（同時利用での上書き防止）
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    temp_path = tmp.name

                mime_map = {'.wav': 'audio/wav', '.mp3': 'audio/mp3', '.m4a': 'audio/m4a'}
                mime_type = mime_map.get(ext, 'audio/mp3')

                # 音声は1回だけアップロードし、再試行ではこれを使い回す
                audio_file_ref = upload_with_retry(client, temp_path, mime_type, status_placeholder)
                audio_file_ref = wait_until_active(client, audio_file_ref, status_placeholder)

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
                ■ 1. 議事録（決定事項・争点・Next Actions）
                ■ 2. 企画案A（タイトル、核心アイデア、コストの引き算、参照すべき海外最新事例、具体的な実行ステップ）
                ■ 3. 企画案B（同上）
                """

                output_text, used_model = generate_with_retry(client, [audio_file_ref, prompt], status_placeholder)

                status_placeholder.empty()
                st.success(f"✅ 解析が完了しました（使用モデル: {used_model}）。成果物(TXT)をダウンロードしてください。")

                st.download_button(
                    label="📥 成果物(TXT)をダウンロードする",
                    data=output_text,
                    file_name="光文社ビジクリ部_議事録_企画案.txt",
                    mime="text/plain",
                    use_container_width=True
                )

                st.markdown("### 🎯 成果物プレビュー")
                st.text(output_text)

            except genai_errors.APIError as e:
                status_placeholder.empty()
                if e.code in RETRYABLE_CODES:
                    st.error(f"Geminiの混雑が続いており、全モデルで再試行しましたが完了できませんでした（エラー{e.code}）。時間をおいて再実行してください。")
                else:
                    st.error(f"Geminiでエラーが発生しました（エラー{e.code}）: {e}")
            except Exception as e:
                status_placeholder.empty()
                st.error(f"エラーが発生しました: {e}")
            finally:
                # 成功・失敗にかかわらず、Gemini側とサーバー側の音声を必ず削除
                if audio_file_ref is not None:
                    try:
                        client.files.delete(name=audio_file_ref.name)
                    except Exception:
                        pass
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
