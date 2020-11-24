import cv2
import pytesseract

from settings import COUNTRY_NAME, ID_TYPE, GRADIENT, CHARACTER_HEIGHT_THRESH, ID_TOP, ID_BOTTOM, ID_LEFT


def date_filter(num_str):

    replace_str = []
    string = num_str
    for ch in num_str:
        if not ch.isdigit():
            replace_str.append(ch)

    for re_ch in replace_str:
        string = string.replace(re_ch, "")

    return string


def bind_closest_element(bind_tuple, thresh_value, axis):
    sorted_values = []
    sorted_value_coordinates = []
    init_value = bind_tuple[0][1][axis]
    tmp_line_value, tmp_line_coordinates = [], []

    for sorted_word, sorted_coordinate in bind_tuple:
        if abs(init_value - sorted_coordinate[axis]) <= thresh_value:
            tmp_line_value.append(sorted_word)
            tmp_line_coordinates.append(sorted_coordinate)
            if axis == 0:
                init_value = sorted_coordinate[axis]

        else:
            sorted_values.append(tmp_line_value[:])
            sorted_value_coordinates.append(tmp_line_coordinates[:])
            tmp_line_coordinates.clear()
            tmp_line_coordinates.append(sorted_coordinate)
            tmp_line_value.clear()
            tmp_line_value.append(sorted_word)
            init_value = sorted_coordinate[axis]

    sorted_values.append(tmp_line_value[:])
    sorted_value_coordinates.append(tmp_line_coordinates[:])

    return sorted_values, sorted_value_coordinates


def estimate_birth_info(info, id_type):
    birth_info = ""

    if id_type == ID_TYPE[0]:
        if info[0] == "3":
            birth_info = info[1:]
    elif id_type == ID_TYPE[1]:
        country_index = info.find(COUNTRY_NAME[:4])
        if country_index != -1:
            birth_info = info.replace(info[country_index:], "")

    else:
        country_index = info.find(COUNTRY_NAME[:4])
        if country_index != -1:
            birth_info = info.replace(info[country_index:len(COUNTRY_NAME)], "")

    return birth_info


def extract_birthday(img, id_type, base_line):

    birth_day = ""
    if id_type == ID_TYPE[0] or id_type == ID_TYPE[1]:
        se_thresh_value = 16
    else:
        se_thresh_value = 15
    h, w = img.shape[:2]
    config = r'-l eng --oem 3 --psm 6'
    ocr_roi = img[int(h * ID_TOP):int(h * ID_BOTTOM), base_line:int(w * ID_LEFT)]
    image_gray = cv2.cvtColor(ocr_roi, cv2.COLOR_BGR2GRAY)
    # _, image_thresh = cv2.threshold(image_gray, OCR_THRESH_VALUE, 255, cv2.THRESH_BINARY)
    image_thresh = cv2.adaptiveThreshold(image_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 27,
                                         se_thresh_value)
    # cv2.imshow("thresh image", cv2.resize(image_thresh, (800, 600)))
    # cv2.waitKey()
    rects = pytesseract.pytesseract.image_to_boxes(image=image_thresh, config=config)
    characters = []
    coordinates = []
    char_width = 0
    char_height = 0
    if id_type == ID_TYPE[2]:
        grad = 0.01
    else:
        grad = GRADIENT
    for rect in rects.splitlines():
        box = rect.split(' ')
        character = box[0]
        x1 = int(box[1])
        x2 = int(box[3])
        y1 = h - int(box[4])
        y2 = h - int(box[2])
        if abs(y2 - y1) < h * CHARACTER_HEIGHT_THRESH:
            continue
        center_x = int(0.5 * (x1 + x2))
        center_y = int(0.5 * (y1 + y2)) + grad * center_x
        char_width += int(x2 - x1)
        char_height += int(y2 - y1)
        characters.append(character)
        coordinates.append([center_x, center_y])

    char_width /= len(rects.splitlines())
    char_height /= len(rects.splitlines())

    if id_type == ID_TYPE[2]:
        char_height = char_height * 1.7

    y_sorted = sorted(zip(characters, coordinates), key=lambda k: k[1][1])
    y_sorted_chars, y_sorted_char_coordinates = bind_closest_element(bind_tuple=y_sorted,
                                                                     thresh_value=char_height, axis=1)
    print(y_sorted_chars)
    for word_list, word_coordinate_list in zip(y_sorted_chars, y_sorted_char_coordinates):

        if len(word_list) < 5:
            continue

        x_sorted = sorted(zip(word_list, word_coordinate_list), key=lambda j: j[1][0])
        x_info = ""
        for x_char, _ in x_sorted:
            if x_char == "~":
                continue
            x_info += x_char
        print(x_info)
        birth_day = estimate_birth_info(info=x_info, id_type=id_type)
        birth_day = date_filter(num_str=birth_day)
        if birth_day != "":
            break

    return birth_day


if __name__ == '__main__':
    frame_path = ""
    frame = cv2.imread(frame_path)
    date_info = extract_birthday(img=frame, id_type=ID_TYPE[0], base_line=200)
    print(date_info)
