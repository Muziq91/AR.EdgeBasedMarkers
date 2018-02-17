from Tkinter import *
from PoseEstimationService import *
from TemplateDetectionService import *
from WebCamService import *
from Utils import *
import tkMessageBox
import timeit
import cv2
import math

LARGE_FONT = ("Verdana", 12)


class TemplateDetectionPage(Frame):
    def __init__(self, parent, controller, template_service):
        Frame.__init__(self, parent, width=1500, height=600, background="white")
        self.controller = controller
        self.pose_estimation_service = PoseEstimationService()
        self.web_cam_service = WebCamService()
        self.template_detection_service = TemplateDetectionService()
        self.template_service = template_service
        self.utils = Utils(controller)

        self.all_templates = self.template_service.get_all_templates_from_disk()
        self.isCameraStarted = False
        self.is_template_submitted = False
        self.submitted_template_coordinates = None
        self.paused = False
        self.selected_template = TemplateModel()
        self.option_menu_value = StringVar()
        self.initialize_toolbar()
        self.initialize_ui_elements()

    def initialize_toolbar(self):
        self.toolbar = Frame(self, bg="white")
        template_names = []

        for template in self.all_templates:
            template_names.append(str(template.name))

        start_camera_button = Button(self.toolbar, text="Start Camera", command=self.on_start_camera_button_click)
        start_camera_button.pack(side=LEFT, padx=2, pady=2)

        submit_template_matching_button = Button(self.toolbar, text="Submit Marker Matching",
                                                 command=self.on_submit_template_matching_button_click)
        submit_template_matching_button.pack(side=LEFT, padx=2, pady=2)

        reset_template_matching_button = Button(self.toolbar, text="Reset Marker Matching",
                                                command=self.on_reset_template_matching_button_click)
        reset_template_matching_button.pack(side=LEFT, padx=2, pady=2)

        detection_threshold_label = Label(self.toolbar, text="Marker Detection threshold: ")
        detection_threshold_label.pack(side=LEFT, padx=2, pady=2)
        self.threshold_slider = Scale(self.toolbar, from_=0, to=1, resolution=0.05, orient=HORIZONTAL)
        self.threshold_slider.set(0.2)
        self.threshold_slider.pack(side=LEFT, padx=2, pady=2)
        self.option_menu_value.set("Select marker")

        if len(template_names) > 0:
            template_selection_option_menu = OptionMenu(self.toolbar, self.option_menu_value, *template_names, command=self.on_select_template_click)
            template_selection_option_menu.grid(row=0, column=0)
            template_selection_option_menu.pack(side=LEFT, padx=10, pady=10)

        self.selected_template_label = Label(self.toolbar)
        self.selected_template_label.grid(row=0, column=3)
        self.selected_template_label.configure(image='')
        self.selected_template_label.pack(side=LEFT)

        template_size_label = Label(self.toolbar, text="Marker Size: ")
        template_size_label.pack(side=LEFT, padx=2, pady=2)
        self.template_size_input = Entry(self.toolbar, bd=3)
        self.template_size_input.pack(side=LEFT, padx=2, pady=2)
        selected_template_text = Label(self.toolbar, text="Selected Marker: ")
        selected_template_text.pack(side=LEFT, padx=2, pady=2)
        self.toolbar.pack(side=TOP,  fill=X)

    def on_select_template_click(self, event):
        selected_template_name= self.option_menu_value.get()
        self.selected_template = TemplateModel()
        for template in self.all_templates:
            if template.name == selected_template_name:
                self.selected_template.id = template.id
                self.selected_template.name = template.name
                self.selected_template.complexity = template.complexity
                self.selected_template.image = template.image
                self.selected_template.total_contour_area = template.total_contour_area
                self.selected_template.total_contour_perimeter = template.total_contour_perimeter
                image_from_array = Image.fromarray(template.image)
                photo_image = ImageTk.PhotoImage(image=image_from_array)
                self.selected_template_label.configure(image=photo_image)
                self.selected_template_label._image_cache = photo_image
                self.update()

    def on_start_camera_button_click(self):
        if self.isCameraStarted:
            return

        self.isCameraStarted = True
        self.web_cam_service.start()
        start_time = None
        while self.isCameraStarted:
            frame = self.web_cam_service.get_current_frame()
            template_matching_frame = frame.copy()
            key_point_detection_frame = frame.copy()

            if not self.is_template_submitted:
                # elapsed time in seconds
                if start_time is None:
                    start_time = timeit.default_timer()

                detection_threshold = self.threshold_slider.get()
                if detection_threshold is None:
                    detection_threshold = 0.2
                else:
                    if detection_threshold == '':
                        detection_threshold = 0.2
                    else:
                        detection_threshold = float(detection_threshold)

                if self.selected_template is not None:
                    self.submitted_template_coordinates = self.template_detection_service.start_template_matching(template_matching_frame, self.selected_template.image, detection_threshold)

                if self.submitted_template_coordinates is not None:
                    elapsed = timeit.default_timer() - start_time
                    start_time = None
                    #print "Match selected template time:" + str(elapsed)
                self.update_label_with_camera_image(template_matching_frame, self.template_matching_label)

            if self.is_template_submitted:
                if self.submitted_template_coordinates is not None:
                    start_x = self.submitted_template_coordinates.start_x
                    start_y = self.submitted_template_coordinates.start_y
                    end_x = self.submitted_template_coordinates.end_x
                    end_y = self.submitted_template_coordinates.end_y
                    self.pose_estimation_service.add_target(key_point_detection_frame, self.selected_template, (start_x, start_y, end_x, end_y))
                    template_section = key_point_detection_frame[start_y:end_y, start_x:end_x]
                    self.is_template_submitted = False
                    self.submitted_template_coordinates = None

            self.start_template_tracking_process(key_point_detection_frame)
            self.update_label_with_camera_image(key_point_detection_frame, self.key_point_detection_label)

    def update_label_with_camera_image(self, frame, label):
        if frame is None:
            return

        if len(frame) <= 0:
            return
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        image_from_array = Image.fromarray(cv2image)
        photo_image = ImageTk.PhotoImage(image=image_from_array)
        label.configure(image=photo_image)
        label._image_cache = photo_image  # avoid garbage collection
        self.update()

    def start_template_tracking_process(self, frame):
        if frame is None:
            return
        tracked = self.pose_estimation_service.track_target(frame)
        target = None
        for item in tracked:
            if len(item) <= 0:
                return
            target = item.target
            (object_vertices, object_floored_vertices) = self.utils.compute_object_vertices(frame, item)
            (observer_image_size_px, observed_image_size_mm) = self.get_target_contour_properties(frame, target.selected_template.size, object_floored_vertices)
            if target.selected_template is not None:
                distance_mm = self.utils.calculate_distance_to_object(observed_image_size_mm, observer_image_size_px)
            else:
                self.controller.update_status_message("Invalid target. Default size set to 50 mm.")
                distance_mm = self.utils.calculate_distance_to_object(50, observer_image_size_px)
            distance_mm = distance_mm*5

            object_texts = []
            if target is not None:
                object_texts.append("Lbl: ")
                object_texts.append(str(target.selected_template.name))
            object_texts.append("Dst(mm): ")
            object_texts.append("{0:.2f}".format(distance_mm))
            object_texts.append("Cplx:")
            object_texts.append(str(target.selected_template.complexity))
            self.utils.draw_object(frame, object_floored_vertices, object_texts)

    def get_target_contour_properties(self, frame, observed_image_size_mm, object_floored_vertices):
        new_observed_image_size_mm = observed_image_size_mm
        box = [np.vstack((object_floored_vertices[0], object_floored_vertices[2]))]
        x_1 = box[0][0][0]
        y_1 = box[0][0][1]
        x_2 = box[0][1][0]
        y_2 = box[0][1][1]
        initial_template_size = math.hypot(x_2 - x_1, y_2 - y_1)

        try:
            image = frame[y_1:y_2, x_1:x_2]
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if gray is None:
                return 0
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            if gray is None:
                return 0
            # threshold the image, then perform a series of erosions +
            # dilations to remove any small regions of noise
            thresh = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.erode(thresh, None, iterations=2)
            thresh = cv2.dilate(thresh, None, iterations=2)

            # find contours in thresholded image, then grab the largest
            # one
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if imutils.is_cv2() else cnts[1]
            c = max(cnts, key=cv2.contourArea)

            extLeft = tuple(c[c[:, :, 0].argmin()][0])
            extRight = tuple(c[c[:, :, 0].argmax()][0])
            extTop = tuple(c[c[:, :, 1].argmin()][0])
            extBot = tuple(c[c[:, :, 1].argmax()][0])

            calculated_image_size = math.hypot(extRight[0] - extLeft[0], extRight[1]- extLeft[1])
            new_observed_image_size_mm = (observed_image_size_mm*calculated_image_size)/initial_template_size
            return calculated_image_size, new_observed_image_size_mm
        except Exception as ex:
            logging.exception("Something went wrong")
            return initial_template_size, observed_image_size_mm


    def on_submit_template_matching_button_click(self):
        self.is_template_submitted = True
        template_size = self.template_size_input.get()
        if template_size == '':
            tkMessageBox.showinfo("No marker size selected", "Because no marker size was selected the default value will be 50 mm.")
            return
        self.selected_template.size = int(template_size)

    def on_reset_template_matching_button_click(self):
        self.is_template_submitted = False
        self.pose_estimation_service.clear_targets()
        self.key_point_detection_label.grid(row=0, column=0)
        self.key_point_detection_label.configure(image='')
        self.key_point_detection_label.pack(side=LEFT)

    def on_resume(self):
        self.is_template_submitted = False
        self.all_templates = self.template_service.get_all_templates_from_disk()
        self.toolbar.destroy()
        self.template_detection_frame.destroy()
        self.initialize_toolbar()
        self.initialize_ui_elements()

    def initialize_ui_elements(self):
        self.template_detection_frame = Frame(self, bg="white")

        self.template_matching_label = Label(self.template_detection_frame)
        self.template_matching_label.grid(row=0, column=0)
        self.template_matching_label.configure(image='')
        self.template_matching_label.pack(side=LEFT)

        self.key_point_detection_label = Label(self.template_detection_frame)
        self.key_point_detection_label.grid(row=0, column=0)
        self.key_point_detection_label.configure(image='')
        self.key_point_detection_label.pack(side=LEFT)

        self.selected_template_label.grid(row=0, column=3)
        self.selected_template_label.configure(image='')
        self.selected_template_label.pack(side=LEFT)

        self.template_detection_frame .pack()

    def on_pause(self):
        self.on_destroy()

    def on_destroy(self):
        if self.isCameraStarted:
            self.isCameraStarted = False
            self.web_cam_service.destroy()
            self.pose_estimation_service.clear_targets()
            self.selected_template = None
