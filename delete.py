import os
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
