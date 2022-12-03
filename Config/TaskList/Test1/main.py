from time import sleep

NAME = "Test_1"
MAX_N = 3
SLEEP_TIME = 2
n = 1
while n <= MAX_N:
    print(f"{NAME}\t{str(n)}")
    sleep(SLEEP_TIME)
    n += 1
raise Exception