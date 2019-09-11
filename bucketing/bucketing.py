import os
import glob
import time
import argparse

from pdb import set_trace

ap = argparse.ArgumentParser()
ap.add_argument("-dn", "--dataset_name", required=True, help="Name of dataset")
args = vars(ap.parse_args())

LIMIT = 1000

def getFileName(filePath):
    return os.path.basename(filePath).split('.')[0]

def listDir(bucketsDirPath):
    return [bucketDir for bucketDir in glob.glob(bucketsDirPath + '/*/')]

def listBucketedImages(bucketsDirPath):
    bucketDirs = listDir(bucketsDirPath)
 
    return [getFileName(imageFilePath.replace('\\', '/'))  for bucketDir in bucketDirs for imageFilePath in glob.glob(bucketDir + '/*jpg') ]

def copyImagesToBucket(datasetName, imageName, lakeDirPath, bucketsDirPath):
    import shutil

    # find lastest bucket
    bucketDirPaths = listDir(bucketsDirPath)
    if len(bucketDirPaths) == 0:
        os.makedirs(os.path.join(bucketsDirPath, f'{datasetName}-bucket_1'))
    lastestBucketDirPath = sorted([bucketDirPath for bucketDirPath in listDir(bucketsDirPath)])[-1]

    # check if lastest bucket is available
    numFile = len([imageFile for imageFile in glob.glob(lastestBucketDirPath + "/*.jpg")])
    if numFile < LIMIT:
        destinationBucketDirPath = lastestBucketDirPath
    else:
        lastBucketNumber = int(os.path.basename(os.path.normpath(lastestBucketDirPath)).split('_')[-1])
        newBucketDirPath = os.path.join(bucketsDirPath, f'{datasetName}-bucket_{lastBucketNumber + 1}')
        os.makedirs(newBucketDirPath)
        destinationBucketDirPath = newBucketDirPath

    shutil.copyfile(os.path.join(lakeDirPath, f"{imageName}.jpg"),
                os.path.join(destinationBucketDirPath, f'{imageName}.jpg'))


def main():
    datasetName = args['dataset_name']
    lakeDirPath = os.path.join(f'../laking/{datasetName}-lake')
    bucketsDirPath = os.path.join(f'./{datasetName}-buckets')
    
    if not os.path.exists(lakeDirPath):
        raise Exception("Lake directory not found")

    if not os.path.exists(bucketsDirPath):
        os.makedirs(bucketsDirPath)

    # read all images in lake
    imagesInLake = [getFileName(imageFilePath.replace('\\', '/')) for imageFilePath in glob.glob(lakeDirPath + '/*.jpg')]
    # list all images not bucketed
    imagesInBucket = listBucketedImages(bucketsDirPath)

    imagesNotInBucket = set(imagesInLake) - set(imagesInBucket)

    for imageName in imagesNotInBucket:
        copyImagesToBucket(datasetName, imageName, lakeDirPath, bucketsDirPath)

if __name__ == "__main__":
    main()