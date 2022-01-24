import datetime

def name_cv2_window(cam_num):
    pass

def name_file(cam_num):
    folder_location = "/output/video/"
    current_date = datetime.datetime.now()
    return str(folder_location + current_date.strftime("%d-%m-%y %H.%M.%S") + f" - Cam{cam_num} Out.avi")
