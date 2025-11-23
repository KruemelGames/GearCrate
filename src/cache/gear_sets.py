"""
Gear Sets Manager - Liest CSV und findet Sets in der DB
"""
import csv
import os

class GearSetsManager:
    def __init__(self, csv_path='Armor-Sets.csv'):
        """Lädt die Set-Definitionen aus CSV"""
        self.csv_path = csv_path
        self.set_definitions = {}
        self.load_set_definitions()
    
    def load_set_definitions(self):
        """Liest die CSV-Datei und speichert Set-Infos"""
        csv_file = os.path.join(os.path.dirname(__file__), '..', '..', self.csv_path)
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                set_name = row['Set-Name']
                self.set_definitions[set_name] = {
                    'helmet': row['Helm(e)'],
                    'core': row['Core/Torso'],
                    'arms': row['Arms'],
                    'legs': row['Legs'],
                    'notes': row.get('Hinweise (mismatching Helm etc.)', '')
                }
        
        print(f"✅ Geladen: {len(self.set_definitions)} Set-Definitionen")
    
    def get_set_variants(self, db_connection, set_name):
        """
        Findet alle Farbvarianten eines Sets in der DB
        
        Beispiel:
        set_name = "ADP"
        Findet: ADP Black, ADP Red, ADP Blue, etc.
        """
        if set_name not in self.set_definitions:
            return []
        
        set_def = self.set_definitions[set_name]
        cursor = db_connection.cursor()
        
        # Suche nach Core-Varianten (die definieren die Farben)
        core_pattern = set_def['core']
        
        cursor.execute("""
            SELECT name FROM items 
            WHERE item_type='Torso' 
            AND name LIKE ?
            ORDER BY name
        """, (f"{core_pattern}%",))
        
        cores = cursor.fetchall()
        variants = []
        
        for (core_name,) in cores:
            # Extrahiere Farbe aus dem Namen
            # z.B. "ADP Core Black" -> "Black"
            variant = self._extract_variant(core_name, core_pattern)
            if variant:
                variants.append(variant)
        
        return variants
    
    def _extract_variant(self, item_name, base_name):
        """
        Extrahiert die Farbvariante aus dem Item-Namen
        
        Beispiel:
        item_name = "ADP Core Black"
        base_name = "ADP Core"
        Return = "Black"
        
        item_name = "Citadel Core Base"
        base_name = "Citadel Core"
        Return = "Base"
        """
        if not item_name.startswith(base_name):
            return None
        
        # Entferne Base-Name, z.B. "ADP Core Black" -> "Black"
        variant = item_name[len(base_name):].strip()
        
        # Wenn leer, ist es die Standard-Variante (ohne Farbe)
        if not variant:
            return 'Base'
        
        # Alle anderen Varianten bleiben wie sie sind
        return variant
    
    def get_set_pieces(self, db_connection, set_name, variant=''):
        """
        Holt alle 4 Teile eines Sets aus der DB
        
        Returns: {
            'helmet': {...},
            'core': {...},
            'arms': {...},
            'legs': {...}
        }
        """
        if set_name not in self.set_definitions:
            return None
        
        set_def = self.set_definitions[set_name]
        cursor = db_connection.cursor()
        
        pieces = {}
        
        # Baue die korrekten Namen für jedes Teil
        if variant:
            helmet_name = f"{set_def['helmet']} {variant}"
            core_name = f"{set_def['core']} {variant}"
            arms_name = f"{set_def['arms']} {variant}"
            legs_name = f"{set_def['legs']} {variant}"
        else:
            helmet_name = set_def['helmet']
            core_name = set_def['core']
            arms_name = set_def['arms']
            legs_name = set_def['legs']
        
        # Hole jedes Teil aus der DB
        for part_type, part_name in [
            ('helmet', helmet_name),
            ('core', core_name),
            ('arms', arms_name),
            ('legs', legs_name)
        ]:
            cursor.execute("SELECT * FROM items WHERE name = ?", (part_name,))
            row = cursor.fetchone()
            
            if row:
                # Konvertiere zu Dict
                columns = [desc[0] for desc in cursor.description]
                pieces[part_type] = dict(zip(columns, row))
            else:
                # Teil nicht gefunden
                pieces[part_type] = None
        
        return pieces
    
    def get_all_sets_summary(self, db_connection):
        """
        Gibt eine Übersicht über alle Sets
        
        Returns: [
            {
                'set_name': 'ADP',
                'variant_count': 25,
                'variants': ['Black', 'Red', ...]
            },
            ...
        ]
        """
        summary = []
        
        for set_name in sorted(self.set_definitions.keys()):
            variants = self.get_set_variants(db_connection, set_name)
            
            summary.append({
                'set_name': set_name,
                'variant_count': len(variants),
                'variants': variants
            })
        
        return summary


# Test-Code
if __name__ == '__main__':
    import sqlite3
    
    # Teste die Klasse
    manager = GearSetsManager()
    
    # Verbinde zur DB
    conn = sqlite3.connect('../../data/inventory.db')
    
    # Teste ADP Set
    print("\n=== ADP Varianten ===")
    variants = manager.get_set_variants(conn, 'ADP')
    print(f"Gefunden: {len(variants)} Varianten")
    print(variants[:5])  # Erste 5
    
    # Teste ein komplettes Set
    print("\n=== ADP Black Set ===")
    pieces = manager.get_set_pieces(conn, 'ADP', 'Black')
    for part_type, piece in pieces.items():
        if piece:
            print(f"  ✓ {part_type}: {piece['name']}")
        else:
            print(f"  ✗ {part_type}: FEHLT!")
    
    conn.close()
