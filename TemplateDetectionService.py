import cv2
import numpy as np
import imutils
import timeit

class TemplateDetectionService(object):

    def __init__(self):
        self.threshold = 0.2
        self.start_time = None

    def start_template_matching(self, template_matching_frame, selected_template_image, detection_threshold):
        if selected_template_image is None:
            return

        if len(selected_template_image) <= 0:
            return

        if self.start_time is None:
            self.start_time = timeit.default_timer()

        self.threshold = detection_threshold
        template_coordinates = self.detect_template(template_matching_frame, selected_template_image)
        if template_coordinates is None:
            new_template_coordinates = type('', (object,),
                                            {"is_found": False, "start_x": 0, "start_y": 0, "end_x": 0,
                                             "end_y": 0})()
        else:
            new_template_coordinates = template_coordinates

        if new_template_coordinates is not None:
            if new_template_coordinates .is_found:
                font = cv2.FONT_HERSHEY_SIMPLEX
                start_x = new_template_coordinates.start_x
                start_y = new_template_coordinates.start_y
                end_x = new_template_coordinates.end_x
                end_y = new_template_coordinates.end_y
                submitted_template_coordinates = new_template_coordinates
                elapsed = timeit.default_timer() - self.start_time
                cv2.rectangle(template_matching_frame, (start_x, start_y),(end_x, end_y), (0, 0, 255), 2)
                cv2.putText(template_matching_frame, "Detect(s):"+"{0:.2f}".format(elapsed), (start_x + 10, start_y + 10), font, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
                self.start_time = None
                return submitted_template_coordinates

        return None

    def detect_template(self, image, template):
        (tH, tW) = template.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        found = None
        for scale in np.linspace(0.2, 1.0, 20)[::-1]:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            resized = imutils.resize(gray, width=int(gray.shape[1] * scale))
            r = gray.shape[1] / float(resized.shape[1])

            # if the resized image is smaller than the template, then break
            # from the loop
            if resized.shape[0] < tH or resized.shape[1] < tW:
                break

            # detect edges in the resized, grayscale image and apply template
            # matching to find the template in the image
            edged = cv2.Canny(resized, 50, 200)
            result = cv2.matchTemplate(edged, template, cv2.TM_CCORR_NORMED)
            # max_val will be the correlation of of the match
            # max_loc will be the location of the template
            (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)

            # if we have found a new maximum correlation value, then ipdate
            # the bookkeeping variable
            if found is None or maxVal > found[0]:
                found = (maxVal, maxLoc, r)

                # unpack the bookkeeping variable and compute the (x, y) coordinates
                # of the bounding box based on the resized ratio
        if found is None:
            return None

        (thresh, maxLoc, r) = found

        if thresh <= self.threshold:
            return None

        (start_x, start_y) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
        (end_x, end_y) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))

        return type('', (object,),
                    {"is_found": True, "start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y})()