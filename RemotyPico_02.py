# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
2024/03/20  RemotePico開発スタート
    v01     sw 2個対応でとりあえず作成、あとは基板ができてから
2024/04/11  send_file.pyを単独で動作させると信号を送信できるが、プログラムに組み込むと動作しない。なんでかわからないが...
    v02     なので、execコマンドでやると送信できた。
2024/04/13  電池駆動用に最初のLED点滅を短く
            信号読み取り失敗時にLED点滅する

64-96行は組み立て後のハードウェアテストプログラムです。
#を消して、順番にテストしてください。


Thonnyで動かすならこのままThonnyで実行してください。
スタンドアローンで実行するには、ファィル名をmain.pyにして電源を繋いでください。

RemotePico_02.py
"""
main_py = 0 # 1の時は自己リブートを有効にする。

import time
from machine import Pin

""" GPIO pin 設定 """""""""
# Remote pin設定
# tx_GPIO = 17   <--  send_file.pyで設定する
rx_GPIO = 1
# 表示用+ED　pin設定
display_LED = 0
# スイッチのpin設定
sw_n = 6 # swの数
sw_pin = [13,15,10,12,14,11] # swのGPIO pin
# パターンでプラスが繋がっているため
dumy = Pin(26, Pin.IN)
""""""""""""  """"""""""""

led2 = Pin(display_LED, Pin.OUT,Pin.PULL_DOWN)
def LED_flash(count=5):
    for _ in range(count):
        led2.on()
        time.sleep(.05)
        led2.off()
        time.sleep(.05)

LED_flash()

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

# sw テスト　確認できたらコメントアウト
# while True:
#     for i in range(6):
#         print(i,SW[i].value() )
#         time.sleep(0.5)

# センサー テスト
# このプログラムを起動した状態で、家電リモコンのスイッチを押すと0が表示される
# 確認できたらコメントアウト
# sensor = Pin(rx_GPIO, Pin.IN)
# while True:
#     print(sensor.value() )
#     time.sleep(0.5)

# LED テスト このテストをする時は、iR-LEDをつける前にする 
# で無いとiR-LEDが壊れる可能性がある
# もし、すでにつけていたらパス
# 確認できたらコメントアウト
# led1 = Pin(tx_GPIO, Pin.OUT,Pin.PULL_DOWN)
# led1 = Pin(tx_GPIO, Pin.OUT,Pin.PULL_DOWN)
# while True:
#     for i in range(6):
#         led1.on()
#         time.sleep(.1)
#         led1.off()
#         time.sleep(.2)

# ハードウェアのチェックが終わったらコメントアウト
# while True:
#     pass


# swが押されたら 0 常時 1
# on_sw_no 押されたswの番号 swの番号は0から始まり基板の表記は0,1,2,3,4,5となっています。
# on_sw_mode 「長押し」or「チョン押し」

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

while True:
    # swがどれか押されるまでswのチェックをする 複数押された場合は 若番が認識される
    sw_all = sw_n
    while sw_all == sw_n:
        sw_all = 0
        #print(SW[0].value(),SW[1].value())
        time.sleep(0.1)
        for i in range(sw_n):
            sw_all = sw_all + SW[i].value() 
    #print(SW[0].value(),SW[1].value())

    # 押されたswを調べる
    for on_sw_no in range(sw_n):
        if SW[on_sw_no].value() == 0:
            break
    # print(on_sw_no)

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

            # コメントアウトの方法だとなぜか送信できない
            # on_sw_noからファィル名を作成
            # file_name = "iR_code_" + str(on_sw_no) + ".json"
            # # ファイルからiR信号を読み込む
            # file_name = "iR_code_5.json"
            # with open(file_name, "r") as file:
            #     loaded_list = json.load(file)
            # # iR信号の送信
            # calibrate_list_bytes = json.dumps(loaded_list[1:]).encode('utf-8')  # JSON文字列をバイト列に変換
            # tx.send(calibrate_list_bytes)  # バイト列を送信
            # print(loaded_list)

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
            exec(code)

        except:
            print("ファイルなし")


    # 長押しなら　　　押されたスイッチのリモコン信号登録処理を行う
    if on_sw_mode == "長押し":
        print("read file")
        LED_flash()
        led2.on()
        signal_list = []
        recive = 0
        while recive == 0:
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
            LED_flash()
            print("読み取り失敗空データでした")
