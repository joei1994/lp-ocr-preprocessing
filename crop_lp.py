import argparse 
import os
import utils
import cv2
import xml.etree.ElementTree as ET
import imgaug as ia
import imgaug.augmenters as iaa
from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage


from pdb import set_trace

ap = argparse.ArgumentParser()
ap.add_argument("-dn", "--dataset_name", type=str, required=True, help='Dataset\'s name')
ap.add_argument("--width", type=int, help="Width of cropped plate")
ap.add_argument("--height", type=int, help="Height of cropped plate")
args = vars(ap.parse_args())

PLATE = 'plate'
PLATE_PADDING = 4

def saveImageAndXml(imageName, image, xml, outputDir):
    cv2.imwrite(os.path.join(outputDir, imageName + '.jpg'), image)

    with open(os.path.join(outputDir, imageName + '.xml'), 'w', encoding='utf-8') as fid:
        fid.write(xml)

def bboxToInt(bndbox):
    xmin, ymin, xmax, ymax = bndbox.find('xmin').text, bndbox.find('ymin').text, bndbox.find('xmax').text, bndbox.find('ymax').text
    xmin, ymin, xmax, ymax = int(float(xmin)), int(float(ymin)), int(float(xmax)), int(float(ymax))
    return xmin, ymin, xmax, ymax

def getCharObjects(xmlFilePath):
    charObjects = []
    annotation = ET.parse(xmlFilePath)
    for obj in annotation.findall('object'):
        objectName = obj.find('name').text
        
        if len(objectName) == 1:
            if ord(objectName) in range(ord('ก'), ord('ฮ') + 1) or ord(objectName) in range(ord('0'), ord('9') + 1):
                xmin, ymin, xmax, ymax = bboxToInt(obj.find('bndbox'))
                charObject = {
                    'name' : objectName,
                    'xmin' : xmin,
                    'ymin' : ymin,
                    'xmax' : xmax,
                    'ymax' : ymax
                }
                charObjects.append(charObject)
    return charObjects

def getPlateObject(xmlFilePath):
    annotation = ET.parse(xmlFilePath).getroot()
    plateObjects = [obj for obj in annotation.findall('object') if obj.find('name').text == PLATE]

    if len(plateObjects) > 0:
        xmin, ymin, xmax, ymax = bboxToInt(plateObjects[0].find('bndbox'))
        return {
            'name' : PLATE,
            'xmin' : xmin,
            'ymin' : ymin,
            'xmax' : xmax,
            'ymax' : ymax
        }

    return None

def calculateNewCharObjects(charObjects, plateObject, padding):
    newCharObjects = []
    for charObject in charObjects:
        newXmin = charObject['xmin'] - plateObject['xmin'] + padding
        newYmin = charObject['ymin'] - plateObject['ymin'] + padding
        newXmax = charObject['xmax'] - plateObject['xmin'] + padding
        newYmax = charObject['ymax'] - plateObject['ymin'] + padding
        newCharObjects.append({
            'name' : charObject['name'],
            'xmin' : newXmin,
            'ymin' : newYmin,
            'xmax' : newXmax,
            'ymax' : newYmax  
        })
    return newCharObjects

def drawBbox(plateImage, charObjects):
    for charObject in charObjects:
        pt1 = charObject['xmin'], charObject['ymin']
        pt2 = charObject['xmax'], charObject['ymax']
        
        cv2.rectangle(plateImage, pt1, pt2, (255,0,0), 1)

