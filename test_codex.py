import unittest
from codex_status import Tracker

def event(kind, stamp, **kw):return {'type':'event_msg','timestamp':stamp,'payload':{'type':kind,**kw}}
def item(kind, stamp, **kw):return {'type':'response_item','timestamp':stamp,'payload':{'type':kind,**kw}}

class Events(unittest.TestCase):
    def test_real_turn_lifecycle(self):
        t=Tracker();t.feed('chat',event('task_started',100),100)
        self.assertEqual(t.snapshot(100)['state'],'thinking')
        t.feed('chat',item('function_call',101,call_id='a',name='exec_command'),101)
        self.assertEqual(t.snapshot(101)['state'],'tool')
        t.feed('chat',item('function_call_output',102,call_id='a'),102)
        self.assertEqual(t.snapshot(102)['state'],'thinking')
        t.feed('chat',event('task_complete',103),103)
        self.assertEqual(t.snapshot(103)['state'],'done')
        self.assertEqual(t.snapshot(110)['state'],'idle')
    def test_parallel_tools_do_not_finish_the_task(self):
        t=Tracker()
        t.feed('one',event('task_started',99),99)
        for cid in ('a','b'):t.feed('one',item('function_call',100,call_id=cid,name='exec_command'),100)
        t.feed('one',item('function_call_output',101,call_id='a'),101)
        self.assertEqual(t.snapshot(101)['state'],'tool')
        t.feed('two',event('task_complete',102),102)
        self.assertEqual(t.snapshot(102)['state'],'tool')
        self.assertEqual(t.snapshot(110)['state'],'tool')
    def test_no_historical_flash_or_permanent_busy(self):
        t=Tracker();t.feed('old',event('task_complete',10),100)
        self.assertEqual(t.snapshot(100)['state'],'idle')
        t.feed('old',event('task_started',100),100)
        self.assertEqual(t.snapshot(401)['state'],'idle')
    def test_explicit_wait_and_interrupt(self):
        t=Tracker();t.feed('a',event('task_started',99),99)
        t.feed('a',item('function_call',100,call_id='q',name='request_user_input'),100)
        self.assertEqual(t.snapshot(100)['state'],'waiting')
        t.feed('a',event('turn_aborted',101),101)
        self.assertEqual(t.snapshot(101)['state'],'idle')
    def test_tool_completion_is_not_turn_completion(self):
        t=Tracker();t.feed('a',event('task_started',100),100)
        t.feed('a',event('item_completed',101,item={'type':'McpToolCall','status':'completed'}),101)
        self.assertEqual(t.snapshot(101)['state'],'thinking')

if __name__=='__main__':unittest.main()

class TailTests(unittest.TestCase):
    def test_partial_record_waits_for_newline(self):
        import tempfile,json
        from pathlib import Path
        from codex_status import Follower
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)/'2026/09/30';folder.mkdir(parents=True)
            p=folder/'rollout-test.jsonl'
            p.write_text(json.dumps(event('task_started',100)))
            f=Follower(root)
            self.assertEqual(f.poll(100)['state'],'idle')
            with p.open('a') as out:out.write('\n')
            self.assertEqual(f.poll(101)['state'],'thinking')

class MainTurnRegression(unittest.TestCase):
    def test_guardian_completion_cannot_interrupt_main_task(self):
        t=Tracker()
        t.feed('main',{'type':'session_meta','payload':{'source':'vscode','thread_source':'user'}},100)
        t.feed('main',event('task_started',100,turn_id='root',root_turn_id='root'),100)
        t.feed('guard',{'type':'session_meta','payload':{'source':{'subagent':{'other':'guardian'}},'thread_source':'guardian_review'}},101)
        t.feed('guard',event('task_started',101,turn_id='review',root_turn_id='root'),101)
        t.feed('guard',event('task_complete',102,turn_id='review'),102)
        self.assertEqual(t.snapshot(102)['state'],'thinking')
        self.assertEqual(t.snapshot(102)['source'],'main')
        t.feed('main',event('task_complete',103,turn_id='root'),103)
        self.assertEqual(t.snapshot(103)['state'],'done')
    def test_child_turn_is_excluded_even_without_metadata(self):
        t=Tracker()
        t.feed('main',event('task_started',100,turn_id='a',root_turn_id='a'),100)
        t.feed('child',event('task_started',101,turn_id='b',root_turn_id='a'),101)
        t.feed('child',event('task_complete',102,turn_id='b'),102)
        self.assertEqual(t.snapshot(102)['state'],'thinking')
    def test_completion_must_match_active_turn(self):
        t=Tracker();t.feed('main',event('task_started',100,turn_id='new'),100)
        t.feed('main',event('task_complete',101,turn_id='old'),101)
        self.assertEqual(t.snapshot(101)['state'],'thinking')
        t.feed('main',event('task_complete',102,turn_id='new'),102)
        self.assertEqual(t.snapshot(102)['state'],'done')
    def test_selected_chat_is_not_preempted_by_another_chat_finishing(self):
        t=Tracker();t.feed('first',event('task_started',100,turn_id='a'),100)
        self.assertEqual(t.snapshot(100)['source'],'first')
        t.feed('second',event('task_started',101,turn_id='b'),101)
        t.feed('second',event('task_complete',102,turn_id='b'),102)
        self.assertEqual(t.snapshot(102)['source'],'first')
        self.assertEqual(t.snapshot(102)['state'],'thinking')
    def test_completion_without_start_does_not_flash(self):
        t=Tracker();t.feed('orphan',event('task_complete',100,turn_id='x'),100)
        self.assertEqual(t.snapshot(100)['state'],'idle')
    def test_failed_tool_is_not_failed_or_completed_main_task(self):
        t=Tracker();t.feed('main',event('task_started',100),100)
        t.feed('main',event('item_completed',101,item={'type':'McpToolCall','status':'failed'}),101)
        self.assertEqual(t.snapshot(101)['state'],'thinking')

class MetadataTailRegression(unittest.TestCase):
    def test_large_guardian_log_is_filtered_using_header_outside_tail(self):
        import tempfile,json
        from pathlib import Path
        from codex_status import Follower
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)/'2026/09/30';folder.mkdir(parents=True)
            records=[{'type':'session_meta','payload':{'thread_source':'guardian_review'}},
                     {'padding':'x'*2_100_000},event('task_started',100,turn_id='review')]
            (folder/'rollout-guardian.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
            f=Follower(root)
            self.assertEqual(f.poll(101)['state'],'idle')
            self.assertIn('rollout-guardian',f.tracker.excluded)
