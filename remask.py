from PIL import Image # Opening and saving images
import csv # Writing to CSV file
import cv2 # Computer vision library
import moviepy.editor # Video functions (length, etc.)
import os # (Deleting files)
from os import path # (Filepath helper)
import numpy as np
import sys
import math

# Global variable to define the fps of the video file to be used
fps = 30

# Defines the number of seconds until RGB values are captured.
TIME_OFFSET = 30 

# Define points to be sampled in the center circle of the dosimeter for testing UV exposure levels.
# testing = [(147, 110), (192, 110), (227, 148), (227, 190), (192, 227), (147, 227), (115, 190), (115, 148)]
testing = []
baseline = []
base_rgb = []

# Define the size ratio of the concentric circles on the dosimeter.
inner_ratio = 0.56
outer_ratio = 0.44

vid_name = ""
video_length = 0
# Defines the number of samples which will be done when searching for the dosimeter.
NUM_SAMPLES = 5

# Horizontal and vertical offsets from the center of a region enclosed by a contour.
X_OFF = 10
Y_OFF = 10

# RGB intervals used to filter the dosimeter from the image.
R_LOWER = 55
R_UPPER = 200
G_LOWER = 40
G_UPPER = 185
B_LOWER = 25
B_UPPER = 250

# Defines the pixel tolerance when determining the dosimeter size.
# Once the dosimeter size is determined, the tolerance prevents random issues from losing the dosimeter.
TOLERANCE = 25

# Default values for the expected dosimeter size. If the dosimeter is not detected, modify these values.
DOS_SIZE_SET = False
DOS_MIN_SIZE = 100
DOS_MAX_SIZE = 500
DOS_WIDTH = 0
DOS_HEIGHT = 0

# Boolean function which determines whether or not the dosimeter is enclosed in a region.
# Treating the center of the region of interest, ROI, as the the origin, The X and Y offsets
# are used to probe the RGB values of the center and the four quadrants of the image. 
# On average, more than half of the samples will be valid and within the yellow region. 
# Potention TO DO: Change the RGB filtering to only central values; more accurate RBG range.
def isDosimeter(ROI):

    # Find the center of the image.
    mid_x = ROI.shape[0] // 2
    mid_y = ROI.shape[1] // 2
    average = 0

    # One sample will occur in each quadrant, as well as the center of the image.
    x_cord = [mid_x, mid_x + X_OFF, mid_x + X_OFF, mid_x - X_OFF, mid_x - X_OFF]
    y_cord = [mid_y, mid_y + Y_OFF, mid_y - Y_OFF, mid_y + Y_OFF, mid_y - Y_OFF]

    for i in range(NUM_SAMPLES):
        
        # Try-except block is necessary to prevent array boundary exceptions
        try:
            b,g,r = ROI[x_cord[i], y_cord[i]] # Extract r,b,g values
            # print(r, g, b) 
        except:
            return False

        # There is likely a better implementation, but this works for checking each RBG pair
        if (R_LOWER < r < R_UPPER):
            if (G_LOWER < g < G_UPPER):
                if (B_LOWER < b < B_UPPER):
                    average += 1

    # If over half of the samples are valid, the region is likely the dosimeter.
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

# Image processing function which crops each individual frame into purely the dosimeter.
def processFrames(frameName, write):
    # Read the frame into memory.
    frame = cv2.imread(frameName, cv2.IMREAD_COLOR)

    # Verify frame has been correctly read
    if (frame is None):
        print("Invalid file path for sample image.")
        # TO DO: Potentially add error handling.
        return False

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

            global DOS_SIZE_SET, DOS_MIN_SIZE, DOS_MAX_SIZE, DOS_HEIGHT, DOS_WIDTH
            if DOS_SIZE_SET == False:
                print("Set the dosimeter!")
                width, height,_ = ROI.shape
                DOS_MIN_SIZE = min(width, height) - TOLERANCE
                DOS_MAX_SIZE = max(width, height) + TOLERANCE
                DOS_SIZE_SET = True
                cv2.imwrite("Origin_cropped.jpg", ROI)
            
            if DOS_WIDTH == 0 and DOS_HEIGHT == 0:
                DOS_WIDTH, DOS_HEIGHT,_ = ROI.shape

            break

    # Terminate program if contour is not found.
    # Feel free to comment out to prevent terminal spam.
    if found_contour == False:
        print("ERROR: Contour was not found in {}".format(frameName))
        # print("Consider modifying of RBG constants or Dosimeter size constants at top of file.")
        # print("Current frame will be skipped.\n")
        return False

    if (write == True):
        cv2.imwrite(frameName, ROI)
    
    return True

