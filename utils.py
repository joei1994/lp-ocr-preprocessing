
import os
import glob

def getFileName(filePath):
    filePath = filePath.replace('\\', '/')
    return os.path.basename(filePath).split('.')[0]

def listSubDirPaths(parentDirPath):
    return [subDirPath.replace('\\', '/') for subDirPath in glob.glob(parentDirPath + '/*/')]

def listFilePaths(dirPath, extension):
    return [f.replace('\\', '/') for f in glob.glob(dirPath + f'/*.{extension}')]    