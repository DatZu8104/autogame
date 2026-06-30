import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

import customtkinter as ctk
import keyboard
import os
import shutil
import time
import json
from tkinter import filedialog
from bot_core import BotLogic
import module4_coordinate_picker as picker # IMPORT THÊM TÍNH NĂNG PICK TỌA ĐỘ

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

IMAGE_DIR = "thu_muc_anh_nhan_dien"
DATA_FILE = "du_lieu_bot.json"

class GameBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Game Auto Bot - V7.5 (Coordinate Mode)")
        self.geometry("1100x700") 
        self.resizable(False, False)

        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR)

        self.bot = BotLogic(dashboard_callback=self.update_dashboard)
        self.vcmd = (self.register(self.validate_number_input), '%P')

        self.app_data = self.load_data()
        self.bot.set_data(self.app_data)
        
        self.current_hotkey = self.app_data["settings"].get("hotkey", "F9")

        self.title_label = ctk.CTkLabel(self, text="GAME AUTOMATION BOT - V7", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(10, 0))

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.left_frame = ctk.CTkFrame(self.main_frame, width=350)
        self.left_frame.pack(side="left", fill="y", padx=(0, 5))
        self.left_frame.pack_propagate(False)

        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.setup_left_panel()
        self.setup_right_panel()
        self.setup_bottom_panel()

        try: keyboard.add_hotkey(self.current_hotkey, self.toggle_bot)
        except Exception: pass

    def validate_number_input(self, P):
        if P in ["", ".", ","]: return True
        try:
            float(P.replace(",", "."))
            return True
        except ValueError: return False

    def load_data(self):
        default_data = {
            "settings": {"loop_delay": 2.0, "hotkey": "F9", "enable_file_log": True},
            "action_pool": [],
            "workflow": []
        }
        if not os.path.exists(DATA_FILE): return default_data
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "action_pool" not in data or "workflow" not in data: return default_data
                
                valid_pool = []
                for act in data.get("action_pool", []):
                    act_type = act.get("type", "image") # Mặc định cũ là ảnh
                    
                    if act_type == "image":
                        if os.path.exists(act.get("image", "")):
                            if "wait_infinite" not in act: act["wait_infinite"] = True
                            if "timeout" not in act: act["timeout"] = 2.0
                            if "action" not in act: act["action"] = "Click"
                            valid_pool.append(act)
                    elif act_type == "coordinate":
                        if "action" not in act: act["action"] = "Click"
                        valid_pool.append(act)
                        
                data["action_pool"] = valid_pool
                return data
        except Exception: return default_data

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.app_data, f, ensure_ascii=False, indent=4)
            self.bot.set_data(self.app_data)
        except Exception as e:
            print(f"[Lỗi] Lưu JSON: {e}")

    # ==========================================
    # CỘT TRÁI: KHO HÀNH ĐỘNG
    # ==========================================
    def setup_left_panel(self):
        ctk.CTkLabel(self.left_frame, text="KHO HÀNH ĐỘNG", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.add_act_btn = ctk.CTkButton(self.left_frame, text="+ Thêm Hành Động Mới", fg_color="teal", hover_color="darkcyan", command=self.open_add_action_dialog)
        self.add_act_btn.pack(pady=5, padx=20, fill="x")
        self.pool_scroll = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.pool_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.render_action_pool()

    def render_action_pool(self):
        for widget in self.pool_scroll.winfo_children(): widget.destroy()
        pool = self.app_data.get("action_pool", [])
        if not pool:
            ctk.CTkLabel(self.pool_scroll, text="Kho rỗng. Hãy tạo mới!", text_color="gray").pack(pady=20)
            if hasattr(self, 'workflow_scroll'): self.render_workflow()
            return

        for act in pool:
            frame = ctk.CTkFrame(self.pool_scroll, fg_color="gray25")
            frame.pack(fill="x", pady=3, padx=2)
            
            top_row = ctk.CTkFrame(frame, fg_color="transparent")
            top_row.pack(fill="x", padx=5, pady=2)
            
            act_type = act.get("type", "image")
            icon = "🖼️ " if act_type == "image" else "🎯 "
            display_name = icon + (act['name'] if len(act['name']) <= 16 else act['name'][:13] + "..")
            
            ctk.CTkLabel(top_row, text=display_name, anchor="w", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            ctk.CTkButton(top_row, text="X", width=20, height=20, fg_color="red", hover_color="darkred", 
                          command=lambda a_id=act['id']: self.delete_action_from_pool(a_id)).pack(side="right")
            
            bot_row = ctk.CTkFrame(frame, fg_color="transparent")
            bot_row.pack(fill="x", padx=5, pady=(0, 5))
            
            if act_type == "image":
                var_inf = ctk.BooleanVar(value=act.get("wait_infinite", True))
                var_to = ctk.StringVar(value=str(act.get("timeout", 2.0)))
                
                chk_inf = ctk.CTkCheckBox(bot_row, text="Chờ vô hạn", variable=var_inf, width=60, checkbox_height=16, checkbox_width=16)
                chk_inf.pack(side="left", padx=(0, 10))
                
                ctk.CTkLabel(bot_row, text="hoặc Skip sau:").pack(side="left", padx=2)
                to_entry = ctk.CTkEntry(bot_row, textvariable=var_to, width=40, height=20, validate="key", validatecommand=self.vcmd)
                to_entry.pack(side="left", padx=2)
                ctk.CTkLabel(bot_row, text="s").pack(side="left")

                to_entry.configure(state="disabled" if var_inf.get() else "normal")

                def on_setting_change(*args, a_id=act['id'], v_i=var_inf, v_t=var_to, ent=to_entry):
                    is_inf = v_i.get()
                    ent.configure(state="disabled" if is_inf else "normal")
                    for a in self.app_data["action_pool"]:
                        if a["id"] == a_id:
                            a["wait_infinite"] = is_inf
                            try: a["timeout"] = float(v_t.get().replace(',', '.'))
                            except ValueError: a["timeout"] = 2.0
                            break
                    self.save_data()

                chk_inf.configure(command=on_setting_change)
                to_entry.bind("<FocusOut>", on_setting_change)
                to_entry.bind("<Return>", on_setting_change)
            else:
                # Nếu là tọa độ, chỉ hiện thông tin X Y
                x_val, y_val = act.get('x', 0), act.get('y', 0)
                ctk.CTkLabel(bot_row, text=f"(Click ngay lập tức) X: {x_val} | Y: {y_val}", text_color="gray").pack(side="left")

        if hasattr(self, 'workflow_scroll'):
            self.render_workflow()

    def open_add_action_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Tạo Hành Động Mới")
        dialog.geometry("380x430")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)

        # Tabs để chọn Loại Dữ Liệu
        tabview = ctk.CTkTabview(dialog, width=350, height=250)
        tabview.pack(padx=10, pady=(10,0))
        tab_img = tabview.add("🖼️ Dùng Ảnh Nhận Diện")
        tab_coord = tabview.add("🎯 Dùng Tọa Độ Cố Định")

        # --- TAB 1: ẢNH ---
        ctk.CTkLabel(tab_img, text="(Mặc định Hành động sẽ Chờ Vô Hạn)\nCó thể chỉnh lại ở ngoài Kho sau.", text_color="gray").pack(pady=(10,0))
        self.temp_image_path = None
        
        def browse_file():
            filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
            if filepath:
                self.temp_image_path = filepath
                img_btn.configure(text=f"...{os.path.basename(filepath)}")

        img_btn = ctk.CTkButton(tab_img, text="Chọn file ảnh", fg_color="gray40", command=browse_file)
        img_btn.pack(pady=15)

        # --- TAB 2: TỌA ĐỘ ---
        coord_frame = ctk.CTkFrame(tab_coord, fg_color="transparent")
        coord_frame.pack(pady=20)
        
        ctk.CTkLabel(coord_frame, text="X:").grid(row=0, column=0, padx=5, pady=5)
        x_entry = ctk.CTkEntry(coord_frame, width=60, validate="key", validatecommand=self.vcmd)
        x_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(coord_frame, text="Y:").grid(row=0, column=2, padx=5, pady=5)
        y_entry = ctk.CTkEntry(coord_frame, width=60, validate="key", validatecommand=self.vcmd)
        y_entry.grid(row=0, column=3, padx=5, pady=5)

        pick_btn = ctk.CTkButton(tab_coord, text="Bắt Tọa Độ (Click)", fg_color="darkred", hover_color="red")
        pick_btn.pack(pady=10)

        def pick_coord_callback(x, y, is_final):
            if x is not None and y is not None:
                x_entry.delete(0, 'end'); x_entry.insert(0, str(x))
                y_entry.delete(0, 'end'); y_entry.insert(0, str(y))
                if not is_final:
                    pick_btn.configure(text=f"Đang dò... X:{x} Y:{y}")
            if is_final:
                pick_btn.configure(text="Bắt Lại Tọa Độ")

        def start_picking():
            pick_btn.configure(text="Đang bắt...")
            picker.CoordinatePicker(dialog, pick_coord_callback)

        pick_btn.configure(command=start_picking)
        ctk.CTkLabel(tab_coord, text="(Click trái để chốt | Chuột phải/ESC để hủy)", text_color="gray").pack()

        # --- PHẦN DƯỚI DÙNG CHUNG ---
        ctk.CTkLabel(dialog, text="Tên nhận diện (VD: Nút Bắt Đầu):").pack(pady=(15,0))
        name_entry = ctk.CTkEntry(dialog, width=250)
        name_entry.pack(pady=5)

        action_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        action_frame.pack(pady=5)
        ctk.CTkLabel(action_frame, text="Loại thao tác:").pack(side="left", padx=5)
        action_type_var = ctk.StringVar(value="Click")
        ctk.CTkOptionMenu(action_frame, values=["Click", "Double Click"], variable=action_type_var, width=120).pack(side="left")

        def save_action():
            name = name_entry.get().strip()
            if not name: return

            act_id = f"A_{int(time.time() * 1000)}"
            current_tab = tabview.get()
            
            if current_tab == "🖼️ Dùng Ảnh Nhận Diện":
                if not self.temp_image_path: return
                ext = os.path.splitext(self.temp_image_path)[1]
                new_filename = f"act_{act_id}{ext}"
                saved_path = os.path.join(IMAGE_DIR, new_filename)
                shutil.copy(self.temp_image_path, saved_path)

                self.app_data["action_pool"].append({
                    "id": act_id, "type": "image", "name": name, 
                    "image": saved_path, "action": action_type_var.get(), 
                    "wait_infinite": True, "timeout": 2.0
                })
            else:
                try: 
                    x_val, y_val = int(x_entry.get()), int(y_entry.get())
                except ValueError: return

                self.app_data["action_pool"].append({
                    "id": act_id, "type": "coordinate", "name": name, 
                    "x": x_val, "y": y_val, "action": action_type_var.get()
                })

            self.save_data()
            self.render_action_pool()
            dialog.destroy()

        ctk.CTkButton(dialog, text="Lưu Hành Động", command=save_action).pack(pady=10)

    def delete_action_from_pool(self, act_id):
        for act in self.app_data["action_pool"]:
            if act["id"] == act_id and act.get("type", "image") == "image" and os.path.exists(act.get("image","")):
                try: os.remove(act["image"])
                except Exception: pass
        self.app_data["action_pool"] = [act for act in self.app_data["action_pool"] if act["id"] != act_id]
        
        for row in self.app_data["workflow"]:
            row["actions"] = [a_id for a_id in row.get("actions", []) if a_id != act_id]
            
        self.save_data()
        self.render_action_pool()

    # ==========================================
    # CỘT PHẢI: DÒNG CHẢY
    # ==========================================
    def setup_right_panel(self):
        header_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(header_frame, text="DÒNG CHẢY (WORKFLOW)", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.add_row_btn = ctk.CTkButton(header_frame, text="+ Thêm Dòng (Khối)", width=120, command=self.add_new_row)
        self.add_row_btn.pack(side="right")

        self.workflow_scroll = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        self.workflow_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.render_workflow()

    def add_new_row(self):
        row_id = f"R_{int(time.time() * 1000)}"
        new_row = {
            "row_id": row_id,
            "row_name": f"Dòng {len(self.app_data['workflow']) + 1}",
            "delay": 0.0,
            "timeout": 0.0,
            "actions": []
        }
        self.app_data["workflow"].append(new_row)
        self.save_data()
        self.render_workflow()

    def delete_row(self, row_id):
        self.app_data["workflow"] = [r for r in self.app_data["workflow"] if r["row_id"] != row_id]
        self.save_data()
        self.render_workflow()

    def render_workflow(self):
        for widget in self.workflow_scroll.winfo_children(): widget.destroy()
        if not self.app_data.get("workflow"):
            ctk.CTkLabel(self.workflow_scroll, text="Chưa có Dòng chảy nào.\nHãy bấm '+ Thêm Dòng' ở góc phải.", text_color="gray").pack(pady=40)
            return

        pool_dict = {f"{'🖼️' if act.get('type','image')=='image' else '🎯'} {act['name']}": act['id'] for act in self.app_data.get("action_pool", [])}
        pool_names = list(pool_dict.keys())

        for idx, row in enumerate(self.app_data["workflow"]):
            r_id = row["row_id"]
            row_frame = ctk.CTkFrame(self.workflow_scroll, fg_color="gray20", border_width=1, border_color="gray40")
            row_frame.pack(fill="x", pady=10, padx=5)

            header = ctk.CTkFrame(row_frame, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=5)

            name_entry = ctk.CTkEntry(header, width=150, font=ctk.CTkFont(weight="bold"))
            name_entry.insert(0, row.get("row_name", f"Dòng {idx+1}"))
            name_entry.pack(side="left")
            name_entry.bind("<FocusOut>", lambda e, r=row, ent=name_entry: self._update_row_val(r, "row_name", ent.get()))

            ctk.CTkLabel(header, text="Delay vào (s):").pack(side="left", padx=(15, 2))
            dl_entry = ctk.CTkEntry(header, width=45, validate="key", validatecommand=self.vcmd)
            dl_entry.insert(0, str(row.get("delay", 0.0)))
            dl_entry.pack(side="left")
            dl_entry.bind("<FocusOut>", lambda e, r=row, ent=dl_entry: self._update_row_val(r, "delay", ent.get()))

            ctk.CTkLabel(header, text="Timeout Dòng (s):").pack(side="left", padx=(15, 2))
            to_entry = ctk.CTkEntry(header, width=45, validate="key", validatecommand=self.vcmd)
            to_entry.insert(0, str(row.get("timeout", 0.0)))
            to_entry.pack(side="left")
            to_entry.bind("<FocusOut>", lambda e, r=row, ent=to_entry: self._update_row_val(r, "timeout", ent.get()))

            ctk.CTkButton(header, text="Xóa Dòng", width=70, fg_color="darkred", hover_color="red", command=lambda rid=r_id: self.delete_row(rid)).pack(side="right")

            actions_frame = ctk.CTkScrollableFrame(row_frame, height=60, orientation="horizontal", fg_color="gray15")
            actions_frame.pack(fill="x", padx=10, pady=5)

            if not row.get("actions"):
                ctk.CTkLabel(actions_frame, text="Chưa có hành động.", text_color="gray").pack(pady=10)
            else:
                for act_idx, act_id in enumerate(row["actions"]):
                    act_info = next((a for a in self.app_data["action_pool"] if a["id"] == act_id), None)
                    if act_info:
                        act_box = ctk.CTkFrame(actions_frame, fg_color="teal", corner_radius=5)
                        act_box.pack(side="left", padx=5, pady=5)
                        ctk.CTkLabel(act_box, text=act_info["name"]).pack(side="left", padx=(10, 5), pady=2)
                        ctk.CTkButton(act_box, text="x", width=20, height=20, fg_color="transparent", hover_color="red",
                                      command=lambda r=row, a_i=act_idx: self._remove_act_from_row(r, a_i)).pack(side="right", padx=(0,5))

            footer = ctk.CTkFrame(row_frame, fg_color="transparent")
            footer.pack(fill="x", padx=10, pady=(5, 10))

            if pool_names:
                selected_act = ctk.StringVar(value=pool_names[0])
                ctk.CTkOptionMenu(footer, values=pool_names, variable=selected_act, width=170).pack(side="left")
                ctk.CTkButton(footer, text="Nhét vào Dòng", width=100, 
                              command=lambda r=row, v=selected_act: self._add_act_to_row(r, pool_dict[v.get()])).pack(side="left", padx=5)
            else:
                ctk.CTkLabel(footer, text="(Tạo hành động trước)", text_color="gray").pack(side="left")

    def _update_row_val(self, row, key, value):
        if key in ["timeout", "delay"]:
            try: row[key] = float(value.replace(",", "."))
            except ValueError: row[key] = 0.0
        else:
            row[key] = value
        self.save_data()

    def _add_act_to_row(self, row, act_id):
        if "actions" not in row: row["actions"] = []
        row["actions"].append(act_id)
        self.save_data()
        self.render_workflow()

    def _remove_act_from_row(self, row, act_idx):
        row["actions"].pop(act_idx)
        self.save_data()
        self.render_workflow()

    # ==========================================
    # KHUNG BÊN DƯỚI: CÀI ĐẶT & DASHBOARD
    # ==========================================
    def setup_bottom_panel(self):
        set_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        set_frame.pack(side="left", fill="y", pady=10, padx=10)

        ctk.CTkLabel(set_frame, text="Nghỉ Toàn Cục (Sau khi xong 1 vòng) (s):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.loop_delay_entry = ctk.CTkEntry(set_frame, width=60, validate="key", validatecommand=self.vcmd)
        self.loop_delay_entry.insert(0, str(self.app_data["settings"].get("loop_delay", 2.0)))
        self.loop_delay_entry.grid(row=0, column=1, padx=5, pady=2)
        self.loop_delay_entry.bind("<FocusOut>", lambda e: self.update_settings())
        self.loop_delay_entry.bind("<Return>", lambda e: self.update_settings())

        ctk.CTkLabel(set_frame, text="Phím tắt Bật/Tắt:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.hotkey_entry = ctk.CTkEntry(set_frame, width=60)
        self.hotkey_entry.insert(0, self.current_hotkey)
        self.hotkey_entry.grid(row=1, column=1, padx=5, pady=2)
        self.hotkey_entry.bind("<Return>", lambda e: self.update_hotkey())

        ctrl_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        ctrl_frame.pack(side="right", fill="y", pady=5, padx=10)

        self.dash_frame = ctk.CTkFrame(ctrl_frame, width=320, height=115, fg_color="gray15", corner_radius=8, border_width=1, border_color="gray30")
        self.dash_frame.pack_propagate(False) 
        self.dash_frame.pack(side="top", pady=(0, 5))

        font_bold = ctk.CTkFont(weight="bold", size=12)
        font_mono = ctk.CTkFont(family="Consolas", size=13, weight="bold") 

        self.lbl_status = ctk.CTkLabel(self.dash_frame, text="Trạng thái: 🔴 Đã dừng", anchor="w", font=font_bold, text_color="gray")
        self.lbl_status.pack(fill="x", padx=10, pady=(5, 0))

        self.lbl_stage = ctk.CTkLabel(self.dash_frame, text="Giai đoạn: -", anchor="w", font=font_bold)
        self.lbl_stage.pack(fill="x", padx=10, pady=(2, 0))

        self.lbl_action = ctk.CTkLabel(self.dash_frame, text="Hành động: -", anchor="w", font=font_bold)
        self.lbl_action.pack(fill="x", padx=10, pady=(2, 0))

        self.lbl_countdown = ctk.CTkLabel(self.dash_frame, text="Đếm ngược: -", anchor="w", font=font_mono, text_color="gold")
        self.lbl_countdown.pack(fill="x", padx=10, pady=(2, 5))

        btn_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        btn_row.pack(side="bottom")

        self.start_button = ctk.CTkButton(btn_row, text=f"START ({self.current_hotkey})", fg_color="green", hover_color="darkgreen", command=self.on_start, width=100)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ctk.CTkButton(btn_row, text="STOP", fg_color="red", hover_color="darkred", command=self.on_stop, state="disabled", width=100)
        self.stop_button.pack(side="right", padx=5)

    def update_settings(self):
        try: cd = float(self.loop_delay_entry.get().replace(",", "."))
        except ValueError: cd = 2.0
        self.app_data["settings"]["loop_delay"] = cd
        self.save_data()

    def update_hotkey(self):
        new_hk = self.hotkey_entry.get().strip()
        if not new_hk: return
        try: keyboard.remove_hotkey(self.current_hotkey)
        except Exception: pass
        try:
            keyboard.add_hotkey(new_hk, self.toggle_bot)
            self.current_hotkey = new_hk
            self.app_data["settings"]["hotkey"] = new_hk
            self.save_data()
            self.start_button.configure(text=f"START ({self.current_hotkey})")
            self.update_dashboard("🟢 Đã đổi phím", f"Phím mới: {new_hk}", "-", "-", "green")
        except ValueError:
            self.update_dashboard("🔴 Phím lỗi", "Không thể gán phím này", "-", "-", "red")
            keyboard.add_hotkey(self.current_hotkey, self.toggle_bot)

    def update_dashboard(self, status, stage, action, countdown, color):
        def _update():
            self.lbl_status.configure(text=f"Trạng thái: {status}", text_color=color)
            self.lbl_stage.configure(text=f"Giai đoạn: {stage}")
            self.lbl_action.configure(text=f"Hành động: {action}")
            self.lbl_countdown.configure(text=f"Đếm ngược: {countdown}")
        self.after(0, _update)

    def toggle_bot(self):
        if not self.bot.is_running: self.after(0, self.on_start)
        else: self.after(0, self.on_stop)

    def on_start(self):
        if self.bot.is_running: return 
        self.update_settings()
        
        if not self.app_data.get("workflow"):
            self.update_dashboard("🔴 Lỗi", "Dòng chảy trống!", "Hãy thêm Dòng ở cột phải", "-", "red")
            return

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.add_act_btn.configure(state="disabled")
        self.add_row_btn.configure(state="disabled")
        self.bot.start()

    def on_stop(self):
        if not self.bot.is_running: return
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.add_act_btn.configure(state="normal")
        self.add_row_btn.configure(state="normal")
        self.bot.stop()

if __name__ == "__main__":
    app = GameBotApp()
    app.mainloop()