"""
2025/04/24
streamlitのweb_RemotePicoW.pyからの信号を受信して動作します。
受信内容は
modified_string + sw + "z" + sec_code
で、
sec_codeはセキュリティコードでこのプログラムに組み込んだコードと比較し一致すればok
z以下を取り除いた内容を
解析して、受信した時間と一致していれば、swを取り出し、対応する動作をさせる。
2025/4/28
確実に信号が届くかなとQOSを2とかにしてみたら欠損がかなりの確率で発生した
QOS=0なら普通に届く、なんか使い方を間違えているのか?
まぁ届くならQOS=0で良いかな
・復号時のチェックで日替わりを考慮していないので、PM11:59分台の信号はエラーになります。
・mqttの信号がテスト時には30-40秒程度遅れて届いてます。
・mqttの到達時間は、ネット環境により実測 数秒から40秒程度ありました。

2025/04/28  thonnyとの接続での確認
2025/04/28  main.pyとしてRemotePicoとしての確認
    02
2025/04/29  resetを組み込み
2025/04/30  なぜか止まってしまうのをWDTで対処
            wdtのmaxが8.3秒なので、時間のかかりそうな箇所にwdt.feed() 
            を配置している。
2025/05/02  設定をconfig.pyに写した
    04

RemotePicoW_04.py
"""
main_py = 1 # 1の時はtmachine.reset()を有効にする。

import network
import time
from lib_mqtt import MQTTClient
# micropythonでは使えない
# import datetime
# import pytz
import ntptime
import time
import config
from machine import Pin,WDT,reset
# picoボード上のLED
led = Pin('LED', Pin.OUT)
def LEDonoff(i=4):
    for _ in range(i):
        led.on()
        time.sleep(.2)
        led.off()
        time.sleep(.2)

# ==== Wi-Fi接続情報 ====
SSID,PASSWORD = config.ID_PASS()

# ==== 暗号キー ====
# ==== セキュリティコード ====
# ==== MQTT トピック 設定 ====
henkan,sec_code_org,MQTT_TOPIC = config.secret_keys()

# ==== MQTTブローカー設定 ====
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
# MQTT_TOPIC configから取得

""" GPIO pin 設定 """""""""
# Remote pin設定
# tx_GPIO = 17   <--  send_file.pyで設定する
rx_GPIO = 1
# 表示用+ED　pin設定
display_LED = 0
# スイッチのpin設定
sw_n = 6 # swの数 6個全て
sw_pin = [13,15,10,12,14,11] # swのGPIO pin
# パターンでプラスが繋がっているため
dumy = Pin(26, Pin.IN)
""""""""""""  """"""""""""

led2 = Pin(display_LED, Pin.OUT,Pin.PULL_DOWN)
led2.on()
time.sleep(0.5)
led2.off()

# from UpyIrTx import UpyIrTx  <--  send_file.pyで設定する
from UpyIrRx import UpyIrRx
import json
import uos
# 信号送信用pin設定  <--  send_file.pyで設定する
# tx_pin = Pin(tx_GPIO, Pin.OUT) 
# tx = UpyIrTx(0, tx_pin)

# 信号受信用pin設定
rx_pin = Pin(rx_GPIO, Pin.IN) 
rx = UpyIrRx(rx_pin)

# picoのGPIOとSWの対応pinの設定
SW = [0,0,0,0,0,0]
SW[0] = Pin(sw_pin[0], Pin.IN, Pin.PULL_UP)
SW[1] = Pin(sw_pin[1], Pin.IN, Pin.PULL_UP)
SW[2] = Pin(sw_pin[2], Pin.IN, Pin.PULL_UP)
SW[3] = Pin(sw_pin[3], Pin.IN, Pin.PULL_UP)
SW[4] = Pin(sw_pin[4], Pin.IN, Pin.PULL_UP)
SW[5] = Pin(sw_pin[5], Pin.IN, Pin.PULL_UP)

# microPythonにはファィルコピーのコマンドが無いみたいなので作る
def copy_file(source, destination):
    try:
        # コピー元ファイルを読み込む
        with open(source, 'rb') as f_source:
            # コピー先ファイルに書き込む
            with open(destination, 'wb') as f_destination:
                # コピー元ファイルからデータを読み取り、コピー先ファイルに書き込む
                while True:
                    data = f_source.read(1024)  # データを1024バイトずつ読み取る
                    if not data:
                        break
                    f_destination.write(data)  # コピー先ファイルにデータを書き込む
        return True
    except OSError as e:
        print("Error:", e)
        return False

# 通信関係でおかしくなった場合、リセット処理をしてみる main_py = 1の場合のみ
def pico_reset():
    time.sleep(3)
    reset()

