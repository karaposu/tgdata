"""Inquiry-only input boundary. Not a product candidate or public input API."""
import os,select,sys,termios

class InputFailure(Exception):
    pass

class InputStopped(EOFError):
    pass


def read_input(prompt, stop_requested, observe=lambda phase,fd,stats:None):
    fd=original=None; value=None; cleanup_error=None
    stats=dict(read_bytes=0,retained_peak=0,chunk_peak=0,invalid=False)
    def point(phase):observe(phase,fd,stats)
    try:
        fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK);point('acquired')
        original=termios.tcgetattr(fd);point('snapshot')
        bad=termios.ISTRIP|termios.IGNCR|termios.INLCR|termios.PARMRK|getattr(termios,'IUCLC',0)
        if (os.tcgetpgrp(fd)!=os.getpgrp() or not original[3]&termios.ICANON
                or not original[3]&termios.ISIG or not original[0]&termios.ICRNL
                or original[0]&bad or original[2]&termios.CSIZE!=termios.CS8):
            raise InputFailure('unsupported_terminal')
        def cc(index):
            value=original[6][index]
            return value if isinstance(value,int) else value[0]
        erase,kill,eof,intr=[cc(i) for i in (termios.VERASE,termios.VKILL,termios.VEOF,termios.VINTR)]
        if len(set((erase,kill,eof,intr)))!=4 or any(x in (10,13) or not (0<x<32 or x==127) for x in (erase,kill,eof,intr)):
            raise InputFailure('unsupported_controls')
        hidden=original[:];hidden[6]=original[6][:]
        hidden[0]&=~(termios.IXON|termios.IXOFF|getattr(termios,'IXANY',0))
        hidden[3]&=~(termios.ECHO|termios.ECHONL|termios.ICANON|termios.IEXTEN)
        hidden[6][termios.VMIN]=1;hidden[6][termios.VTIME]=0
        disabled=bytes([os.fpathconf(fd,'PC_VDISABLE')])
        hidden[6][termios.VQUIT]=disabled;hidden[6][termios.VSUSP]=disabled
        if stop_requested():raise InputStopped()
        termios.tcsetattr(fd,termios.TCSANOW,hidden)
        if termios.tcgetattr(fd)!=hidden:raise InputFailure('hide_failed')
        point('hidden')
        if stop_requested():raise InputStopped()
        print(prompt,end='',file=sys.stderr,flush=True)
        data=bytearray();reason=None;finished=False
        while not finished:
            if stop_requested():raise InputStopped()
            ready,_,_=select.select([fd],[],[],0.05)
            if stop_requested():raise InputStopped()
            if not ready:continue
            try:chunk=os.read(fd,256)
            except BlockingIOError:continue
            if not chunk:raise InputStopped()
            stats['read_bytes']+=len(chunk);stats['chunk_peak']=max(stats['chunk_peak'],len(chunk))
            point('read')
            for byte in chunk:
                if stop_requested():raise InputStopped()
                if byte==10:finished=True;break
                if byte==eof:raise InputStopped()
                if reason is not None:continue
                if byte==kill:data.clear();continue
                if byte==erase:
                    try:shorter=data.decode('utf-8')[:-1].encode('utf-8')
                    except UnicodeError:reason='invalid_encoding'
                    else:data[:]=shorter
                elif byte<32 or byte==127:reason='unsupported_control'
                elif len(data)>=128:reason='input_too_long'
                else:data.append(byte)
                stats['retained_peak']=max(stats['retained_peak'],len(data))
                if reason is not None:
                    data.clear();stats['invalid']=True;point('invalid')
                    print('\nInput rejected; finishing this line. Ctrl-C stops.',file=sys.stderr,flush=True)
            if finished:point('framed')
        print(file=sys.stderr,flush=True)
        if reason is not None:raise InputFailure(reason)
        try:value=data.decode('utf-8')
        except UnicodeError:raise InputFailure('invalid_encoding') from None
        point('decoded')
    finally:
        if fd is not None:
            if original is not None:
                try:termios.tcflush(fd,termios.TCIFLUSH)
                except Exception:cleanup_error='flush_failed'
                try:
                    point('restore')
                    termios.tcsetattr(fd,termios.TCSANOW,original)
                    if termios.tcgetattr(fd)!=original:cleanup_error='restore_failed'
                    point('restored')
                except Exception:cleanup_error='restore_failed'
            try:os.close(fd);point('closed')
            except Exception:
                if cleanup_error is None:cleanup_error='close_failed'
        if cleanup_error is not None:raise InputFailure(cleanup_error) from None
    if stop_requested():raise InputStopped()
    return value,stats
