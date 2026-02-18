import streamlit as st # type:ignore
import pandas as pd # type:ignore
import json
import plotly.express as px # type:ignore
from datetime import date
from pathlib import Path

# ページ設定
st.set_page_config(page_title="レシート帳簿", layout="wide")

st.markdown(
    """
    <style>
    /* 全体の背景 */
    .stApp {
        /*
        background-image: url("assets/bg.png"); 画像を引っ張ってくるときはこう app_ver3.pyと同じ階層のassetsフォルダ直下にあるbg.pngを参照する、の意 
        background-size: cover; 画面いっぱい 
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed; スクロールしても固定
        */
        background-color: #f6f0e6;
    }

    /* サイドバーの背景 */
    section[data-testid="stSidebar"] {
        background-color: #eee6d8;
    }

    /* カードやコンテナっぽい部分を少し浮かせる */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- データ保存用ファイルの配置 ---
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data.json"

# --- データ保存用ファイルdata.jsonの新規作成 ---
def load_data():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # {"records": [...]} の形式
    if isinstance(data, dict):
        return data.get("records", [])

    # [...] の形式（過去データ救済用）
    if isinstance(data, list):
        return data

    return []


def save_data(records):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"records": records}, f, ensure_ascii=False, indent=2)

# --- データの読み込み ---
if "data_list" not in st.session_state:
    st.session_state.data_list = load_data()

# --- 1. サイドバー：入力エリア & 月間フィルター ---
with st.sidebar:
    st.title("💸 記録フォーム")
    
    # --- 入力フォーム ---
    with st.form("receipt_form", clear_on_submit=True):
        st.subheader("レシート内容を入力")
        shop_name = st.text_input("店名")
        pay_mean = st.selectbox(
            "支払い方法",
            ["現金", "クレジットカード", "iD", "PayPay", "楽天カード", "交通系IC", "その他", "---"],
            index=7
        )
        price = st.number_input("金額", min_value=0, step=1)
        expense_date = st.date_input("日付", date.today())
        submit_button = st.form_submit_button("記録する")

    if submit_button:
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
        save_data(st.session_state.data_list)

        st.toast(f"「{shop_name}」を記録しました！", icon="✅")
        st.rerun() # グラフに即時反映させるため

    st.divider()
    
    # --- 月間フィルターの追加 ---
    st.subheader("🔍 表示設定")
    if st.session_state.data_list:
        temp_df = pd.DataFrame(st.session_state.data_list)
        temp_df["年月"] = pd.to_datetime(temp_df["日付"]).dt.strftime('%Y-%m')
        month_list = sorted(temp_df["年月"].unique(), reverse=True)
        selected_month = st.selectbox("表示月を選択", month_list)
    else:
        selected_month = date.today().strftime('%Y-%m')

# --- 2. メインエリア：ダッシュボード ---
st.title("📊 家計簿ダッシュボード")

if st.session_state.data_list:
    # データ処理
    df_all = pd.DataFrame(st.session_state.data_list)
    df_all["日付_dt"] = pd.to_datetime(df_all["日付"]) # 計算用のdatetime型
    df_all["表示日付"] = df_all["日付_dt"].dt.strftime('%Y/%m/%d') # 表示用の整形
    df_all["年月"] = df_all["日付_dt"].dt.strftime('%Y-%m')

    # 選択された月でフィルタリング
    df = df_all[df_all["年月"] == selected_month].copy()

    # 3つの指標
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{selected_month} の合計", f"{df['金額'].sum():,} 円")
    m2.metric("記録件数", f"{len(df)} 件")
    # 「今日」の支出はフィルタに関わらず全体から計算、または今月の中から計算
    today_str = date.today().strftime('%Y/%m/%d')
    today_sum = df_all[df_all["表示日付"] == today_str]["金額"].sum()
    m3.metric("今日の支出", f"{today_sum:,} 円")

    st.divider()

    col1, col2 = st.columns([1, 1])

    # --- グラフ ---
    with col1:
        st.subheader(f"📅 {selected_month} の支出推移")
        daily_sum = df.groupby("表示日付")["金額"].sum().reset_index()
        fig = px.bar(daily_sum, x="表示日付", y="金額", text_auto=True)
        fig.update_layout(xaxis_title="日付", yaxis_title="金額")
        st.plotly_chart(fig, use_container_width=True)

    # --- 履歴一覧 ---
    with col2:
        st.subheader("📋 履歴一覧")
        # 編集用に表示日付ではなく「日付」を使用（保存形式維持のため）
        display_df = df.sort_values("日付", ascending=False)[["日付", "店名", "支払い方法", "金額"]]
        
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="data_editor_key"
        )

        # 編集保存ロジック（簡易化：全データをマージして保存）
        if st.button("変更を保存"):
            # フィルタ外のデータと、編集後のデータを合体させる
            others = df_all[df_all["年月"] != selected_month][["日付", "店名", "支払い方法", "金額"]]
            final_df = pd.concat([others, edited_df], ignore_index=True)
            st.session_state.data_list = final_df.to_dict("records")
            save_data(st.session_state.data_list)
            st.success("データを保存しました！")
            st.rerun()

    st.divider()

    col3, col4 = st.columns([1, 1])
    with col3:
        st.subheader("💳 支払い方法の割合")
        pay_sum = df.groupby("支払い方法")["金額"].sum().reset_index()
        fig_pie = px.pie(
            pay_sum, 
            values="金額", 
            names="支払い方法", 
            hole=0.5, # ドーナツの穴
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col4:
    # ここは将来のために空けておくか、簡単な統計を出す
        st.subheader("💡 今月のプチ分析")
        most_used_pay = pay_sum.loc[pay_sum['金額'].idxmax(), '支払い方法'] if not pay_sum.empty else "なし"
        st.info(f"今月最も使っている支払い方法は **{most_used_pay}** です。")
    
    # おまけ：総額を大きく出すなど
        st.metric("今月の平均日給（仮）", f"{int(df['金額'].sum() / 30):,} 円/日")


else:
    st.info("サイドバーからデータを入力してください。")