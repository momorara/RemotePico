"""
2023/09/04  passCordを当日の月日とした、さらにこれを暗号化して送信する。
            passCodeは月日としようとしたが、一日同じなので、
            # 時間と日にした
            ただし、ラズパイ上では日時は合っているが、streamit上では、9時間ずれているので注意
            pytzを使って補正した

2025/04/21  RemotePicoをWebAppで制御できるように改造
2025/04/24  セキュリティコードを有効にする
2025/05/01  henkanをsecrets.toml として、cloudに保存した

説明、
スイッチ6個のうち1つが押されると、mqttを送信する
送信する際のトピックはtopicで設定されたもの1つ
送信内容は、日、時間により暗号化されたものと末尾にスイッチの番号が付与される。

受信側で、復号化して日と時間が一致していれば、正しい信号と考え
末尾のスイッチ番号により操作を行う。

mqttの信号は平文で送っているので、同じ内容を送られ妨害されたことがあり
このようにしている、この対策以降妨害はない模様。

web_RemotePicoW.py
"""
import streamlit as st
import paho.mqtt.client as mqtt     # MQTTのライブラリをインポート
from time import sleep              # 3秒間のウェイトのために使う
import random
import string
import datetime
import pytz

# シークレット設定
henkan = st.secrets["secret_keys"]["henkan"]
# mqttトピック
topic = st.secrets["secret_keys"]["topic"]

# 設定値
broker = "broker.hivemq.com"          # 無料mqttブローカー
Web_title = 'WebRemote v40'

# スイッチの名称変更が可能です。
sw_name0  = 'SW-0 @ RemotePico'
sw_name1  = 'SW-1 @ RemotePico'
sw_name2  = 'SW-2 @ RemotePico'
sw_name3  = 'SW-3 @ RemotePico'
sw_name4  = 'SW-4 @ RemotePico'
sw_name5  = 'SW-5 @ RemotePico'

# pin_code 日時から作成するコードでpicoW側でも作り、照合する。
# sec_code webで都度入力するセキュリティコード　picoW側で設定しておいたものと照合する。
sec_code = "null"
# 画面上6桁の数字としているが、zを除くアルファベットも使えます。
"""
Copyright (c) 2025 TKJ_Works
"""

# ランダム文字列を作る
def generate_random_string(length):
    # 現在の日付と時刻を取得
    current_datetime = datetime.datetime.now()
    # 年、月、日、時、分、秒を取得
    day = current_datetime.day
    minute = current_datetime.minute
    second = current_datetime.second
    # 年、月、日、時、分、秒を文字列に変換し、結合して種(seed)とする
    seed = f"{day}-{minute}-{second}"
    # 乱数生成器に種(seed)を設定
    random.seed(seed)
    # 半角アルファベット（大文字と小文字）を含む文字列を作成
    characters = string.ascii_letters
    random_string = ""
    # 指定された長さまでループを実行
    for _ in range(length):
        # 半角アルファベットからランダムに文字を選び、それをrandom_stringに追加
        random_character = random.choice(characters)
        random_string += random_character
    return random_string