# Dosimeter size parameters initialization function.
# Depending on how the video is shot and where the dosimeter is within it, the number of pixels 
# describing the size of the dosimeter may vary. This function will process the first valid frame
# of the video and update the size constants to the current value of the dosimeter.
def initDosSize(filename):
    try:
        video = cv2.VideoCapture(filename)
    except:
        print("ERROR: Unable to open video {}".format(filename))
        print("Terminating program...")
        sys.exit(0)

    # A simple way to skip x seconds into a video is by reading the first
    # FPS * TIME_OFFSET images and ignoring them.
    frames_skipped = fps * TIME_OFFSET
    current_frame = 0

    # Offset the video by TIME_OFFSET seconds.
    while current_frame < frames_skipped:
        _,_ = video.read() # Ignore the current image
        current_frame += 1 

    # Capture the first "valid" frame of the video.
    success,origin_frame = video.read()
    cv2.imwrite("origin_frame.jpg", origin_frame)

    processFrames("origin_frame.jpg", True)

    if (DOS_SIZE_SET == True):
        return True

    return False

def initSamples():
    # Assumes the sizes are valid, since the initDosSize function will cause program to terminate
    # if the dosimeter was not found prior.
    
    # Testing is a list of tuples corresponding to all the points RGB values will be sampled.
    global testing, baseline
    tolerance = math.floor((DOS_WIDTH + DOS_HEIGHT) / 20) # Average, w and h and divide by 10.
    w_center = DOS_WIDTH // 2
    h_center = DOS_HEIGHT // 2

    inner_diam = inner_ratio * (DOS_WIDTH + DOS_HEIGHT) // 4
    outer_width = outer_ratio * (DOS_WIDTH + DOS_HEIGHT) // 8
    outer_offset = DOS_WIDTH - outer_width

    testing_x_pos =  [w_center, w_center, w_center + inner_diam - tolerance, w_center, w_center - inner_diam + tolerance]
    testing_y_pos = [h_center, h_center - inner_diam + tolerance, h_center, h_center + inner_diam - tolerance, h_center]

    baseline_x_pos = [outer_width, outer_width + tolerance, outer_width + (2 * tolerance), outer_width + (3 * tolerance), 
    outer_offset, outer_offset - tolerance, outer_offset - (2 * tolerance), outer_offset - (3 * tolerance)]
    
    baseline_y_pos = [h_center + tolerance, h_center + (2 * tolerance), h_center + (3 * tolerance), h_center + (4 * tolerance),
    h_center + tolerance, h_center + (2 * tolerance), h_center + (3 * tolerance), h_center + (4 * tolerance)]

    # List includes the sample points for both the inner circle and outer ring.
    # x_pos =  [w_center, w_center, w_center + inner_diam - tolerance, w_center, w_center - inner_diam + tolerance,
    # outer_width, outer_width + tolerance, outer_width + (2 * tolerance), outer_width + (3 * tolerance), 
    # outer_offset, outer_offset - tolerance, outer_offset - (2 * tolerance), outer_offset - (3 * tolerance)]
    
    # y_pos = [h_center, h_center - inner_diam + tolerance, h_center, h_center + inner_diam - tolerance, h_center,
    # h_center + tolerance, h_center + (2 * tolerance), h_center + (3 * tolerance), h_center + (4 * tolerance),
    # h_center + tolerance, h_center + (2 * tolerance), h_center + (3 * tolerance), h_center + (4 * tolerance)]

    test_samples = len(testing_y_pos)
    baseline_samples = len(baseline_x_pos)

    print("(X,Y) points which will sample the dosimeter.")
    for i in range(test_samples):
        testing.append((testing_x_pos[i], testing_y_pos[i]))
        print(testing[i])

    print()
    
    print ("(X, Y) points which will sample the baseline value of the dosimeter")
    for i in range(baseline_samples):
        baseline.append((baseline_x_pos[i], baseline_y_pos[i]))
        print(baseline[i])
    return

