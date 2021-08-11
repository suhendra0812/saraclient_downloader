import os
import glob
import requests
from tqdm import tqdm
from datetime import datetime
from auscophub import saraclient
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


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
    def __init__(self, startdate, enddate, polygon):
        self.startdate = startdate
        self.enddate = enddate
        self.polygon = polygon

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

        all_gdf.reset_index(drop=True, inplace=True)

        return all_gdf


class DownloadFile:
    def __init__(self, url, token, filename):
        self.url = url
        self.params = (("_bearer", token),)
        self.filename = filename

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


def plotting(polygon_gdf, result_gdf):
    fig = plt.figure()
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


def main():
    basepath = os.path.dirname(os.path.abspath(__file__))

    username = "suhendra0812@gmail.com"
    password = "kuningan08121995"
    token = Login(username, password).login()

    s = input("startdate (yyyymmdd): ")
    e = input("enddate (yyymmdd): ")

    startdate = datetime.strptime(s, "%Y%m%d").strftime("%Y-%m-%d")
    enddate = datetime.strptime(e, "%Y%m%d").strftime("%Y-%m-%d")

    polygon_files = glob.glob(f"{basepath}/region/*.geojson")
    print("Region found:", len(polygon_files))
    for i, polygon_file in enumerate(polygon_files):
        print(f"{i+1}. Region file: {os.path.basename(polygon_file)}")
        polygon_gdf = gpd.read_file(polygon_file)
        polygon = polygon_gdf.geometry[0].to_wkt()
        region = os.path.splitext(os.path.basename(polygon_file))[0]
        download = f"{basepath}/download/{region}"

        data = GetData(startdate, enddate, polygon)
        results = data.get_results()

        results_len = len(results)
        print(f"Data found: {results_len}")
        if results_len > 0:
            for i, result in enumerate(results):
                filename = result["properties"]["productIdentifier"]
                print(f"{i+1}. {filename}")

            result_gdf = data.get_geodataframe()

            plot_option = input("Plotting (y/n): ")

            if plot_option == "y":
                fig = plotting(polygon_gdf, result_gdf)

                selection = True
                while selection:
                    frame_option = input("Frame selection (e.g: 1,2,3,...,n / all): ")
                    if frame_option == "all":
                        frame_list = list(range(len(results)))
                    else:
                        frame_list = [int(f)-1 for f in frame_option.split(",")]
                        frame_gdf = result_gdf[result_gdf.index.isin(frame_list)].copy()
                        plot_option = input("Plotting (y/n): ")
                        if plot_option == "y":
                            fig = plotting(polygon_gdf, frame_gdf)
                    
                    select_option = input("Continue selection (y/n): ")
                    if select_option == "y":
                        selection = True
                    else:
                        selection = False

            download_option = input("Download (y/n): ")

            if download_option == "y":
                for i, result in enumerate(results):
                    if i in frame_list:
                        print(f"Downloading Sentinel 1 ({i+1}/{len(results)})")
                        url = result["properties"]["services"]["download"]["url"]
                        filename = result["properties"]["productIdentifier"]
                        print(f"{i+1}. {filename}")
                        output_path = os.path.join(download, f"{filename}.zip")
                        DownloadFile(url, token, output_path).download()


if __name__ == "__main__":
    main()
