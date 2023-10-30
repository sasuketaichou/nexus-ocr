import inspect
import cv2
import fitz
import numpy as np
from fuzzywuzzy import process
from datetime import datetime
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="en")


def correct_month(input_month):
    # List of correct month names
    correct_months = [
        "Jan",
        "Feb",
        "Mac",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    # Find the nearest correct month
    best_match, score = process.extractOne(input_month, correct_months)

    if score >= 60:

        if best_match == 'Mac':
            best_match = 'Mar'
        return best_match
    else:
        # If the score is below the threshold, return the original input
        return input_month


def pdf2image(pdf_path, page_number=0):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)
    img = page.get_pixmap().tobytes("png")
    image = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)

    # Remove the alpha channel if present
    image = image[:, :, :3]

    return image


def extract_coord(templates, filename, key, file_dct, shape):
    h, w = shape

    if filename not in [value for value in file_dct]:
        print(filename, "is missing!!")

        return -1, -1, -1, -1

    try:
        coord = templates[file_dct[filename]][key]["bounding_box_percent"]
        px1, py1, px2, py2 = coord["x1"], coord["y1"], coord["x2"], coord["y2"]

        x1 = px1 * w / 100
        y1 = py1 * h / 100
        x2 = px2 * w / 100
        y2 = py2 * h / 100

    except KeyError as e:
        print(key, "is missing!!")

        x1, y1, x2, y2 = -1, -1, -1, -1

    return int(x1), int(y1), int(x2), int(y2)


def padded(image):
    # Define the desired size of padding
    scale = 2
    top_padding = 0 * scale
    bottom_padding = 20 * scale
    left_padding = 0 * scale
    right_padding = 20 * scale

    # Add padding to the image
    padded_image = cv2.copyMakeBorder(
        image,
        top_padding,
        bottom_padding,
        left_padding,
        right_padding,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )

    return padded_image


def process_gaussian_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (99, 99), 0)
    divided = cv2.divide(gray, blur, scale=255)

    return padded(divided)


def process_median_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 51)
    divided = np.ma.divide(gray, blur).data
    normed = np.uint8(255 * divided / divided.max())

    return padded(normed)


def execute(filename, templates, file_dct, debug=False):
    filetype = filename.split(".")[-1]

    if filetype in ["jpg", "jpeg", "JPG"]:
        image = cv2.imread(filename)

    elif filetype == "pdf":
        image = pdf2image(filename)

    output = {}
    for key in ["address", "name", "date"]:
        x1, y1, x2, y2 = extract_coord(
            templates, filename, key, file_dct, image.shape[:2]
        )

        ## flag missing key
        if x1 == -1:
            continue

        if debug:
            print(x1, y1, x2, y2)

        txt = extract_text(image[y1:y2, x1:x2], debug)

        if key == "date":
            # Extract day, month, and year from the OCR result
            day, month, year = txt.split()

            corrected_month = correct_month(month)
            corrected_date_string = f"{day} {corrected_month} {year}"

            # Convert the corrected date string to a datetime object
            input_date = datetime.strptime(corrected_date_string, "%d %b %Y")
            txt = input_date.strftime('%y%m%d')

            if debug:
                print('date', txt)


        output[key] = txt

    return output


def extract_text(image, debug):
    all_functions = [
        func
        for name, func in globals().items()
        if inspect.isfunction(func) and name.startswith("process")
    ]

    res_txts = []
    res_scores = []

    # Sorting
    for func in all_functions:
        result = ocr.ocr(func(image))

        ys = []
        txts = []
        scores = []

        for lines in result:
            for line in lines:
                y_pos = line[0][0][-1]
                txt, score = line[-1]

                ys.append(y_pos)
                txts.append(txt)
                scores.append(score)

        combined = list(zip(ys, txts, scores))

        # Sort the list of tuples based on the first element (y position)
        sorted_combined = sorted(combined, key=lambda x: x[0])
        sorted_ys, sorted_txts, sorted_scores = zip(*sorted_combined)

        res_txts.append(sorted_txts)
        res_scores.append(sorted_scores)

    # Voting
    if debug:
        print("result text", res_txts)
        print("result score", res_scores)
    selected_strings = []

    for i in range(len(res_scores[0])):
        # Compare scores for each index and select the string with the maximum score
        max_score_index = max(range(len(res_scores)), key=lambda j: res_scores[j][i])
        selected_strings.append(res_txts[max_score_index][i])

    result = "\n".join(selected_strings)

    return result
