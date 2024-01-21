import cv2

class VideoCapture:
    def __init__(self, src=0, width=960, height=720, exposure=0.06):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) # Set 0.25 to select manual exposure
        self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure) # Set exposure

    def read(self):
        grabbed, frame = self.cap.read()
        return grabbed, frame

    def read_cropped(self):
        correct, img = self.read()
        if(correct):
            img_cropped = img[:,180:800]
            _, img_encoded = cv2.imencode('.jpg', img_cropped)
            return img_encoded