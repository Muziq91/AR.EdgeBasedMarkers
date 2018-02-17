import sqlite3
from collections import namedtuple
import cv2

class TemplateModel():

    def __init__(self):
        self.id = 0
        self.name = ""
        self.size = 50
        self.complexity = 0
        self.total_contour_area = 0
        self.total_contour_perimeter = 0
        self.image = []
