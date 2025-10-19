import threading
import time
from queue import Queue, Empty

class PipeAggregator:
    def __init__(self):
        self.q_out = Queue()
        self.q_err = Queue()

    def reader(self, stream, q: Queue):
        for line in iter(stream.readline, b""):
            q.put(line.decode(errors="replace"))
        stream.close()

    def start(self, proc):
        t1 = threading.Thread(target=self.reader, args=(proc.stdout, self.q_out), daemon=True)
        t2 = threading.Thread(target=self.reader, args=(proc.stderr, self.q_err), daemon=True)
        t1.start(); t2.start()

    def drain_chunk(self, q: Queue, max_chars=20000):
        buf = []
        total = 0
        try:
            while True:
                s = q.get_nowait()
                buf.append(s)
                total += len(s)
                if total >= max_chars:
                    break
        except Empty:
            pass
        return "".join(buf)
