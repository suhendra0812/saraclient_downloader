import os
from pathlib import Path
import requests
from tqdm import tqdm
from auscophub import saraclient
import json
import geopandas as gpd

try:
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
except ModuleNotFoundError:
    pass


class Login:
    def __init__(self, username, password):
        self.session = requests.Session()
        self.username = username
        self.password = password

    def login(self):
        data = f'{{"email":"{self.username}","password":"{self.password}"}}'
        session = self.session.post(
            "https://copernicus.nci.org.au/sara.server/1.0//api/user/connect", data=data
        )
        token = session.json()["token"]

        return token


class GetData:
    def __init__(self, startdate, enddate, polygon: Path | str):
        self.startdate = startdate
        self.enddate = enddate
        self.polygon = self.get_wkt(polygon)

    @staticmethod
    def get_wkt(path):
        gdf = gpd.read_file(path)
        return gdf.unary_union.wkt

    def get_results(self):
        urlOpener = saraclient.makeUrlOpener()
        sentinel = 1
        paramList = [
            f"startDate={self.startdate}",
            f"completionDate={self.enddate}",
            "productType=GRD",
            # 'polarisation=VH,VV',
            # 'orbitDirection=Ascending',
            f"geometry={self.polygon}",
        ]
        results = saraclient.searchSara(urlOpener, sentinel, paramList)

        return results

    def get_geodataframe(self):
        results = self.get_results()
        all_gdf = gpd.GeoDataFrame()
        for result in results:
            feat_json = json.dumps(result)
            feat_gdf = gpd.read_file(feat_json)
            all_gdf = all_gdf.append(feat_gdf)

        all_gdf.sort_values(by="startDate", inplace=True, ignore_index=True)

        return all_gdf


class DownloadFile(Login):
    def __init__(self, url, filename, username, password):
        super().__init__(username, password)
        self.url = url
        self.filename = filename
        self.token = self.login()
        self.params = (("_bearer", self.token),)

    def download(self):
        response = requests.get(self.url, self.params, stream=True)
        # Total size in bytes.
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024  # 1 Kilobyte

        folder = os.path.dirname(self.filename)
        os.makedirs(folder, exist_ok=True)

        if os.path.exists(self.filename):
            if os.path.getsize(self.filename) != total_size:
                t = tqdm(total=total_size, unit="B", unit_scale=True)
                with open(self.filename, "wb") as handle:
                    for data in response.iter_content(block_size):
                        t.update(len(data))
                        handle.write(data)
                t.close()
                if total_size != 0 and t.n != total_size:
                    print("ERROR, something went wrong")
            else:
                print(f"-> {os.path.basename(self.filename)} is already downloaded")
        else:
            t = tqdm(total=total_size, unit="B", unit_scale=True)
            with open(self.filename, "wb") as handle:
                for data in response.iter_content(block_size):
                    t.update(len(data))
                    handle.write(data)
            t.close()
            if total_size != 0 and t.n != total_size:
                print("ERROR, something went wrong")
        
        return response


def plotting(polygon_gdf, result_gdf, figsize=(15, 10)):
    fig = plt.figure(figsize=figsize)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines(draw_labels=True)

    polygon_gdf.plot(
        facecolor="none",
        edgecolor="lime",
        linewidth=2,
        label="polygon",
        ax=ax
    )

    result_gdf.plot(
        facecolor="none",
        edgecolor="red",
        label="result",
        ax=ax,
    )
    for j, geom in enumerate(result_gdf.geometry):
        centroid = geom.centroid
        ax.text(centroid.x, centroid.y, j + 1, ha="center", va="center")

    xmin, ymin, xmax, ymax = result_gdf.total_bounds

    threshold = 0.5

    ax.set_xlim([xmin - threshold, xmax + threshold])
    ax.set_ylim([ymin - threshold, ymax + threshold])

    fig.tight_layout()

    plt.show()

    return fig
