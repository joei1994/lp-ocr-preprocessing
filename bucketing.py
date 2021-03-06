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

def listSubDirs(parentDirPath):
    return [subDirPath.replace('\\', '/') for subDirPath in glob.glob(parentDirPath + '/*/')]

def listImageFiles(dirPath):
    return [f.replace('\\', '/') for f in glob.glob(dirPath + '/*.jpg')]

def copyImagesToBucket(datasetName, imageName, datasetsDirPath, bucketsDirPath):
    import shutil

    # find lastest bucket
    bucketDirPaths = listSubDirs(bucketsDirPath)
    if len(bucketDirPaths) == 0:
        os.makedirs(os.path.join(bucketsDirPath, f'{datasetName}-bucket_1'))
    lastestBucketDirPath = sorted([bucketDirPath for bucketDirPath in listSubDirs(bucketsDirPath)])[-1]

    # check if lastest bucket is available
    numFile = len(listImageFiles(lastestBucketDirPath))
    if numFile < LIMIT:
        destinationBucketDirPath = lastestBucketDirPath
    else:
        lastBucketNumber = int(os.path.basename(os.path.normpath(lastestBucketDirPath)).split('_')[-1])
        newBucketDirPath = os.path.join(bucketsDirPath, f'{datasetName}-bucket_{lastBucketNumber + 1}')
        os.makedirs(newBucketDirPath)
        destinationBucketDirPath = newBucketDirPath

    def getSubDatasetDirPath(imageName):
        for subDatasetDirPath in listSubDirs(datasetsDirPath):
            imageNames = [getFileName(imageFilePath) for imageFilePath in listImageFiles(subDatasetDirPath)]
            if imageName in imageNames:
                break
            
        return subDatasetDirPath

    shutil.copyfile(os.path.join(getSubDatasetDirPath(imageName), f"{imageName}.jpg"),
                os.path.join(destinationBucketDirPath, f'{imageName}.jpg'))

def main():
    datasetName = args['dataset_name']
    datasetsDirPath = os.path.join(f'./datasets/{datasetName}')
    bucketsDirPath = os.path.join(f'./buckets/{datasetName}')

    if not os.path.exists(datasetsDirPath):
        raise Exception("Dataset not found")

    if not os.path.exists(bucketsDirPath):
        os.makedirs(bucketsDirPath)

    # read all images from dataset
    imagesInDataset = [getFileName(imageFilePath) for datasetDirPath in listSubDirs(datasetsDirPath) for imageFilePath in listImageFiles(datasetDirPath)]
    
    # list all images not bucketed
    imagesInBucket = [getFileName(imageFilePath) for bucketDirPath in listSubDirs(bucketsDirPath) for imageFilePath in listImageFiles(bucketDirPath)]
    imagesNotInBucket = set(imagesInDataset) - set(imagesInBucket)
    
    for imageName in imagesNotInBucket:
        copyImagesToBucket(datasetName, imageName, datasetsDirPath, bucketsDirPath)

if __name__ == "__main__":
    main()