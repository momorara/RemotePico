# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
v1.0
セキュリティ設定等をプログラムから切り離した。
"""

def ID_PASS():
    # wifiのssidとパスワード
    ssid        = 'abc'
    password    = 'abcdef'
    return ssid,password

def secret_keys():
    # 暗号化キー
    # 同じアルハァベットがないようにする
    henkan = "opqrstuvwxyzabcdefghijklmn"

    # この文字列が受信した文字列のzの後についてなければ、エラーとする
    # エラーの仕方は、時間mmをおかしな時間に変更することでおこなう
    sec_code_org = "test1"

    # mqttのアドレスのようなもの
    MQTT_TOPIC = b"tkj/remote/2025/test123"  # 文字列ではなくバイト列にすること

    return henkan,sec_code_org,MQTT_TOPIC

def main():
    print(ID_PASS())
    print(secret_keys())

if __name__=='__main__':
    main()
