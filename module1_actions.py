import pydirectinput
import time

def click_at(x, y, pre_delay=0.1):
    """Di chuyển chuột đến tọa độ (x, y) và click."""
    pydirectinput.moveTo(x, y)
    time.sleep(pre_delay)  # Đợi một chút để game kịp nhận diện chuột di chuyển
    pydirectinput.click()

def hold_key(key, hold_time=0.5):
    """Giữ một phím trong khoảng thời gian nhất định."""
    pydirectinput.keyDown(key)
    time.sleep(hold_time)
    pydirectinput.keyUp(key)

def tap_key(key):
    """Nhấn thả một phím nhanh."""
    pydirectinput.press(key)