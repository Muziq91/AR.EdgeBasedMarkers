from Tkinter import *
from TemplateService import *
from CameraCalibrationPage import *
from CreateTemplatePage import *
from TemplateDetectionPage import *

class ApplicationLayout(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.template_service = TemplateService()
        self.geometry("1500x600")
        self.container = Frame(self)
        self.protocol("WM_DELETE_WINDOW", self.on_quit_menu_item_click)
        self.status_label_message = StringVar()
        self.initialize_status_bar()
        self.main_menu = Menu(self)
        self.config(menu=self.main_menu)
        self.initialize_menu()

        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.camera_calibration_data = None
        self.frames = {}

        for page in (CameraCalibrationPage, CreateTemplatePage, TemplateDetectionPage):
            frame = page(self.container, self, self.template_service)
            self.frames[page] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.activeFrame = CameraCalibrationPage;
        self.show_frame(CameraCalibrationPage)

    def show_frame(self, cont):
        self.activeFrame = self.frames[cont]
        self.activeFrame.tkraise()

    def initialize_status_bar(self):
        self.status_label_message.set('')
        status_label = Label(self, textvariable=self.status_label_message, bd=1, relief=SUNKEN, anchor=W)
        status_label.pack(side=BOTTOM, fill=X)

    def update_status_message(self, message):
        self.status_label_message.set(message)

    def initialize_menu(self):
        file_menu = Menu(self.main_menu , tearoff=False)
        self.main_menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Camera Calibration", command=self.on_camera_calibration_menu_item_click)
        file_menu.add_command(label="New Marker...", command=self.on_create_new_template_menu_item_click)
        file_menu.add_command(label="Marker Detection", command=self.on_template_detection_menu_item_click)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_quit_menu_item_click)

    def on_camera_calibration_menu_item_click(self):
        self.activeFrame.on_pause()
        self.show_frame(CameraCalibrationPage)
        self.activeFrame.on_resume()

    def on_create_new_template_menu_item_click(self):
        self.activeFrame.on_pause()
        self.show_frame(CreateTemplatePage)
        self.activeFrame.on_resume()

    def on_template_detection_menu_item_click(self):
        self.activeFrame.on_pause()
        self.show_frame(TemplateDetectionPage)
        self.activeFrame.on_resume()

    def on_quit_menu_item_click(self):
        self.activeFrame.on_destroy()
        self.destroy()
        self.quit()

    def update_camera_calibration_data(self, new_camera_calibration_data):
        self.camera_calibration_data = new_camera_calibration_data

    def get_camera_calibration_data(self):
        return self.camera_calibration_data