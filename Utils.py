import cv2
import numpy as np
import logging

class Utils(object):

    def __init__(self, controller):
        self.threshold = 0.2
        self.object_real_world_mm = 50
        self.controller = controller
        self.camera_calibration_data = self.controller.get_camera_calibration_data()
        self.overlay_vertices = np.float32([[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0],
                                            [0.5, 0.5, 4]])

    def compute_object_vertices(self, img, tracked):
        start_x, start_y, end_x, end_y = tracked.target.rect
        quad_3d = np.float32([[start_x, start_y, 0], [end_x, start_y, 0],
                              [end_x, end_y, 0], [start_x, end_y, 0]])
        h, w = img.shape[:2]
        K = np.float64([[w, 0, 0.5 * (w - 1)],
                        [0, w, 0.5 * (h - 1)],
                        [0, 0, 1.0]])
        dist_coef = np.zeros(4)
        ret, rvec, tvec = cv2.solvePnP(quad_3d, tracked.quad, K, dist_coef)
        verts = self.overlay_vertices * [(end_x - start_x), (end_y - start_y),
                                         -(end_x - start_x) * 0.3] + (start_x, start_y, 0)
        verts = cv2.projectPoints(verts, rvec, tvec, K, dist_coef)[0].reshape(-1, 2)

        verts_floor = np.int32(verts).reshape(-1, 2)
        return (verts, verts_floor)

    def draw_object(self, img, object_vertices, texts):
        (start_x, start_y), (end_x, end_y) = object_vertices[0], object_vertices[2]
        cv2.rectangle(img, (start_x, start_y), (end_x, end_y), (255, 255, 255), cv2.FILLED, 8, 0);
        font = cv2.FONT_HERSHEY_SIMPLEX
        deficit = 15
        for text in texts:
            cv2.putText(img, text, (start_x + 10, start_y + deficit), font, 0.35, (0, 0, 0), 1, cv2.LINE_AA)
            deficit = deficit+10

    def calculate_distance_to_object(self, real_world_template_size_mm, image_size):
        if self.camera_calibration_data is None:
            self.camera_calibration_data = self.controller.get_camera_calibration_data()

        distance_mm = 0

        if self.camera_calibration_data is None:
            return distance_mm

        x = (self.camera_calibration_data.m * self.camera_calibration_data.width) / self.camera_calibration_data.width
        size_object_on_image_sensor = image_size / x

        if size_object_on_image_sensor != 0:
            distance_mm = real_world_template_size_mm * self.camera_calibration_data.focal_length / size_object_on_image_sensor
        return distance_mm

    def get_canny_edge_image(self, image):

        if image is None:
            return
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if gray is not None:
                gaussian_blur = cv2.GaussianBlur(gray, (5, 5), 0)
                canny_image = cv2.Canny(gaussian_blur, 100, 200)
                return canny_image
        except Exception as ex:
            logging.exception("Something went wrong")
            return None
        return None

    def calculate_all_contour_area(self, im, contours):
        contourArea = 0;

        for contour in contours:
            contourArea = contourArea + cv2.contourArea(contour)

        if len(contours) > 0:
            contourArea = contourArea / len(contours)

        return contourArea

    def calculate_all_contour_perimeter(self, contours):
        contourPerimeter = 0;
        for contour in contours:
            contourPerimeter = contourPerimeter +cv2.arcLength(contour,True)

        if len(contours) > 0:
            contourPerimeter = contourPerimeter / len(contours)
        return contourPerimeter