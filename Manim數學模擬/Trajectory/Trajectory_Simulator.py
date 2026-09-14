import hashlib
import os
import subprocess
from manim import *
import numpy as np
import streamlit as st
import sympy as sp

# 顏色選單
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
# 1. Manim 數學軌跡繪製場景
# ==========================================
class DynamicTrajectoryScene(Scene):

  def construct(self):
    curve_type = os.getenv("TRAJ_TYPE", "Rose Curve (玫瑰線)")
    param_a = float(os.getenv("TRAJ_PARAM_A", 2.5))
    param_b = float(os.getenv("TRAJ_PARAM_B", 3.0))
    custom_x_str = os.getenv("TRAJ_CUSTOM_X", "a * cos(b * t)")
    custom_y_str = os.getenv("TRAJ_CUSTOM_Y", "a * sin(t)")
    color_name = os.getenv("TRAJ_COLOR", "紅色 (Red)")
    font_size_val = int(os.getenv("TRAJ_FONT_SIZE", 24))
    draw_time = float(os.getenv("TRAJ_DRAW_TIME", 4.0))

    curve_color = COLOR_MAP.get(color_name, RED)

    axes = Axes(
        x_range=[-4, 4, 1],
        y_range=[-4, 4, 1],
        x_length=6.5,
        y_length=6.5,
        axis_config={"color": GREY},
    ).to_edge(RIGHT, buff=0.8)

    str_a = f"{int(param_a)}" if param_a.is_integer() else f"{param_a:.1f}"
    str_b = f"{int(param_b)}" if param_b.is_integer() else f"{param_b:.1f}"

    # 軌跡公式解析
    if "Rose Curve" in curve_type:
      b_val = int(param_b) if param_b.is_integer() else param_b
      t_max = 2 * np.pi if int(b_val) % 2 == 1 else 4 * np.pi
      curve_func = lambda t: axes.c2p(
          param_a * np.cos(b_val * t) * np.cos(t),
          param_a * np.cos(b_val * t) * np.sin(t),
      )
      latex_formula = rf"r = {str_a} \cdot \cos({str_b} \theta)"

    elif "Butterfly Curve" in curve_type:
      t_max = 4 * np.pi
      curve_func = lambda t: axes.c2p(
          np.sin(t)
          * (np.exp(np.cos(t)) - 2 * np.cos(4 * t) - np.sin(t / 12) ** 5),
          np.cos(t)
          * (np.exp(np.cos(t)) - 2 * np.cos(4 * t) - np.sin(t / 12) ** 5),
      )
      latex_formula = (
          r"r = e^{\cos\theta} - 2\cos(4\theta) +"
          r" \sin^5\left(\frac{\theta}{12}\right)"
      )

    elif "Cardioid" in curve_type:
      t_max = 2 * np.pi
      curve_func = lambda t: axes.c2p(
          param_a * (1 - np.cos(t)) * np.cos(t),
          param_a * (1 - np.cos(t)) * np.sin(t),
      )
      latex_formula = rf"r = {str_a} \cdot (1 - \cos\theta)"

    elif "Astroid" in curve_type:
      t_max = 2 * np.pi
      curve_func = lambda t: axes.c2p(
          param_a * (np.cos(t) ** 3),
          param_a * (np.sin(t) ** 3),
      )
      latex_formula = (
          rf"x = {str_a}\cos^3(t), \quad y = {str_a}\sin^3(t)"
      )

    elif "Custom Formula" in curve_type:
      t_max = 2 * np.pi
      t, a, b = sp.symbols("t a b")

      expr_x = sp.sympify(custom_x_str)
      expr_y = sp.sympify(custom_y_str)

      func_x = sp.lambdify((t, a, b), expr_x, modules=["numpy"])
      func_y = sp.lambdify((t, a, b), expr_y, modules=["numpy"])

      curve_func = lambda t_val: axes.c2p(
          func_x(t_val, param_a, param_b),
          func_y(t_val, param_a, param_b),
      )

      latex_x = sp.latex(expr_x.subs({a: param_a, b: param_b}))
      latex_y = sp.latex(expr_y.subs({a: param_a, b: param_b}))
      latex_formula = f"x(t) = {latex_x}, \\quad y(t) = {latex_y}"

    else:  # Lissajous Curve
      t_max = 2 * np.pi
      curve_func = lambda t: axes.c2p(
          2.5 * np.sin(param_a * t),
          2.5 * np.sin(param_b * t),
      )
      latex_formula = (
          rf"x = \sin({str_a}t), \quad y = \sin({str_b}t)"
      )

    # 繪製畫面
    title = Text(
        "軌跡模擬器 (Trajectory Simulator)",
        font_size=font_size_val + 2,
        color=YELLOW,
    ).to_corner(UL, buff=0.5)
    curve_name_text = Text(
        f"類型: {curve_type}", font_size=font_size_val, color=WHITE
    ).next_to(title, DOWN, buff=0.2, aligned_edge=LEFT)

    
    formula_math = MathTex(
        latex_formula, font_size=font_size_val + 6, color=curve_color
    ).next_to(curve_name_text, DOWN, buff=0.3, aligned_edge=LEFT)

    self.play(
        Create(axes, run_time=1.0),
        Write(title, run_time=0.6),
        Write(curve_name_text, run_time=0.6),
        Write(formula_math, run_time=0.8),
    )

    t_param = ValueTracker(0)

    parametric_curve = always_redraw(
        lambda: ParametricFunction(
            curve_func,
            t_range=[0, max(0.001, t_param.get_value())],
            color=curve_color,
            stroke_width=3,
        )
    )

    moving_dot = always_redraw(
        lambda: Dot(
            point=curve_func(t_param.get_value()), color=WHITE, radius=0.08
        )
    )

    self.add(parametric_curve, moving_dot)

    self.play(
        t_param.animate.set_value(t_max),
        run_time=draw_time,
        rate_func=linear,
    )

    self.wait(1.5)


