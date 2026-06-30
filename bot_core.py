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
    def __init__(self, dashboard_callback):
        self.is_running = False
        self.bot_thread = None
        self.update_dashboard = dashboard_callback 
        self.app_data = {}
        self.data_lock = threading.Lock() 

        self.state_status = "🔴 Đã dừng"
        self.state_stage = "-"
        self.state_action = "-"
        self.state_countdown = "-"
        self.state_color = "gray"

    def set_data(self, data):
        with self.data_lock:
            self.app_data = data

    def _update_ui(self):
        if self.update_dashboard:
            self.update_dashboard(
                self.state_status, self.state_stage, 
                self.state_action, self.state_countdown, self.state_color
            )

    def log_message(self, message, level="INFO"):
        if level == "INFO": logging.info(message)
        elif level == "WARNING": logging.warning(message)
        elif level == "ERROR": logging.error(message)
        elif level == "ACTION": logging.info(f"> {message}")

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.state_status = "🟢 Đang hoạt động"
            self.state_color = "green"
            self._update_ui()
            self.bot_thread = threading.Thread(target=self._loop, daemon=True)
            self.bot_thread.start()

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.log_message("Đang dừng bot...", "INFO")
            self.state_status = "🔴 Đã dừng"
            self.state_stage = "-"
            self.state_action = "-"
            self.state_countdown = "-"
            self.state_color = "gray"
            self._update_ui()

    def _get_action_from_pool(self, action_id, pool):
        for act in pool:
            if act.get("id") == action_id: return act
        return None

    def _loop(self):
        self.log_message("=== BẮT ĐẦU CHẠY BOT ===", "INFO")
        
        while self.is_running:
            with self.data_lock:
                settings = self.app_data.get("settings", {})
                action_pool = self.app_data.get("action_pool", [])
                workflow = self.app_data.get("workflow", [])
                
            loop_delay = float(settings.get("loop_delay", 2.0))

            if not workflow:
                self.log_message("Dòng chảy trống!", "ERROR")
                time.sleep(2)
                continue

            for row in workflow:
                if not self.is_running: break
                
                row_name = row.get("row_name", "Dòng không tên")
                short_row = row_name if len(row_name) <= 22 else row_name[:19] + "..."
                row_delay = float(row.get("delay", 0.0))
                row_timeout = float(row.get("timeout", 0.0))
                
                self.log_message(f"--- BƯỚC VÀO: {row_name} ---", "INFO")
                self.state_stage = f"[{short_row}]"
                self.state_action = "💤 Đang chuẩn bị..."
                self.state_countdown = "-"
                self._update_ui()
                
                if row_delay > 0:
                    self.state_action = "💤 Đợi vào Dòng..."
                    wait_start = time.time()
                    while self.is_running and (time.time() - wait_start) < row_delay:
                        self.state_countdown = f"⏳ Delay: {(time.time() - wait_start):.1f}s / {row_delay:.1f}s"
                        self._update_ui()
                        time.sleep(0.1) 
                
                if not self.is_running: break
                
                current_actions = []
                for act_id in row.get("actions", []):
                    act = self._get_action_from_pool(act_id, action_pool)
                    # Sửa lại: Nếu là tọa độ thì không cần check os.path.exists(ảnh)
                    if act:
                        if act.get("type") == "coordinate" or os.path.exists(act.get("image", "")):
                            current_actions.append(act)

                row_start_time = time.time()

                for act in current_actions:
                    if not self.is_running: break
                    
                    act_type = act.get("type", "image")
                    action_click_type = act.get("action", "Click")
                    short_act = act['name'] if len(act['name']) <= 18 else act['name'][:15] + "..."
                    
                    # ==========================================
                    # NHÁNH 1: HÀNH ĐỘNG TỌA ĐỘ
                    # ==========================================
                    if act_type == "coordinate":
                        x, y = int(act.get("x", 0)), int(act.get("y", 0))
                        self.state_action = f"🎯 Click điểm: X:{x} Y:{y}"
                        self.state_countdown = "✅ Xong"
                        self._update_ui()
                        
                        if action_click_type == "Double Click": actions.double_click_at(x, y)
                        else: actions.click_at(x, y)
                            
                        self.log_message(f"Click Tọa độ '{act['name']}' ({action_click_type})", "ACTION")
                        
                        w_start = time.time()
                        while self.is_running and (time.time() - w_start) < 0.5:
                            time.sleep(0.1)
                            
                        continue # Bỏ qua phần dưới, lập tức nhảy sang Action tiếp theo
                    
                    # ==========================================
                    # NHÁNH 2: HÀNH ĐỘNG TÌM ẢNH (Logic cũ)
                    # ==========================================
                    act_start_time = time.time()
                    wait_infinite = act.get("wait_infinite", True)
                    act_timeout = float(act.get("timeout", 2.0))
                    
                    while self.is_running:
                        if not wait_infinite:
                            self.state_countdown = f"⏩ Skip bước: {(time.time() - act_start_time):.1f}s / {act_timeout:.1f}s"
                        elif row_timeout > 0:
                            self.state_countdown = f"⏱️ Timeout: {(time.time() - row_start_time):.1f}s / {row_timeout:.1f}s"
                        else:
                            self.state_countdown = "♾️ Chờ vô hạn"
                        
                        self.state_action = f"🔍 Đang quét: [{short_act}]"
                        self._update_ui()

                        if row_timeout > 0 and (time.time() - row_start_time) >= row_timeout:
                            self.log_message(f"Hết {row_timeout}s Timeout Dòng -> Ép thoát!", "WARNING")
                            break 
                            
                        pos = vision.find_template_on_screen(act["image"], threshold=0.8)
                        if pos:
                            x, y = pos
                            
                            self.state_action = f"🖱️ Đã nhấn: [{short_act}]"
                            self.state_countdown = "✅ Hoàn thành"
                            self._update_ui()

                            if action_click_type == "Double Click": actions.double_click_at(x, y)
                            else: actions.click_at(x, y)
                                
                            self.log_message(f"Nhận diện '{act['name']}' ({action_click_type})", "ACTION")
                            
                            w_start = time.time()
                            while self.is_running and (time.time() - w_start) < 0.5:
                                time.sleep(0.1)
                            break 
                        else:
                            if not wait_infinite:
                                if (time.time() - act_start_time) >= act_timeout:
                                    self.log_message(f"Không thấy '{act['name']}' -> SKIP", "WARNING")
                                    break 
                            
                            w_start = time.time()
                            while self.is_running and (time.time() - w_start) < 0.5:
                                if not wait_infinite:
                                    self.state_countdown = f"⏩ Skip bước: {(time.time() - act_start_time):.1f}s / {act_timeout:.1f}s"
                                elif row_timeout > 0:
                                    self.state_countdown = f"⏱️ Timeout: {(time.time() - row_start_time):.1f}s / {row_timeout:.1f}s"
                                self._update_ui()
                                time.sleep(0.1) 
                            
                    if row_timeout > 0 and (time.time() - row_start_time) >= row_timeout:
                        break

            if self.is_running:
                self.log_message(f"Đã xong 1 vòng. Nghỉ {loop_delay}s...", "INFO")
                self.state_stage = "🔄 Hoàn thành 1 vòng"
                self.state_action = "☕ Đứng xả hơi..."
                
                loop_wait_start = time.time()
                while self.is_running and (time.time() - loop_wait_start) < loop_delay:
                    self.state_countdown = f"⏳ Nghỉ toàn cục: {(time.time() - loop_wait_start):.1f}s / {loop_delay:.1f}s"
                    self._update_ui()
                    time.sleep(0.1)
                
        self.log_message("=== BOT ĐÃ DỪNG HOÀN TOÀN ===", "INFO")