# lp-ocr-preprocessing
## Setup
1. Clone forked repo to local machine
2. Create virtual environment and active it
```
  conda create -n <venv-name> python=3.6
  conda activate <nenv-name>
```
3. Install dependencies, by run the followings commands
```
  pip install opencv-python
  conda config --add channeds conda-forge
  conda install imgaug
```
## Save raw Data
1. Change directory to dataset directory 
```
  cd <project-root-dir>/dataset/<dataset-name-dir> 
```
2. Place dataset into that directory
## Bucketing Dataset
1. Change directory to <project-root-dir>
2. Run the following command
```
  python bucketing -dn <dataset-name>
```
3. The result will be saved at `<project-root-dir>/buckets/<dataset-name>/<datasetname-bucket_X>`
## Tag Data
1. Open http://dataturks.iapp.co.th/projects/login 
2. Log in with
>
	  Email : iwachirawit@iapp.co.th
	  Password : iapp2019
3. Create new dataset
4. Upload compressed bucket e.g. upload `<project-root-dir>/buckets/<dataset-name>/<datasetname-bucket_X>.zip`
## Download Tagged Data
1. Open http://dataturks.iapp.co.th/projects/login 
2. Log in with
>
	  Email : iwachirawit@iapp.co.th
	  Password : iapp2019
3. Select desired dataset
4. Click on `options` button at upper right corner, then click download you

After downloading finished you will get json file as a result
1. Place downloaded json file under `<project-root-dir>/dataturks/json/<datasetname>`

After that, you need to convert tagged data from json format into PascalVOC format
1. Change directory to `<project-root-dir>`, run the following commands
```
  dataturks_to_PascalVOC.py -dn <datasetname>
```
2. You will get dataset in PascalVOC format at <project-root-dir>/dataturks/pascalVOC>/<datasetname>

## Crop only Plate object for training OCR model
1. Change project root directory
```
  cd <project-root-dir>
```
2. Run
```
  python crop_lp.py -dn <datasetname> —height <desired height>
```
3. You will get the result under `<project-root-dir>/cropped_lps/<datasetname>`