# ==========================================
# 2. Streamlit GUI 介面與控制面板
# ==========================================
st.set_page_config(
    page_title="軌跡模擬器 Trajectory Simulator", layout="wide"
)

st.header("📐 軌跡模擬器 (Trajectory Simulator)")

# --- 側邊欄控制面板 ---
st.sidebar.header("🎛️ 軌跡與公式參數")

curve_type = st.sidebar.selectbox(
    "選擇圖案軌跡種類",
    options=[
        "Rose Curve (玫瑰線)",
        "Lissajous Curve (李薩茹圖形)",
        "Butterfly Curve (蝴蝶曲線)",
        "Cardioid (心形線)",
        "Astroid (星形線)",
        "Custom Formula (自訂公式)",
    ],
    index=0,
)

param_a = st.sidebar.slider("參數 A (振幅 / 頻率)", 0.5, 5.0, 2.5, 0.1)
param_b = st.sidebar.slider("參數 B (花瓣數 / 頻率比)", 1.0, 10.0, 3.0, 1.0)

# 自訂公式輸入區域
custom_x = "a * cos(b * t)"
custom_y = "a * sin(t)"

if "Custom Formula" in curve_type:
  st.sidebar.markdown("---")
  st.sidebar.subheader("✍️ 輸入自訂參數式 (可使用 a, b, t)")
  custom_x = st.sidebar.text_input(
      "x(t) =", value="a * cos(b * t)", help="例如: a * cos(b * t) 或 sin(t)**3"
  )
  custom_y = st.sidebar.text_input(
      "y(t) =", value="a * sin(t)", help="例如: a * sin(b * t) 或 cos(t)"
  )

st.sidebar.markdown("---")
st.sidebar.subheader("🎨 視覺與渲染設定")

color_choice = st.sidebar.selectbox(
    "軌跡顏色", options=[c[0] for c in COLOR_PALETTE], index=1
)
draw_time = st.sidebar.slider("軌跡繪製時長 (秒)", 2.0, 10.0, 4.0, 0.5)

