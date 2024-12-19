import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta
import sqlite3
import plotly.express as px

# データベースへの接続
conn = sqlite3.connect('reservations.db', check_same_thread=False)
c = conn.cursor()

# テーブルの作成（テーブルスキーマの変更に注意）
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
                # 重複予約のチェック
                conflicts = []
                # 既存の予約を取得
                c.execute('SELECT equipment, start_datetime, end_datetime FROM reservations')
                existing_reservations = c.fetchall()

                for item in equipment:
                    for existing_equipment_str, existing_start_str, existing_end_str in existing_reservations:
                        existing_equipment = existing_equipment_str.split(', ')
                        if item in existing_equipment:
                            existing_start = datetime.fromisoformat(existing_start_str)
                            existing_end = datetime.fromisoformat(existing_end_str)
                            if not (end_datetime <= existing_start or start_datetime >= existing_end):
                                conflicts.append(item)
                                break  # 一度見つかったら次のアイテムへ

                if conflicts:
                    st.error(f'以下の備品は選択した期間に既に予約されています：{", ".join(conflicts)}')
                    st.info('別の期間を選択するか、これらの備品を外して再度お試しください。')
                else:
                    # 予約データの挿入（1レコードにまとめる）
                    equipment_str = ', '.join(equipment)
                    c.execute('''
                        INSERT INTO reservations (department, name, equipment, start_datetime, end_datetime, remarks)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (department, name, equipment_str, start_datetime.isoformat(), end_datetime.isoformat(), remarks))
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
                    equipment = st.multiselect('備品を選択してください（複数選択可）', equipment_list, reservation['備品'].values[0].split(', '))

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
                            # 自分以外の予約を取得
                            c.execute('SELECT equipment, start_datetime, end_datetime FROM reservations WHERE id != ?', (selected_id,))
                            existing_reservations = c.fetchall()

                            for item in equipment:
                                for existing_equipment_str, existing_start_str, existing_end_str in existing_reservations:
                                    existing_equipment = existing_equipment_str.split(', ')
                                    if item in existing_equipment:
                                        existing_start = datetime.fromisoformat(existing_start_str)
                                        existing_end = datetime.fromisoformat(existing_end_str)
                                        if not (new_end_datetime <= existing_start or new_start_datetime >= existing_end):
                                            conflicts.append(item)
                                            break  # 一度見つかったら次のアイテムへ

                            if conflicts:
                                st.error(f'以下の備品は選択した期間に既に予約されています：{", ".join(conflicts)}')
                                st.info('別の期間を選択するか、これらの備品を外して再度お試しください。')
                            else:
                                # 予約の更新
                                equipment_str = ', '.join(equipment)
                                c.execute('''
                                    UPDATE reservations
                                    SET department = ?, name = ?, equipment = ?, start_datetime = ?, end_datetime = ?, remarks = ?
                                    WHERE id = ?
                                ''', (department, name, equipment_str, new_start_datetime.isoformat(), new_end_datetime.isoformat(), remarks, selected_id))
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

    # 日付選択機能を追加
    selected_date = st.date_input('表示したい日付を選択してください', date.today())

    # データベースから予約データを取得
    c.execute('SELECT * FROM reservations')
    reservations = c.fetchall()

    if reservations:
        # データフレームに変換
        df = pd.DataFrame(reservations, columns=['ID', '部署', '氏名', '備品', '開始日時', '終了日時', '備考'])
        # 日時のフォーマットを調整
        df['開始日時'] = pd.to_datetime(df['開始日時'])
        df['終了日時'] = pd.to_datetime(df['終了日時'])

        # 選択した日の予約のみを表示
        selected_day = pd.Timestamp(selected_date)
        next_day = selected_day + timedelta(days=1)
        df = df[(df['開始日時'] < next_day) & (df['終了日時'] > selected_day)]

        if df.empty:
            st.write(f'{selected_date}の予約はありません。')
        else:
            # 各予約を備品ごとに分解
            expanded_rows = []
            for idx, row in df.iterrows():
                equipment_items = row['備品'].split(', ')
                for item in equipment_items:
                    new_row = row.copy()
                    new_row['備品'] = item
                    expanded_rows.append(new_row)

            expanded_df = pd.DataFrame(expanded_rows)
            # 各予約にユニークな色を割り当てる
            expanded_df['予約番号'] = expanded_df['ID'].astype(str)

            # ガントチャートでカレンダー表示を作成
            fig = px.timeline(
                expanded_df,
                x_start="開始日時",
                x_end="終了日時",
                y="備品",
                color="予約番号",
                hover_data=['部署', '氏名', '備考'],
                title=f"予約カレンダー（{selected_date}）",
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig.update_yaxes(autorange="reversed")  # Y軸を反転（上から下に時系列順）

            # 表示期間を選択した日のみに設定
            fig.update_xaxes(
                range=[
                    selected_day,
                    next_day
                ],
                tickformat="%H:%M"
            )

            # グラフを表示
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.write('現在、予約はありません。')
