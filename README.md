# SARA Client Downloader

## Installation
### 1. Install auscophub-1.2.1
- Download [auscophub-1.2.1](https://github.com/CopernicusAustralasia/auscophub/releases/download/1.2.1/auscophub-1.2.1.zip) or you can check the latest one in [here](https://github.com/CopernicusAustralasia/auscophub/releases)
- Extract it
- Install it through:
```
cd auscophub-1.2.1
python -m pip install .
```
or
```
cd auscophub-1.2.1
python setup.py install
```

### 2. Install other dependencies
#### Linux and MacOS
Install through `requirements.txt` file directly
```
python -m pip install -r requirements.txt
```
#### Windows
- Install **pipwin** using `python -m pip install pipwin`
- Run `pipwin refresh`
- Install **GDAL**, **Fiona** and **Cartopy** using `pipwin install <package name>`
```
pipwin install gdal
pipwin install fiona
pipwin install cartopy
```
- Install remaining dependencies through `requirements.txt` file
```
python -m pip install -r requirements.txt
```

## Usage
- Create region file as Area of Interest (AoI) in **GeoJSON** format and put in the `region` folder relatively as `saraclient_downloader.py` is located
- Run `python saraclient_downloader.py`
