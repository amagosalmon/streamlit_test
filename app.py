import streamlit as st
import pandas as pd
from datetime import date, timedelta

# 仮の備品リスト
equipment_list = ['ノートパソコン', 'プロジェクター', '会議用スピーカー', 'デジタルカメラ']

# 予約データの初期化
if 'reservations' not in st.session_state:
    st.session_state['reservations'] = pd.DataFrame(columns=['氏名', '備品', '開始日', '終了日', '備考'])

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
            # 予約データの追加
            new_reservation = {
                '氏名': name,
                '備品': equipment,
                '開始日': start_date,
                '終了日': end_date,
                '備考': remarks
            }
            st.session_state['reservations'] = st.session_state['reservations'].append(new_reservation, ignore_index=True)
            st.success('予約が完了しました！')

# 予約一覧の表示
st.header('予約一覧')
if not st.session_state['reservations'].empty:
    st.dataframe(st.session_state['reservations'])
else:
    st.write('現在、予約はありません。')