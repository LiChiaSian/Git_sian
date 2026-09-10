import hashlib
import os
import subprocess
from manim import *
import numpy as np
import streamlit as st

# 可選顏色清單 (供自動切換使用)
COLOR_PALETTE = [
    ("藍色 (Blue)", BLUE),
    ("紅色 (Red)", RED),
    ("綠色 (Green)", GREEN),
    ("黃色 (Yellow)", YELLOW),
    ("橙色 (Orange)", ORANGE),
    ("紫色 (Purple)", PURPLE),
    ("青色 (Teal)", TEAL),
]

COLOR_MAP = dict(COLOR_PALETTE)


# ==========================================
# 1. Manim 多狹縫演進動畫場景 (分段重置 + 動態變色)
# ==========================================
class DynamicSlitDiffraction(Scene):

    def construct(self):
        # 讀取環境變數
        wavelength_nm = float(os.getenv("WAVE_LAMBDA", 500))
        slit_width_um = float(os.getenv("WAVE_SLIT", 2.0))
        target_num_slits = int(os.getenv("WAVE_NUM_SLITS", 2))
        slit_distance_um = float(os.getenv("WAVE_SLIT_D", 10.0))
        start_color_name = os.getenv("WAVE_COLOR", "藍色 (Blue)")
        font_size_val = int(os.getenv("WAVE_FONT_SIZE", 18))
        is_continuous = os.getenv("WAVE_CONTINUOUS", "False") == "True"

        # 找出起始顏色在調色盤中的索引位置
        palette_colors = [c[1] for c in COLOR_PALETTE]
        start_color = COLOR_MAP.get(start_color_name, BLUE)
        try:
            start_color_idx = palette_colors.index(start_color)
        except ValueError:
            start_color_idx = 0

        # 物理單位換算
        wavelength = wavelength_nm / 500.0
        b = slit_width_um / 2.0
        d = slit_distance_um / 2.0

        # 計算光強公式
        def calc_intensity(x, num_slits):
            beta = (np.pi * b * x) / wavelength
            diffraction = 1.0 if abs(beta) < 1e-5 else (np.sin(beta) / beta) ** 2

            if num_slits == 1:
                return diffraction

            gamma = (np.pi * d * x) / wavelength
            if abs(np.sin(gamma)) < 1e-5:
                interference = num_slits**2
            else:
                interference = (np.sin(num_slits * gamma) / np.sin(gamma)) ** 2

            total_intensity = (diffraction * interference) / (num_slits**2)
            return min(total_intensity, 1.0)

        # 固定背景：坐標軸與屏上外框
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[0, 1.2, 0.5],
            x_length=10,
            y_length=3.5,
            axis_config={"color": GREY},
        ).to_edge(UP, buff=0.8)

        x_label = Text("sin(θ)", font_size=font_size_val).next_to(
            axes.x_axis, RIGHT, buff=0.2
        )
        y_label = Text("I / I₀", font_size=font_size_val).next_to(
            axes.y_axis, UP, buff=0.2
        )

        stripe_rect = Rectangle(
            width=10, height=0.5, stroke_color=WHITE, stroke_width=1
        ).next_to(axes, DOWN, buff=0.35)

        stripe_label = Text(
            "Screen Pattern (屏上條紋光斑)",
            font_size=max(12, font_size_val - 2),
            color=LIGHT_GREY,
        ).next_to(stripe_rect, DOWN, buff=0.15)

        # 繪製背景框架
        self.play(
            Create(axes, run_time=1.0),
            Write(x_label, run_time=0.6),
            Write(y_label, run_time=0.6),
            Create(stripe_rect, run_time=0.8),
            Write(stripe_label, run_time=0.6),
        )
        self.wait(0.5)

        # 決定播放的 N 值列表
        slit_sequence = (
            list(range(1, target_num_slits + 1))
            if is_continuous
            else [target_num_slits]
        )

        # 進行分段展示、自動變色與還原
        for idx, current_n in enumerate(slit_sequence):
            # 依據 N 值的遞增切換至下一個顏色
            current_color_idx = (start_color_idx + idx) % len(palette_colors)
            current_color = palette_colors[current_color_idx]

            # 1. 標題與參數說明
            title_str = (
                f"Single Slit Diffraction (N = 1)"
                if current_n == 1
                else f"Multi-Slit Interference (N = {current_n})"
            )
            formula_title = Text(
                title_str, font_size=font_size_val, color=YELLOW
            ).to_corner(UL, buff=0.25)

            param_subtitle = Text(
                f"λ = {wavelength_nm:.0f} nm | b = {slit_width_um:.1f} μm | d = {slit_distance_um:.1f} μm",
                font_size=max(12, font_size_val - 2),
                color=LIGHT_GREY,
            ).next_to(formula_title, DOWN, buff=0.1, aligned_edge=LEFT)

            self.play(
                Write(formula_title, run_time=0.8),
                Write(param_subtitle, run_time=0.6),
            )

            # 2. 繪製當前 N 值與對應顏色的曲線
            curve = axes.plot(
                lambda x: calc_intensity(x, current_n),
                color=current_color,
                x_range=[-4, 4],
                use_smoothing=False,
            )
            self.play(Create(curve, run_time=2.0))

            # 3. 建立屏上光斑條紋 (套用當前顏色)
            x_vals = np.linspace(-4, 4, 200)
            dx = 10.0 / 200
            stripe_group = VGroup()

            for x in x_vals:
                intensity = calc_intensity(x, current_n)
                rect = Rectangle(
                    width=dx + 0.01,
                    height=0.48,
                    fill_color=current_color,
                    fill_opacity=intensity,
                    stroke_width=0,
                )
                rect.move_to(
                    stripe_rect.get_center() + np.array([x * (10.0 / 8.0), 0, 0])
                )
                stripe_group.add(rect)

            self.play(FadeIn(stripe_group, run_time=1.0))

            # 4. 停頓展示
            self.wait(2.0)

            # 5. 若後面還有下一個 N 值，清除當前圖層並準備進入下一顏色
            if idx < len(slit_sequence) - 1:
                self.play(
                    Uncreate(curve, run_time=1.0),
                    FadeOut(stripe_group, run_time=0.8),
                    Unwrite(formula_title, run_time=0.5),
                    Unwrite(param_subtitle, run_time=0.5),
                )
                self.wait(0.8)


