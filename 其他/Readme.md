# 🔬 狹縫繞射與干涉 (Slit Diffraction & Interference) 模擬器

這是一個結合 **Streamlit** Web 互動介面與 **Manim** 數學動畫引擎的物理模擬器。使用者可以透過圖形化介面動態調整光學參數（波長、狹縫寬度、狹縫間距與狹縫數量），並即時渲染出高畫質的強度分佈曲線與屏上條紋光斑動畫。

---

## 🌟 專案亮點

- **🎛️ 互動式 Web 介面**：基於 Streamlit 構建，支援滑桿調整各種光學參數。
- **🎬 高畫質物理動畫**：利用 Manim 引擎精準繪製繞射與干涉強度分佈曲線 ($I/I_0$)。
- **🌈 漸進式演進與自動變色模式**：啟用漸進模式時，動畫會從單狹縫 ($N=1$) 逐步演進至設定的目標狹縫數 ($N$)，每次增加狹縫時自動更換顏色。
- **⚡ 快取機制 (MD5 Hash)**：自動記錄參數組合，若重複渲染相同參數將自動載入快取影片，省去等待時間[cite: 1]。

---

## 📐 物理原理與公式

本模擬器結合了單狹縫繞射 (Diffraction) 與多狹縫干涉 (Interference) 的物理公式[cite: 1]：

1. **單狹縫繞射因子 ($\beta$)**[cite: 1]：
   $$\beta = \frac{\pi b \sin\theta}{\lambda}$$
   其中 $b$ 為狹縫寬度，$\lambda$ 為入射光波長[cite: 1]。

2. **多狹縫干涉因子 ($\gamma$)**[cite: 1]：
   $$\gamma = \frac{\pi d \sin\theta}{\lambda}$$
   其中 $d$ 為狹縫間距[cite: 1]。

3. **總相對光強 $I(\theta)$**[cite: 1]：
   - **單狹縫 ($N=1$)**[cite: 1]：
     $$I(\theta) = I_0 \left( \frac{\sin \beta}{\beta} \right)^2$$
   - **多狹縫 ($N > 1$)**[cite: 1]：
     $$I(\theta) = I_0 \left( \frac{\sin \beta}{\beta} \right)^2 \left( \frac{\sin N\gamma}{\sin \gamma} \right)^2$$

---

## 🛠️ 環境需求與安裝步驟

### 1. 安裝系統依賴 (Manim 所需)
Manim 引擎依賴系統的 `ffmpeg` 進行影片合成[cite: 1]。請先確保已安裝：

- **Windows**: 可透過 `winget install ffmpeg` 或 `choco install ffmpeg` 安裝[cite: 1]。
- **Mac**: `brew install ffmpeg`[cite: 1]
- **Linux (Ubuntu)**: `sudo apt install ffmpeg`[cite: 1]

### 2. 安裝 Python 相關套件
建議使用 Python 3.9+ 虛擬環境[cite: 1]，並安裝以下套件：

```bash
pip install manim numpy streamlit