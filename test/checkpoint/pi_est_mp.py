import sys

from multiprocessing import Process
from random import random


def pi(count):
    inside = 0
    for i in range(count):
        a = random()
        b = random()
        if a*a + b*b <= 1:
            inside += 1

    print(float(inside) / float(count) * 4)


if __name__ == "__main__":
    count = int(sys.argv[1])
    ps = [Process(target=pi, args=(count,)) for i in range(4)]
    for p in ps:
        p.start()
    for p in ps:
        p.join()
