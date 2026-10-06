import os
import pandas as pd
from datetime import date
import streamlit as st
import google.generativeai as genai

# ページ基本設定
st.set_page_config(page_title="LeanBulk AI Pro", page_icon="💪", layout="centered")

# --- Secrets / API Key 設定 ---
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.warning("⚠️ GEMINI_API_KEY が設定されていません。StreamlitのSecrets設定でAPIキーを登録してください。")

# --- データ保存用 CSV 設定 ---
DATA_FILE = "ppl_training_logs.csv"

def load_logs():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["日付", "部位", "種目名", "重量(kg)", "レップ数", "セット数", "メモ"])

def save_log(new_row):
    df = load_logs()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    return df

st.title("💪 LeanBulk AI Pro")
st.caption("あなた専用のパーソナル食事・トレーニング・ボディチェック管理アプリ")

# タブ作成
tab1, tab2, tab3 = st.tabs(["📸 AI食事・カロリー計算", "🏋️‍♂️ PPLトレログ", "📸 AIボディチェック"])

# --- TAB 1: AI食事・カロリー計算 ---
with tab1:
    st.header("📸 食事解析 & PFC自動計算")
    st.info("シフトや体調に合わせたPFCバランスを自動チェック！脂質は40g以下を意識しましょう。")
    
    input_type = st.radio("入力方法を選択", ["テキスト入力", "画像アップロード"], key="diet_type")
    
    if input_type == "テキスト入力":
        user_meal = st.text_area("食べたものを入力（例: 鯖缶1缶、白米200g、味噌汁、納豆1パック）")
        if st.button("AIで解析する", key="btn_text_diet"):
            if not api_key:
                st.error("APIキーが設定されていません。")
            elif user_meal:
                with st.spinner("AIがPFCとカロリーを計算中..."):
                    prompt = f"""
                    以下の食事内容を分析し、概算のカロリー、タンパク質(P)、脂質(F)、炭水化物(C)を出力してください。
                    また、フィジーク大会に向けたリーンバルク（脂質40g以下管理）としてのフィードバックを簡潔に記載してください。
                    食事内容: {user_meal}
                    """
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
            else:
                st.warning("食事内容を入力してください。")

    else:
        uploaded_file = st.file_uploader("食事の写真をアップロード", type=["jpg", "jpeg", "png"], key="diet_img")
        if uploaded_file and st.button("画像からAI解析する", key="btn_img_diet"):
            if not api_key:
                st.error("APIキーが設定されていません。")
            else:
                with st.spinner("画像を解析中..."):
                    image_data = uploaded_file.getvalue()
                    image_parts = [{"mime_type": uploaded_file.type, "data": image_data}]
                    prompt = "この画像に写っている食事の概算カロリーおよびPFC（タンパク質・脂質・炭水化物）を算出し、リーンバルク視点でのコメントを添えてください。"
                    response = model.generate_content([prompt, image_parts[0]])
                    st.markdown(response.text)

# --- TAB 2: PPLトレログ ---
with tab2:
    st.header("🏋️‍♂️ PPL トレーニング記録")
    
    # 既存ログの読み込み
    df_logs = load_logs()
    
    col_split, col_date = st.columns([2, 1])
    with col_split:
        split_type = st.selectbox("本日のトレーニング種別", ["Push (胸・肩前中部・三頭)", "Pull (背中・肩後部・二頭)", "Legs (脚・腹筋)"])
    with col_date:
        today_date = st.date_input("日付", date.today())

    st.subheader("📝 種目入力")
    exercise_name = st.text_input("種目名", placeholder="例: インクライン・ダンベルプレス")

    # --- 前回記録の自動参照機能 ---
    if exercise_name and not df_logs.empty:
        prev_logs = df_logs[df_logs["種目名"].astype(str).str.strip().str.lower() == exercise_name.strip().lower()]
        if not prev_logs.empty:
            last_record = prev_logs.iloc[-1]
            st.success(f"💡 **前回の記録 ({last_record['日付']})**: {last_record['重量(kg)']}kg × {last_record['レップ数']}Reps ({last_record['セット数']}セット)")
        else:
            st.info("💡 この種目の過去ログはまだありません。今日の記録が初となります！")

    col_w, col_r, col_s = st.columns(3)
    with col_w:
        weight = st.number_input("重量 (kg)", min_value=0.0, max_value=500.0, value=30.0, step=0.5)
    with col_r:
        reps = st.number_input("レップ数 (Rep)", min_value=1, max_value=100, value=8, step=1)
    with col_s:
        sets = st.number_input("セット数", min_value=1, max_value=20, value=3, step=1)
        
    memo = st.text_input("メモ（感覚・シート角度・ベンチ穴の位置など）", placeholder="例: ハンマーベンチ3個目の穴（30度）。ラスト1レップ粘れた")

    if st.button("トレーニングを記録・保存する", use_container_width=True):
        if exercise_name:
            new_data = {
                "日付": str(today_date),
                "部位": split_type.split(" ")[0],
                "種目名": exercise_name,
                "重量(kg)": weight,
                "レップ数": reps,
                "セット数": sets,
                "メモ": memo
            }
            df_logs = save_log(new_data)
            st.success(f"✅ 「{exercise_name}」を記録しました！")
            st.rerun()
        else:
            st.warning("種目名を入力してください。")

    st.divider()

    # --- 本日のトレーニングサマリー（メニュー一覧） ---
    st.subheader(f"📋 本日のメニュー一覧 ({today_date})")
    today_logs = df_logs[df_logs["日付"] == str(today_date)]
    
    if not today_logs.empty:
        for idx, row in today_logs.iterrows():
            memo_str = f" ｜ 💬 {row['メモ']}" if pd.notna(row['メモ']) and row['メモ'] != "" else ""
            st.markdown(f"・ **{row['種目名']}**: `{row['重量(kg)']}kg` × `{row['レップ数']}R` × `{row['セット数']}Set` {memo_str}")
    else:
        st.write("本日の記録はまだありません。種目を入力して追加してください！")

    st.divider()

    # --- 過去の全トレーニング履歴一覧 ---
    with st.expander("📊 過去のトレーニング全履歴を見る"):
        if not df_logs.empty:
            st.dataframe(df_logs.sort_values(by="日付", ascending=False), use_container_width=True)
        else:
            st.write("保存された履歴はまだありません。")

# --- TAB 3: AIボディチェック ---
with tab3:
    st.header("📸 トレ後ボディチェック & AI評価")
    st.info("トレ後の写真から、張り具合・むくみ・カットをAIが客観的に分析します！")
    
    body_img = st.file_uploader("身体の写真をアップロード", type=["jpg", "jpeg", "png"], key="body_img")
    if body_img and st.button("AIボディチェックを実行", key="btn_body_check"):
        if not api_key:
            st.error("APIキーが設定されていません。")
        else:
            with st.spinner("フィジーク目線でボディコンディションを分析中..."):
                image_data = body_img.getvalue()
                image_parts = [{"mime_type": body_img.type, "data": image_data}]
                prompt = """
                あなたはフィジーク競技のトップコーチです。
                添付された身体の写真を客観的に分析し、以下のポイントでフィードバックを行ってください：
                1. 大胸筋・三角筋・腹筋などの張り具合・パンプ感
                2. カット・絞り具合およびむくみ感
                3. バルクアップにおける短評とアドバイス
                """
                response = model.generate_content([prompt, image_parts[0]])
                st.markdown(response.text)