# 預設影片文字大小為 24 pt
font_size = st.sidebar.slider("影片文字大小 (pt)", 14, 28, 24, 1)

btn_render = st.sidebar.button("▶️ 開始渲染軌跡動畫", type="primary")

# --- 主介面配置：分割為 上區塊 (影片) 與 下區塊 (說明) ---
video_container = st.container()
st.markdown("---")
info_container = st.container()

param_hash = hashlib.md5(
    f"Traj_v6_{curve_type}_{param_a}_{param_b}_{custom_x}_{custom_y}_{color_choice}_{draw_time}_{font_size}".encode()
).hexdigest()[:8]
output_dir = "./media/videos/Trajectory_Simulator/480p15"
target_video_path = f"{output_dir}/Trajectory_{param_hash}.mp4"
default_video_path = f"{output_dir}/DynamicTrajectoryScene.mp4"

# 1. 上方區塊：影片展示
with video_container:
  st.subheader("🎬 軌跡模擬影片區")
  if btn_render:
    if os.path.exists(target_video_path):
      st.success("⚡ 載入快取模擬影片成功！")
      st.video(target_video_path)
    else:
      with st.spinner("🚀 Manim 正在根據數學公式計算並渲染動態軌跡..."):
        env = os.environ.copy()
        env["TRAJ_TYPE"] = str(curve_type)
        env["TRAJ_PARAM_A"] = str(param_a)
        env["TRAJ_PARAM_B"] = str(param_b)
        env["TRAJ_CUSTOM_X"] = str(custom_x)
        env["TRAJ_CUSTOM_Y"] = str(custom_y)
        env["TRAJ_COLOR"] = str(color_choice)
        env["TRAJ_FONT_SIZE"] = str(font_size)
        env["TRAJ_DRAW_TIME"] = str(draw_time)

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
            "DynamicTrajectoryScene",
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if os.path.exists(default_video_path):
          os.rename(default_video_path, target_video_path)
          st.success("✨ 軌跡渲染完成！")
          st.video(target_video_path)
        else:
          st.error("影片渲染失敗！請檢查輸入的公式是否有誤。詳細訊息：")
          st.code(result.stderr if result.stderr else result.stdout)
  else:
    if os.path.exists(target_video_path):
      st.video(target_video_path)
    else:
      st.info("💡 請點擊左側邊欄的『▶️ 開始渲染軌跡動畫』按鈕產生模擬影片。")

