import cv2
import numpy as np
import mss

# Khởi tạo sct 1 lần duy nhất, tái sử dụng để chống tràn RAM/CPU
sct = mss.mss()

def find_template_on_screen(template_path, threshold=0.8):
    """
    Tìm template trên màn hình.
    Trả về (x, y) là tọa độ tâm của ảnh nếu tìm thấy, ngược lại trả về None.
    """
    try:
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            return None
        
        h, w, _ = template.shape

        # Dùng monitors[0] (All monitors) an toàn trên mọi máy
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)
        
        screen_np = np.array(screenshot)
        screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_BGRA2BGR)

        result = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # FIX: Cộng thêm tọa độ gốc của khung hình (monitor["left"] và monitor["top"])
            center_x = monitor["left"] + max_loc[0] + int(w / 2)
            center_y = monitor["top"] + max_loc[1] + int(h / 2)
            return (center_x, center_y)
            
        return None
    except Exception as e:
        print(f"[Vision Error] Lỗi khi nhận diện: {e}")
        return None