import sqlite3

# データベースへの接続
conn = sqlite3.connect('reservations.db')
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

# データの追加、取得、表示などの処理をSQLiteに置き換えます