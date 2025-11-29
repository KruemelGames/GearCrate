"""
Quick Bulk Import - Importiert Items direkt von CStone API
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.backend import API

def main():
    print("=" * 80)
    print("QUICK BULK IMPORT - Direkt von CStone API")
    print("=" * 80)
    print()

    # Initialize API
    api = API()

    # Kategorien zum Testen
    test_categories = {
        'Helmets': {'url': 'FPSArmors?type=Helmets', 'type': 'Helmet'},
    }

    print("Verfügbare Kategorien:")
    print("1. Nur Helmets (zum Testen)")
    print("2. Alle FPS Armor (Torsos, Arms, Legs, Helmets, Backpacks, Undersuits)")
    print("3. Alle Kleidung (Hüte, Brillen, etc.)")
    print("4. ALLES")
    print()

    choice = input("Auswahl (1-4): ").strip()

    categories = {}

    if choice == '1':
        categories = test_categories
    elif choice == '2':
        categories = {
            'Torsos': {'url': 'FPSArmors?type=Torsos', 'type': 'Torso'},
            'Arms': {'url': 'FPSArmors?type=Arms', 'type': 'Arms'},
            'Legs': {'url': 'FPSArmors?type=Legs', 'type': 'Legs'},
            'Helmets': {'url': 'FPSArmors?type=Helmets', 'type': 'Helmet'},
            'Backpacks': {'url': 'FPSArmors?type=Backpacks', 'type': 'Backpack'},
            'Undersuits': {'url': 'FPSArmors?type=Undersuits', 'type': 'Undersuit'},
        }
    elif choice == '3':
        categories = {
            'Hüte': {'url': 'FPSClothes?type=Hat', 'type': 'Hat'},
            'Brillen': {'url': 'FPSClothes?type=Eyes', 'type': 'Eyes'},
            'Handschuhe': {'url': 'FPSClothes?type=Hands', 'type': 'Hands'},
            'Jacken': {'url': 'FPSClothes?type=Jacket', 'type': 'Jacket'},
            'T-Shirts': {'url': 'FPSClothes?type=Shirt', 'type': 'Shirt'},
            'Jumpsuits': {'url': 'FPSClothes?type=Jumpsuit', 'type': 'Jumpsuit'},
            'Hosen': {'url': 'FPSClothes?type=Legs', 'type': 'Pants'},
            'Schuhe': {'url': 'FPSClothes?type=Feet', 'type': 'Shoes'},
        }
    elif choice == '4':
        categories = {
            'Torsos': {'url': 'FPSArmors?type=Torsos', 'type': 'Torso'},
            'Arms': {'url': 'FPSArmors?type=Arms', 'type': 'Arms'},
            'Legs': {'url': 'FPSArmors?type=Legs', 'type': 'Legs'},
            'Helmets': {'url': 'FPSArmors?type=Helmets', 'type': 'Helmet'},
            'Backpacks': {'url': 'FPSArmors?type=Backpacks', 'type': 'Backpack'},
            'Undersuits': {'url': 'FPSArmors?type=Undersuits', 'type': 'Undersuit'},
            'Hüte': {'url': 'FPSClothes?type=Hat', 'type': 'Hat'},
            'Brillen': {'url': 'FPSClothes?type=Eyes', 'type': 'Eyes'},
            'Handschuhe': {'url': 'FPSClothes?type=Hands', 'type': 'Hands'},
            'Jacken': {'url': 'FPSClothes?type=Jacket', 'type': 'Jacket'},
            'T-Shirts': {'url': 'FPSClothes?type=Shirt', 'type': 'Shirt'},
            'Jumpsuits': {'url': 'FPSClothes?type=Jumpsuit', 'type': 'Jumpsuit'},
            'Hosen': {'url': 'FPSClothes?type=Legs', 'type': 'Pants'},
            'Schuhe': {'url': 'FPSClothes?type=Feet', 'type': 'Shoes'},
        }
    else:
        print("Ungültige Auswahl!")
        return

    print()
    print(f"Starte Import für {len(categories)} Kategorien...")
    print("=" * 80)

    total_found = 0
    total_imported = 0
    total_skipped = 0

    for cat_name, cat_data in categories.items():
        print(f"\n📦 {cat_name}")
        print("-" * 80)

        try:
            # Hole Items von CStone
            items = api.get_category_items(cat_data['url'])
            total_found += len(items)

            print(f"Gefunden: {len(items)} Items")

            # Importiere jedes Item
            for i, item in enumerate(items, 1):
                # Check if exists
                existing = api.get_item(item['name'])

                if existing:
                    # Item existiert - aktualisiere IMMER das Bild (für Updates oder fehlende Bilder)
                    print(f"  [{i}/{len(items)}] 🔄 {item['name']} (existiert, aktualisiere Bild...)")
                    try:
                        # Lade Bild herunter und speichere es
                        import tempfile
                        import requests
                        import os

                        response = requests.get(item['image_url'], timeout=10)
                        if response.status_code == 200:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                                tmp_file.write(response.content)
                                tmp_path = tmp_file.name

                            # Lösche alte Bilder falls vorhanden
                            if existing.get('image_path') and os.path.exists(existing['image_path']):
                                try:
                                    # Lösche auch Thumbnails
                                    base_path = os.path.splitext(existing['image_path'])[0]
                                    for suffix in ['', '_thumb.png', '_medium.png']:
                                        old_file = existing['image_path'] if suffix == '' else base_path + suffix
                                        if os.path.exists(old_file):
                                            os.remove(old_file)
                                except Exception as del_err:
                                    print(f"    Warnung: Alte Dateien konnten nicht gelöscht werden: {del_err}")

                            # Speichere neues Bild
                            image_path = api.cache.save_image(item['image_url'], tmp_path, cat_data['type'])

                            try:
                                os.remove(tmp_path)
                            except:
                                pass

                            # Update DB mit Bildpfad
                            api.db.conn.execute(
                                "UPDATE items SET image_url = ?, image_path = ? WHERE name = ?",
                                (item['image_url'], image_path, item['name'])
                            )
                            api.db.conn.commit()
                            print(f"  [{i}/{len(items)}] ✅ {item['name']} (Bild aktualisiert)")
                            total_imported += 1
                    except Exception as e:
                        print(f"  [{i}/{len(items)}] ❌ Fehler beim Bild-Update: {e}")
                        total_skipped += 1
                else:
                    # Add item
                    result = api.add_item(
                        name=item['name'],
                        item_type=cat_data['type'],
                        image_url=item['image_url'],
                        notes=None,
                        initial_count=0  # Count = 0, nur zur Datenbank hinzufügen
                    )

                    if result.get('success'):
                        print(f"  [{i}/{len(items)}] ✅ {item['name']}")
                        total_imported += 1
                    else:
                        print(f"  [{i}/{len(items)}] ❌ {item['name']} - {result.get('error')}")

                # Rate limiting - nicht zu schnell
                if i % 10 == 0:
                    import time
                    time.sleep(0.5)

        except Exception as e:
            print(f"❌ Fehler bei Kategorie {cat_name}: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 80)
    print("✅ IMPORT ABGESCHLOSSEN")
    print("=" * 80)
    print(f"Gefunden:     {total_found}")
    print(f"Importiert:   {total_imported}")
    print(f"Übersprungen: {total_skipped}")
    print("=" * 80)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Import abgebrochen!")
    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
