import cv2
import numpy as np
import mediapipe as mp

class ObjectDetector:
    def __init__(self, ip_address="192.168.123.100", port=9201):
        self.confidence_threshold = 0.5
        self.pipeline = self._build_pipeline(ip_address, port)
        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open video stream")

        self.net = cv2.dnn.readNetFromCaffe("model/MobileNetSSD_deploy.prototxt", 
                                            "model/MobileNetSSD_deploy.caffemodel")

        self.classes = [
            "background", "aeroplane", "bicycle", "bird", "boat",
            "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
            "dog", "horse", "motorbike", "person", "pottedplant",
            "sheep", "sofa", "train", "tvmonitor"
        ]

        self.person_detected = False
        self.waving_detected = False

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()

    def _build_pipeline(self, ip_address, port):
        return (
            "udpsrc address={} port={} "
            "! application/x-rtp,media=video,encoding-name=H264 "
            "! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink"
        ).format(ip_address, port)

    def detect_and_display(self):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None

        frame = cv2.flip(frame, 0)
        self.person_detected = False
        self.waving_detected = False

        blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.confidence_threshold:
                idx = int(detections[0, 0, i, 1])
                if self.classes[idx] == "person":
                    self.person_detected = True

                    
                    self._run_pose_detection(frame)

                x1 = int(detections[0, 0, i, 3] * frame.shape[1])
                y1 = int(detections[0, 0, i, 4] * frame.shape[0])
                x2 = int(detections[0, 0, i, 5] * frame.shape[1])
                y2 = int(detections[0, 0, i, 6] * frame.shape[0])

                label = f"{self.classes[idx]}: {confidence:.2f}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        cv2.imshow("Object Detection", frame)
        return frame

    def _run_pose_detection(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)

        if results.pose_landmarks:
            # Get landmarks
            landmarks = results.pose_landmarks.landmark
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]

            # Check if hand is above shoulder (waving gesture)
            if (left_wrist.y < left_shoulder.y) or (right_wrist.y < right_shoulder.y):
                self.waving_detected = True  

    def is_person_detected(self):
        return self.person_detected

    def is_waving_detected(self):
        return self.waving_detected

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()
