import re
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


district_map = {
    'Ajapnyak': 'Աջափնյակ',
    'Avan': 'Ավան',
    'Davtashen': 'Դավթաշեն',
    'Erebuni': 'Էրեբունի',
    'Kanaker-Zeytun': 'Քանաքեռ-Զեյթուն',
    'Kentron': 'Կենտրոն',
    'Malatia-Sebastia': 'Մալաթիա-Սեբաստիա',
    'Nor Nork': 'Նոր Նորք',
    'Nubarashen': 'Նուբարաշեն',
    'Shengavit': 'Շենգավիթ',
    'Arabkir': 'Արաբկիր'
}

geocoded_path = "data/geocoded_addresses.csv"
geojson_path = "data/districts.geojson"
all_addresses_path = "data/all_addresses_with_districts.csv"

def find_district():
    geocoded_data = pd.read_csv(geocoded_path)
    districts = gpd.read_file(geojson_path)

    # There are Kotayk, Armavir ... 
    geocoded_data = geocoded_data[~geocoded_data['Address'].str.contains('Region', na=False)]
    geocoded_data = geocoded_data[~geocoded_data['coordinates'].isna()]

    # Function to find district using coordinates
    def find(cords):
        lat, long = str(cords).split(',')
        point = [Point(long, lat)]
        house_gdf = gpd.GeoDataFrame(geometry=point, crs="EPSG:4326")  # Make sure CRS matches

        # Perform a spatial join to match houses with districts
        houses_with_districts = gpd.sjoin(house_gdf, districts, how="left", predicate="within")

        # Print the resulting dataframe
        return houses_with_districts.iloc[0]['name_arm']

    # Function to replace English names with Armenian equivalents
    def replace_with_armenian(address):
        match = re.search(pattern, address)
        if match:
            district = match.group(1).strip()
            # Replace with Armenian if available in the dictionary
            return district_map.get(district, district)
        return None
    
    # Fistly we try to extract 'The Administrative District' patter.
    pattern = r'The Administrative District of ([\w\s]+),'
    geocoded_data['District'] = geocoded_data['Address'].apply(lambda x: re.search(pattern, x).group(1) if re.search(pattern, x) else None)
    geocoded_data['District'] = geocoded_data['Address'].apply(replace_with_armenian)
    
    # Then we try to find usig coordinates
    geocoded_data['District'] = geocoded_data.apply(
        lambda row: find(row['coordinates']) if row['District'] is None else row['District'],
        axis=1
    )
    
    geocoded_data['District'] = geocoded_data['coordinates'].apply(func=find)
    geocoded_data = geocoded_data[~geocoded_data['District'].isna()]
    
    geocoded_data.drop(columns='id').to_csv(all_addresses_path, index=False)