def getPixelColor(image_name, x, y):
    # Create a PIL.Image object
    try:
        image = Image.open(image_name)
    except IOError:
        return None

    # Convert to RGB colorspace
    image_rgb = image.convert("RGB")

    # Get color from (x, y) coordinates
    w = int(x)
    h = int(y)
    if (w < 0 or w >= DOS_WIDTH):
        return -1, -1, -1
    if (h < 0 or h >= DOS_HEIGHT):
        return -1, -1, -1

    r, g, b = image_rgb.getpixel((int(x),int(y)))
    return 

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
        print("Error in sampleColor(): Image: {} was not found.".format(image_name))
        return None

    # Convert to RGB colorspace
    image_rgb = image.convert("RGB")

    red = []
    green = []
    blue = []

    # Loop over the predetermined sample points and append rgb values to list.
    for x, y in values:
        r, g, b = image_rgb.getpixel((int(x),int(y)))
        red.append(r)
        green.append(g)
        blue.append(b)

    # Average the rgb values for each sample point.
    red_val = round(average(red))
    green_val = round(average(green))
    blue_val = round(average(blue))

    return red_val, green_val, blue_val

# Function to extract frames
# "filename" is a string that contains the name of the video file to be processed
# "filter" is a boolean that denotes whether to filter frames or not
# When filter = 1, only the frames from each 10th second are captured (Ex 30 frames @ 0, 10, 20 30, etc.)
# When filter = 0, all frames are captured
def getTheFrames(filename, filter):
    # Path to video file
    video = cv2.VideoCapture(filename)

    # Used as counter variables
    count = 1
    second = 0
    minute = 0
    framecount = 0
    frame_offset= fps* TIME_OFFSET

    # success fiend shows whether a frame was correctly extracted
    success = 1

    # Create a local directory storing all of the frames for a given test.
    try:
        os.mkdir(vid_name + "_results")
    except:
        pass # If the file exists, its fine.

    # Change to the created directory.
    os.chdir(vid_name + "_results")
    
    # Open the csv file.
    data_file = vid_name + ".csv"

    # Create/open the csv file for writing.
    with open(data_file, "w") as csvfile:
        file_writer = csv.writer(csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        file_writer.writerow(["Baseline RGB values:", "R", "G", "B"])
        file_writer.writerow(["", base_rgb[0], base_rgb[1], base_rgb[2]])
        file_writer.writerow(["Minute", "Second", "Frame", "R", "G", "B"])
        
        while success:
            # vidObj object calls read function to extract a singular frame
            success, image = video.read()

            # Set bounds on frames between 1 and 30, wrapping back to 1
            if (count > fps):
                second += 1
                count = 1

            # Set bounds on seconds from 0 to 59, wrapping back to 0
            # Ex: 0:59:28...0:59:29...0:59:30...1:00:01...1:00:02...
            if (second == 60):
                minute += 1
                print("{} minute(s) processed.".format(minute))
                second = 0

            # Skip the first thirty seconds of video.
            if (framecount < frame_offset):
                framecount += 1
                count += 1
                continue

            frame = ("frame_%d_%d_%d.jpg" % (minute, second, count))
            if filter:
                if second % 10 == 0:
                    cv2.imwrite(frame, image)
                    framecount += 1

                    if (processFrames(frame, True) == False):
                        file_writer.writerow([minute, second, count, -1, -1, -1])
                        continue

                    r, g, b = sampleColor(frame,testing)
                    file_writer.writerow([minute, second, count, r, g, b])
                    
            else:
                cv2.imwrite(frame, image)
                framecount += 1

                if (processFrames(frame, True) == False):
                        file_writer.writerow([minute, second, count, -1, -1, -1])
                        continue

                r, g, b = sampleColor(frame,testing)
                file_writer.writerow([minute, second, count, r, g, b])

            count += 1

            # Uncomment to remove the cropped images from being saved.
            # try:
            #     os.remove(str(frame))
            # except:
            #     pass
            

    # return to folder above.
    os.chdir("../")
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
    global vid_name, video_length
    vid_name = filename.rsplit('.',1)[0]
    
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

    # Initialize the dosimeter size for the given video.
    if (initDosSize(filename) == False):
        print("Was unable to determine dosimeter from provided video. Please modify the rgb or size thresholds based on the origin image")
        print("Terminating the program...")
        sys.exit(1)

    # Initialize the sample points based off the size of the dosimeter.
    initSamples()

    # Calculate the baseline rgb values for the origin frame.
    global base_rgb
    base_r, base_g, base_b = sampleColor("Origin_cropped.jpg", baseline)
    base_rgb = [base_r, base_g, base_b]

    print(base_rgb)

    # Call getTheFrames to parse the video, called "filename", into individual frames
    print("Fetching frames. This may take some time, please wait...")

    count = getTheFrames(filename, choice)
    print("Successfully exported %d frames." % count)

if __name__ == "__main__":
    main()