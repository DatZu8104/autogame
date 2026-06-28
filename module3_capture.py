import mss
import mss.tools
import os
from datetime import datetime

def auto_capture(save_folder="screenshots", region=None):
    """
    Chụp màn hình và tự động lưu vào thư mục.
    - save_folder: Tên thư mục chứa ảnh (mặc định là 'screenshots').
    - region: Tuple (left, top, width, height) nếu chỉ muốn chụp một góc. Để None sẽ chụp toàn màn hình.
    Trả về đường dẫn của file ảnh vừa lưu.
    """
    # Tự động tạo thư mục nếu chưa tồn tại
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Đặt tên file theo ngày giờ chi tiết đến từng giây
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}.png"
    filepath = os.path.join(save_folder, filename)

    try:
        with mss.mss() as sct:
            if region:
                # Cắt đúng vùng chỉ định
                monitor = {"left": region[0], "top": region[1], "width": region[2], "height": region[3]}
            else:
                # Chụp toàn bộ màn hình số 1
                monitor = sct.monitors[1]
            
            # Lấy ảnh và lưu ra file
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=filepath)
            
        return filepath
    except Exception as e:
        print(f"[Capture] Lỗi khi chụp ảnh: {e}")
        return None