
https://github.com/user-attachments/assets/c9656ed6-12d6-4952-b09d-b48968ac1423

# 狹縫繞射與干涉 (Slit Diffraction & Interference) 模擬

這是一個結合 **Streamlit** Web 互動介面與 **Manim** 數學動畫引擎的物理模擬器。使用者可以透過圖形化介面動態調整光學參數（波長、狹縫寬度等），並即時渲染出高畫質的強度分佈曲線與光斑動畫。

---

## 專案簡介

- **互動式 Web 介面**：基於 Streamlit 構建，支援調整參數。
- **高畫質物理動畫**：利用 Manim 引擎精準繪製繞射與干涉強度分佈曲線。
- **漸進式演進與自動變色模式**：啟用漸進模式時，動畫會從單狹縫 ($N=1$) 逐步演進至設定的目標狹縫數 ($N$)，並自動更換顏色。

---

## 物理公式

本模擬器結合了單狹縫繞射 (Diffraction) 與多狹縫干涉 (Interference) 的物理公式：

1. **單狹縫繞射因子 ($\beta$)**：
   $$\beta = \frac{\pi b \sin\theta}{\lambda}$$
   其中 $b$ 為狹縫寬度，$\lambda$ 為入射光波長。

2. **多狹縫干涉因子 ($\gamma$)**：
   $$\gamma = \frac{\pi d \sin\theta}{\lambda}$$
   其中 $d$ 為狹縫間距。

3. **總相對光強 $I(\theta)$**：
   - **單狹縫 ($N=1$)**：
     $$I(\theta) = I_0 \left( \frac{\sin \beta}{\beta} \right)^2$$
   - **多狹縫 ($N > 1$)**：
     $$I(\theta) = I_0 \left( \frac{\sin \beta}{\beta} \right)^2 \left( \frac{\sin N\gamma}{\sin \gamma} \right)^2$$

---

## 環境需求與安裝步驟

### 1. 安裝系統依賴 (Manim 所需)
Manim 引擎依賴系統的 `ffmpeg` 進行影片合成。請先確保已安裝：

- **Windows**: 可透過 `winget install ffmpeg` 或 `choco install ffmpeg` 安裝。
- **Mac**: `brew install ffmpeg`
- **Linux (Ubuntu)**: `sudo apt install ffmpeg`

### 2. 安裝 Python 相關套件
建議使用 Python 3.9+ 虛擬環境，並安裝以下套件：

```bash
pip install manim numpy streamlit
```

### 3.執行方式
下載或複製專案檔：
確保 multiple_slit_interference.py 在您的專案目錄中。

啟動 Streamlit 服務：
在專案目錄中 Terminal 輸入以下指令：
streamlit run multiple_slit_interference.py

瀏覽器會自動開啟控制面板（預設為 http://localhost:8501）。
操作模擬器：在左側側邊欄調整參數。
- 點擊 ▶️ 開始渲染物理模擬影片 按鈕，等待系統生成動畫並播放或下載。
