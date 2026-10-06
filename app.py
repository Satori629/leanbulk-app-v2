import os
import pandas as pd
from datetime import date
import streamlit as st

# ページ基本設定
st.set_page_config(page_title="LeanBulk AI Pro", page_icon="💪", layout="centered")

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
st.caption("PPL トレーニング記録 & 履歴管理システム")

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
