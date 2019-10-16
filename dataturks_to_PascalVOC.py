import argparse
import sys
import os
import json
import logging
import requests
from PIL import Image
from pdb import set_trace
import re
import utils
###################  INSTALLATION NOTE #######################
##############################################################

## pip install requests
## pip install pillow

###############################################################
       ###############################################################

#enable info logging.
logging.getLogger().setLevel(logging.INFO)

HOST = 'http://dataturks.iapp.co.th'

def getImageNameFromUrl(image_url):
    return image_url.split("/")[-1].split('_')[-1]

def maybe_download(image_url, image_dir):
    """Download the image if not already exist, return the location path"""
    imageName = getImageNameFromUrl(image_url)
    imageFilePath = os.path.join(image_dir, imageName)

    if (os.path.exists(imageFilePath)):
        return imageFilePath

    #else download the image
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(imageFilePath, 'wb') as f:
                f.write(response.content)
                return imageFilePath
        else:
            raise ValueError( "Not a 200 response")
    except Exception as e:
        logging.exception("Failed to download image at " + image_url + " \n" + str(e) + "\nignoring....")
        raise e


def get_xml_for_bbx(bbx_label, bbx_data, width, height):

    if len(bbx_data['points']) == 4:
        #Regular BBX has 4 points of the rectangle.
        xmin = width*min(bbx_data['points'][0][0], bbx_data['points'][1][0], bbx_data['points'][2][0], bbx_data['points'][3][0])
        ymin = height * min(bbx_data['points'][0][1], bbx_data['points'][1][1], bbx_data['points'][2][1],
                           bbx_data['points'][3][1])

        xmax = width * max(bbx_data['points'][0][0], bbx_data['points'][1][0], bbx_data['points'][2][0],
                           bbx_data['points'][3][0])
        ymax = height * max(bbx_data['points'][0][1], bbx_data['points'][1][1], bbx_data['points'][2][1],
                           bbx_data['points'][3][1])

    else:
        #OCR BBX format has 'x','y' in one point.
        # We store the left top and right bottom as point '0' and point '1'
        xmin = int(bbx_data['points'][0]['x']*width)
        ymin = int(bbx_data['points'][0]['y']*height)
        xmax = int(bbx_data['points'][1]['x']*width)
        ymax = int(bbx_data['points'][1]['y']*height)

    xml = "<object>\n"
    xml = xml + "\t<name>" + bbx_label + "</name>\n"
    xml = xml + "\t<pose>Unspecified</pose>\n"
    xml = xml + "\t<truncated>Unspecified</truncated>\n"
    xml = xml + "\t<difficult>Unspecified</difficult>\n"
    xml = xml + "\t<occluded>Unspecified</occluded>\n"
    xml = xml + "\t<bndbox>\n"
    xml = xml +     "\t\t<xmin>" + str(xmin) + "</xmin>\n"
    xml = xml +     "\t\t<xmax>" + str(xmax) + "</xmax>\n"
    xml = xml +     "\t\t<ymin>" + str(ymin) + "</ymin>\n"
    xml = xml +     "\t\t<ymax>" + str(ymax) + "</ymax>\n"
    xml = xml + "\t</bndbox>\n"
    xml = xml + "</object>\n"
    return xml


def convert_to_PascalVOC(dataturks_labeled_item, outputDir):
    def isStartWithHttp(url):
        if re.match(r'http', url):
            return True
        else:
            return False
    """Convert a dataturks labeled item to pascalVOCXML string.
      Args:
        dataturks_labeled_item: JSON of one labeled image from dataturks.
        image_dir: Path to  directory to downloaded images (or a directory already having the images downloaded).
        xml_out_dir: Path to the dir where the xml needs to be written.
      Returns:
        None.
      Raises:
        None.
      """
    try:
        data = json.loads(dataturks_labeled_item)
        if len(data['annotation']) == 0:
            logging.info("Ignoring Skipped Item");
            return False;

        #width = data['annotation'][0]['imageWidth']
        #height = data['annotation'][0]['imageHeight']
        image_url = data['content']
        if not isStartWithHttp(image_url):
            image_url = HOST + image_url
        
        imageFilePath = maybe_download(image_url, outputDir)

        with Image.open(imageFilePath) as img:
            width, height = img.size
        
        imageExtension = imageFilePath.split('.')[-1]

        if imageExtension in ['jpg', 'jpeg']:
            imageName = os.path.basename(imageFilePath).split('.')[0]
        else:
            raise("Image extension not found")

        
        image_dir_folder_name = outputDir.split("/")[-1]

        xml = "<annotation>\n<folder>" + image_dir_folder_name + "." + imageExtension + "</folder>\n"
        xml = xml + "<filename>" + imageName +"</filename>\n"
        xml = xml + "<path>" + imageFilePath +"</path>\n"
        xml = xml + "<source>\n\t<database>Unknown</database>\n</source>\n"
        xml = xml + "<size>\n"
        xml = xml +     "\t<width>" + str(width) + "</width>\n"
        xml = xml +    "\t<height>" + str(height) + "</height>\n"
        xml = xml +    "\t<depth>Unspecified</depth>\n"
        xml = xml +  "</size>\n"
        xml = xml + "<segmented>Unspecified</segmented>\n"

        for bbx in data['annotation']:
            if not bbx:
                continue;
            #Pascal VOC only supports rectangles.
            if "shape" in bbx and bbx["shape"] != "rectangle":
                continue;

            bbx_labels = bbx['label']
            #handle both list of labels or a single label.
            if not isinstance(bbx_labels, list):
                bbx_labels = [bbx_labels]

            for bbx_label in bbx_labels:
                xml = xml + get_xml_for_bbx(bbx_label, bbx, width, height)

        xml = xml + "</annotation>"

        #output to a file.
        xmlFilePath = os.path.join(outputDir,  imageName + ".xml")
        
        
        with open(xmlFilePath, 'w', encoding='utf-8') as f:
            f.write(xml)
        return True
    except Exception as e:
        logging.exception("Unable to process item " + dataturks_labeled_item + "\n" + "error = "  + str(e))
        return False    



def main():
    if (not os.path.exists(jsonDir)):
        logging.exception(
            "Please specify a valid path to dataturks JSON directory, " + jsonDir + " doesn't exist")
        return
    if (not os.path.isdir(outputDir)):
        logging.exception("Please specify a valid directory path to download images, " + outputDir + " doesn't exist")
        return

    allJsonFilePath = utils.listFilePaths(jsonDir, 'json')
    lines = []
    for jsonFile in allJsonFilePath:
        with open(jsonFile, 'r', encoding='utf-8') as f:
            lines += f.readlines()
    
    if (not lines or len(lines) == 0):
        logging.exception(
            "Please specify a valid path to dataturks JSON output file, " + jsonFile + " is empty")
        return

    count = 0;
    success = 0
    for line in lines:
        status = convert_to_PascalVOC(line, outputDir)
        if (status):
            success = success + 1

        count+=1;
        print(count)
        if (count % 10 == 0):
            logging.info(str(count) + " items done ...")

    logging.info("Completed: " + str(success) + " items done, " + str(len(lines) - success)  + " items ignored due to errors or for being skipped items.")

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-dn', '--dataset_name', type=str, required=True, help='Dataset name')
    args = vars(ap.parse_args())    

    global datasetName    
    global outputDir

    datasetName = args['dataset_name']
    jsonDir = os.path.join('./dataturks/json', datasetName)
    outputDir = os.path.join('./dataturks/pascalVOC', datasetName)

    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    main()