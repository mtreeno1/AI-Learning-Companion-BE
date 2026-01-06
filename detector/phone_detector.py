from ultralytics import YOLO

class PhoneDetector:
    def __init__(self, model_path="models/yolov8n.pt"):
        self.model = YOLO(model_path)

    def detect(self, frame, conf=0.5):
        results = self.model(frame, conf=conf, verbose=False)
        phones = []

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = self.model.names[cls]
                if label == "cell phone":
                    phones.append(box.xyxy[0].cpu().numpy())

        return phones