def createPlateXml(plateImage, newCharObjects, imageFilePath):
    imageFilePath.replace('\\', '/')
    folder = imageFilePath.split('/')[-2]
    fileName = utils.getFileName(imageFilePath)

    xml = "<annotation>\n"
    #xml = xml + "<folder>" + folder + "</folder>\n"
    xml = xml + "<filename>" + fileName + "</filename>\n"
    #xml = xml + "<path>" + imageFilePath + "</path>\n"
    xml = xml + "<size>\n" 
    xml = xml + "\t<width>" + str(plateImage.shape[1]) + "</width>\n"
    xml = xml + "\t<height>" + str(plateImage.shape[0]) + "</height>\n"
    xml = xml + "\t<depth>" + "Unspecified" + "</depth>\n"
    xml = xml + "</size>\n"
    xml = xml + "<segmented>" + "Unspecified" + "</segmented>\n"

    for charObject in newCharObjects:
        xml = xml + "<object>\n"
        xml = xml + "\t<name>" + charObject['name'] + "</name>\n"
        xml = xml + "\t<pose>" + "Unspecified" + "</pose>\n"
        xml = xml + "\t<truncated>" + "Unspecified" + "</truncated>\n"
        xml = xml + "\t<difficult>" + "Unspecified" + "</difficult>\n"
        xml = xml + "\t<occluded>" + "Unspecified" + "</occluded>\n"
        xml = xml + "\t<bndbox>\n"
        xml = xml + "\t\t<xmin>" + str(charObject['xmin']) + "</xmin>\n"
        xml = xml + "\t\t<xmax>" + str(charObject['xmax']) + "</xmax>\n"
        xml = xml + "\t\t<ymin>" + str(charObject['ymin']) + "</ymin>\n"
        xml = xml + "\t\t<ymax>" + str(charObject['ymax']) + "</ymax>\n"
        xml = xml + "\t</bndbox>\n"
        xml = xml + "</object>\n"
    xml = xml + "</annotation>"
    return xml

def resize(image, objects, width, heigth):
    def updateObjectBbox(obj, resizedBbox):
        obj['xmin'] = resizedBbox.x1
        obj['ymin'] = resizedBbox.y1
        obj['xmax'] = resizedBbox.x2
        obj['ymax'] = resizedBbox.y2
        return obj
    
    bbs = BoundingBoxesOnImage([BoundingBox(x1=obj['xmin'], y1=obj['ymin'], x2=obj['xmax'], y2=obj['ymax']) for obj in objects], shape=image.shape)

    if width == None and heigth != None:
        width = 'keep-aspect-ratio'
    elif width != None and heigth == None:
        heigth = 'keep-aspect-ratio'

    seq = iaa.Sequential([iaa.Resize({"width": width, "height": heigth})])
    resizedImage, resizedBboxes = seq(image=image, bounding_boxes=bbs)

    updatedObjects = [updateObjectBbox(obj, resizedBboxes.bounding_boxes[i]) for i, obj in enumerate(objects)]
    return resizedImage, updatedObjects

def cropPlate(carImageFilePath, xmlFilePath, newWidth = None, newHeight = None):
    carImage = cv2.imread(carImageFilePath)
    cv2.cvtColor(carImage, cv2.COLOR_BGR2RGB)
    plateObject = getPlateObject(xmlFilePath)
    if plateObject != None:
        # crop plate image
        plateImage = carImage[plateObject['ymin'] - PLATE_PADDING : plateObject['ymax'] + PLATE_PADDING, plateObject['xmin'] - PLATE_PADDING : plateObject['xmax'] + PLATE_PADDING]
        # calculate new chars object
        newCharObjects = calculateNewCharObjects(getCharObjects(xmlFilePath), plateObject, PLATE_PADDING)

        if newWidth != None or newHeight != None:
            plateImage, newCharObjects = resize(plateImage, newCharObjects, newWidth, newHeight)

        #drawBbox(plateImage, newCharObjects)

        xml = createPlateXml(plateImage, newCharObjects, carImageFilePath)
        return plateImage, xml
    else:
        raise Exception("Plate Object Not Found")

def main():
    width = args['width']
    height = args['height']

    datasetName = args['dataset_name']
    pascalVOCDirPath = os.path.join('./dataturks/pascalVOC/', datasetName)
    croppedLpDirPath = os.path.join('./cropped_lps/', datasetName)

    if not os.path.exists(croppedLpDirPath):
        os.makedirs(croppedLpDirPath)

    for carImageFilePath in utils.listFilePaths(pascalVOCDirPath, 'jpg'):
        imageName = utils.getFileName(carImageFilePath)
        xmlFilePath = os.path.join(pascalVOCDirPath, imageName + '.xml')

        try:
            plateImage, xml = cropPlate(carImageFilePath, xmlFilePath, newWidth=width, newHeight=height)
        except Exception:
            print("Plate Object Not Found")
            continue

        saveImageAndXml(imageName, plateImage, xml, croppedLpDirPath)

if __name__ == "__main__":
    main()