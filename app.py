import streamlit as st # type:ignore
import pandas as pd # type:ignore
import json
import plotly.express as px # type:ignore
from datetime import date
from pathlib import Path

# ページ設定：ワイドレイアウトにするとダッシュボードらしくなります
st.set_page_config(page_title="レシート帳簿", layout="wide")

DATA_FILE = Path("data/payments.json")

# --- データ操作 ---
def load_data():
    if not DATA_FILE.exists():
        return {"records": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- データの読み込み セッションの初期化 ---
if "data_list" not in st.session_state:
    st.session_state.data_list = load_data().get("records", [])

# --- 1. サイドバー：入力エリア ---
with st.sidebar:
    st.title("💸 記録フォーム")
    with st.form("receipt_form", clear_on_submit=True):
        st.subheader("レシート内容を入力")
        shop_name = st.text_input("店名")
        pay_mean = st.selectbox(
            "支払い方法",
            ["現金", "クレジットカード", "iD", "PayPay", "楽天カード", "交通系IC", "その他", "---"]
        )
        price = st.number_input("金額", min_value=0, step=1)
        expense_date = st.date_input("日付", date.today())
        
        submit_button = st.form_submit_button("記録する")

    if submit_button:
        # 支払い方法の事故防止
        if pay_mean == "---":
            st.warning("支払い方法を選んでください。")
            st.stop()
        
        new_data = {
            "日付": str(expense_date), 
            "店名": shop_name,
            "支払い方法": pay_mean, 
            "金額": int(price)
        }
        st.session_state.data_list.append(new_data)
        save_data({"records": st.session_state.data_list})

        st.toast(f"「{shop_name}」を記録しました！", icon="✅")

# --- 2. メインエリア：ダッシュボードの表示・可視化 ---
st.title("📊 家計簿ダッシュボード")

if st.session_state.data_list:
    df = pd.DataFrame(st.session_state.data_list)
    df["日付"] = pd.to_datetime(df["日付"]).dt.strftime('%Y/%m/%d')
    
    # 3つの指標を横に並べて表示
    m1, m2, m3 = st.columns(3)
    m1.metric("合計支出", f"{df['金額'].sum():,} 円")
    m2.metric("記録件数", f"{len(df)} 件")
    m3.metric(
        "今日の支出", 
        f"{df[df['日付'].dt.date == date.today()]['金額'].sum():,} 円"
    )

    st.divider()

    # 画面を左右に分割
    col1, col2 = st.columns([1, 1])

    # --- グラフ ---
    with col1:
        st.subheader("📅 日別の支出推移")
        # Plotlyで動く棒グラフを作成
        daily_sum = df.groupby("日付")["金額"].sum().reset_index()
        fig = px.bar(daily_sum, x="日付", y="金額", text_auto=True)
        fig.update_traces(marker_color='#1f77b4') # 落ち着いた青色
        st.plotly_chart(fig, use_container_width=True) #

    # --- 編集可能な履歴表の描画
    with col2:
        st.subheader("📋 履歴一覧:クリックで編集可能")

        edited_df = st.data_editor(
            df.sort_values("日付", ascending=False),
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
        )

        # 編集があったら即保存
        if not edited_df.equals(df.sort_values("日付", ascending=False)):
            # 日付を文字列に戻して保存
            edited_df["日付"] = edited_df["日付"].astype(str)
            st.session_state.data_list = edited_df.to_dict("records")
            save_data({"records": st.session_state.data_list})
            st.toast("履歴を更新しました", icon="💾")
            st.rerun()

else:
    st.info("サイドバーからデータを入力してください。")