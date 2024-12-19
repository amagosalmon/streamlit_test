import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta
import sqlite3
import plotly.express as px

# データベースへの接続
conn = sqlite3.connect('reservations.db', check_same_thread=False)
c = conn.cursor()

# テーブルの作成
c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department TEXT,
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

# サイドバーで表示内容を選択
st.sidebar.title("メニュー")
page = st.sidebar.radio("表示を選択してください", ["新規予約", "予約一覧", "予約カレンダー"])

if page == "新規予約":
    # 予約フォームの作成
    st.header('新規予約')
    with st.form('reservation_form'):
        department = st.text_input('部署を入力してください')
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
            if not department:
                st.error('部署を入力してください。')
            elif not name:
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
                            INSERT INTO reservations (department, name, equipment, start_datetime, end_datetime, remarks)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (department, name, item, start_datetime.isoformat(), end_datetime.isoformat(), remarks))
                    conn.commit()
                    st.success('予約が完了しました！')

elif page == "予約一覧":
    # 予約一覧の表示と編集・キャンセル機能
    st.header('予約一覧')

    # データベースから予約データを取得
    c.execute('SELECT * FROM reservations ORDER BY start_datetime')
    reservations = c.fetchall()

    if reservations:
        # データフレームに変換
        df = pd.DataFrame(reservations, columns=['ID', '部署', '氏名', '備品', '開始日時', '終了日時', '備考'])
        # 日時のフォーマットを整える
        df['開始日時'] = pd.to_datetime(df['開始日時'])
        df['終了日時'] = pd.to_datetime(df['終了日時'])
        df['開始'] = df['開始日時'].dt.strftime('%Y-%m-%d %H:%M')
        df['終了'] = df['終了日時'].dt.strftime('%Y-%m-%d %H:%M')
        # 予約の表示
        st.dataframe(df[['ID', '部署', '氏名', '備品', '開始', '終了', '備考']])

        # 予約の選択
        st.subheader('編集またはキャンセルしたい予約のIDを入力してください')
        selected_id = st.number_input('予約ID', min_value=1, step=1)
        action = st.selectbox('アクションを選択してください', ['選択してください', '編集', 'キャンセル'])

        if action == '編集':
            st.subheader('予約の編集')
            reservation = df[df['ID'] == selected_id]
            if not reservation.empty:
                with st.form('edit_form'):
                    department = st.text_input('部署を入力してください', reservation['部署'].values[0])
                    name = st.text_input('氏名を入力してください', reservation['氏名'].values[0])
                    equipment = st.multiselect('備品を選択してください（複数選択可）', equipment_list, [reservation['備品'].values[0]])

                    # 日付と時間の入力
                    start_datetime = reservation['開始日時'].values[0]
                    end_datetime = reservation['終了日時'].values[0]

                    start_date = st.date_input('開始日を選択してください', start_datetime.date())
                    start_time = st.time_input('開始時間を選択してください', start_datetime.time())
                    end_date = st.date_input('終了日を選択してください', end_datetime.date())
                    end_time = st.time_input('終了時間を選択してください', end_datetime.time())

                    remarks = st.text_area('備考があればご記入ください', reservation['備考'].values[0])
                    submit = st.form_submit_button('更新する')

                    if submit:
                        # 日時の組み合わせ
                        new_start_datetime = datetime.combine(start_date, start_time)
                        new_end_datetime = datetime.combine(end_date, end_time)

                        # 入力チェック
                        if not department:
                            st.error('部署を入力してください。')
                        elif not name:
                            st.error('氏名を入力してください。')
                        elif not equipment:
                            st.error('最低でも1つの備品を選択してください。')
                        elif new_start_datetime >= new_end_datetime:
                            st.error('開始日時は終了日時より前にしてください。')
                        else:
                            # 重複予約のチェック
                            conflicts = []
                            for item in equipment:
                                c.execute('''
                                    SELECT * FROM reservations
                                    WHERE equipment = ?
                                    AND id != ?
                                    AND (
                                        (start_datetime < ? AND end_datetime > ?)
                                    )
                                ''', (item, selected_id, new_end_datetime.isoformat(), new_start_datetime.isoformat()))
                                conflict = c.fetchall()
                                if conflict:
                                    conflicts.append(item)

                            if conflicts:
                                st.error(f'以下の備品は選択した期間に既に予約されています：{", ".join(conflicts)}')
                                st.info('別の期間を選択するか、これらの備品を外して再度お試しください。')
                            else:
                                # 予約の更新
                                c.execute('''
                                    UPDATE reservations
                                    SET department = ?, name = ?, equipment = ?, start_datetime = ?, end_datetime = ?, remarks = ?
                                    WHERE id = ?
                                ''', (department, name, ', '.join(equipment), new_start_datetime.isoformat(), new_end_datetime.isoformat(), remarks, selected_id))
                                conn.commit()
                                st.success('予約が更新されました！')
            else:
                st.warning('指定されたIDの予約が見つかりませんでした。')

        elif action == 'キャンセル':
            st.subheader('予約のキャンセル')
            reservation = df[df['ID'] == selected_id]
            if not reservation.empty:
                st.write('以下の予約をキャンセルしますか？')
                st.table(reservation[['ID', '部署', '氏名', '備品', '開始', '終了', '備考']])
                confirm = st.button('キャンセルする')

                if confirm:
                    # 予約の削除
                    c.execute('DELETE FROM reservations WHERE id = ?', (selected_id,))
                    conn.commit()
                    st.success('予約がキャンセルされました！')
            else:
                st.warning('指定されたIDの予約が見つかりませんでした。')

    else:
        st.write('現在、予約はありません。')

elif page == "予約カレンダー":
    # 予約カレンダーの表示
    st.header('予約カレンダー')

    # データベースから予約データを取得
    c.execute('SELECT * FROM reservations')
    reservations = c.fetchall()

    if reservations:
        # データフレームに変換
        df = pd.DataFrame(reservations, columns=['ID', '部署', '氏名', '備品', '開始日時', '終了日時', '備考'])
        # 日時のフォーマットを調整
        df['開始日時'] = pd.to_datetime(df['開始日時'])
        df['終了日時'] = pd.to_datetime(df['終了日時'])

        # 当日の予約のみを表示
        today = pd.Timestamp(date.today())
        df = df[(df['開始日時'] >= today) & (df['開始日時'] < today + timedelta(days=1))]

        if df.empty:
            st.write('本日の予約はありません。')
        else:
            # 各予約にユニークな色を割り当てる
            df['予約番号'] = df['ID'].astype(str)

            # ガントチャートでカレンダー表示を作成
            fig = px.timeline(
                df,
                x_start="開始日時",
                x_end="終了日時",
                y="備品",
                color="予約番号",
                hover_data=['部署', '氏名', '備考'],
                title="予約カレンダー（本日）",
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig.update_yaxes(autorange="reversed")  # Y軸を反転（上から下に時系列順）

            # 表示期間を当日のみに設定
            fig.update_xaxes(
                range=[
                    today,
                    today + timedelta(days=1)
                ],
                tickformat="%H:%M"
            )

            # グラフを表示
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.write('現在、予約はありません。')