# 複号化
def decryption(modified_string):
    text = modified_string.decode('utf-8')  # または 'ascii'
    # セキュリティコード取り出し
    index = text.rfind('z')
    text_f = text[:index]  # zの位置を基準にその前の文字列を取り出す
    sec_code = text[index + 1:] # zの位置を基準にその後ろの文字列を取り出す

    print(text,text_f,sec_code)

    mm_s = text_f[3]
    d1_s = text_f[6]
    d2_s = text_f[9]
    m6_s = text_f[12]
    print("暗号化:",mm_s,d1_s,d2_s,m6_s)
    # 変換して数字に戻す
    
    mm = henkan.find(mm_s)
    d1 = henkan.find(d1_s) -10
    d2 = henkan.find(d2_s) -7
    m6 = henkan.find(m6_s) -9
    print("復号結果:",mm,d1,d2,m6)

    # セキュリティコードが違っている場合
    if sec_code_org != sec_code:
        mm = 30 #30時間という異常な数字にする
    return mm,d1,d2,m6,text_f

def ntp():
    try:
        # NTPで現在のUTC時刻を取得
        ntptime.settime()
    except:
        print("ntpエラー1")
        # ntpでエラーになるので、ホストを変えてみた
        ntptime.host = "time.google.com"  # または "ntp.nict.jp"（日本のNTP）
        try:
            ntptime.settime()  # これで RTC が UTC に設定される
        except:
            try:
                print("ntpエラー2")
                time.sleep(1)
                ntptime.host = "ntp.nict.jp" #（日本のNTP）
                ntptime.settime()  # これで RTC が UTC に設定される
            except:
                if main_py == 1:# ntp失敗でリセット処理をしてみる
                    pico_reset()

def now_time(flag):
    if flag == 0:# 起動時にntpする
        # ntpが成功するまで続ける
        ntp_err =1
        while ntp_err == 1:
            try:
                ntp()
                ntp_err =0
            except:
                time.sleep(1)
                # ntpが失敗したらwifiを接続し直してやってみる
                connect_wifi()

    # JST（UTC+9）に変換
    current_datetime_jst = time.localtime(time.time() + 9 * 60 * 60)
    formatted = "{}年{:02d}月{:02d}日 {:02d}:{:02d}:{:02d}".format(
    current_datetime_jst[0],  # 年
    current_datetime_jst[1],  # 月
    current_datetime_jst[2],  # 日
    current_datetime_jst[3],  # 時
    current_datetime_jst[4],  # 分
    current_datetime_jst[5]   # 秒
    )
    print("現在の日本時間:", formatted)

    # 必要な情報を取得 pythonの場合は、以下変更する事
    # 必要な情報をインデックスで取得 micropython
    day    = current_datetime_jst[2]
    hour   = current_datetime_jst[3]
    minute = current_datetime_jst[4]
    print(day,hour,minute)
    return day,hour,minute

# Wi-Fi接続関数
def connect_wifi():
    # wifi接続中LEDが点灯、接続できたら4回点滅して、消灯する。
    led.on()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(0.5)  # 少し待ってから再度有効化
    wlan.active(True)
    time.sleep(0.5)  # 少し待つ
    wlan.connect(SSID, PASSWORD)
    print("Wi-Fi接続中...")
    count = 10
    while not wlan.isconnected():
        time.sleep(0.5)
        count = count -1
        if count == 0 and main_py ==1:
            pico_reset() # wifi失敗でリセット処理をしてみる
    print("Wi-Fi接続完了:", wlan.ifconfig())
    led.off()
    time.sleep(0.3) 
    LEDonoff(8)

# --------------- メッセージ受信時のコールバック関数 ---------------
def message_callback(topic, msg):
    print("メッセージ受信:", topic, msg)
    mm,d1,d2,m6,text = decryption(msg)
    try:
        day,hour,minute = now_time(1)
    except:
        # ntpでエラーになったことがあるので
        time.sleep(3)
        try:
            day,hour,minute = now_time()
        except:
            time.sleep(3)
            if main_py ==1:
                pico_reset() # 失敗でリセット処理をしてみる

    # 2つ届く場合があるので、1つ処理したら、しばらくは無視するようにするべきか?

    # 日時によるセキュリティチェック
    dd = d1*10+d2
    # mqttの信号が概ね30秒遅れて届くので、毎正時に遅れの考慮が必要
    if dd == day and (hour == mm or hour-1 == mm) :
        # print("日時間が一致")
        if m6 == minute//6 or m6 == minute//6 -1:
            # print("分が一致")
            pass_check = 0
        else:
            if minute//6 == 0 and m6 == 9:
                # print("分が一致")
                pass_check = 0
            else:
                pass_check = 1
    else:
        pass_check = 1

    # 不一致の場合、その結果を保存してはどうか?
    if pass_check == 1:
        # パスコードが不一致 妨害行為のようです。
        # データを保存
        print("パスコード一致せず、妨害行為のようです。")
    else:
        print("パスコード一致")
        sw_no = -1
        try:
            sw_no = int(text[-1])
            print("sw:",sw_no)
        except:
            print("sw_noがおかしい")

    # パスコードが一致して、sw 0-5の場合 チョン押しの処理
    if pass_check == 0 and sw_no != -1:
        try:
            print("send file")
            on_sw_no = sw_no
            # 不要ファィルを削除
            try:uos.remove("data.json")
            except:pass
            #送信するファイルを'data.json'としてコピー
            # コピー元ファイル名とコピー先ファイル名を指定
            source_file = "iR_code_" + str(on_sw_no) + ".json"
            destination_file = 'data.json'
            # ファイルをコピーする
            if copy_file(source_file, destination_file):
                print("File copied successfully.")
            else:
                print("File copy failed.")

            # print("最終テストで送信する")
            # data.jsonを送信する
            with open('send_file.py', 'r') as f:
                code = f.read()
            exec(code)

        except:
            print("ファイルなし")
    return

