from time import time
import pyautogui

def test(num):
    start = time()
    for i in range(num):
        sign = -1 if i % 2 else 1
        pyautogui.moveRel(sign*100,sign*100, _pause=0)
    end = time()
    print(f"{num} moves: {end-start}")

test(1)   # 0.1 sec
test(10)  # 1 sec
test(100) # 10 sec