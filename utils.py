
import os
import glob

def getFileName(filePath):
    filePath = filePath.replace('\\', '/')
    return os.path.basename(filePath).split('.')[0]

def listSubDirPaths(parentDirPath):
    return [subDirPath.replace('\\', '/') for subDirPath in glob.glob(parentDirPath + '/*/')]

def listImageFilePaths(dirPath):
    return [f.replace('\\', '/') for f in glob.glob(dirPath + '/*.jpg')]    