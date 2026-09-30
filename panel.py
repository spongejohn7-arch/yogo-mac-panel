"""Local UI for yogo. Only the renderer thread owns the USB handle."""
import json
import math
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from connection import PanelDisplay
from yogo.frame import Frame, parse_color
from yogo.font import GLYPHS, lit_indices
from yogo.daemon import RENDERERS, render_idle
from codex_status import Follower
from robot_theme import robot_frame
from world_themes import world_frame

PORT = 18765
ORIGIN = f'http://127.0.0.1:{PORT}'
TOKEN = secrets.token_urlsafe(32)


def validate(data):
    if not isinstance(data, dict): raise ValueError('操作参数无效')
    mode = data.get('mode')
    if mode not in ('solid', 'pixels', 'rainbow', 'text', 'off', 'stop', 'codex'):
        raise ValueError('请选择显示方式')
    try: brightness = float(data.get('brightness', .6))
    except (ValueError, TypeError): raise ValueError('亮度应在 0–100% 之间')
    if not math.isfinite(brightness) or not 0 <= brightness <= 1:
        raise ValueError('亮度应在 0–100% 之间')
    theme = data.get('theme', 'robot')
    if theme not in ('robot', 'simple', 'garden', 'space'): raise ValueError('请选择有效的显示主题')
    color = data.get('color', '#3399ff')
    if not isinstance(color, str) or len(color)>30: raise ValueError('颜色无效')
    try: rgb = parse_color(color)
    except ValueError: raise ValueError('颜色无效')
    text = data.get('text', 'YOGO')
    if mode == 'text' and (not isinstance(text, str) or not 1 <= len(text) <= 48):
        raise ValueError('文字长度应为 1–48 个字符')
    if mode == 'text' and any(ch not in GLYPHS and ch.upper() not in GLYPHS for ch in text):
        raise ValueError('小屏支持英文字母、数字、空格和 ! ? . -，暂不支持中文')
    pixels = data.get('pixels')
    if mode == 'pixels':
        if not isinstance(pixels,list) or len(pixels)!=36 or any(
            not isinstance(p,list) or len(p)!=3 or any(type(c)!=int or not 0<=c<=255 for c in p)
            for p in pixels): raise ValueError('图片应包含 36 个有效像素')
    return dict(mode=mode, brightness=brightness, rgb=rgb, text=text, pixels=pixels, theme=theme)


def render(c, elapsed):
    mode=c['mode']
    if mode=='codex':
        state=c.get('_codex',{'state':'idle','age':0})
        fn=RENDERERS.get(state['state'])
        age=elapsed if state['state']=='idle' else state['age']
        if c.get('theme','robot')=='robot': f=robot_frame(state['state'],age)
        elif c['theme'] in ('garden','space'): f=world_frame(c['theme'],state['state'],age)
        else: f=fn(age) if fn else render_idle(elapsed,'breathe')
    elif mode=='rainbow': f=Frame.rainbow((elapsed/5)%1)
    elif mode=='pixels': f=Frame.from_pixels(c['pixels'])
    elif mode=='solid': f=Frame.solid(c['rgb'])
    elif mode=='text':
        f=Frame()
        for i in lit_indices(c['text'][int(elapsed/1.2)%len(c['text'])]): f.pixels[i]=c['rgb']
    else: f=Frame()
    return f.scaled(c['brightness']).pixels


class Controller:
    def __init__(self):
        self.lock=threading.Lock()
        self.follower=Follower()
        self.codex_next=0
        self.codex_state={"state":"idle","label":"待机","available":False,"age":0,"active":0,"source":""}
        self.command=validate({'mode':'stop'})
        self.version=0
        self.closed=threading.Event()
        self.state=dict(connected=False, transport=None, battery=None, mode='stop', error='', pixels=[[0,0,0]]*36, version=0, theme='robot', brightness=.6)
        self.thread=threading.Thread(target=self.run,daemon=True)
        self.thread.start()

    def submit(self,data):
        command=validate(data)
        with self.lock:
            self.command=command
            self.version+=1
            return self.version

    def snapshot(self):
        with self.lock: return {**self.state, 'codex':dict(self.codex_state)}

    def update(self,**values):
        with self.lock: self.state.update(values)

    def run(self):
        dev=None
        applied=-1
        t0=0
        next_status=0
        try:
            while not self.closed.is_set():
                try:
                    if time.monotonic()>=self.codex_next:
                        codex=self.follower.poll()
                        with self.lock:self.codex_state=codex
                        self.codex_next=time.monotonic()+.5
                    if dev is None:
                        dev=PanelDisplay.open_first()
                        applied=-1
                        next_status=0
                    with self.lock: c,version=dict(self.command),self.version
                    now=time.monotonic()
                    if version!=applied:
                        if c['mode']=='stop': dev.end_stream()
                        t0=now
                    if now>=next_status:
                        power=dev.power_info()
                        if power is None: raise RuntimeError('键盘没有响应，请检查键盘连接并退出其他键盘控制软件')
                        self.update(connected=True,transport='2.4G' if dev.wireless else 'USB',battery=power['percent'],error='')
                        next_status=now+5
                    c['_codex']={**self.codex_state, 'age':self.codex_state['age']+max(0,now-(self.codex_next-.5))}
                    pixels=render(c,now-t0)
                    if c['mode']!='stop': dev.show(pixels)
                    self.update(mode=c['mode'],pixels=pixels,version=version,error='',theme=c['theme'],brightness=c['brightness'])
                    applied=version
                    self.closed.wait((.20 if dev.wireless else .10) if c['mode']!='stop' else .3)
                except Exception as exc:
                    self.update(connected=False,transport=None,battery=None,error=str(exc))
                    if dev:
                        try: dev.close()
                        except Exception: pass
                    dev=None
                    self.closed.wait(2)
        finally:
            if dev:
                try: dev.end_stream()
                finally: dev.close()

    def close(self):
        self.closed.set()
        self.thread.join(5)


class Handler(BaseHTTPRequestHandler):
    controller=None
    def log_message(self,*args): pass
    def reply(self,status,data,kind='application/json; charset=utf-8'):
        body=json.dumps(data,ensure_ascii=False).encode() if isinstance(data,dict) else data
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)
    def allowed(self):
        return self.headers.get('Host')==f'127.0.0.1:{PORT}'
    def do_GET(self):
        if not self.allowed(): return self.reply(403,{'error':'无效的访问地址'})
        if self.path=='/api/status':
            return self.reply(200,{**self.controller.snapshot(),'token':TOKEN})
        files={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        if self.path not in files: return self.reply(404,{'error':'页面不存在'})
        kind={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[self.path]
        self.reply(200,Path(__file__).with_name(files[self.path]).read_bytes(),kind)
    def do_POST(self):
        if not self.allowed() or self.headers.get('Origin')!=ORIGIN or self.headers.get('X-Yogo-Token')!=TOKEN:
            return self.reply(403,{'error':'页面已过期，请刷新后重试'})
        if self.path!='/api/control': return self.reply(404,{'error':'操作不存在'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<8192: raise ValueError('操作数据过大或为空')
            data=json.loads(self.rfile.read(length))
            version=self.controller.submit(data)
            self.reply(200,{'ok':True,'version':version})
        except (ValueError,TypeError) as exc: self.reply(400,{'error':str(exc)})


def main():
    server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
    Handler.controller=Controller()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        Handler.controller.close()
        server.server_close()

if __name__=='__main__': main()
