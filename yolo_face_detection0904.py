import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
from ultralytics import YOLO


class YoloIntegratedApp:

  def __init__(self, root):
    self.root = root
    self.root.title("YOLO 實時鏡頭 / 本機圖片辨識與手動匡列控制介面")
    self.root.geometry("1450x920")

    # 1. 初始化 YOLO 模型與狀態變數
    self.model = YOLO("yolov8n.pt")
    self.cap = None
    self.is_running = False
    self.is_detecting = False  # 防止背景線程重複堆疊

    self.current_boxes = []  # 存放當前影格的標註資訊
    self.selected_idx = None
    self.custom_count = 0

    self.last_frame = None  # 原始 OpenCV BGR 影像
    self.last_annotated_frame = None  # 繪製後的 BGR 影像
    self.tk_img = None  # 保持 Tkinter 影像引用

    # Canvas 視角控制
    self.zoom_scale = 1.0
    self.pan_x = 0
    self.pan_y = 0

    # 右鍵匡列控制
    self.draw_start_x = None
    self.draw_start_y = None
    self.temp_draw_box = None

    self.output_dir = "captures"
    os.makedirs(self.output_dir, exist_ok=True)

    # 2. 建立介面
    self.create_widgets()
    self.scan_cameras()

    # 3. 關閉視窗時安全釋放資源
    self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

  def find_working_cameras(self):
    available_cameras = []
    for index in range(5):
      cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # Windows 加速
      if not cap.isOpened():
        cap = cv2.VideoCapture(index)
      if cap.isOpened():
        ret, _ = cap.read()
        if ret:
          available_cameras.append(index)
        cap.release()
    return available_cameras

  def scan_cameras(self):
    cameras = self.find_working_cameras()
    if cameras:
      self.camera_combo["values"] = cameras
      self.camera_combo.current(0)
      self.log_message(f"掃描成功，找到可用攝影機：{cameras}")
    else:
      self.log_message("【警告】未偵測到可用攝影機！")

  def log_message(self, message):
    timestamp = time.strftime("[%H:%M:%S]")
    log_text = f"{timestamp} {message}\n"
    self.log_text_widget.config(state=tk.NORMAL)
    self.log_text_widget.insert(tk.END, log_text)
    self.log_text_widget.see(tk.END)
    self.log_text_widget.config(state=tk.DISABLED)

  def create_widgets(self):
    control_frame = tk.LabelFrame(
        self.root,
        text=" 綜合辨識與標註控制面板 ",
        font=("微軟正黑體", 11, "bold"),
        padx=10,
        pady=5,
    )
    control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    # 列 1：鏡頭與圖片控制
    row1 = tk.Frame(control_frame)
    row1.pack(fill=tk.X, pady=2)

    tk.Label(row1, text="選擇鏡頭:", font=("微軟正黑體", 10, "bold")).pack(
        side=tk.LEFT, padx=(5, 2)
    )
    self.camera_var = tk.StringVar()
    self.camera_combo = ttk.Combobox(
        row1, textvariable=self.camera_var, width=6, state="readonly"
    )
    self.camera_combo.pack(side=tk.LEFT, padx=(0, 5))

    self.btn_toggle_cam = tk.Button(
        row1,
        text="啟動攝影機",
        command=self.toggle_camera,
        font=("微軟正黑體", 10, "bold"),
        bg="#4CAF50",
        fg="white",
    )
    self.btn_toggle_cam.pack(side=tk.LEFT, padx=5)

    tk.Button(
        row1,
        text="重新掃描鏡頭",
        command=self.scan_cameras,
        font=("微軟正黑體", 10),
    ).pack(side=tk.LEFT, padx=5)

    # 實時快照按鈕
    self.btn_snapshot = tk.Button(
        row1,
        text="📸 實時快照",
        command=self.take_snapshot,
        font=("微軟正黑體", 10, "bold"),
        bg="#E91E63",
        fg="white",
    )
    self.btn_snapshot.pack(side=tk.LEFT, padx=(15, 5))

    tk.Button(
        row1,
        text="📁 載入本機圖片",
        command=self.select_local_image,
        font=("微軟正黑體", 10, "bold"),
        bg="#2196F3",
        fg="white",
    ).pack(side=tk.LEFT, padx=5)

    self.btn_repredict = tk.Button(
        row1,
        text="重新辨識圖片",
        command=self.run_image_detection,
        font=("微軟正黑體", 10),
        state=tk.DISABLED,
    )
    self.btn_repredict.pack(side=tk.LEFT, padx=5)

    tk.Button(
        row1,
        text="💾 完整儲存 (含文字)",
        command=self.save_current_data,
        font=("微軟正黑體", 10, "bold"),
        bg="#FF9800",
        fg="white",
    ).pack(side=tk.LEFT, padx=10)

    tk.Label(
        row1,
        text="💡 提示：【右鍵拖曳】手動匡列 | 【左鍵】畫布平移 | 【滾輪】縮放",
        font=("微軟正黑體", 9, "bold"),
        fg="#D32F2F",
    ).pack(side=tk.LEFT, padx=5)

    # 列 2：參數調整
    row2 = tk.Frame(control_frame)
    row2.pack(fill=tk.X, pady=2)

    tk.Label(row2, text="Confidence (conf):", font=("微軟正黑體", 10)).pack(
        side=tk.LEFT, padx=(5, 2)
    )
    self.conf_slider = tk.Scale(
        row2,
        from_=0.01,
        to=1.00,
        resolution=0.01,
        orient=tk.HORIZONTAL,
        length=130,
    )
    self.conf_slider.set(0.40)
    self.conf_slider.pack(side=tk.LEFT, padx=(0, 15))

    tk.Label(row2, text="IOU (門檻):", font=("微軟正黑體", 10)).pack(
        side=tk.LEFT, padx=(5, 2)
    )
    self.iou_slider = tk.Scale(
        row2,
        from_=0.01,
        to=1.00,
        resolution=0.01,
        orient=tk.HORIZONTAL,
        length=130,
    )
    self.iou_slider.set(0.50)
    self.iou_slider.pack(side=tk.LEFT, padx=(0, 15))

    tk.Label(row2, text="Image Size:", font=("微軟正黑體", 10)).pack(
        side=tk.LEFT, padx=(5, 2)
    )
    self.imgsz_var = tk.StringVar(value="640")
    ttk.Combobox(
        row2,
        textvariable=self.imgsz_var,
        values=["320", "640", "1280"],
        width=6,
        state="readonly",
    ).pack(side=tk.LEFT, padx=(0, 15))

    tk.Label(row2, text="Device:", font=("微軟正黑體", 10)).pack(
        side=tk.LEFT, padx=(5, 2)
    )
    self.device_var = tk.StringVar(value="cpu")
    ttk.Combobox(
        row2,
        textvariable=self.device_var,
        values=["cpu", "0"],
        width=6,
        state="readonly",
    ).pack(side=tk.LEFT, padx=(0, 15))

    # 列 3：類別選擇
    row3 = tk.Frame(control_frame)
    row3.pack(fill=tk.X, pady=2)

    tk.Label(
        row3, text="辨識與參考物勾選:", font=("微軟正黑體", 10, "bold")
    ).pack(side=tk.LEFT, padx=(5, 5))
    self.cls_all_var = tk.BooleanVar(value=True)
    self.cls_person_var = tk.BooleanVar(value=False)
    self.cls_car_var = tk.BooleanVar(value=False)
    self.cls_bottle_var = tk.BooleanVar(value=False)
    self.cls_cellphone_var = tk.BooleanVar(value=False)

    tk.Checkbutton(
        row3,
        text="全部類別",
        variable=self.cls_all_var,
        command=self.toggle_all_classes,
        font=("微軟正黑體", 10),
    ).pack(side=tk.LEFT, padx=4)
    tk.Checkbutton(
        row3,
        text="人 (0)",
        variable=self.cls_person_var,
        command=self.uncheck_all_var,
        font=("微軟正黑體", 10),
    ).pack(side=tk.LEFT, padx=4)
    tk.Checkbutton(
        row3,
        text="汽車 (2)",
        variable=self.cls_car_var,
        command=self.uncheck_all_var,
        font=("微軟正黑體", 10),
    ).pack(side=tk.LEFT, padx=4)
    tk.Checkbutton(
        row3,
        text="🔍 寶特瓶 (39)",
        variable=self.cls_bottle_var,
        command=self.uncheck_all_var,
        font=("微軟正黑體", 10, "bold"),
        fg="#00796B",
    ).pack(side=tk.LEFT, padx=4)
    tk.Checkbutton(
        row3,
        text="🔍 手機 (67)",
        variable=self.cls_cellphone_var,
        command=self.uncheck_all_var,
        font=("微軟正黑體", 10, "bold"),
        fg="#00796B",
    ).pack(side=tk.LEFT, padx=4)

    # 日誌區
    row_log = tk.Frame(control_frame)
    row_log.pack(fill=tk.X, pady=(5, 2))

    log_scroll = tk.Scrollbar(row_log)
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    self.log_text_widget = tk.Text(
        row_log,
        height=3,
        font=("Consolas", 9),
        bg="#1e1e1e",
        fg="#00ff00",
        state=tk.DISABLED,
        yscrollcommand=log_scroll.set,
    )
    self.log_text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
    log_scroll.config(command=self.log_text_widget.yview)

    # 主顯示區
    main_body = tk.Frame(self.root)
    main_body.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

    self.canvas = tk.Canvas(main_body, bg="#2b2b2b")
    self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 5))

    self.canvas.bind("<MouseWheel>", self.on_zoom)
    self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
    self.canvas.bind("<B1-Motion>", self.on_drag_motion)
    self.canvas.bind("<ButtonPress-3>", self.on_draw_start)
    self.canvas.bind("<B3-Motion>", self.on_draw_motion)
    self.canvas.bind("<ButtonRelease-3>", self.on_draw_end)

    # 右側清單與控制區
    list_frame = tk.LabelFrame(
        main_body, text=" 框選物件資訊與管理 ", font=("微軟正黑體", 10, "bold"), width=380
    )
    list_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
    list_frame.pack_propagate(False)

    # --- 新增：排序控制列 ---
    sort_frame = tk.Frame(list_frame)
    sort_frame.pack(fill=tk.X, padx=5, pady=(5, 2))

    tk.Label(sort_frame, text="物件排序:", font=("微軟正黑體", 9, "bold")).pack(
        side=tk.LEFT, padx=(2, 5)
    )
    self.sort_var = tk.StringVar(value="序號 (預設)")
    sort_options = [
        "序號 (預設)",
        "名稱 (A-Z)",
        "信心度 (高->低)",
        "信心度 (低->高)",
        "面積 Size (大->小)",
        "面積 Size (小->大)",
    ]
    self.sort_combo = ttk.Combobox(
        sort_frame,
        textvariable=self.sort_var,
        values=sort_options,
        width=16,
        state="readonly",
    )
    self.sort_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
    self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.sort_objects())

    # 清單列表容器
    box_container = tk.Frame(list_frame)
    box_container.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    self.obj_listbox = tk.Listbox(
        box_container, font=("Consolas", 9), selectmode=tk.SINGLE
    )
    scrollbar = tk.Scrollbar(
        box_container, orient=tk.VERTICAL, command=self.obj_listbox.yview
    )
    self.obj_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.obj_listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # --- 新增：多元刪除按鈕區 ---
    btn_del_frame = tk.Frame(list_frame)
    btn_del_frame.pack(fill=tk.X, padx=5, pady=5)

    btn_delete_selected = tk.Button(
        btn_del_frame,
        text="刪除單一選取",
        command=self.delete_selected_item,
        font=("微軟正黑體", 9, "bold"),
        bg="#F44336",
        fg="white",
    )
    btn_delete_selected.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    btn_delete_custom = tk.Button(
        btn_del_frame,
        text="僅刪自訂框",
        command=self.delete_custom_items,
        font=("微軟正黑體", 9),
        bg="#FF9800",
        fg="white",
    )
    btn_delete_custom.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    btn_clear_all = tk.Button(
        btn_del_frame,
        text="清除全部框",
        command=self.clear_all_items,
        font=("微軟正黑體", 9),
        bg="#D32F2F",
        fg="white",
    )
    btn_clear_all.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    self.obj_listbox.bind("<<ListboxSelect>>", self.on_list_select)

  # --- 類別切換邏輯 ---
  def toggle_all_classes(self):
    if self.cls_all_var.get():
      self.cls_person_var.set(False)
      self.cls_car_var.set(False)
      self.cls_bottle_var.set(False)
      self.cls_cellphone_var.set(False)

  def uncheck_all_var(self):
    self.cls_all_var.set(False)

  def get_selected_classes(self):
    if self.cls_all_var.get():
      return None
    selected = []
    if self.cls_person_var.get():
      selected.append(0)
    if self.cls_car_var.get():
      selected.append(2)
    if self.cls_bottle_var.get():
      selected.append(39)
    if self.cls_cellphone_var.get():
      selected.append(67)
    return selected if selected else None

  # --- 物件排序邏輯 (新功能) ---
  def sort_objects(self):
    if not self.current_boxes:
      return

    mode = self.sort_var.get()
    if mode == "名稱 (A-Z)":
      self.current_boxes.sort(key=lambda x: x["name"].lower())
    elif mode == "信心度 (高->低)":
      self.current_boxes.sort(key=lambda x: x["conf"], reverse=True)
    elif mode == "信心度 (低->高)":
      self.current_boxes.sort(key=lambda x: x["conf"])
    elif mode == "面積 Size (大->小)":
      self.current_boxes.sort(key=lambda x: x["area"], reverse=True)
    elif mode == "面積 Size (小->大)":
      self.current_boxes.sort(key=lambda x: x["area"])
    else:  # 預設序號排序
      self.current_boxes.sort(key=lambda x: x.get("original_id", x["id"]))

    self.selected_idx = None
    self.render_canvas()
    self.update_listbox()
    self.log_message(f"[排序] 已更新列表順序 -> {mode}")

  # --- 物件刪除邏輯 (擴充功能) ---
  def delete_selected_item(self):
    selection = self.obj_listbox.curselection()
    if not selection:
      self.log_message("【提示】請先在右側列表中選取要刪除的項目！")
      return
    del_idx = selection[0]
    removed = self.current_boxes.pop(del_idx)
    self.selected_idx = None
    self.log_message(f"[刪除] 已移除項目：{removed['name']}")
    self.render_canvas()
    self.update_listbox()

  def delete_custom_items(self):
    initial_count = len(self.current_boxes)
    self.current_boxes = [
        box for box in self.current_boxes if not box.get("is_custom")
    ]
    deleted_count = initial_count - len(self.current_boxes)
    self.selected_idx = None
    self.render_canvas()
    self.update_listbox()
    self.log_message(f"[刪除] 已清除 {deleted_count} 個手動自訂框")

  def clear_all_items(self):
    if not self.current_boxes:
      return
    self.current_boxes.clear()
    self.selected_idx = None
    self.render_canvas()
    self.update_listbox()
    self.log_message("[刪除] 已清空畫面上所有標註框")

  # --- 實時快照功能 ---
  def take_snapshot(self):
    if self.last_frame is None:
      self.log_message("【警告】當前無視訊畫面，無法截圖！請先啟動鏡頭或開啟圖片。")
      return

    raw_img = self.last_frame.copy()
    annotated_img = (
        self.last_annotated_frame.copy()
        if self.last_annotated_frame is not None
        else raw_img
    )

    def _save_task():
      timestamp = time.strftime("%Y%m%d_%H%M%S")
      raw_path = os.path.join(self.output_dir, f"snapshot_{timestamp}_raw.jpg")
      annotated_path = os.path.join(
          self.output_dir, f"snapshot_{timestamp}_annotated.jpg"
      )

      counter = 1
      while os.path.exists(raw_path):
        raw_path = os.path.join(
            self.output_dir, f"snapshot_{timestamp}_{counter}_raw.jpg"
        )
        annotated_path = os.path.join(
            self.output_dir, f"snapshot_{timestamp}_{counter}_annotated.jpg"
        )
        counter += 1

      cv2.imwrite(raw_path, raw_img)
      cv2.imwrite(annotated_path, annotated_img)

      saved_filename = os.path.basename(raw_path).replace("_raw.jpg", "_*.jpg")
      msg = f"[📸 快照成功] 已存至 -> {saved_filename}"
      self.root.after(0, lambda: self.log_message(msg))

    threading.Thread(target=_save_task, daemon=True).start()

  # --- 本機圖片與攝影機處理邏輯 ---
  def select_local_image(self):
    path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.webp")]
    )
    if path:
      if self.is_running:
        self.stop_camera()

      img_array = np.fromfile(path, np.uint8)
      self.last_frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

      if self.last_frame is None:
        self.log_message("【錯誤】無法讀取圖片檔！")
        return

      self.btn_repredict.config(state=tk.NORMAL)
      self.custom_count = 0
      self.current_boxes = []
      self.reset_zoom()

      self.run_image_detection()
      self.log_message(f"已載入圖片：{os.path.basename(path)}")

  def run_image_detection(self):
    if self.last_frame is None:
      return

    custom_boxes = [box for box in self.current_boxes if box.get("is_custom")]

    results = self.predict_frame(self.last_frame)
    self.current_boxes = self.parse_yolo_boxes(results)
    self.current_boxes.extend(custom_boxes)

    self.sort_objects()
    self.render_canvas()
    self.update_listbox()

  def toggle_camera(self):
    if self.is_running:
      self.stop_camera()
    else:
      cam_idx = self.camera_var.get()
      if cam_idx == "":
        self.log_message("【錯誤】請先選取攝影機編號！")
        return

      self.cap = cv2.VideoCapture(int(cam_idx), cv2.CAP_DSHOW)
      if not self.cap.isOpened():
        self.cap = cv2.VideoCapture(int(cam_idx))

      if not self.cap.isOpened():
        self.log_message(f"【錯誤】無法開啟鏡頭 {cam_idx}")
        return

      self.is_running = True
      self.btn_repredict.config(state=tk.DISABLED)
      self.custom_count = 0
      self.current_boxes = []
      self.reset_zoom()
      self.btn_toggle_cam.config(
          text="停止攝影機", bg="#F44336", fg="white"
      )

      self.log_message(f"啟動攝影機 {cam_idx}，串流中...")
      threading.Thread(target=self.camera_stream_loop, daemon=True).start()

  def stop_camera(self):
    self.is_running = False
    if self.cap:
      self.cap.release()
      self.cap = None
    self.btn_toggle_cam.config(
        text="啟動攝影機", bg="#4CAF50", fg="white"
    )
    self.log_message("攝影機已停止。")

  def camera_stream_loop(self):
    while self.is_running and self.cap and self.cap.isOpened():
      ret, frame = self.cap.read()
      if not ret:
        time.sleep(0.03)
        continue

      self.last_frame = frame.copy()

      if not self.is_detecting:
        self.is_detecting = True
        custom_boxes = [
            box for box in self.current_boxes if box.get("is_custom")
        ]

        results = self.predict_frame(frame)
        new_boxes = self.parse_yolo_boxes(results)
        new_boxes.extend(custom_boxes)

        self.current_boxes = new_boxes
        self.is_detecting = False

      self.root.after(0, self.render_canvas)
      self.root.after(0, self.update_listbox)

      time.sleep(0.03)

  def predict_frame(self, frame):
    return self.model.predict(
        source=frame,
        conf=self.conf_slider.get(),
        iou=self.iou_slider.get(),
        imgsz=int(self.imgsz_var.get()),
        classes=self.get_selected_classes(),
        device=self.device_var.get(),
        verbose=False,
    )

  def parse_yolo_boxes(self, results):
    parsed = []
    boxes = results[0].boxes
    for i, box in enumerate(boxes):
      cls_id = int(box.cls[0])
      cls_name = self.model.names[cls_id]
      conf = float(box.conf[0])
      xyxy = box.xyxy[0].cpu().numpy().astype(int)

      w = xyxy[2] - xyxy[0]
      h = xyxy[3] - xyxy[1]
      parsed.append({
          "id": i + 1,
          "original_id": i + 1,
          "name": cls_name,
          "conf": conf,
          "box": xyxy,
          "width": w,
          "height": h,
          "area": w * h,
          "is_custom": False,
      })
    return parsed

  # --- 畫布繪製與更新 ---
  def render_canvas(self):
    if self.last_frame is None:
      return

    img = self.last_frame.copy()

    if self.selected_idx is not None:
      img = cv2.addWeighted(img, 0.4, np.zeros_like(img), 0.6, 0)

    for i, item in enumerate(self.current_boxes):
      x1, y1, x2, y2 = item["box"]
      is_custom = item["is_custom"]
      label = f"#{i+1} {item['name']}"

      if self.selected_idx is not None and i != self.selected_idx:
        cv2.rectangle(img, (x1, y1), (x2, y2), (100, 100, 100), 1)
      else:
        if self.selected_idx is not None and i == self.selected_idx:
          img[y1:y2, x1:x2] = self.last_frame[y1:y2, x1:x2]
          color = (0, 0, 255)
          thickness = 3
        else:
          color = (0, 165, 255) if is_custom else (0, 255, 0)
          thickness = 2

        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(
            img,
            label,
            (x1, max(20, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    if self.temp_draw_box is not None:
      tx1, ty1, tx2, ty2 = self.temp_draw_box
      cv2.rectangle(img, (tx1, ty1), (tx2, ty2), (0, 255, 255), 2)

    self.last_annotated_frame = img.copy()

    h, w = img.shape[:2]
    nw, nh = int(w * self.zoom_scale), int(h * self.zoom_scale)

    if nw > 0 and nh > 0:
      resized = cv2.resize(img, (nw, nh))
      rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
      pil_img = Image.fromarray(rgb_img)

      self.tk_img = ImageTk.PhotoImage(image=pil_img)

      self.canvas.delete("all")
      self.canvas.create_image(
          self.pan_x, self.pan_y, anchor=tk.NW, image=self.tk_img
      )

  def update_listbox(self):
    self.obj_listbox.delete(0, tk.END)
    for i, item in enumerate(self.current_boxes):
      item["id"] = i + 1
      tag = "⭐" if item["is_custom"] else ""
      conf_str = (
          "自訂區域"
          if item["is_custom"]
          else f"{item['conf']*100:2.0f}%"
      )
      display_str = (
          f"[{i+1:02d}] {tag}{item['name']:<8} | {conf_str} | "
          f"{item['width']}x{item['height']}px"
      )
      self.obj_listbox.insert(tk.END, display_str)

  # --- 右鍵手動劃框與座標轉換 ---
  def canvas_to_image_coords(self, cx, cy):
    if self.last_frame is None:
      return 0, 0
    ix = int((cx - self.pan_x) / self.zoom_scale)
    iy = int((cy - self.pan_y) / self.zoom_scale)
    h, w = self.last_frame.shape[:2]
    return max(0, min(ix, w)), max(0, min(iy, h))

  def on_draw_start(self, event):
    if self.last_frame is None:
      return
    self.draw_start_x, self.draw_start_y = self.canvas_to_image_coords(
        event.x, event.y
    )

  def on_draw_motion(self, event):
    if self.draw_start_x is None:
      return
    curr_x, curr_y = self.canvas_to_image_coords(event.x, event.y)
    self.temp_draw_box = (
        min(self.draw_start_x, curr_x),
        min(self.draw_start_y, curr_y),
        max(self.draw_start_x, curr_x),
        max(self.draw_start_y, curr_y),
    )
    self.render_canvas()

  def on_draw_end(self, event):
    if self.draw_start_x is None:
      return
    curr_x, curr_y = self.canvas_to_image_coords(event.x, event.y)
    x1, y1 = min(self.draw_start_x, curr_x), min(self.draw_start_y, curr_y)
    x2, y2 = max(self.draw_start_x, curr_x), max(self.draw_start_y, curr_y)
    w, h = x2 - x1, y2 - y1

    self.temp_draw_box = None
    if w > 5 and h > 5:
      self.custom_count += 1
      custom_item = {
          "id": len(self.current_boxes) + 1,
          "original_id": 999 + self.custom_count,
          "name": f"手動區域_{self.custom_count}",
          "conf": 1.0,
          "box": np.array([x1, y1, x2, y2]),
          "width": w,
          "height": h,
          "area": w * h,
          "is_custom": True,
      }
      self.current_boxes.append(custom_item)
      self.log_message(f"[手動匡列] 已新增自訂框：手動區域_{self.custom_count}")

    self.draw_start_x = None
    self.draw_start_y = None
    self.sort_objects()
    self.render_canvas()
    self.update_listbox()

  # --- 其他互動與畫布控制 ---
  def on_list_select(self, event):
    selection = self.obj_listbox.curselection()
    if selection:
      idx = selection[0]
      self.selected_idx = None if self.selected_idx == idx else idx
      self.render_canvas()

  def reset_zoom(self):
    self.zoom_scale = 1.0
    self.pan_x = 0
    self.pan_y = 0

  def on_zoom(self, event):
    if self.last_frame is None:
      return
    factor = 1.1 if event.delta > 0 else 0.9
    if 0.1 <= self.zoom_scale * factor <= 5.0:
      self.zoom_scale *= factor
      self.render_canvas()

  def on_drag_start(self, event):
    self.start_x, self.start_y = event.x, event.y

  def on_drag_motion(self, event):
    if self.last_frame is None:
      return
    self.pan_x += event.x - self.start_x
    self.pan_y += event.y - self.start_y
    self.start_x, self.start_y = event.x, event.y
    self.render_canvas()

  def save_current_data(self):
    if self.last_frame is None or self.last_annotated_frame is None:
      self.log_message("【警告】無可儲存的數據！")
      return

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base = f"saved_{timestamp}"

    cv2.imwrite(
        os.path.join(self.output_dir, f"{base}_raw.jpg"), self.last_frame
    )
    cv2.imwrite(
        os.path.join(self.output_dir, f"{base}_annotated.jpg"),
        self.last_annotated_frame,
    )

    txt_path = os.path.join(self.output_dir, f"{base}_info.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
      f.write(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
      f.write(f"物件數: {len(self.current_boxes)}\n" + "=" * 50 + "\n")
      for i, item in enumerate(self.current_boxes):
        x1, y1, x2, y2 = item["box"]
        f.write(
            f"[{i+1:02d}] {item['name']:<12} | Box:({x1},{y1},{x2},{y2}) |"
            f" Size:{item['width']}x{item['height']}px\n"
        )

    self.log_message(f"[成功] 檔案已儲存至 -> {self.output_dir}/{base}*")

  def on_closing(self):
    self.is_running = False
    if self.cap:
      self.cap.release()
    self.root.destroy()


if __name__ == "__main__":
  root = tk.Tk()
  app = YoloIntegratedApp(root)
  root.mainloop()