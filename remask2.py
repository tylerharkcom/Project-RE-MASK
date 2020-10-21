from PIL import Image # Opening and saving images
import csv # Writing to CSV file
import cv2 # Computer vision library
import moviepy.editor # Video functions (length, etc.)
import os # (Deleting files)
from os import path # (Filepath helper)
import numpy as np # ???
import sys # ???

# Global variable to define the fps of the video file to be used
fps = 30

# Define points to be used to determine baseline color. See README for a diagram and more info.
baseline = [(43, 208), (60, 249), (90, 281), (134, 300), (211, 301), (255, 281), (282, 249), (298, 207)]

# Define points to be sampled in the center circle of the dosimeter for testing UV exposure levels.
testing = [(147, 110), (192, 110), (227, 148), (227, 190), (192, 227), (147, 227), (115, 190), (115, 148)]

video_name = ""

NUM_SAMPLES = 5

X_OFF = 10
Y_OFF = 10

R_LOWER = 140
R_UPPER = 180
G_LOWER = 70
G_UPPER = 180
B_LOWER = 45
B_UPPER = 150

FINAL_WIDTH = 500
FINAL_HEIGHT = 500

TOLERANCE = 15
DOS_MIN_SIZE = 300
DOS_MIN_SIZE = 350

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

# To whomever is using this code, typical usage will be python3 Process_Frame.py <File_Name>
# The code below has been designed to be used within a script, hence the abstraction.
def processFrames(frameName, m, s, c):
    # Read the frame into memory.
    frame = cv2.imread(frameName, cv2.IMREAD_COLOR)

    # Verify frame has been correctly read
    if (frame is None):
        print("Invalid file path for sample image.")
        # TO DO: Potentially add error handling.
        return

    # Convert the original image into grayscale, and apply OTSU filtering to it.
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(frame_gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # Find the contours within the image.
    contours,_ = cv2.findContours(threshold, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    # Sort the contours based on area; returns a list with descending contour areas.
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
    try:
        os.remove("frameName")
    except:
        pass

    cv2.imwrite("frame_%d_%d_%d.jpg" % (m, s, c), ROI)

# Essentially call the process frame on a singular image.
def initDosSize(first_frame):
    processFrames(frameName, m, s, c)

def getPixelColor(image_name, x, y):
    # Create a PIL.Image object
    try:
        image = Image.open(image_name)
    except IOError:
        return None

    # Convert to RGB colorspace
    image_rgb = image.convert("RGB")

    # Get color from (x, y) coordinates
    r, g, b = image_rgb.getpixel((int(x),int(y)))

    return r, g, b

# TODO: Figure out how to standardize the folder path so that it's not hardcoded here...
def deleteFrames():
    #providing the path of the folder
    #r = raw string literal
    folder_path = ('/Users/tylerharkcom/Desktop/rgb')
    #using listdir() method to list the files of the folder
    test = os.listdir(folder_path)
    #taking a loop to remove all the images
    #using ".png" extension to remove only png images
    #using os.remove() method to remove the files
    for images in test:
        if images.endswith(".jpg"):
            os.remove(os.path.join(folder_path, images))

def getData(video_length, filter, filename):
    minute = 0
    second = 0
    count = 1
    minutes, seconds = convertTime(video_length)
    data_file = filename + ".csv"
    with open(data_file, 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        r_b, g_b, b_b = sampleColor("frame_0_0_1.jpg", baseline)
        filewriter.writerow(['Baseline', 'RGB', 'Color', r_b, g_b, b_b])
        filewriter.writerow(['Minute', 'Second', 'Frame', 'R', 'G', 'B'])
        if filter:
            for minute in range(0, (minutes + 1)):
                for second in range(0, 60, 10):
                    for count in range (1, 31):
                        frame = "frame_%d_%d_%d.jpg" % (minute, second, count)
                        if path.exists(frame) != True:
                            break
                        r, g, b = sampleColor(frame, testing)
                        filewriter.writerow([minute, second, count, r, g, b])
        else:
            for minute in range(0, (minutes + 1)):
                for second in range(0, 60):
                    for count in range (1, 31):
                        frame = "frame_%d_%d_%d.jpg" % (minute, second, count)
                        if path.exists(frame) != True:
                            break
                        r, g, b = sampleColor(frame, testing)
                        filewriter.writerow([minute, second, count, r, g, b])
    deleteFrames()

def convertTime(secs):
    mins = secs // 60
    secs %= 60
    return mins, secs

def average(list):
    return sum(list)/len(list)

def sampleColor(image_name, values):
    # Create a PIL.Image object
    try:
        image = Image.open(image_name)
    except IOError:
        # print("Error in sampleColor(): Image not found.")
        return None
    # Convert to RGB colorspace
    image_rgb = image.convert("RGB")

    red = []
    green = []
    blue = []

    for x, y in values:
        r, g, b = image_rgb.getpixel((int(x),int(y)))
        red.append(r)
        green.append(g)
        blue.append(b)

    red_val = round(average(red))
    green_val = round(average(green))
    blue_val = round(average(blue))

    return red_val, green_val, blue_val

# Function to extract frames
# "filename" is a string that contains the name of the video file to be processed
# "filter" is a boolean that denotes whether to filter frames or not
# When filter = 1, only the 30 frames from each 10th second are captured (30 frames @ 0, 10, 20 30, etc.)
# When filter = 0, all frames are captured
def getTheFrames(filename, filter):
    # Path to video file
    video = cv2.VideoCapture(filename)

    # Used as counter variables
    count = 1
    second = 0
    minute = 0
    framecount = 0

    # checks whether frames were extracted
    success = 1

    while success:
        # vidObj object calls read
        # function extract frames
        success, image = video.read()

        # Set bounds on frames between 1 and 30, wrapping back to 1
        if (count > 30):
            second += 1
            count = 1

        # Set bounds on seconds from 0 to 59, wrapping back to 0
        # Ex: 0:59:28...0:59:29...0:59:30...1:00:01...1:00:02...
        if (second == 60):
            minute += 1
            second = 0

        if filter:
            if second % 10 == 0:
                frame = ("frame_%d_%d_%d.jpg" % (minute, second, count))
                cv2.imwrite(frame, image)
                processFrames(frame, minute, second, count)
                framecount += 1
        else:
            frame = ("frame_%d_%d_%d.jpg" % (minute, second, count))
            cv2.imwrite(frame, image)
            processFrames(frame, minute, second, count)
            framecount += 1

        count += 1

    return framecount

def main():
    # Get file name to be analyzed
    print("Please enter the filename of the .mp4 file to be analyzed: ")
    filename = str(input())

    # If the file cannot be found, try to get a new filename
    while path.exists(filename) != True:
        print("Error: File not found. Please check the filename and try again.")
        print("Please enter the filename of the .mp4 file to be analyzed: ")
        filename = str(input())

    # rsplit() returns an array, split on the delimiter passed in
    # Here, it splits the ".mp4" off of the video file
    # (Ex: "test.123.mp4" becomes ["test.123", "mp4"])
    vid_name = filename.rsplit('.',1)

    # Get video length in minutes/seconds for frame iteration purposes
    video = moviepy.editor.VideoFileClip(filename)
    video_length = int(video.duration)
    minutes, seconds = convertTime(video_length)

    # Extract the frames from the video file
    print("Would you like to get all data of the file, or a filtered set of data?")
    print("WARNING: Selecting all data will yield a large amount of data.")
    print("Enter '1' for all data, or enter '2' for filtered data: ")
    choice = int(input())

    # Cycles until a valid option is passed by the user
    while choice != 1 and choice != 2:
        print("Error: Invalid selection.")
        print("Would you like to get all data of the file, or a filtered set of data?")
        print("WARNING: Selecting all data will yield a large amount of data.")
        print("Enter '1' for all data, or enter '2' for filtered data: ")
        choice = int(input())

    # Call getTheFrames to parse the video, called "filename", into individual frames
    print("Fetching frames. This may take some time, please wait...")
    count = getTheFrames(filename, choice)
    print("Successfully exported %d frames." % count)

    print("Processing RGB values for each frame. This may take some time, please wait...")

    # Get rgb data for the selected x,y coordinate over the generated frames
    # Deletes all frame files once the data is captured
    # vid_name[0] passes the full name of the video file without the ".mp4"
    # (Ex: "test.123.mp4" becomes "test.123")
    getData(video_length, choice, vid_name[0])


if __name__ == "__main__":
    main()
