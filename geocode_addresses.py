import os
import time
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()
YANDEX_API_KEY = os.getenv("YANDEX_KEY")

geocoded_path = "data/geocoded_addresses.csv"
list_data_address = "data/scraped_data.csv"


def geocode():
    # read new addresses
    df = pd.read_csv(list_data_address)

    # This part removes all addresses which contain '›'
    # and keeps only addresses which are in Yerevan.
    df = df[df.Address.notna()]
    df = df[~df.Address.str.contains('›')]
    yvn_list = ['երևան', 'yerevan', 'ереван']
    df.Address = df.Address.apply(lambda x: x.lower().strip())
    df = df[df.Address.str.contains('|'.join(yvn_list))]
    
    addresses = df['Address']

    # Initialize Selenium driver using webdriver-manager for automatic setup
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    
    # Use webdriver-manager to automatically download and manage ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options, service=service)
    # driver = webdriver.Chrome()

    # Function to geocode an address using the Yandex API via Selenium
    def geocode_address(address):
        html_content = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Geocoding with Yandex API</title>
            <script src="https://api-maps.yandex.ru/2.1/?lang=en_US&apikey={YANDEX_API_KEY}" type="text/javascript"></script>
            <script type="text/javascript">
                function geocodeAddress(address) {{
                    return new Promise((resolve, reject) => {{
                        ymaps.ready(function () {{
                            ymaps.geocode(address).then(function (res) {{
                                var coords = res.geoObjects.get(0).geometry.getCoordinates();
                                var foundAddress = res.geoObjects.get(0).properties.get('text');
                                resolve({{'coords': coords, 'foundAddress': foundAddress}});
                            }}, function (err) {{
                                reject(err);
                            }});
                        }});
                    }});
                }}
            </script>
        </head>
        <body>
            <script>
                var result = '';
                geocodeAddress('{address}').then(function(response) {{
                    document.body.setAttribute('data-coords', response.coords);
                    document.body.setAttribute('data-found-address', response.foundAddress);
                }});
            </script>
        </body>
        </html>
        '''


        # Load the HTML content
        driver.get("data:text/html;charset=utf-8," + html_content)

        # Wait for the JavaScript to finish executing
        time.sleep(1)

        # Retrieve the result from the body attribute
        coords = driver.find_element(By.TAG_NAME, 'body').get_attribute('data-coords')
        found_address = driver.find_element(By.TAG_NAME, 'body').get_attribute('data-found-address')

        return found_address, coords

   # Load existing geocoded addresses if the CSV file exists
    if os.path.exists(geocoded_path):
        geocoded_addresses = pd.read_csv(geocoded_path)
        existing_addresses = set(list(geocoded_addresses['Address'].values))
    else:
        geocoded_addresses = pd.DataFrame(columns=['id', 'Address', 'found_address', 'coordinates'])
        existing_addresses = set()


    # Create an empty list to store the new geocoding results
    results = []

    for index, address in tqdm(enumerate(addresses)): 
        # Check for repeated address in existing geocoded addresses
        if address in existing_addresses:
            continue

        try:
            # found_address, coordinates = geocode_address(address + ', Yerevan')
            found_address, coordinates = geocode_address(address)
            
            if found_address is None:
                time.sleep(5)
                found_address, coordinates = geocode_address(address)

                  
            results.append({
                'id': index,
                'Address': address,
                'found_address': found_address,
                'coordinates': coordinates
            })
            
            existing_addresses.add(address)
            
        except Exception as e:
            results.append({
                'id': index,
                'Address': address,
                'found_address': 'Error',
                'coordinates': 'Error'
            })

        except KeyboardInterrupt:
            # Create a DataFrame for the new results
            result_df = pd.DataFrame(results)

            # Append new addresses to existing ones, avoiding duplicates
            updated_df = pd.concat([geocoded_addresses, result_df]).drop_duplicates(subset=['Address'])

            # Save the updated DataFrame to the CSV file
            updated_df.to_csv(geocoded_path, index=False)
            break

    # Final save in case of normal execution
    if results:  # If new results were found
        result_df = pd.DataFrame(results)
        updated_df = pd.concat([geocoded_addresses, result_df]).drop_duplicates(subset=['Address'])
        updated_df.to_csv(geocoded_path, index=False)

    # Close the Selenium driver
    driver.quit()

if __name__ == "__main__":
    geocode()