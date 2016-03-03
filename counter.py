import time
from multiprocessing import Process, Value, Lock

class Counter(object):
    def __init__(self, initval=0):
        self.val = Value('i', initval)
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    def value(self):
        with self.lock:
            return self.val.value

def count(counter):
    for i in range(50):
        time.sleep(0.01)
        counter.increment()
        counter2.increment()


if __name__ == '__main__':
    counter1 = Counter(0)
    counter2 = Counter(10)
    procs = [Process(target=count, args=(counter1,)) for i in range(10)]



    for p in procs: p.start()
    for p in procs: p.join()

    print('Counter1 value:  %s' % counter1.value() )
    print('Counter2 value:  %s' % counter2.value() )