# ==========================================
# 2. Streamlit GUI 介面與控制面板
# ==========================================
st.set_page_config(page_title="狹縫繞射/干涉模擬器", layout="centered")
st.title("🔬 狹縫繞射與干涉 (Slit Diffraction & Interference) 模擬器")

# --- 側邊欄控制面板 ---
st.sidebar.header("🎛️ 光學參數控制面板")

is_continuous = st.sidebar.checkbox(
    "🎬 啟用漸進播放模式 (N+1 時自動切換下一個顏色)",
    value=True,
)

num_slits = st.sidebar.slider("目標狹縫數量 N", 1, 10, 3, 1)
wavelength = st.sidebar.slider("入射光波長 λ (nm)", 380.0, 750.0, 500.0, 10.0)
slit_width = st.sidebar.slider("狹縫寬度 b (μm)", 0.5, 10.0, 2.0, 0.1)

if num_slits > 1:
    slit_distance = st.sidebar.slider("狹縫間距 d (μm)", 1.0, 20.0, 8.0, 0.5)
else:
    slit_distance = 10.0

st.sidebar.markdown("---")
st.sidebar.subheader("🎨 視覺樣式設定")

color_choice = st.sidebar.selectbox(
    "選擇起始顏色 (漸進模式下將依次輪替)",
    options=[c[0] for c in COLOR_PALETTE],
    index=0,
)

font_size = st.sidebar.slider("影片文字大小 (pt)", 14, 28, 18, 1)

st.sidebar.markdown("---")
st.sidebar.subheader("📐 即時帶入變數公式")

if is_continuous:
    st.info(f"💡 漸進模式：將從 $N=1$ 展示至 $N={num_slits}$，每次 $N+1$ 都會自動更換線條與光斑顏色。")

if num_slits == 1:
    st.sidebar.latex(r"I(\theta) = I_0 \left( \frac{\sin \beta}{\beta} \right)^2")
else:
    st.sidebar.latex(
        r"I(\theta) = I_0 \left( \frac{\sin \beta}{\beta} \right)^2 \left( \frac{\sin N\gamma}{\sin \gamma} \right)^2"
    )

# --- 主畫面執行按鈕 ---
if st.button("▶️ 開始渲染物理模擬影片", type="primary"):
    param_hash = hashlib.md5(
        f"Slit_v3_{num_slits}_{wavelength}_{slit_width}_{slit_distance}_{color_choice}_{font_size}_{is_continuous}".encode()
    ).hexdigest()[:8]
    output_dir = "./media/videos/multiple_slit_interference/480p15"
    target_video_path = f"{output_dir}/Diffraction_{param_hash}.mp4"
    default_video_path = f"{output_dir}/DynamicSlitDiffraction.mp4"

    if os.path.exists(target_video_path):
        st.success("⚡ 載入快取模擬影片成功！")
        st.video(target_video_path)
    else:
        with st.spinner("🚀 Manim 正在計算並渲染漸進變色動畫影片..."):
            env = os.environ.copy()
            env["WAVE_NUM_SLITS"] = str(num_slits)
            env["WAVE_LAMBDA"] = str(wavelength)
            env["WAVE_SLIT"] = str(slit_width)
            env["WAVE_SLIT_D"] = str(slit_distance)
            env["WAVE_COLOR"] = str(color_choice)
            env["WAVE_FONT_SIZE"] = str(font_size)
            env["WAVE_CONTINUOUS"] = str(is_continuous)

            current_script = os.path.basename(__file__)

            cmd = [
                "python",
                "-m",
                "manim",
                "-ql",
                "--fps",
                "15",
                "--media_dir",
                "./media",
                "--disable_caching",
                current_script,
                "DynamicSlitDiffraction",
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if os.path.exists(default_video_path):
                os.rename(default_video_path, target_video_path)
                st.success("✨ 渲染完成！")
                st.video(target_video_path)
            else:
                st.error("影片渲染失敗！詳細錯誤訊息如下：")
                st.code(result.stderr if result.stderr else result.stdout)