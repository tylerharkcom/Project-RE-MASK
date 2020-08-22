import numpy as np
import cv2, sys

# Width/Height constants are used only for debugging. Constants define the 
# output window which will be displayed to the user.
FINAL_WIDTH = 500
FINAL_HEIGHT = 500

# Number of samples which will occur during dosimeter evaluation.
NUM_SAMPLES = 5

# Offset constants define where the region enclosed by a countour sampled with
# respect to the center of the image.
X_OFF = 10
Y_OFF = 10

# RGB constants define the range of RBG values the dosimeter lies between.
# These values will likely need some additional tweaking as we evaluate more videos.
R_LOWER = 140
R_UPPER = 180
G_LOWER = 70
G_UPPER = 180
B_LOWER = 45
B_UPPER = 150

# Depending on where the dosimeter is within the image, the minimum and maximum size
# may vary. The MIN and MAX constants define the minimum and maximum region the dosimeter 
# may be, for example, the dosimeter must be between 300 and 350 pixels, squared. (By default)
DOS_MIN_SIZE = 300
DOS_MAX_SIZE = 350

# Boolean function which returns whether or not the region enclosing a contour is
# the dosimeter. The function will sample several points inside of the region to 
# verify the sample points are within the expected dosimeter values; if so the dosimeter is there.

# WARNING:
# There may be sampling issues, which will cause an array out of bounds exception, as the contours get smaller.
# If a region is 10x10 pixels, it will be impossible to probe the RGB values. However, it is incredibly
# unlikely the dosimeter will not be found. Since the size of the dosimeter is checked first, this error
# should not occur. More testing will be required to determine reliability.
def isDosimeter(ROI):

    # Find the center of the image
    mid_x = ROI.shape[0] // 2
    mid_y = ROI.shape[1] // 2
    average = 0

    # One sample will occur in each quadrant, as well as the center of the image.
    x_cord = [mid_x, mid_x + X_OFF, mid_x + X_OFF, mid_x - X_OFF, mid_x - X_OFF]
    y_cord = [mid_y, mid_y + Y_OFF, mid_y - Y_OFF, mid_y + Y_OFF, mid_y - Y_OFF]

    for i in range(NUM_SAMPLES):
        b,g,r = ROI[x_cord[i], y_cord[i]] # Extract r,b,g values
        # print(r, g, b)

        # There is likely a better implementation, but this works for now.
        if (R_LOWER < r < R_UPPER):
            if (G_LOWER < g < G_UPPER):
                if (B_LOWER < b < B_UPPER):
                    average += 1
    
    # If half of the samples are valid, the region is likely the dosimeter.
    if (average > (NUM_SAMPLES // 2)):
        return True

    return False

# Boolean function which determines if a region is approximately the size of the dosimeter.
# The expected size will be within the DOS_MIN_SIZE and DOS_MAX_SIZE squared.
def in_size(ROI):
    width, height,_ = ROI.shape # Extract region parameters
    if (DOS_MIN_SIZE <= width <= DOS_MAX_SIZE):
        if (DOS_MIN_SIZE <= height <= DOS_MAX_SIZE):
            return True
    return False

# Usage: python3 Process_Frame.py <insert filename>
# The code below has been designed to be used within a script, hence the abstraction.
def main(file_path):
    # Read the frame into memory.
    frame = cv2.imread(file_path, cv2.IMREAD_COLOR)

    # Verify frame has been correctly read.
    if (frame is None):
        print("Invalid file path for sample image.")
        sys.exit(0)

    # Convert the original image into grayscale, and apply OTSU filtering to it.
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(frame_gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # Find the contours within the image.
    contours,_ = cv2.findContours(threshold, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    # Sort the contours based on area; returns a list with descending contour areas.
    # The dosimeter is likely within the first 5, potentially 10, contours.
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Loop through all the contours to find the dosimeter.
    found_contour = False
    for c in contours:
        # Extract the region enclosing a specific contour.
        x,y,w,h = cv2.boundingRect(c)
        ROI = frame[y : y + h, x : x + w]

        if in_size(ROI) and isDosimeter(ROI):
            found_contour = True
            break

    # # Display the cropped region to the user. Uncomment this block to display
    # # the dosimeter region to the user.
    # cv2.namedWindow("Final", cv2.WINDOW_AUTOSIZE)
    # threshold = cv2.resize(threshold, (FINAL_WIDTH, FINAL_HEIGHT))
    # cv2.imshow("Final", threshold)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # Print an error to the console if no dosimeter is found.
    if (found_contour == False):
        print("No dosimeter found in frame: " + sys.argv[1])
        sys.exit(0)

    cv2.imwrite("Cropped_Dosimeter.jpg", ROI)

if __name__=="__main__":
    main(sys.argv[1])