# --------------- メイン処理 -----------------------
connect_wifi()
# 接続後すぐにmqttに行くと時間がかかるようだ
time.sleep(3)
now_time(0)

led.on()
client = MQTTClient(client_id="pico_client", server=MQTT_BROKER, port=MQTT_PORT)
client.set_callback(message_callback)
client.connect()
client.subscribe(MQTT_TOPIC, qos=0)
led.off()

print("MQTT接続 & 購読中...")
count = 10
# 8秒以内にfeedされなければリセット max 8.3秒らしい
wdt = WDT(timeout=8000)
try:
    while True:

        # mqttのチェック
        try:
            if count == 0:
                # sleepを長くすると、取りこぼしが発生するので、短くする。
                led2.on()
                client.check_msg()  # メッセージが来ているか確認
                led2.off()
                # LEDの点滅を間引く
                #print(".")
                led.on()
                time.sleep(0.05)
                led.off()
                # time.sleep(0.8)
                count = 50
                wdt.feed()  # WDTをリセット
            else:
                time.sleep(0.1)
                count = count -1
        except:
            time.sleep(3)
            # 失敗したら　rebootさせましょう

        # 押されたswを調べる on_sw_no=6で何も押されていない
        for on_sw_no in range(sw_n+1):
            # print(on_sw_no)
            try:
                if SW[on_sw_no].value() == 0:
                    break
            except:
                pass
        # print(on_sw_no)

        if on_sw_no != 6:# なにか押されたら

            # 0.8秒後に再度確認して、押されていたら「長押し」、押されていなかったら「チョン押し」
            time.sleep(0.8)
            if SW[on_sw_no].value() == 0:
                on_sw_mode = "長押し"
            else:
                on_sw_mode = "チョン押し"
            print(on_sw_no, on_sw_mode)

            # チョン押しなら　押されたスイッチのリモコン信号を送信
            if on_sw_mode == "チョン押し":
                try:
                    print("send file")

                    # 不要ファィルを削除
                    try:uos.remove("data.json")
                    except:pass
                    #送信するファイルを'data.json'としてコピー
                    # コピー元ファイル名とコピー先ファイル名を指定
                    source_file = "iR_code_" + str(on_sw_no) + ".json"
                    destination_file = 'data.json'
                    # ファイルをコピーする
                    if copy_file(source_file, destination_file):
                        print("File copied successfully.")
                    else:
                        print("File copy failed.")

                    # data.jsonを送信する
                    with open('send_file.py', 'r') as f:
                        code = f.read()
                    wdt.feed()  # WDTをリセット
                    exec(code)

                except:
                    print("ファイルなし")

            # 長押しなら　　　押されたスイッチのリモコン信号登録処理を行う
            if on_sw_mode == "長押し":
                print("read file")
                LEDonoff()
                led2.on()
                signal_list = []
                recive = 0
                while recive == 0:
                    wdt.feed()  # WDTをリセット
                    rx.record(3000)
                    if rx.get_mode() == UpyIrRx.MODE_DONE_OK:
                        signal_list = rx.get_calibrate_list()
                        recive = 1
                        print("1")
                    else:
                        signal_list = []
                    print("2")
                # on_sw_noからファィル名を作成
                file_name = "iR_code_" + str(on_sw_no) + ".json"
                # 受信したiR信号をファイルに保存
                with open(file_name, "w") as file:
                    json.dump(signal_list, file)
                led2.off()

                # 読み取りの結果空データならLED点滅
                if signal_list == []:
                    LEDonoff()
                    print("読み取り失敗空データでした")

except KeyboardInterrupt:
    client.disconnect()
    print("切断しました")

