"""Panel transport: probe active links and require matching device acknowledgements."""
import time
from yogo.device import YogoDisplay, ProtocolError


class PanelDisplay(YogoDisplay):
    @classmethod
    def open_first(cls):
        errors=[]
        for dev in sorted(cls.discover(), key=lambda d:d.wireless):
            try:
                dev.open()
                # Power replies fit both report sizes; upstream read_config assumes USB.
                if dev.power_info() is None:
                    raise ProtocolError('电量查询没有回应')
                return dev
            except Exception as exc:
                errors.append(f'{"2.4G" if dev.wireless else "USB"}: {exc}')
                dev.close()
        detail='；'.join(errors) or '未检测到键盘或接收器'
        raise ProtocolError(f'{detail}。请连接 USB 或切换到 2.4G，并退出其他键盘控制软件')

    def _transfer(self, packet, read_reply=True, timeout=None):
        if self._dev is None:
            raise RuntimeError('device not open')
        self._dev.write(b'\x00'+packet)
        if not read_reply:
            return None
        deadline=time.monotonic()+(timeout if timeout is not None else (900 if self.wireless else 300))/1000
        while time.monotonic()<deadline:
            rx=self._dev.read(self.buffer_len, timeout=max(1,int((deadline-time.monotonic())*1000)))
            if not rx:
                break
            if len(rx)>=8 and rx[0]==0xAA and rx[1]==packet[1] and rx[5]==packet[5]:
                return rx
        raise ProtocolError('键盘回应超时，请检查连接、档位及电量')
