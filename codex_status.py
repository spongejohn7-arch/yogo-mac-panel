"""Read-only Codex main-turn follower; never retain conversation contents."""
import json
import time
from datetime import datetime
from pathlib import Path

LABELS = {'idle':'待机', 'thinking':'正在工作', 'tool':'运行工具',
          'waiting':'等待输入', 'done':'本轮完成', 'error':'本轮出错'}
RUNNING = {'thinking', 'tool', 'waiting'}

class Tracker:
    def __init__(self):
        self.sessions = {}
        self.excluded = set()
        self.selected = None

    def feed(self, source, record, now):
        if not isinstance(record, dict):
            return
        payload = record.get('payload', {})
        if not isinstance(payload, dict):
            return
        typ, kind = record.get('type'), payload.get('type')
        if typ == 'session_meta':
            origin = payload.get('source')
            if (isinstance(origin, dict) and 'subagent' in origin
                    or payload.get('thread_source') not in (None, 'user')):
                self.excluded.add(source)
                self.sessions.pop(source, None)
            return
        if source in self.excluded:
            return
        stamp = record.get('timestamp', now)
        try:
            stamp = (float(stamp) if isinstance(stamp, (float, int)) else
                     datetime.fromisoformat(stamp.replace('Z', '+00:00')).timestamp())
        except (ValueError, TypeError, AttributeError):
            return
        if typ == 'event_msg' and kind == 'task_started':
            turn, root = payload.get('turn_id'), payload.get('root_turn_id')
            if root is not None and turn != root:
                self.excluded.add(source)
                self.sessions.pop(source, None)
                return
            previous = self.sessions.get(source)
            if previous and stamp < previous['last']:
                return
            self.sessions[source] = dict(state='thinking', since=stamp, last=stamp,
                                         started=stamp, turn=turn, tools=set(), running=True)
            return
        session = self.sessions.get(source)
        # A completion without its matching main-turn start is not evidence of success.
        if not session or not session['running'] or stamp < session['last']:
            return
        turn = payload.get('turn_id')
        if turn is not None and session['turn'] is not None and turn != session['turn']:
            return
        state = None
        if typ == 'event_msg':
            if kind == 'task_complete':
                if turn != session['turn']:
                    return
                state = 'done'
                session['running'] = False
                session['tools'].clear()
            elif kind in ('turn_aborted', 'task_aborted', 'session_end'):
                state = 'idle'
                session['running'] = False
                session['tools'].clear()
            elif kind == 'turn_failed':
                state = 'error'
                session['running'] = False
                session['tools'].clear()
            elif kind in ('exec_approval_request', 'apply_patch_approval_request', 'request_user_input'):
                state = 'waiting'
            elif kind == 'token_count' and session['state'] in RUNNING:
                session['last'] = stamp
            # item_completed (success OR failure) is a step, not a task boundary.
        elif typ == 'response_item':
            if kind in ('function_call', 'custom_tool_call'):
                session['tools'].add(payload.get('call_id', 'unknown'))
                name = payload.get('name', '').split('.')[-1]
                state = 'waiting' if name == 'request_user_input' else 'tool'
            elif kind in ('function_call_output', 'custom_tool_call_output'):
                session['tools'].discard(payload.get('call_id', 'unknown'))
                state = 'tool' if session['tools'] else 'thinking'
            elif kind in ('reasoning', 'message') and session['state'] in RUNNING:
                session['last'] = stamp
        if state:
            if state != session['state']:
                session['since'] = stamp
            session['state'], session['last'] = state, stamp

    def snapshot(self, now):
        eligible = {}
        for source, session in self.sessions.items():
            ttl = 6 if session['state'] in ('done', 'error') else 300
            if session['state'] != 'idle' and 0 <= now - session['last'] < ttl:
                eligible[source] = session
        # Follow one main user turn without allowing another chat to interrupt it.
        if self.selected not in eligible:
            active = {k:v for k,v in eligible.items() if v['running']}
            self.selected = max(active, key=lambda k:active[k]['started']) if active else None
        if self.selected is None:
            return dict(state='idle', label=LABELS['idle'], age=0, source='', active=0)
        session = eligible[self.selected]
        return dict(state=session['state'], label=LABELS[session['state']],
                    age=max(0, now-session['since']), source=self.selected[-8:],
                    active=sum(s['running'] for s in eligible.values()))

class Follower:
    def __init__(self,root=None):
        self.root=Path(root or Path.home()/'.codex/sessions')
        self.tracker=Tracker();self.positions={};self.next_scan=0;self.paths=[];self.error=''
    def poll(self,now=None):
        now=time.time() if now is None else now
        if now>=self.next_scan:
            try:
                # Only today's/yesterday's local logs; include long-running recently updated sessions.
                candidates=[p for p in self.root.glob('*/*/*/rollout-*.jsonl') if now-p.stat().st_mtime<86400]
                self.paths=sorted(candidates,key=lambda p:p.stat().st_mtime,reverse=True)[:32]
                self.next_scan=now+3
            except OSError:self.error='无法读取 Codex 本地事件';self.next_scan=now+3
        for path in self.paths:
            try:
                size=path.stat().st_size
                pos=self.positions.get(path)
                with path.open('rb') as f:
                    if pos is None or pos>size:
                        try:
                            header=json.loads(f.readline())
                            if isinstance(header,dict) and header.get('type')=='session_meta':
                                self.tracker.feed(path.stem,header,now)
                        except (ValueError,UnicodeDecodeError):pass
                        pos=max(0,size-2_000_000);f.seek(pos)
                        if pos:f.readline()
                    else:f.seek(pos)
                    while True:
                        start=f.tell();line=f.readline(2_000_001)
                        if not line:break
                        if not line.endswith(b'\n'):
                            f.seek(start);break
                        try:record=json.loads(line)
                        except (ValueError,UnicodeDecodeError):continue
                        self.tracker.feed(path.stem,record,now)
                    self.positions[path]=f.tell()
            except OSError:continue
        state=self.tracker.snapshot(now)
        return {**state,'sessions':len(self.paths),'available':bool(self.paths),'notice':self.error}
