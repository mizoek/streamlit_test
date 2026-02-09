import streamlit as st # type:ignore
import pandas as pd #type:ignore
import json
import plotly.express as px # type:ignore
from datetime import date
from pathlib import Path

st.set_page_config(page_title="レシート帳簿", layout="wide")

DATA_FILE = Path("data/payments_ver2.json")

# --------------------
# データI/O
# --------------------
def load_data():
    if not DATA_FILE.exists():
        return {"records": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if "data_list" not in st.session_state:
    st.session_state.data_list = load_data().get("records", [])

# --------------------
# DataFrame化
# --------------------
if st.session_state.data_list:
    df_all = pd.DataFrame(st.session_state.data_list)
    df_all["日付"] = pd.to_datetime(df_all["日付"])
    df_all["年月"] = df_all["日付"].dt.strftime("%Y-%m")
else:
    df_all = pd.DataFrame(columns=["日付", "店名", "支払い方法", "金額", "年月"])

# --------------------
# サイドバー（ツリー型入力）
# --------------------
with st.sidebar:
    st.title("💸 記録フォーム")

    pay_list = sorted(df_all["支払い方法"].unique().tolist())
    pay_list = ["現金", "クレジットカード", "iD", "PayPay", "楽天カード", "交通系IC", "その他"] + pay_list
    pay_list = list(dict.fromkeys(pay_list))

    pay = st.selectbox("支払い方法", pay_list)

    # 選択された支払い方法の年月一覧
    df_pay = df_all[df_all["支払い方法"] == pay]

    today = date.today()

    # 2000~2100年までの年月を選択
    year = st.number_input("年", min_value=2000, max_value=2100, value=today.year)
    month_num = st.number_input("月", min_value=1, max_value=12, value=today.month)

    month = f"{int(year)}-{int(month_num):02d}"

    #month_list = sorted(df_pay["年月"].unique().tolist(), reverse=True)

    # 今月をデフォルトに追加
    #current_month = date.today().strftime("%Y-%m")
    #if current_month not in month_list:
    #    month_list = [current_month] + month_list

    #month = st.selectbox("年月", month_list)

    with st.form("receipt_form", clear_on_submit=True):
        st.subheader(f"{pay} / {month} の記録")

        shop_name = st.text_input("店名")
        price = st.number_input("金額", min_value=0, step=1)

        day = st.number_input("日", min_value=1, max_value=31, value=date.today().day)

        submit_button = st.form_submit_button("記録する")

    if submit_button:
        full_date = f"{month}-{int(day):02d}"

        new_data = {
            "日付": full_date,
            "店名": shop_name,
            "支払い方法": pay,
            "金額": int(price)
        }

        st.session_state.data_list.append(new_data)
        save_data({"records": st.session_state.data_list})
        st.toast(f"「{shop_name}」を記録しました！", icon="✅")
        st.rerun()

# --------------------
# メイン画面（ツリー連動）
# --------------------
st.title("📊 家計簿ダッシュボード")

if not df_all.empty:
    # 選択中ツリーでフィルタ
    df_view = df_all[
        (df_all["支払い方法"] == pay) &
        (df_all["年月"] == month)
    ]

    # メトリクス
    m1, m2, m3 = st.columns(3)
    m1.metric("この月の支出", f"{df_view['金額'].sum():,} 円")
    m2.metric("件数", f"{len(df_view)} 件")
    m3.metric("全期間合計", f"{df_all['金額'].sum():,} 円")

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📅 日別支出（この月）")
        daily_sum = df_view.groupby(df_view["日付"].dt.day)["金額"].sum().reset_index()
        daily_sum.columns = ["日", "金額"]

        fig = px.bar(daily_sum, x="日", y="金額", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📋 履歴")
        st.dataframe(
            df_view.sort_values("日付", ascending=False),
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("サイドバーからデータを入力してください。")
