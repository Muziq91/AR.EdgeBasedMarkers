from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
from WebCamService import *
import cv2
from TemplateModel import *
import logging

LARGE_FONT = ("Verdana", 12)


class CreateTemplatePage(Frame):

    def __init__(self, parent, controller, template_service):
        Frame.__init__(self, parent, width=1500, height=600, background="white")
        self.controller = controller
        self.web_cam_service = WebCamService()
        self.template_service = template_service
        self.isCameraStarted = False
        self.isDragFinished = False

        self.create_custom_template_frame = Frame(self, bg="white")
        self.canny_edge_camera_label = Label(self.create_custom_template_frame)
        self.camera_label = Label(self.create_custom_template_frame)
        self.template_label = Label(self.create_custom_template_frame)

        self.region_of_interest = []
        self._drag_data = {"start_x": 0, "start_y": 0, "end_x": 0, "end_y": 0}
        self.initialize_toolbar()

    def initialize_toolbar(self):
        toolbar = Frame(self, bg="white")
        start_camera_button = Button(toolbar, text="Start Camera", command=self.on_start_camera_button_click)
        start_camera_button.pack(side=LEFT, padx=2, pady=2)

        save_selected_template = Button(toolbar, text="Save Marker", command=self.on_save_template_button_click)
        save_selected_template.pack(side=LEFT, padx=2, pady=2)

        self.template_name_input = Entry(toolbar, bd=3)
        self.template_name_input.pack(side=LEFT, padx=2, pady=2)
        toolbar.pack(side=TOP, fill=X)

    def on_start_camera_button_click(self):
        if self.isCameraStarted:
            return

        self.controller.update_status_message("Start camera")
        self.isCameraStarted = True
        self.web_cam_service.start()
        self._drag_data = {"start_x": 0, "start_y": 0, "end_x": 0, "end_y": 0}

        while self.isCameraStarted:
            frame = self.web_cam_service.get_current_frame()
            canny_edge_frame = frame.copy()
            draw_frame = frame.copy()

            canny_edge_frame = self.canny_edge_detection(canny_edge_frame)
            self.update_label_with_image(self.canny_edge_camera_label, canny_edge_frame, False)
            self.canny_edge_camera_label.pack(side=LEFT)

            self.draw_region_of_interest(draw_frame)
            self.update_label_with_image(self.camera_label, draw_frame, True)
            self.update_template(canny_edge_frame)

    def update_template(self, frame):
        if frame is None:
            return

        if len(frame) <= 0:
            return

        if self.isDragFinished:
            start_x = self._drag_data["start_x"]
            start_y = self._drag_data["start_y"]
            end_x = self._drag_data["end_x"]
            end_y = self._drag_data["end_y"]
            self.region_of_interest = frame[start_y:end_y, start_x: end_x]
            (im2, contours, hierarchy) = cv2.findContours(self.region_of_interest .copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            tempalte_complexity = len(contours)
            self.controller.update_status_message("Selected marker has complexity: " + str(tempalte_complexity))
            self.update_label_with_image(self.template_label, self.region_of_interest, False)
            self.isDragFinished = False

    def update_label_with_image(self, label, frame, convert_to_rgba):
        if frame is None:
            return

        if len(frame) <= 0:
            return
        if convert_to_rgba:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            image_from_array = Image.fromarray(cv2image)
        else:
            image_from_array = Image.fromarray(frame)
        photo_image = ImageTk.PhotoImage(image=image_from_array)
        label.configure(image=photo_image)
        label._image_cache = photo_image  # avoid garbage collection
        self.update()

    def on_save_template_button_click(self):
        self.controller.update_status_message("Start saving marker")
        if self.region_of_interest is None:
            tkMessageBox.showinfo("No marker selected", "No region selected.")
            return

        if len(self.region_of_interest) <= 0:
            tkMessageBox.showinfo("No marker selected", "No region selected.")
            return

        if self.is_template_duplicate(self.region_of_interest.copy()):
            self.controller.update_status_message("Duplicate marker detected")
            tkMessageBox.showinfo("Duplicate Marker", "This marker already exists in the database.")
            return

        template_name = self.template_name_input.get()
        if template_name == '':
            tkMessageBox.showinfo("Field cannot be empty", "Name field cannot be empty.")
            return

        template = TemplateModel()
        template.name = template_name
        template.image = self.region_of_interest
        self.template_service.save_template_to_disk(template)

        self.controller.update_status_message("Marker saved successfully")

    def is_template_duplicate(self, current_template):
        all_templates = self.template_service.get_all_templates_from_disk()
        threshold = 0.7
        (ct_h, ct_w) = current_template.shape[:2]

        for template in all_templates:
            #template.image = cv2.cvtColor(template.image, cv2.COLOR_BGR2GRAY)
            (t_h, t_w) = template.image.shape[:2]
            try:
                if ct_h <= t_h and ct_w <= t_w:
                    res = cv2.matchTemplate(template.image, current_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    if max_val >= threshold:
                        return True
            except Exception as ex:
                logging.exception("Something went wrong")
                continue
        return False

    def on_resume(self):
        self.initialize_ui_elements()

    def initialize_ui_elements(self):
        self.camera_label.grid(row=0, column=2)

        self.camera_label.bind("<ButtonPress-1>", self.on_mouse_press)
        self.camera_label.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.camera_label.bind("<B1-Motion>", self.on_mouse_motion)
        self.camera_label.configure(image='')

        self.camera_label.pack(side=LEFT)

        self.canny_edge_camera_label.grid(row=0, column=1)
        self.canny_edge_camera_label.configure(image='')
        self.canny_edge_camera_label.pack(side=LEFT)

        self.template_label.grid(row=0, column=3)
        self.template_label.configure(image='')
        self.template_label.pack(side=LEFT)
        self.create_custom_template_frame.pack()

    def on_pause(self):
        self.on_destroy()

    def on_destroy(self):
        if self.isCameraStarted:
            self.isCameraStarted = False
            self.web_cam_service.destroy()
            self.create_custom_template_frame.pack_forget()

    def on_mouse_press(self, event):
        if not self.isCameraStarted:
            return

        self.isDragFinished = False
        # record the item and its location
        self._drag_data["start_x"] = event.x
        self._drag_data["start_y"] = event.y
        self._drag_data["end_x"] = event.x
        self._drag_data["end_y"] = event.y

    def on_mouse_release(self, event):
        if not self.isCameraStarted:
            return

        self.isDragFinished = True

    def on_mouse_motion(self, event):
        if not self.isCameraStarted:
            return
        self._drag_data["end_x"] = event.x
        self._drag_data["end_y"] = event.y

    def draw_region_of_interest(self, img):
        if not self._drag_data:
            return False

        start_x = self._drag_data["start_x"]
        start_y = self._drag_data["start_y"]
        end_x = self._drag_data["end_x"]
        end_y = self._drag_data["end_y"]
        cv2.rectangle(img, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        return True

    def canny_edge_detection(self, image):
        if image is None:
            return

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gaussian_blur = cv2.GaussianBlur(gray, (5, 5), 0)
        canny_image = cv2.Canny(gaussian_blur, 100, 200)
        return canny_image
