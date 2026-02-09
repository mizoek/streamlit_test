import streamlit as st #type:ignore
import pandas as pd #type:ignore

def custom_uploader():
    st.info("👇のエリアにファイルをドラッグするか、「Browse files」から選択してください")

    uploaded_file = st.file_uploader(
        "ファイルドラッグ＆ドロップ、または選択してください",
        type=["csv", "png", "jpg", "pdf"]
    )

    if uploaded_file is not None:
        filename = uploaded_file.name.lower()

        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
                st.write("中身をチラ見せ：")
                st.dataframe(df.head())
            except Exception as e:
                st.error(f"CSVの読み込みに失敗しました: {e}")

        elif filename.endswith((".png", ".jpg", ".jpeg")):
            st.image(uploaded_file, caption="プレビュー")

        elif filename.endswith(".pdf"):
            st.warning("PDFはまだプレビューできません")

        else:
            st.warning(f"{uploaded_file.name} は未対応の形式です")

    return uploaded_file
