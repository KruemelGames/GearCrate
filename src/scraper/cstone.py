"""
CStone.space scraper to fetch item images and data
"""
import os
import requests
from bs4 import BeautifulSoup
import re
import time


class CStoneScraper:
    BASE_URL = "https://finder.cstone.space"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_item(self, item_name):
        """Search for an item on CStone"""
        try:
            # Search URL
            search_url = f"{self.BASE_URL}/Search"
            params = {'search': item_name}
            
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find item links (this is a simplified example, may need adjustment)
            # CStone structure might vary, this is a starting point
            results = []
            
            # Look for item cards or links
            item_elements = soup.find_all('a', href=re.compile(r'/FPSArmors1/|/Search/'))
            
            for element in item_elements[:10]:  # Limit to first 10 results
                item_href = element.get('href')
                item_text = element.get_text(strip=True)
                
                if item_text and item_href:
                    results.append({
                        'name': item_text,
                        'url': f"{self.BASE_URL}{item_href}" if not item_href.startswith('http') else item_href
                    })
            
            return results
        
        except Exception as e:
            print(f"Error searching item: {e}")
            return []
    
    def get_item_image(self, item_url):
        """Get image URL from item page"""
        try:
            response = self.session.get(item_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find image - CStone usually has images in specific tags
            # This might need adjustment based on actual page structure
            img_tag = soup.find('img', src=re.compile(r'\.(jpg|jpeg|png|webp)'))
            
            if img_tag and img_tag.get('src'):
                img_url = img_tag['src']
                if not img_url.startswith('http'):
                    img_url = f"{self.BASE_URL}{img_url}"
                return img_url
            
            return None
        
        except Exception as e:
            print(f"Error fetching image: {e}")
            return None
    
    def download_image(self, image_url, save_path):
        """Download image from URL to local path"""
        try:
            print(f"    Downloading: {image_url}")
            response = self.session.get(image_url, timeout=15, stream=True)

            # Check if successful
            if response.status_code == 404:
                print(f"    ✗ Image not found (404): {image_url}")
                return False

            response.raise_for_status()

            # Save image
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify file was created and has content
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                print(f"    ✓ Image downloaded: {os.path.getsize(save_path)} bytes")
                return True
            else:
                print(f"    ✗ Downloaded file is empty or doesn't exist")
                return False

        except Exception as e:
            print(f"    ✗ Error downloading image: {e}")
            return False

    def get_category_items(self, category_url):
        """
        Get all items from a specific category on CStone
        category_url: z.B. 'FPSArmors?type=Torsos' oder 'FPSClothes?type=Hat'
        Returns: List of items with name and image_url
        """
        try:
            # CStone verwendet API-Endpoints statt HTML-Parsing
            # Format: 'FPSArmors?type=Torsos' -> '/GetArmors/Torsos'
            # Format: 'FPSClothes?type=Hat' -> '/GetClothes/Hat'

            # Parse category_url
            if '?' not in category_url:
                print(f"Invalid category_url format (missing '?type='): {category_url}")
                return []

            parts = category_url.split('?type=')
            if len(parts) != 2:
                print(f"Invalid category_url format: {category_url}")
                return []

            category_type = parts[0]  # 'FPSArmors' oder 'FPSClothes'
            item_type = parts[1]      # 'Torsos', 'Hat', etc.

            # Baue API-URL
            if category_type == 'FPSArmors':
                api_url = f"{self.BASE_URL}/GetArmors/{item_type}"
            elif category_type == 'FPSClothes':
                api_url = f"{self.BASE_URL}/GetClothes/{item_type}"
            else:
                print(f"Unknown category type: {category_type}")
                return []

            print(f"Fetching from API: {api_url}")

            # API-Request
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()

            # Parse JSON
            data = response.json()
            items = []

            print(f"Received {len(data)} items from API")

            # Konvertiere API-Response zu unserem Format
            for item_data in data:
                item_name = item_data.get('Name')
                item_id = item_data.get('ItemId')

                if not item_name or not item_id:
                    continue

                # Baue Image-URL (CStone verwendet ein Standard-Pattern für Bilder)
                # Format: https://cstone.space/uifimages/{ItemId}.png
                image_url = f"https://cstone.space/uifimages/{item_id}.png"

                # Baue Item-URL
                if category_type == 'FPSArmors':
                    item_url = f"{self.BASE_URL}/FPSArmors1/{item_id}"
                elif category_type == 'FPSClothes':
                    item_url = f"{self.BASE_URL}/FPSClothes1/{item_id}"
                else:
                    item_url = None

                items.append({
                    'name': item_name,
                    'image_url': image_url,
                    'item_url': item_url,
                    'item_id': item_id,
                    'sold': item_data.get('Sold', 1)  # 1 = verkauft im Spiel, 0 = nicht verkauft
                })

            print(f"Parsed {len(items)} items successfully")
            return items

        except Exception as e:
            print(f"Error fetching category items: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_item_details(self, item_name):
        """
        Get full details for a specific item (image, properties, etc.)
        Returns: dict with image_url and properties
        """
        try:
            # Suche zuerst nach dem Item
            search_results = self.search_item(item_name)

            if not search_results:
                print(f"No results found for: {item_name}")
                return None

            # Nimm das erste Ergebnis
            item_url = search_results[0].get('url')

            if not item_url:
                return None

            # Hole die Details von der Item-Seite
            response = self.session.get(item_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Finde das Bild
            image_url = None
            img_tag = soup.find('img', src=re.compile(r'\.(jpg|jpeg|png|webp)'))

            if img_tag and img_tag.get('src'):
                image_url = img_tag['src']
                if not image_url.startswith('http'):
                    image_url = f"{self.BASE_URL}{image_url}"

            # Finde Properties (falls vorhanden)
            properties = {}

            # TODO: Parse properties from the page if needed
            # This depends on the page structure

            return {
                'image_url': image_url,
                'properties': properties
            }

        except Exception as e:
            print(f"Error getting item details: {e}")
            return None
