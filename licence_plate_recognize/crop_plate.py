import yolov5
import cv2
import os
import time

# Load YOLOv5 license plate detection model
model = yolov5.load('keremberke/yolov5n-license-plate')
model.conf = 0.25  # Confidence threshold

# Input/output paths
input_dir = "input_images"
output_dir = "cropped_plates"
os.makedirs(output_dir, exist_ok=True)

# Loop through images in input directory
for filename in os.listdir(input_dir):
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        continue

    start_time = time.time()
    image_path = os.path.join(input_dir, filename)
    image = cv2.imread(image_path)

    # Perform detection
    results = model(image)
    predictions = results.pred[0]

    # Loop through detections
    for i, det in enumerate(predictions):
        x1, y1, x2, y2, conf, cls = map(int, det[:6])
        cropped = image[y1:y2, x1:x2]
        cropped_filename = f"{os.path.splitext(filename)[0]}_plate_{i}.jpg"
        cropped_path = os.path.join(output_dir, cropped_filename)
        cv2.imwrite(cropped_path, cropped)
        end_time = time.time()
        print(f"Cropped plate saved: {cropped_path}. Detected in {end_time-start_time}s")

