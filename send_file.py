"""
@iotberrypi(sunday programmer)さんの記事
https://qiita.com/iotberrypi/items/a2c739049bee4bb615c8
のhttps://github.com/meloncookie/RemotePy
を使わせていただきpicoでの学習リモコンを構築

MIT License

Copyright (c) 2022 meloncookie

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

2024/03/15 start 
                iR信号を受信して、ファィル保存
                その保存したファィルを読み込んで、送信する。

"""
from machine import Pin
from UpyIrTx import UpyIrTx
import json

tx_pin = Pin(17, Pin.OUT) 
tx = UpyIrTx(0, tx_pin)

# ファイルからiR信号を読み込む
with open("data.json", "r") as file:
    loaded_list = json.load(file)

# iR信号の送信
calibrate_list_bytes = json.dumps(loaded_list[1:]).encode('utf-8')  # JSON文字列をバイト列に変換
tx.send(calibrate_list_bytes)  # バイト列を送信

print(loaded_list)

tx.send(loaded_list)