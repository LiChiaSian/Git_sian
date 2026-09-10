import cv2
import os
import urllib.request

# 1. 取得當前專案資料夾路徑
current_dir = os.path.dirname(os.path.abspath(__file__))

face_xml_name = 'haarcascade_frontalface_default.xml'
eye_xml_name = 'haarcascade_eye.xml'

# 定義下載備用函式 (若電腦本機找不到時自動從 GitHub 下載)
def get_cascade_path(xml_name):
    # 檢查 1: OpenCV 內建預設路徑
    cv2_path = os.path.join(cv2.data.haarcascades, xml_name)
    if os.path.exists(cv2_path):
        return cv2_path
    
    # 檢查 2: 本地專案資料夾
    local_path = os.path.join(current_dir, xml_name)
    if os.path.exists(local_path):
        return local_path
    
    # 若皆找不到，自動從 OpenCV 官方 GitHub 下載
    print(f"[提示] 本機未找到 {xml_name}，正在自動從官方 GitHub 下載...")
    url = f"https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{xml_name}"
    try:
        urllib.request.urlretrieve(url, local_path)
        print(f"[成功] {xml_name} 下載完成！")
        return local_path
    except Exception as e:
        print(f"[錯誤] 下載失敗: {e}")
        return None

# 2. 取得模型完整路徑
face_cascade_path = get_cascade_path(face_xml_name)
eye_cascade_path = get_cascade_path(eye_xml_name)

if not face_cascade_path or not eye_cascade_path:
    print("[錯誤] 無法取得 Haar Cascade 訓練模型！請檢查網路連線。")
    exit()

# 載入分類器
face_cascade = cv2.CascadeClassifier(face_cascade_path)
eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

if face_cascade.empty() or eye_cascade.empty():
    print("[錯誤] 載入 Haar Cascade XML 檔案失敗，檔案可能損毀。")
    exit()

print("[成功] Haar Cascade 模型載入成功！")

# 3. 開啟攝影機(筆電鏡頭:0，DroidCamApp連手機:1)
camera_index = 1
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print(f"[錯誤] 無法開啟攝影機 (索引 {camera_index})！請確認連線。")
    exit()

print("人臉偵測已啟動，按下鍵盤 'q' 鍵可關閉程式...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[錯誤] 無法接收影像訊號。")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    # 偵測人臉
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, "Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        roi_gray = gray[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]

        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=10)
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (255, 0, 0), 2)

    cv2.imshow('Mobile Webcam - Realtime Face Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()