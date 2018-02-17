from CreateTemplatePage import *
from TemplateDetectionPage import *
from Tkinter import *
import os
from WebCamService import *
from PIL import Image, ImageTk

from TemplateModel import *
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import math

LARGE_FONT = ("Verdana", 12)


class CameraCalibrationPage(Frame):

    def __init__(self, parent, controller, template_service):
        Frame.__init__(self, parent, width=1500, height=600, background="white")
        self.cameraCalibrationFrame = Frame(self, bg="white")
        self.web_cam_service = WebCamService()
        self.camera_calibration_label = Label(self.cameraCalibrationFrame)
        self.create_camera_calibration_images_label = Label(self.cameraCalibrationFrame)
        self.isCameraStarted = False
        self.calibration_image = None
        self.calibration_image_counter = 0
        self.initialize_toolbar()

        self.camera_focal_length = 3.67  # mm
        self.ratio_width = 4
        self.ratio_height = 3
        self.diagonal_field_of_view = 83  # degrees
        self.diagonal_field_of_view_radians = math.radians(self.diagonal_field_of_view)

        self.controller = controller
        self.camera_calibration_data = type('', (object,),
                                        {"isFound": False, "height": 0, "width": 0, "number_of_pixels": 0, "focal_length":0,
                                         "diagonal_field_of_view":0, "vertical_field_of_view":0, "horizontal_field_of_view":0,
                                         "f_x": 0, "f_y": 0, "c_x": 0,
                                         "c_y": 0, "m_x": 0, "m_y": 0, "m":0})()

    def initialize_toolbar(self):
        toolbar = Frame(self, bg="white")

        start_calibration_button = Button(toolbar, text="Start Calibration",
                                          command=self.on_start_calibration_button_click)
        start_calibration_button.pack(side=LEFT, padx=2, pady=2)

        start_calibration_button = Button(toolbar, text="Create Calibration Images",
                                          command=self.on_create_calibration_images_button_click)
        start_calibration_button.pack(side=LEFT, padx=2, pady=2)

        start_calibration_button = Button(toolbar, text="Save Image",
                                          command=self.on_save_image_button_click)
        start_calibration_button.pack(side=LEFT, padx=2, pady=2)
        toolbar.pack(side=TOP, fill=X)

    def on_create_calibration_images_button_click(self):
        self.initialize_ui_elements()
        if self.isCameraStarted:
            return
        self.web_cam_service.start();
        self.isCameraStarted = True

        while self.isCameraStarted:
            frame = self.web_cam_service.get_current_frame()
            if frame is not None:
                self.calibration_image = frame.copy()
                self.update_label_with_image(self.create_camera_calibration_images_label, self.calibration_image)

    def on_save_image_button_click(self):

        if self.calibration_image is None:
            return
        new_image = Image.fromarray(self.calibration_image)
        image_path = "cameraCalibrationImages/calibrationImage"+str(self.calibration_image_counter)+".jpg"
        new_image.save(image_path)
        self.controller.update_status_message("Image saved successfully, at location "+image_path)
        self.calibration_image_counter = self.calibration_image_counter + 1

    def on_start_calibration_button_click(self):
        self.controller.update_status_message("Start calibration process")
        self.initialize_ui_elements()
        # termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
        objp = np.zeros((6 * 7, 3), np.float32)
        objp[:, :2] = np.mgrid[0:7, 0:6].T.reshape(-1, 2)

        # Arrays to store object points and image points from all the images.
        objpoints = []  # 3d point in real world space
        imgpoints = []  # 2d points in image plane.
        images = [name for name in os.listdir("cameraCalibrationImages/") if name.endswith(".jpg")]

        if len(images) <= 0:
            self.controller.update_status_message("No calibration images found.")
            tkMessageBox.showinfo("No calibration images", "No calibration images found. Please create some images to start the calibration process.")
            return

        height = 0
        width = 0
        for fname in images:
            img = cv2.imread("cameraCalibrationImages/" + fname)
            (height, width) = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (7, 6), None)

            # If found, add object points, image points (after refining them)
            if ret == True:
                objpoints.append(objp)

                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                imgpoints.append(corners2)

                # Draw and display the corners
                img = cv2.drawChessboardCorners(img, (7, 6), corners2, ret)
                self.update_label_with_image(self.camera_calibration_label, img)
        try:
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        except Exception:
            self.controller.update_status_message("Calibration failed.")
            tkMessageBox.showerror("Calibration failed",
                                  "The calibration process encountered an issue, there might be some problems with the calibration images. Please try to retake the images from many different angles.")
            return

        self.camera_calibration_data.height = height
        self.camera_calibration_data.width = width
        self.camera_calibration_data.focal_length = self.camera_focal_length
        self.camera_calibration_data.number_of_pixels = height*width
        self.camera_calibration_data.f_x = mtx[0][0]
        self.camera_calibration_data.f_y = mtx[1][1]
        self.camera_calibration_data.c_x = mtx[0][2]
        self.camera_calibration_data.c_y = mtx[1][2]
        self.camera_calibration_data.m_x = self.camera_calibration_data.f_x/self.camera_focal_length
        self.camera_calibration_data.m_y = self.camera_calibration_data.f_y/self.camera_focal_length
        m_average = (self.camera_calibration_data.m_x + self.camera_calibration_data.m_y)/2
        self.camera_calibration_data.m = m_average / self.camera_focal_length

        self.controller.update_camera_calibration_data(self.camera_calibration_data)
        self.controller.update_status_message("Finish calibration process")

    def update_label_with_image(self, label, frame):
        if frame is None:
            return

        if len(frame) <= 0:
            return
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        image_from_array = Image.fromarray(cv2image)
        photo_image = ImageTk.PhotoImage(image=image_from_array)
        label.configure(image=photo_image)
        label._image_cache = photo_image  # avoid garbage collection
        label.pack()
        self.update()

    def on_destroy(self):
        self.controller.update_status_message("Finish calibration process")
        if self.isCameraStarted:
            self.isCameraStarted = False
            self.web_cam_service.destroy()

    def on_resume(self):
        self.controller.update_status_message("Resume calibration process")
        self.initialize_ui_elements()

    def initialize_ui_elements(self):
        self.camera_calibration_label.grid(row=0, column=0)
        self.camera_calibration_label.configure(image='')
        self.camera_calibration_label.pack(side=LEFT)

        self.create_camera_calibration_images_label.grid(row=0, column=0)
        self.create_camera_calibration_images_label.configure(image='')
        self.create_camera_calibration_images_label.pack(side=LEFT)

        self.cameraCalibrationFrame.pack()

    def on_pause(self):
        self.controller.update_status_message("Pause calibration process")
        self.on_destroy()
