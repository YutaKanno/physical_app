import pandas as pd
import streamlit as st
import plotly.express as px
import statsmodels.api as sm
import sqlite3

st.set_page_config(
        page_title="My Streamlit App",
        page_icon="📈",
        layout="wide",  # ウィンドウサイズに合わせて広く表示
    )


conn = sqlite3.connect('id_database.db')
id_list = pd.read_sql_query("SELECT * FROM id_table", conn)
conn.close()

conn = sqlite3.connect('physical_rawdata.db')
rawdata_original = pd.read_sql_query("SELECT * FROM physical_rawdata", conn)
conn.close()

# タブを作成
tab1, tab2, tab3 = st.tabs(["グラフ", "ID入力", "テストデータ入力"])

with tab1:
    if st.button("データを更新"):
        conn = sqlite3.connect('physical_rawdata.db')
        rawdata_original = pd.read_sql_query("SELECT * FROM physical_rawdata", conn)
        conn.close()
        st.success("データが更新されました")
        
    rawdata_original['date'] = pd.to_datetime(rawdata_original['date'])  # 例: 2025/04/13 形式

    id_list_unique = id_list.drop_duplicates(subset=['ID'])  # ID列で重複を削除
    rawdata = rawdata_original.merge(id_list_unique[['ID', '名前']], on='ID', how='left')
    # データを表示
    st.write(rawdata)


    

    st.title("Plot Physical Data")

    # 名前とTest Itemの選択
    names = rawdata['名前'].unique()
    test_items = rawdata['Test Item'].unique()

    selected_test = st.selectbox("Test種目を選択", test_items)
    selected_name = st.selectbox("名前を選択", names)

    # フィルタリング
    filtered = rawdata[
        (rawdata['名前'] == selected_name) &
        (rawdata['Test Item'] == selected_test)
    ]


    if filtered.empty:
        st.warning("該当データがありません")
    else:
        filtered = filtered.sort_values(by='date') 
        X = pd.to_datetime(filtered['date']).map(pd.Timestamp.toordinal)  # 日付を数値に変換
        X = sm.add_constant(X)  # 定数項（切片）を追加
        y = filtered['Result']

        # 回帰モデルを作成
        model = sm.OLS(y, X)
        results = model.fit()

        # 回帰直線の予測値を計算
        filtered['trendline'] = results.predict(X)

        # 時系列グラフをプロット
        fig = px.line(filtered, x='date', y='Result', markers=True,
                    title=f"{selected_name} の {selected_test} の推移",
                    labels={"date": "日付", "Result": "結果"})

        # 回帰直線を追加（オレンジ色の点線）
        fig.add_scatter(x=filtered['date'], y=filtered['trendline'], mode='lines', name='回帰直線', line=dict(color='orange', dash='dot'))


        st.plotly_chart(fig, use_container_width=True)
            

with tab2:
    st.header("ID入力")
    st.write("現在のIDリスト:")
    st.write(id_list)

    st.write("IDリストの更新:")
    with st.form("id_form"):
        new_name = st.text_input("新しい名前(ja)を入力")
        new_eng_name = st.text_input("新しい名前(eng)を入力")
        new_id = st.text_input("新しいIDを入力")
        submitted = st.form_submit_button("追加")
        if submitted:
            conn = sqlite3.connect('id_database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO id_table (名前, Name, ID) VALUES (?, ?, ?)", (new_name, new_eng_name, new_id))
            conn.commit()
            conn.close()
            st.success("新しいIDが追加されました")
            
        st.write("最新のIDリストを再表示:")
        id_list = pd.read_sql_query("SELECT * FROM id_table", sqlite3.connect('id_database.db'))
        st.write(id_list)
    # 一番下の行を削除するボタンをフォーム外に移動
    st.write("一番下の行を削除するには以下のボタンを押してください:")
    if st.button("一番下の行を削除"):
        conn = sqlite3.connect('id_database.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM id_table WHERE rowid = (SELECT MAX(rowid) FROM id_table)")
        conn.commit()
        conn.close()
        st.success("一番下の行が削除されました")
        # 最新のIDリストを再表示
        id_list = pd.read_sql_query("SELECT * FROM id_table", sqlite3.connect('id_database.db'))
        st.write(id_list)
        

with tab3:
    st.header("テストデータ入力")
    
    with st.form("test_data_form"):
        test_name = st.text_input("名前(ja)を選択")
        test_date = st.date_input("日付を入力")
        test_pos = st.selectbox('ポジションを選択', ['P', 'C', 'IF', 'OF'])
        test_item = st.selectbox("Test Itemを選択", rawdata_original['Test Item'].unique())
        test_result = st.text_input("結果を入力")
        submitted = st.form_submit_button("追加")
        
        
        
        if submitted:
            if test_name not in id_list['名前'].values:
                st.warning("入力された名前はIDリストに存在しません")
                st.stop()
            else:
                test_eng_name = id_list.loc[id_list['名前'] == test_name, 'Name'].values[0]
                test_id = id_list.loc[id_list['名前'] == test_name, 'ID'].values[0]
                test_id = int(test_id)
                test_name_2 = f'{test_pos}_{test_name}'
            
            try:
                float(test_result)
            except ValueError:
                st.warning("結果は数値型で入力してください")
                st.stop()
                
            
                
            conn = sqlite3.connect('physical_rawdata.db')
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO physical_rawdata (Name_1, date, ID, Name_2, Position, [Test Item], Result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (test_eng_name, test_date, test_id, test_name_2, test_pos, test_item, test_result))
            conn.commit()
            conn.close()
            st.success("新しいテストデータが追加されました")
            
            
            
            conn = sqlite3.connect('physical_rawdata.db')
            rawdata_original = pd.read_sql_query("SELECT * FROM physical_rawdata", conn)
            conn.close()
            
            st.write(rawdata_original)
       
        
    st.write("一番下の行を削除するには以下のボタンを押してください:")
    if st.button("一番下の行を削除 (テストデータ)"):
        conn = sqlite3.connect('physical_rawdata.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM physical_rawdata WHERE rowid = (SELECT MAX(rowid) FROM physical_rawdata)")
        conn.commit()
        conn.close()
        st.success("一番下の行が削除されました")
        # 最新のテストデータを再表示
        conn = sqlite3.connect('physical_rawdata.db')
        rawdata_original = pd.read_sql_query("SELECT * FROM physical_rawdata", conn)
        conn.close()
        st.write(rawdata_original)
            
      
        
        

        