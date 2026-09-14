import cv2
import numpy as np
import os

# 1. 取得動態資料夾路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'shapes.jpg')

def imread_unicode(file_path):
    if not os.path.exists(file_path):
        return None
    img_data = np.fromfile(file_path, dtype=np.uint8)
    return cv2.imdecode(img_data, cv2.IMREAD_COLOR)

# 2. 讀取圖片
src = imread_unicode(image_path)

if src is None:
    print(f"[錯誤] 無法讀取圖片！請確認 '{image_path}' 是否存在。")
    exit()

# 3. 前處理：灰階 -> 高斯模糊 -> 二值化 Threshold
gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY_INV)

# 4. 尋找輪廓
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

result = src.copy()
print(f"[資訊] 共檢測到 {len(contours)} 個輪廓")

# 5. 分析每個輪廓
for i, cnt in enumerate(contours):
    area = cv2.contourArea(cnt)
    if area < 100:  # 過濾微小的噪點
        continue

    # 繪製輪廓外框（綠線）
    cv2.drawContours(result, contours, i, (0, 255, 0), 2)

    # 計算輪廓的形心（中心點）
    M = cv2.moments(cnt)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        # 在圖形中心點寫上記號
        cv2.putText(result, f"#{i+1}", (cx - 10, cy + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

# 6. 顯示結果
cv2.imshow('Original Image', src)
cv2.imshow('Binary Thresh', thresh)
cv2.imshow('Detected Contours', result)

cv2.waitKey(0)
cv2.destroyAllWindows()