import sys
from random import random


def main():
    count = int(sys.argv[1])
    inside = 0

    for _ in range(count):
        a = random()
        b = random()
        if a*a + b*b <= 1:
            inside += 1

    print(float(inside) / float(count) * 4)


if __name__ == "__main__":
    main()
