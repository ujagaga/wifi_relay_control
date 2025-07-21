import cv2
import os

# Path to known authorized plate images
KNOWN_DIR = "authorized_plates"
# Path to a new cropped plate to check
QUERY_PATH = "cropped_plates/1_plate_0.jpg"
# ORB feature matcher parameters
MATCH_THRESHOLD = 20  # Adjust as needed


def load_authorized_descriptors():
    sift = cv2.SIFT_create()
    descriptors = []
    for filename in os.listdir(KNOWN_DIR):
        path = os.path.join(KNOWN_DIR, filename)
        image = cv2.imread(path, 0)
        if image is None:
            continue
        kp, desc = sift.detectAndCompute(image, None)
        if desc is not None:
            descriptors.append(desc)
    return descriptors


def is_plate_authorized(query_path, known_descriptors):
    sift = cv2.SIFT_create()
    bf = cv2.BFMatcher()

    query_img = cv2.imread(query_path, 0)
    if query_img is None:
        print("Failed to load query image.")
        return False

    kp_query, desc_query = sift.detectAndCompute(query_img, None)
    if desc_query is None:
        return False

    for i, desc_known in enumerate(known_descriptors):
        matches = bf.knnMatch(desc_query, desc_known, k=2)
        # Apply ratio test as per Lowe's paper
        good = [m for m, n in matches if m.distance < 0.75 * n.distance]
        print(f"Matching with plate {i + 1}: {len(good)} good matches")
        if len(good) >= MATCH_THRESHOLD:
            return True

    return False


if __name__ == "__main__":
    known_descs = load_authorized_descriptors()
    result = is_plate_authorized(QUERY_PATH, known_descs)
    print("✅ Authorized" if result else "❌ Not authorized")
