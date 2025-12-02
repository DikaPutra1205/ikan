import cv2
import mediapipe as mp
import time
import numpy as np

# Konfigurasi (Sama seperti game.py)
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MOUTH_OPEN_THRESHOLD = 0.05
TRACKING_X_MIN = 0.2
TRACKING_X_MAX = 0.8
TRACKING_Y_MIN = 0.2
TRACKING_Y_MAX = 0.8

def run_benchmark():
    print("==========================================")
    print("  BENCHMARK KINERJA: COMPUTER VISION (CV)")
    print("==========================================")
    print("Inisialisasi Mediapipe...")

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Kamera tidak ditemukan.")
        return

    print("\n[INSTRUKSI PENGUJIAN]")
    print("1. Pastikan wajah Anda terlihat jelas di kamera.")
    print("2. Benchmark akan berjalan selama 300 Frames (kurang lebih 10-15 detik).")
    print("3. Cobalah gerakkan kepala dan buka mulut seperti saat bermain.")
    print("Tekan ENTER untuk memulai...")
    input()

    print("Mulai mengukur...")

    frame_count = 0
    max_frames = 300
    
    latencies = []
    detection_counts = 0
    
    start_time_total = time.time()

    while frame_count < max_frames:
        iter_start = time.time()

        success, image = cap.read()
        if not success:
            continue

        # Pre-processing
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 2. Inference Latency (Waktu proses AI)
        inference_start = time.time()
        results = face_mesh.process(image_rgb)
        inference_end = time.time()

        # 3. Post-processing Latency (Logika Game)
        if results.multi_face_landmarks:
            detection_counts += 1
            face_landmarks = results.multi_face_landmarks[0].landmark
            
            # Logika hitung koordinat (sama seperti game.py)
            nose_tip = face_landmarks[1]
            percent_x = (nose_tip.x - TRACKING_X_MIN) / (TRACKING_X_MAX - TRACKING_X_MIN)
            percent_y = (nose_tip.y - TRACKING_Y_MIN) / (TRACKING_Y_MAX - TRACKING_Y_MIN)
            
            # Logika deteksi mulut
            lip_top = face_landmarks[13]
            lip_bottom = face_landmarks[14]
            lip_distance = abs(lip_top.y - lip_bottom.y)
            is_eating = lip_distance > MOUTH_OPEN_THRESHOLD

        iter_end = time.time()
        
        # Hitung latensi (Hanya proses inferensi + logic, tidak termasuk waktu tunggu kamera/IO)
        # Ini merepresentasikan overhead CPU akibat AI
        frame_latency = (iter_end - inference_start) * 1000 # ms
        latencies.append(frame_latency)
        
        frame_count += 1
        
        # Feedback visual minimal
        if frame_count % 50 == 0:
            print(f"Progress: {frame_count}/{max_frames} frames...")

    end_time_total = time.time()
    total_duration = end_time_total - start_time_total

    cap.release()
    
    # Analisis Data
    avg_latency = np.mean(latencies)
    min_latency = np.min(latencies)
    max_latency = np.max(latencies)
    std_dev_latency = np.std(latencies) # Jitter
    actual_fps = frame_count / total_duration
    accuracy_rate = (detection_counts / frame_count) * 100

    print("\n==========================================")
    print("  HASIL PENGUJIAN")
    print("==========================================")
    print(f"Total Frames Diproses : {frame_count}")
    print(f"Total Durasi Waktu    : {total_duration:.2f} detik")
    print("------------------------------------------")
    print(f"1. LATENCY (Processing Time per Frame):")
    print(f"   - Rata-rata        : {avg_latency:.2f} ms")
    print(f"   - Terbaik (Min)    : {min_latency:.2f} ms")
    print(f"   - Terburuk (Max)   : {max_latency:.2f} ms")
    print(f"   - Jitter (Stabil?) : {std_dev_latency:.2f} ms (Semakin kecil semakin baik)")
    print("------------------------------------------")
    print(f"2. THROUGHPUT:")
    print(f"   - Real-time FPS    : {actual_fps:.2f} FPS")
    print("------------------------------------------")
    print(f"3. ACCURACY (Face Detection Rate):")
    print(f"   - Terdeteksi       : {accuracy_rate:.2f}%")
    print("   (Jika di bawah 90%, cek pencahayaan ruangan)")
    print("==========================================")

if __name__ == "__main__":
    # Instalasi numpy jika belum ada (biasanya sudah ada dengan mediapipe/opencv)
    try:
        run_benchmark()
    except ImportError as e:
        print("Error: Library kurang lengkap.")
        print(f"Details: {e}")
        print("Coba jalankan: pip install numpy opencv-python mediapipe")
