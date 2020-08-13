import numpy as np
import sys
import cv2

FINAL_WIDTH = 500
FINAL_HEIGHT = 500

# To whomever is using this code, typical usage will be python3 Process_Frame.py <File_Name>
# The code below has been designed to be used within a script, hence the abstraction.
def main(file_path):
    # Read the frame into memory.
    frame = cv2.imread(file_path, cv2.IMREAD_COLOR)

    # Verify frame has been correctly read
    if (frame is None):
        print("Invalid file path for sample image.")
        sys.exit(0)

    # Convert the original image into grayscale, and apply OTSU filtering to it.
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(frame_gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # Find the contours within the image.
    contours,_ = cv2.findContours(threshold, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    # Sort the contours based on area; returns a list with descending contour areas.
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # The first contour will be the entire image, the next largest will isolate the dosimeter.
    cnt = contours[1]

    # Extract the dosimeter from the original image.
    x,y,w,h = cv2.boundingRect(cnt)
    ROI = frame[y : y + h, x : x + w]

    # # Display the cropped region to the user. Uncomment this block to display
    # # the dosimeter region to the user.
    # cv2.namedWindow("Final", cv2.WINDOW_AUTOSIZE)
    # ROI = cv2.resize(ROI, (FINAL_WIDTH, FINAL_HEIGHT))
    # cv2.imshow("Final", ROI)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    cv2.imwrite("Cropped_Dosimeter.jpg", ROI)

if __name__=="__main__":
    main(sys.argv[1])