import cv2
from threading import Thread


class WebCamService:
    def __init__(self):
        self.current_thread = Thread(target=self._update_frame, args=())

    # create thread for capturing images
    def start(self):
        self.video_capture = cv2.VideoCapture(0)
        self.current_frame = self.video_capture.read()[1]

        if self.current_thread.isAlive():
            return
        self.current_thread.start()

    def _update_frame(self):
        while True:
            frame = self.video_capture.read()[1]
            if frame is not None:
                self.current_frame = frame.copy()

    # get the current frame
    def get_current_frame(self):
        return self.current_frame

    def destroy(self):
        self.video_capture.release()