def encryption():
    # 例: 長さが20のランダムな文字列を生成
    random_string = generate_random_string(30)

    # UTC時間を取得
    current_datetime_utc = datetime.datetime.now(pytz.utc)
    # 日本標準時（JST）に変換
    jst_timezone = pytz.timezone('Asia/Tokyo')
    current_datetime_jst = current_datetime_utc.astimezone(jst_timezone)
    # 必要な情報を取得
    minute = current_datetime_jst.minute
    day = current_datetime_jst.day
    hour = current_datetime_jst.hour
    # 分については、コード化を1桁にするため 6 で割る
    # さらに 複合の際には 6で割った数字と　+1した分を　OKとする
    print(minute,"分なので6で割ると",minute//6)

    # パスコードを計算
    passCode = hour * 1000 + day * 10 + minute//6
    print("passCode",passCode)
    
    # passCodeを一桁ごとの数字に分解
    hh = int(passCode/1000)
    d1 = int((passCode - hh*1000)/100)
    d2 = int(passCode/10) - hh*100 - d1*10
    m6 = passCode - hh*1000 - d1*100 - d2*10
    print(passCode,hh,d1,d2,m6)
    #
    # henkan = "abcdefghijklmnopqrstuvwxyz"
    # henkan = "lmstuvhinogpjabcdefkqwxyzr"  # たまに変えると良い、受信側も変えること
    hh_s = henkan[hh]
    d1_s = henkan[d1+10] # 全体を使うように
    d2_s = henkan[d2+7]  # 全体を使うように
    m6_s = henkan[m6+9]  # 全体を使うように
    # ランダム文字に埋め込む
    modified_string = (
    random_string[:3] + hh_s + random_string[5:7] +
    d1_s + random_string[9:11] + d2_s + random_string[13:15] + m6_s + random_string[17:])
    # print(hh,d1,d2,m6)
    print(hh_s ,d1_s ,d2_s ,m6_s)
    # print(modified_string)
    return modified_string

# --------------- publish ---------------
# ブローカーに接続できたときの処理
def on_connect(client, userdata, flag, rc):
  print("Connected with result code " + str(rc))

# ブローカーが切断したときの処理
def on_disconnect(client, userdata, flag, rc):
  if rc != 0:
     print("Unexpected disconnection.")

# publishが完了したときの処理
def on_publish(client, userdata, mid):
  print("publish: {0}".format(mid))

def mqtt_pub(broker,topic,pin_code):
    try:
        client = mqtt.Client()                 # クラスのインスタンス(実体)の作成
        client.on_connect = on_connect         # 接続時のコールバック関数を登録
        client.on_disconnect = on_disconnect   # 切断時のコールバックを登録
        client.on_publish = on_publish         # メッセージ送信時のコールバック
        print()
        print('***',broker,'***')
        sleep(1)
        client.connect(broker, 1883, 60)  # 接続先は自分自身
        print('connect')
        sleep(1)
        # 通信処理スタート
        client.loop_start()    # subはloop_forever()だが，pubはloop_start()で起動だけさせる
        print('loop_start')
        sleep(3)
        # 除湿器スタートコマンド送信
        print('publish topic',topic)
        client.publish(topic, pin_code, qos=0)
        sleep(1)
        # プローカーの調子が悪くmqttが通らなくてもエラーにならない
        # なので、2個届いてしまう。
    except:
        print('publish error')

def mqtt_broker_set(topic,pin_code):
    # ブローカーが調子の悪い時があるので、切り替えてpubします。
    # なので、調子の良い時には2つのpublishが届くので、注意が必要
    # broker = 'mqtt.eclipseprojects.io' 
    # mqtt_pub(broker,pin_code,topic)
    # broker = 'broker.emqx.io'

    # ここで送信する
    # broker = "broker.hivemq.com"
    mqtt_pub(broker,topic,pin_code)

def input():
    # webAppの画面を構成
    date1 = st.date_input('Input date1')
    date2 = st.date_input('Input date2')

    remote_sw0  = st.button(sw_name0) # remote_sw0
    remote_sw1  = st.button(sw_name1) # remote_sw1
    remote_sw2  = st.button(sw_name2) # remote_sw2
    remote_sw3  = st.button(sw_name3) # remote_sw3
    remote_sw4  = st.button(sw_name4) # remote_sw4
    remote_sw5  = st.button(sw_name5) # remote_sw5
    
    #return air_on_izumo,air_off,air_on_sozu,defumdy,date1,date2
    return remote_sw0,remote_sw1,remote_sw2,remote_sw3,remote_sw4,remote_sw5,date1,date2

def main():

    # 暗号を作成する
    modified_string = encryption()
            
    st.title(Web_title)

    temp,humdy = 24,45  # ダミー表示
    st.write("温度:",temp," / 湿度:",humdy)

    remote_sw0,remote_sw1,remote_sw2,remote_sw3,remote_sw4,remote_sw5,date1,date2 = input()
    st.write(remote_sw0,remote_sw1,remote_sw2,remote_sw3,remote_sw4,remote_sw5)

    # 暗号を作成する
    modified_string = encryption()

    # セキュリティコード入力
    sec_code = st.text_input('セキュリティコードを数字6桁で入力してください。')
    st.write("入力内容:",sec_code)
    
    # 押されたボタンによって、publish内容を変える。
    sw = 9
    # topic = "tkj/remote/2025/sw012345"
    if remote_sw0 == True :
        sw = "0"
    if remote_sw1 == True :
        sw = "1"
    if remote_sw2 == True :
        sw = "2"
    if remote_sw3 == True :
        sw = "3"
    if remote_sw4 == True :
        sw = "4"
    if remote_sw5 == True :
        sw = "5"

    # ボタンが押されていることが送信の条件
    if remote_sw0 == True or remote_sw1 == True or remote_sw2 == True or remote_sw3 == True or remote_sw4 == True or remote_sw5 == True:
        # mqttでpublishする
        st.write('publish',topic,modified_string , sw , sec_code)
        mqtt_broker_set(topic,modified_string + sw + "z" + sec_code)
        # "z"があるのは、受信側でsec_codeを取り出すためです。
        # mqtt_broker_set(topic,modified_string + sw )

    # 表示をリセット
    reset  = st.button('reset')

if __name__ == '__main__':
    main()