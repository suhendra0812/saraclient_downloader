# SARA Client Downloader
__SARA Client Downloader__ is a Sentinel data downloader from [Sentinel Australasia Regional Access (SARA)](https://copernicus.nci.org.au/) which provides free access to data from all Sentinel satellites for the South-East Asia and South Pacific region. The script is based on __Australian Regional Copernicus Hub__. In current version, the script download Sentinel 1 data only.

## Installation
Install depedencies using `requirements.txt` file
```
$ python -m pip install -r requirements.txt
```
### Windows (Optional)
Install Cartopy (adding basemap to plot)
- Install **pipwin** using `python -m pip install pipwin`
- Run `pipwin refresh`
- Install **Cartopy** using `pipwin`
```
$ pipwin install cartopy
```

## Usage
- Import modules
```python
import os
from saraclient_downloader import GetData, DownloadFile
```
- Get data availablilty in SARA client using `GetData` class with passing such parameters: _startdate_, _enddate_ and _polygon_ file. And it will return list of __FeatureCollection__ if succeed, which contain data information including data URL.
```python
startdate = "2021-10-28" # yyyy-mm-dd
enddate = "2021-10-28" # yyyy-mm-dd
polygon = "aoi.geojson" # or other geospatial shape format
data = GetData(startdate, enddate, polygon)
results = data.get_results()
```
- (Optional) we can also plot the result using matplotlib
```python
import geopandas as gpd
from saraclient_downloader import plotting

result_gdf = data.get_geodataframe()
polygon_gdf = gpd.read_file(polygon)
fig = plotting(polygon_gdf, result_gdf, figsize=(15,10))
fig.savefig("results.png, bbox_inches="tight")
```
![Result image](img/results.png)
- Download data using `DownloadFile` class and pass it with data _url_ and _output_path_ where data will be stored and SARA client authentication (_username_ and _password_).
```python
username = "your SARA client username"
password = "your SARA client password"

# As 'results' is a list, we should iterate each feature to obtain information
for result in results:
    url = result["services"]["download"]["url"]
    filename = result["properties"]["productIdentifier"]
    output_path = os.path.join("C:\download", f"{filename}.zip")
    DownloadFile(url, output_path, username, password).download()
```