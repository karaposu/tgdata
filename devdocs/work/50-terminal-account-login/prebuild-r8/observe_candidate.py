"""Test-only observations of the clean candidate; no supplied input/outcome state."""
import os,sys
from unittest.mock import patch
import combined_suite as base

ti=base.terminal_input
InputFailure=ti.TerminalInputError
InputStopped=ti.TerminalStopped

def read_input(prompt,stop_requested,observe=lambda *args:None):
    stats=dict(read_bytes=0,retained_peak=0,chunk_peak=0,invalid=False)
    state=dict(fd=None,gets=0,sets=0,final=False,framed=False,decoded=False,invalid=False,frame=None)
    native={n:getattr(os,n) for n in ('open','close','read')}
    get=ti.termios.tcgetattr;put=ti.termios.tcsetattr;flush=ti.termios.tcflush
    def point(stage):observe(stage,state['fd'],stats)
    def peak(frame):
        if frame is not None:
            data=frame.f_locals.get('data')
            if data is not None:stats['retained_peak']=max(stats['retained_peak'],len(data))
    def opening(path,*args,**kw):
        fd=native['open'](path,*args,**kw)
        if path=='/dev/tty':state['fd']=fd;point('acquired')
        return fd
    def getting(fd):
        result=get(fd)
        if fd==state['fd']:
            state['gets']+=1
            if state['gets']==1:point('snapshot')
            elif state['final']:point('restored')
        return result
    def setting(fd,when,attrs):
        target=fd==state['fd']
        if target:
            state['sets']+=1
            if state['sets']==2:point('restore')
            elif state['sets']==3:point('restore_final')
        result=put(fd,when,attrs)
        if target:
            if state['sets']==1:point('hidden')
            if state['sets']==3:state['final']=True
        return result
    def flushing(fd,queue):
        result=flush(fd,queue)
        if fd==state['fd'] and state['sets']==2:point('settled')
        return result
    def reading(fd,count):
        result=native['read'](fd,count)
        if fd==state['fd']:
            stats['read_bytes']+=len(result);stats['chunk_peak']=max(stats['chunk_peak'],len(result))
            peak(state['frame']);point('read')
        return result
    def closing(fd):
        result=native['close'](fd)
        if fd==state['fd']:point('closed')
        return result
    def tracer(frame,event,arg):
        if frame.f_code is not ti.read_hidden.__code__:return None
        state['frame']=frame;peak(frame);local=frame.f_locals
        if local.get('reason') is not None and not state['invalid']:
            state['invalid']=True;stats['invalid']=True;point('invalid')
        if local.get('finished') and not state['framed']:
            state['framed']=True;point('framed')
        if local.get('value') is not None and not state['decoded']:
            state['decoded']=True;point('decoded')
        # Once invalid, native read wrappers continue observing data/chunk bounds;
        # skip per-byte tracing of a huge discarded paste. No candidate state changes.
        if state['invalid'] and not local.get('data'):
            frame.f_trace_lines=False
        return tracer
    previous=sys.gettrace()
    try:
        with patch.object(os,'open',opening),patch.object(os,'close',closing),patch.object(os,'read',reading), \
             patch.object(ti.termios,'tcgetattr',getting),patch.object(ti.termios,'tcsetattr',setting),patch.object(ti.termios,'tcflush',flushing):
            sys.settrace(tracer)
            value=ti.read_hidden(prompt,stop_requested)
            return value,stats
    finally:
        sys.settrace(previous);state['frame']=None
