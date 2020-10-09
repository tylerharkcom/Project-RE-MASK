import os
from os import path
import cv2
from PIL import Image
import csv
import moviepy.editor

x = 516
y = 1178

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
                cv2.imwrite("frame_%d_%d_%d.jpg" % (minute, second, count), image)
                framecount += 1
        else:
            cv2.imwrite("frame_%d_%d_%d.jpg" % (minute, second, count), image)
            framecount += 1

        count += 1

    return framecount

def getPixelColor(image_name, x, y):
    # Create a PIL.Image object
    try:
        image = Image.open(image_name)
    except IOError:
        return None
    # Convert to RGB colorspace
    image_rgb = image.convert("RGB")

    # # Coordinates begin on top left of the image
    # print('Enter X coordinate:')
    # x = input()
    #
    # print('Enter Y coordinate:')
    # y = input()

    # Get color from (x, y) coordinates
    rgb_value = image_rgb.getpixel((int(x),int(y)))

    return rgb_value

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

def convertTime(secs):
    mins = secs // 60
    secs %= 60
    return mins, secs

def getData(video_length):
    minute = 0
    second = 0
    count = 1
    minutes, seconds = convertTime(video_length)
    with open("data.csv", 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow(['Baseline', 'RGB', 'Color', getPixelColor("frame_0_0_1.jpg", 573, 1241)])
        filewriter.writerow(['Minute', 'Second', 'Frame', 'RGB'])
        for minute in range(0, (minutes + 1)):
            for second in range(0, 60):
                for count in range (1, 31):
                    frame = "frame_%d_%d_%d.jpg" % (minute, second, count)
                    rgb = getPixelColor(frame, x, y)
                    if (rgb == None):
                        break
                    filewriter.writerow([minute, second, count, rgb])
    deleteFrames()

def startProg():

    # Get file name to be analyzed
    print("Please enter the filename of the .mp4 file to be analyzed: ")
    filename = str(input())

    # If the file cannot be found, try to get a new filename
    while path.exists(filename) != True:
        print("Error: File not found. Please check the filename and try again.")
        print("Please enter the filename of the .mp4 file to be analyzed: ")
        filename = str(input())

    video = moviepy.editor.VideoFileClip(filename)
    video_length = int(video.duration)

    print("Would you like to get all data of the file, or a filtered set of data?")
    print("Enter '1' for all data, or enter '2' for filtered data: ")
    choice = int(input())

    # print("Please enter a name for the final data file: ")
    # data_filename = str(input())
    # while path.exists(data_filename) == True:
    #     print("Error: Filename already exists. Please try a different name.")
    #     print("Please enter a name for the final data file: ")
    #     data_filename = str(input())

    while choice != 1 and choice != 2:
        print("Error: Invalid selection.")
        print("Would you like to get all data of the file, or a filtered set of data?")
        print("Enter '1' for all data, or enter '2' for filtered data: ")
        choice = int(input())

    print("Fetching frames. This may take some time, please wait...")

    if choice == 1:
        count = getTheFrames(filename, choice)
        print("Successfully exported %d frames." % count)
    else:
        count = getTheFrames(filename, choice)
        print("Successfully exported %d frames." % count)

    print("Processing RGB values for each frame. This may take some time, please be patient...")
    # Get rgb data for the selected x,y coordinate over the generated frames
    # Deletes all frame files once the data is captured
    getData(video_length)

startProg()
