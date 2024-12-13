import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3

# データベースへの接続
conn = sqlite3.connect('reservations.db', check_same_thread=False)
c = conn.cursor()

# テーブルの作成
c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        equipment TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        remarks TEXT
    )
''')
conn.commit()

# 備品リスト
equipment_list = ['ノートパソコン', 'プロジェクター', '会議用スピーカー', 'デジタルカメラ']

# アプリのタイトル
st.title('備品貸し出し予約システム')

# 予約フォームの作成
with st.form('reservation_form'):
    st.header('新規予約')
    name = st.text_input('氏名を入力してください')
    equipment = st.selectbox('備品を選択してください', equipment_list)
    start_date = st.date_input('開始日を選択してください', date.today())
    end_date = st.date_input('終了日を選択してください', date.today() + timedelta(days=1))
    remarks = st.text_area('備考があればご記入ください')
    submit = st.form_submit_button('予約する')

    if submit:
        # 入力チェック
        if not name:
            st.error('氏名を入力してください。')
        elif start_date > end_date:
            st.error('開始日は終了日より前の日付を選択してください。')
        else:
            # 予約データの挿入
            c.execute('''
                INSERT INTO reservations (name, equipment, start_date, end_date, remarks)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, equipment, start_date.isoformat(), end_date.isoformat(), remarks))
            conn.commit()
            st.success('予約が完了しました！')

# 予約一覧の表示
st.header('予約一覧')

# データベースから予約データを取得
c.execute('SELECT * FROM reservations ORDER BY start_date')
reservations = c.fetchall()

if reservations:
    # データフレームに変換
    df = pd.DataFrame(reservations, columns=['ID', '氏名', '備品', '開始日', '終了日', '備考'])
    st.dataframe(df)
else:
    st.write('現在、予約はありません。')
