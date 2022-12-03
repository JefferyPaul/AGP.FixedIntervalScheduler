from time import sleep

NAME = "Test_2"
MAX_N = 5
SLEEP_TIME = 1
n = 1
while n <= MAX_N:
    print(f"{NAME}\t{str(n)}")
    sleep(SLEEP_TIME)
    n += 1