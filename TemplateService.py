import sqlite3
from TemplateModel import *
from PIL import Image, ImageTk
import numpy as np
import cv2
import glob
import base64

sqlite_file = 'template.sqlite'

class TemplateService():

    def __init__(self):
        self.folder_name = "alLTemplates"
        connection = sqlite3.connect(sqlite_file)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS templates(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, template BLOB)")
        connection.commit()
        connection.close()

    def save_template_to_disk(self, template):
        im = Image.fromarray(template.image)
        im.save(self.folder_name+"/"+template.name+'.png')

    def insert_new_template(self, template):
        connection = sqlite3.connect(sqlite_file)
        cursor = connection.cursor()
        _, enc = cv2.imencode(".jpg", template.image)
        templates = [(template.name, base64.b64encode(enc))]
        cursor.executemany(
            "INSERT INTO templates(name, template) VALUES(?, ?)", templates)
        connection.commit()
        connection.close()

    def get_all_templates_from_disk(self):
        all_templates = []
        for filename in glob.glob(self.folder_name+'/*.png'):  # assuming gif
            name = filename.split('\\')[1].split('.')[0]
            image = Image.open(filename)
            is_grey_scale = self.is_grey_scale(image)
            template = TemplateModel()
            template.image = np.array(image)
            if not is_grey_scale:
                template.image = cv2.cvtColor(template.image, cv2.COLOR_BGR2GRAY)
            template.name = name
            (im2, contours, hierarchy) = cv2.findContours(template.image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            template.complexity = len(contours)
            template.total_contour_area = self.calculate_all_contour_area(contours)
            template.total_contour_perimeter = self.calculate_all_contour_perimeter(contours)
            all_templates.append(template)

        return all_templates

    def get_all_templates(self):
        all_templates = []
        connection = sqlite3.connect(sqlite_file)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, template FROM templates")
        all_rows = cursor.fetchall()
        for row in all_rows:
            template = TemplateModel()
            template.id = row[0]
            template.name = row[1]
            jpg_original = base64.b64decode(row[2])
            img = cv2.imdecode(np.frombuffer(jpg_original, np.uint8), 1)
            template.image = img
            all_templates.append(template)
        return all_templates

    def calculate_all_contour_area(self, contours):
        contourArea = 0;
        for contour in contours:
            contourArea = contourArea + cv2.contourArea(contour)

        return contourArea

    def calculate_all_contour_perimeter(self, contours):
        contourPerimeter = 0;
        for contour in contours:
            contourPerimeter = contourPerimeter +cv2.arcLength(contour,True)

        return contourPerimeter

    def is_grey_scale(self, img):
        if img.tile[0] is None:
            return
        if len(img.tile[0])<=0:
            return

        return img.tile[0][3] != "RGBA"
