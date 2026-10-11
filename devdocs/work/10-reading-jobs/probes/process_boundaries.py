"""Observe current Python/OS pipe behavior before choosing the worker lifetime."""
import asyncio
import json
import subprocess
import sys
import tempfile
import time


def threaded_read():
    code = '''import asyncio,sys
async def main():
    loop=asyncio.get_running_loop()
    work=asyncio.create_task(read(loop))
    await asyncio.sleep(.1)
    work.cancel()
    try: await work
    except asyncio.CancelledError: print('cancelled-await',flush=True)
async def read(loop):
    print('reading',flush=True)
    return await loop.run_in_executor(None,sys.stdin.buffer.readline)
asyncio.run(main())
'''
    p = subprocess.Popen([sys.executable, '-c', code], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    try:
        assert p.stdout.readline() == b'reading\n'
        assert p.stdout.readline() == b'cancelled-await\n'
        time.sleep(.1)
        alive = p.poll() is None
        assert alive
        p.stdin.close()
        p.stdin = None
        _, err = p.communicate(timeout=3)
        assert p.returncode == 0, err
        print(json.dumps(dict(case='executor_stdin_cancellation', await_cancelled=True,
                              process_waits_for_stdin=True, exits_after_eof=True)))
    finally:
        if p.poll() is None:
            p.kill()
            p.communicate()


def output_backpressure():
    code = "import sys;sys.stderr.write('writing\\n');sys.stderr.flush();sys.stdout.buffer.write(b'x'*(2*1024*1024));sys.stdout.flush();sys.stderr.write('finished\\n')"
    p = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert p.stderr.readline() == b'writing\n'
        time.sleep(.1)
        assert p.poll() is None
        out, err = p.communicate(timeout=3)
        assert len(out) == 2 * 1024 * 1024 and err == b'finished\n' and p.returncode == 0
        print(json.dumps(dict(case='stdout_backpressure', bytes=2097152,
                              producer_waited_for_reader=True, completed_after_drain=True)))
    finally:
        if p.poll() is None:
            p.kill()
            p.communicate()


async def regular_file():
    with tempfile.TemporaryFile() as stream:
        reader = asyncio.StreamReader()
        try:
            transport, _ = await asyncio.get_running_loop().connect_read_pipe(
                lambda: asyncio.StreamReaderProtocol(reader), stream)
        except (ValueError, PermissionError, OSError) as error:
            print(json.dumps(dict(case='read_pipe_regular_file', rejected=type(error).__name__)))
        else:
            transport.close()
            raise AssertionError('Platform accepts regular file; revisit the portability premise')


if __name__ == '__main__':
    threaded_read()
    output_backpressure()
    asyncio.run(regular_file())
