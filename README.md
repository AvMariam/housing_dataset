# Apartments' Project

This project is designed to **scrape, clean, geocode, and process house-related data**. The repository contains Python scripts and Jupyter notebooks to help you collect, analyze, and prepare real estate data for further use.

---

## Project Structure

1) Install the Requirements via

```pip install -r requirements.txt```

2) Run geocode_addresses.py to convert addresses to latitude and longitude coordinates.

```python geocode_addresses.py```

3) Find District Information

Run find_district.py to extract or enrich the dataset with district-level information based on addresses.

```python find_district.py```

4) Use the cleaning.ipynb notebook to clean the raw data and save the resulting dataset to `data/cleaned_data.csv`.
