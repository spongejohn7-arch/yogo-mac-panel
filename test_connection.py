import unittest
from unittest.mock import patch
from yogo.device import ProtocolError
from connection import PanelDisplay

class Wire:
 def __init__(self, replies): self.replies=list(replies); self.closed=False
 def write(self, data): return len(data)
 def read(self, size, timeout): return self.replies.pop(0) if self.replies else b''
 def close(self): self.closed=True

def reply(cmd=48, seq=1, status=85):
 return bytes([170,cmd,0,0,0,seq,0,status,80,0])+bytes(22)

class Connections(unittest.TestCase):
 def device(self, replies, wireless=True):
  d=PanelDisplay(b'test',4607 if wireless else 4507,'test',wireless)
  d._dev=Wire(replies)
  d._session_at=__import__('time').monotonic()
  return d
 def test_timeout_cannot_report_successful_frame(self):
  d=self.device([])
  with self.assertRaises(ProtocolError): d.show([(0,0,0)]*36)
 def test_stale_reply_is_not_accepted_as_current_power(self):
  d=self.device([reply(seq=99),reply()])
  self.assertEqual(d.power_info()['percent'],80)
  self.assertEqual(len(d._dev.replies),0)
 def test_rejected_frame_is_error(self):
  d=self.device([reply(cmd=60,status=15)])
  with self.assertRaises(ProtocolError):d.show([(0,0,0)]*36)
 def test_wireless_frame_uses_three_acknowledged_packets(self):
  d=self.device([reply(cmd=60,seq=i) for i in (1,2,3)])
  d.show([(0,0,0)]*36)
  self.assertEqual(len(d._dev.replies),0)
 def test_unresponsive_usb_falls_back_to_wireless(self):
  usb=self.device([],False); radio=self.device([reply(cmd=16),reply(seq=2)])
  radio._session_at=0; usb._session_at=0
  with patch.object(PanelDisplay,'discover',return_value=[usb,radio]), patch.object(PanelDisplay,'open',lambda d:d):
   self.assertIs(PanelDisplay.open_first(),radio)
  self.assertTrue(usb._dev is None or usb._dev.closed)
