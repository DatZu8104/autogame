import threading
import time
import os
import logging
from datetime import datetime
import module1_actions as actions
import module2_vision as vision

log_filename = f"nhat_ky_bot_{datetime.now().strftime('%Y%m%d')}.txt"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    encoding='utf-8'
)

class BotLogic:
    def __init__(self, status_callback):
        self.is_running = False
        self.bot_thread = None
        self.update_status = status_callback 
        self.app_data = {}
        self.data_lock = threading.Lock() 

    def set_data(self, data):
        with self.data_lock:
            self.app_data = data

    def log_message(self, message, color="blue", level="INFO"):
        self.update_status(message, color)
        if level == "INFO": logging.info(message)
        elif level == "WARNING": logging.warning(message)
        elif level == "ERROR": logging.error(message)
        elif level == "ACTION": logging.info(f"> {message}")

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.bot_thread = threading.Thread(target=self._loop, daemon=True)
            self.bot_thread.start()

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.log_message("Đang dừng bot...", "gray", "INFO")

    def _get_action_from_pool(self, action_id, pool):
        for act in pool:
            if act.get("id") == action_id: return act
        return None

    def _loop(self):
        self.log_message("=== BẮT ĐẦU CHẠY BOT ===", "green", "INFO")
        
        while self.is_running:
            with self.data_lock:
                settings = self.app_data.get("settings", {})
                action_pool = self.app_data.get("action_pool", [])
                workflow = self.app_data.get("workflow", [])
                
            loop_delay = float(settings.get("loop_delay", 2.0))

            if not workflow:
                self.log_message("Dòng chảy trống, hãy cấu hình ở giao diện!", "red", "ERROR")
                time.sleep(2)
                continue

            # BĂNG CHUYỀN CHẠY TỪ DÒNG 1 -> DÒNG CUỐI (100% Tuần Tự)
            for row in workflow:
                if not self.is_running: break
                
                row_name = row.get("row_name", "Dòng không tên")
                row_delay = float(row.get("delay", 0.0))
                row_timeout = float(row.get("timeout", 0.0))
                
                self.log_message(f"--- CHUẨN BỊ BƯỚC VÀO: {row_name} ---", "green", "INFO")
                
                # 1. THỰC HIỆN DELAY CHỜ VÀO DÒNG
                if row_delay > 0:
                    self.log_message(f"Đợi {row_delay}s trước khi bắt đầu dòng này...", "orange", "INFO")
                    wait_start = time.time()
                    while self.is_running and (time.time() - wait_start) < row_delay:
                        time.sleep(0.1) # Check liên tục để không bị kẹt khi user bấm Stop
                
                if not self.is_running: break
                
                # Nạp các hành động của dòng này
                current_actions = []
                for act_id in row.get("actions", []):
                    act = self._get_action_from_pool(act_id, action_pool)
                    if act and os.path.exists(act["image"]): 
                        current_actions.append(act)

                row_start_time = time.time()

                # 2. CHẠY TUẦN TỰ TỪNG HÀNH ĐỘNG TRONG DÒNG
                for act in current_actions:
                    if not self.is_running: break
                    
                    act_start_time = time.time()
                    wait_infinite = act.get("wait_infinite", True)
                    act_timeout = float(act.get("timeout", 2.0))
                    
                    while self.is_running:
                        # Check Timeout của Dòng trước tiên
                        if row_timeout > 0 and (time.time() - row_start_time) >= row_timeout:
                            self.log_message(f"{row_name}: Hết {row_timeout}s Timeout Dòng -> Ép thoát!", "orange", "WARNING")
                            break 
                            
                        pos = vision.find_template_on_screen(act["image"], threshold=0.8)
                        if pos:
                            x, y = pos
                            actions.click_at(x, y)
                            self.log_message(f"Hoàn thành '{act['name']}'", "blue", "ACTION")
                            time.sleep(0.5) # Nghỉ cơ bản 0.5s sau khi click
                            break # Xong ô này, qua ô kế tiếp
                        else:
                            # Xử lý Bỏ qua (Skip) của riêng ô này
                            if not wait_infinite:
                                if (time.time() - act_start_time) >= act_timeout:
                                    self.log_message(f"Không thấy '{act['name']}' sau {act_timeout}s -> SKIP", "orange", "WARNING")
                                    break 
                            
                            time.sleep(0.5) 
                            
                    # Nếu nguyên nhân văng khỏi vòng lặp là do Hết giờ Dòng, thì ngắt luôn cả luồng hành động
                    if row_timeout > 0 and (time.time() - row_start_time) >= row_timeout:
                        break

            # Hết 1 vòng kịch bản (đã chạy xong dòng cuối cùng)
            if self.is_running:
                self.log_message(f"Đã xong 1 vòng. Đứng nghỉ {loop_delay}s trước khi lặp lại...", "green", "INFO")
                time.sleep(loop_delay)
                
        self.log_message("=== BOT ĐÃ DỪNG HOÀN TOÀN ===", "gray", "INFO")