import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta
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
        start_datetime TEXT NOT NULL,
        end_datetime TEXT NOT NULL,
        remarks TEXT
    )
''')
conn.commit()

# 備品リストの更新
equipment_list = [
    '三角スピーカーマイク①',
    '三角スピーカーマイク②',
    '三角スピーカーマイク③',
    '三角スピーカーマイク④',
    '小型スピーカーマイク①',
    '小型スピーカーマイク②',
    '5連スピーカーマイク',
    'WEBカメラ（ズーム機能付き高画質）①',
    'WEBカメラ（ズーム機能付き高画質）②',
    'WEBカメラ（小型）',
    '三脚①',
    '三脚②',
    'プロジェクター①',
    'プロジェクター②',
    'プロジェクター③',
    'プロジェクター④',
    'ノートパソコン①',
    'ノートパソコン②',
    'Zoom'
]

# アプリのタイトル
st.title('備品貸し出し予約システム')

# 予約フォームの作成
with st.form('reservation_form'):
    st.header('新規予約')
    name = st.text_input('氏名を入力してください')
    equipment = st.multiselect('備品を選択してください（複数選択可）', equipment_list)

    # 日付と時間の入力
    start_date = st.date_input('開始日を選択してください', date.today())
    start_time = st.time_input('開始時間を選択してください', time(hour=9))
    end_date = st.date_input('終了日を選択してください', date.today())
    end_time = st.time_input('終了時間を選択してください', time(hour=10))

    remarks = st.text_area('備考があればご記入ください')
    submit = st.form_submit_button('予約する')

    if submit:
        # 日時の組み合わせ
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)

        # 入力チェック
        if not name:
            st.error('氏名を入力してください。')
        elif not equipment:
            st.error('最低でも1つの備品を選択してください。')
        elif start_datetime >= end_datetime:
            st.error('開始日時は終了日時より前にしてください。')
        else:
            # 各備品について重複予約をチェック
            conflicts = []
            for item in equipment:
                c.execute('''
                    SELECT * FROM reservations
                    WHERE equipment = ?
                    AND (
                        (start_datetime < ? AND end_datetime > ?)
                    )
                ''', (item, end_datetime.isoformat(), start_datetime.isoformat()))
                conflict = c.fetchall()
                if conflict:
                    conflicts.append(item)

            if conflicts:
                st.error(f'以下の備品は選択した期間に既に予約されています：{", ".join(conflicts)}')
                st.info('別の期間を選択するか、これらの備品を外して再度お試しください。')
            else:
                # 予約データの挿入（各備品ごと）
                for item in equipment:
                    c.execute('''
                        INSERT INTO reservations (name, equipment, start_datetime, end_datetime, remarks)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (name, item, start_datetime.isoformat(), end_datetime.isoformat(), remarks))
                conn.commit()
                st.success('予約が完了しました！')

# 予約一覧の表示
st.header('予約一覧')

# データベースから予約データを取得
c.execute('SELECT * FROM reservations ORDER BY start_datetime')
reservations = c.fetchall()

if reservations:
    # データフレームに変換
    df = pd.DataFrame(reservations, columns=['ID', '氏名', '備品', '開始日時', '終了日時', '備考'])
    # 日時のフォーマットを整える
    df['開始日時'] = pd.to_datetime(df['開始日時']).dt.strftime('%Y-%m-%d %H:%M')
    df['終了日時'] = pd.to_datetime(df['終了日時']).dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(df)
else:
    st.write('現在、予約はありません。')
