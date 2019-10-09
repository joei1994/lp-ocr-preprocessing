import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import glob
import matplotlib
from matplotlib import pyplot as plt
import xml.etree.ElementTree as ET
from matplotlib.pyplot import imshow
from collections import Counter
import re
from utils import getFileName

from pdb import set_trace

ap = argparse.ArgumentParser()
ap.add_argument('--dataset_dir', type=str, required=True, help="Path to dataset directory relative to this file")
args = vars(ap.parse_args())

def separate():
    print("="*80)

def drawBoundingBox(image_path, xml_path, font_dir):
    # Prepare image
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    drawer = ImageDraw.Draw(image)    

    # Prepare Ground Truth
    tree = ET.parse(xml_path)
    root = tree.getroot()

    objects = [obj for obj in root.findall('object')]
    for obj in objects:
        label = obj.find('name').text

        xmin = float(obj.find('bndbox').find('xmin').text)
        ymin = float(obj.find('bndbox').find('ymin').text)
        xmax = float(obj.find('bndbox').find('xmax').text)
        ymax = float(obj.find('bndbox').find('ymax').text)
        
        drawer.line([(xmin, ymin),
                    (xmax, ymin),
                    (xmax, ymax),
                    (xmin, ymax),
                    (xmin, ymin)], fill=(255,0,0), width=2)
        font = ImageFont.truetype(font_dir, 20)
        drawer.text((xmin + (xmax - xmin) / 2, ymax), label, font = font, fill=(255,0,0))
    return image

def main():
    datasetDirPath = args['dataset_dir']
    separate()
    print("Number of images must equals to Number of xmls")
    image_paths = [f.replace('\\', '/') for f in glob.glob(datasetDirPath + '**/*.jpg')]
    xml_paths = [f.replace('\\', '/') for f in glob.glob(datasetDirPath + '**/*.xml')]
    print(f"\tnumber of images = {len(image_paths)}, number of xmls = {len(xml_paths)}")
    separate()

    print("Validate  labels")
    char_label_set = set()
    for xml_path in xml_paths:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    
        for obj in root.findall('object'):
            label = obj.find('name').text
            char_label_set.add(label)
    print(sorted(list(char_label_set)))
    print(f"Number of all label : {len(char_label_set)}")
    separate()

    print("List Duplicate images and xmls")
    image_names = [getFileName(image_path) for image_path in image_paths]
    duplicated_image = [count for item, count in Counter(image_names).items() if count > 1]
    xml_names = [getFileName(xml_path) for xml_path in xml_paths]
    duplicated_xml = [count for item, count in Counter(xml_names).items() if count > 1]
    print(f"\tDuplicated Images = ", duplicated_image)
    print(f"\tDuplicated Xmls = ", duplicated_xml)
    separate()

    print("\tImage which missing xml ", set(image_names) - set(xml_names))
    print("\tXml which missing image ", set(xml_names) - set(image_names))
    separate()

    print("Plotting Bounding Box")
    font_dir = './validate/fonts/angsa.ttf'
    output_dir = './validate/tmp/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for image_path in image_paths:
        image_name = getFileName(image_path)
        xml_path  = os.path.join(datasetDirPath, image_name + '.xml')
        drawedImage = drawBoundingBox(image_path, xml_path, font_dir=font_dir)
        drawedImage.save(os.path.join(output_dir, getFileName(image_path) + '.jpg'))
    print("Done")
    separate()
if __name__ == "__main__":
    main()