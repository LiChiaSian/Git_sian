

https://github.com/user-attachments/assets/8db9d934-1ab9-48ba-8359-38938196ea01


# 數學公式軌跡模擬器 (Trajectory Simulator)

這是一個結合 **Streamlit** 互動式 Web 介面與 **Manim** 數學動畫引擎的動態軌跡模擬器。可透過控制面板調整極座標與參數，並進行動態公式解析與即時影片渲染。

---

## 專案介紹

- **互動介面**：提供控制各項參數。
- **經典範例曲線**：
  - 玫瑰線 (Rose Curve)
  - 利薩茹圖形 (Lissajous Curve)
  - 蝴蝶曲線 (Butterfly Curve)
  - 心形線 (Cardioid)
  - 星形線 (Astroid)
- **自訂數學公式**：輸入自訂 $x(t)$ 與 $y(t)$ 參數式，即時解析並轉換為可渲染的數學動畫。
- **視覺個人化**：可自訂軌跡顏色、動畫繪製時間等。

---

## 經典軌跡數學公式

1. **玫瑰線 (Rose Curve)**
   $$r = a \cdot \cos(b\theta)$$

2. **李薩茹圖形 (Lissajous Curve)**
   $$x = \sin(at), \quad y = \sin(bt)$$

3. **心形線 (Cardioid)**
   $$r = a \cdot (1 - \cos\theta)$$

4. **星形線 (Astroid)**
   $$x = a\cos^3(t), \quad y = a\sin^3(t)$$

5. **蝴蝶曲線 (Butterfly Curve)**
   $$r = e^{\cos\theta} - 2\cos(4\theta) + \sin^5\left(\frac{\theta}{12}\right)$$

---

## 🛠️ 環境需求與安裝

### 1. 安裝系統依賴 (FFmpeg)
Manim 引擎依賴系統的 `ffmpeg` 進行影片合成。請先確保已安裝：

- **Windows**: `winget install ffmpeg` 或 `choco install ffmpeg`
- **Mac**: `brew install ffmpeg`
- **Linux (Ubuntu)**: `sudo apt install ffmpeg`

### 2. 安裝 Python 相關套件

建議使用 Python 3.9+ 虛擬環境，並執行以下指令安裝套件：

```bash
pip install manim numpy streamlit sympy