# 2. 下方區塊：公式與參數說明
with info_container:
  st.subheader("📖 當前軌跡方程式與參數對應說明")

  str_a = f"{int(param_a)}" if param_a.is_integer() else f"{param_a:.1f}"
  str_b = f"{int(param_b)}" if param_b.is_integer() else f"{param_b:.1f}"

  if "Rose" in curve_type:
    b_val = int(param_b) if param_b.is_integer() else param_b
    t_range_str = (
        r"0 \to 2\pi" if int(b_val) % 2 == 1 else r"0 \to 4\pi"
    )
    t_desc = (
        "因花瓣係數為奇數，旋轉 1 圈 ($2\\pi$) 即可完整閉合"
        if int(b_val) % 2 == 1
        else "因花瓣係數為偶數，需要旋轉 2 圈 ($4\\pi$) 才能繪製完全部 $2b$ 個花瓣"
    )

    st.latex(rf"r = {str_a} \cdot \cos({str_b}\theta)")
    st.markdown(f"""
        * **公式類型**：玫瑰線 (Rose Curve)
        * **參數 A (振幅)**：對應公式中的 $a = {str_a}$，控制花瓣延伸的最大半徑。
        * **參數 B (花瓣數)**：對應公式中的 $b = {str_b}$。
            * 當 $b$ 為奇數時，圖形擁有 $b$ 個花瓣。
            * 當 $b$ 為偶數時，圖形擁有 $2b$ 個花瓣。
        * **$\\theta$ 繪製範圍**：$\\theta \\in [{t_range_str}]$（{t_desc}）。
        """)

  elif "Lissajous" in curve_type:
    st.latex(rf"x = \sin({str_a}t), \quad y = \sin({str_b}t)")
    st.markdown(f"""
        * **公式類型**：李薩茹圖形 (Lissajous Curve)
        * **參數 A (X 軸頻率)**：對應公式中的 $a = {str_a}$，控制 X 軸方向的簡諧振動頻率。
        * **參數 B (Y 軸頻率)**：對應公式中的 $b = {str_b}$，控制 Y 軸方向的簡諧振動頻率。
        * **幾何意義**：兩軸頻率比 $a : b$ 決定了曲線的封閉形狀與交點數量。
        * **$t$ 繪製範圍**：$t \\in [0, 2\\pi]$（簡諧波形的基本週期範圍）。
        """)

  elif "Cardioid" in curve_type:
    st.latex(rf"r = {str_a} \cdot (1 - \cos\theta)")
    st.markdown(f"""
        * **公式類型**：心形線 (Cardioid)
        * **參數 A (放縮尺度)**：對應公式中的 $a = {str_a}$，決定心形圖形放縮的大小。
        * **參數 B (無影響)**：心形線為固定幾何特徵曲線，不依賴參數 B 改變形狀。
        * **$\\theta$ 繪製範圍**：$\\theta \\in [0, 2\\pi]$（繞行原點 1 圈 $360^\\circ$ 即可繪製完整心形軌跡）。
        """)

  elif "Astroid" in curve_type:
    st.latex(rf"x = {str_a}\cos^3(t), \quad y = {str_a}\sin^3(t)")
    st.markdown(f"""
        * **公式類型**：星形線 (Astroid)
        * **參數 A (頂點距離)**：對應公式中的 $a = {str_a}$，決定星形四個尖點到原點的距離。
        * **參數 B (無影響)**：標準星形線只有 4 個尖點，幾何特徵固定。
        * **$t$ 繪製範圍**：$t \\in [0, 2\\pi]$（參數 $t$ 走完一圈即可通過四個象限的頂點並閉合）。
        """)

  elif "Butterfly" in curve_type:
    st.latex(
        r"r = e^{\cos\theta} - 2\cos(4\theta) +"
        r" \sin^5\left(\frac{\theta}{12}\right)"
    )
    st.markdown("""
        * **公式類型**：蝴蝶曲線 (Butterfly Curve)
        * **參數 A / B (無影響)**：經典蝴蝶曲線由 Fay 固定的超越函數組成，形狀由自然常數與三角函數固有頻率決定。
        * **$\\theta$ 繪製範圍**：$\\theta \\in [0, 4\\pi]$（因包含高次與分頻三角函數，需繞行 2 圈以展現豐富的翅膀輪廓）。
        """)

  elif "Custom Formula" in curve_type:
    try:
      t_s, a_s, b_s = sp.symbols("t a b")
      ex = sp.sympify(custom_x).subs({a_s: param_a, b_s: param_b})
      ey = sp.sympify(custom_y).subs({a_s: param_a, b_s: param_b})
      st.latex(rf"x(t) = {sp.latex(ex)}, \quad y(t) = {sp.latex(ey)}")
      st.markdown(f"""
            * **公式類型**：自訂參數式 (Custom Formula)
            * **參數 A**：即時帶入變數 $a = {str_a}$。
            * **參數 B**：即時帶入變數 $b = {str_b}$。
            * **自訂公式**：$x(t) = \\text{{{custom_x}}}$, $\\quad y(t) = \\text{{{custom_y}}}$
            * **$t$ 繪製範圍**：$t \\in [0, 2\\pi]$（預設涵蓋一個完整的二維三角週期）。
            """)
    except Exception as e:
      st.error("自訂公式語法解析錯誤！")