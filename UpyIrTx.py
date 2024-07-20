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
"""

from rp2 import PIO, asm_pio, StateMachine
from micropython import const

# IR TX class for RaspberryPi pico
# micropython v1.17 - v1.18(latest as of 2022/5)

@asm_pio(autopull=True, pull_thresh=32, sideset_init=PIO.OUT_LOW)
def pio_wave():
    T = const(26)      # Period: 1/38kHz*1M [us]
    OF_TIM = const(18) # Duty(30%) off time [us]
    OF_POR = const(0)  # Idle level
    ON_TIM = const(8)  # Duty(30%) on time [us]
    ON_POR = const(1)  # not Idle level
    wrap_target()
    out(x, 32).side(OF_POR)
    label('on')
    set(y, ON_TIM).side(ON_POR)
    label('on_loop')
    jmp(x_dec, 'mid1').side(ON_POR)
    label('mid1')
    jmp(not_x, 'of').side(ON_POR)
    jmp(y_dec, 'on_loop').side(ON_POR)
    set(y, OF_TIM).side(OF_POR)
    label('of_loop')
    jmp(x_dec, 'mid2').side(OF_POR)
    label('mid2')
    jmp(not_x, 'of').side(OF_POR)
    jmp(y_dec, 'of_loop').side(OF_POR)
    jmp('on').side(OF_POR)
    label('of')
    out(x, 32).side(OF_POR)
    label('stay')
    jmp(x_dec, 'stay').side(OF_POR)[2]
    wrap()

class UpyIrTx():

    # Fixed: (freq=38000, duty=30, idle_level=0)
    def __init__(self, ch, pin, *args, **kwargs):
        self._sm = None
        if ch < 0 or ch > 7:
            raise(IndexError())
        self._sm = StateMachine(ch, pio_wave, freq=3000000, sideset_base=pin)
        self._sm.active(1)

    def __del__(self):
        if self._sm:
            self._sm.active(0)

    def send(self, signal_tuple):
        # Blocking until transmission
        if not signal_tuple:
            return(True)
        if len(signal_tuple) % 2 == 0:
            return(False)
        for i in signal_tuple:
            self._sm.put(i)
        self._sm.put(100)  # Last idle level 100us
        return(True)

    def send_cls(self, ir_rx):
        # Blocking until transmission
        if ir_rx.get_record_size() != 0:
            return(self.send(ir_rx.get_calibrate_list()))
        else:
            return(False)
