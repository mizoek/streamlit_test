import streamlit as st #type:ignore
from uploader import custom_uploader

st.title("ファイル管理アプリ")

# 自作のアップローダーを呼び出す
file = custom_uploader()

if file:
    st.success(f"ファイル「{file.name}」を読み込みました！") 