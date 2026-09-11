# 其他範例 (Examples)

本資料夾包含使用 **OpenCV** 、**Python** 實作的基礎範例程式碼。

---

## 🛠️ 範例程式說明

### 1. 🔷 幾何圖形輪廓分析 (`Shape Analysis.py`)
- **功能**：讀取圖像並進行灰階化、高斯模糊與二值化前處理，自動標記圖片中的各個物體輪廓並計算其中心點 (Centroid)。
- **特點**：支援含中文路徑的圖片讀取 (`np.fromfile` & `cv2.imdecode`)。
- **必要檔案**：執行時同資料夾下需包含 `shapes.jpg` 圖像檔。

### 2. 👤 即時人臉與眼睛偵測 (`face_detection.py`)
- **功能**：開啟 WebCam 攝影機（支援手機 DroidCam 或筆電鏡頭），運用 **Haar Cascade** 分類器即時偵測人臉與眼睛區域。
- **特點**：若本機缺少模型檔 (`.xml`)，程式將自動從 OpenCV 官方 GitHub 下載。
- **操作方式**：執行後按下鍵盤 `q` 鍵即可關閉攝影機視窗。

---

## 📦 環境需求與安裝

請確保已安裝以下 Python 基礎套件：

```bash
pip install opencv-python numpy
