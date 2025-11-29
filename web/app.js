// GearCrate - Frontend Logic with Sorting & Filtering
// Image sizes: Thumb (search) → Medium (inventory) → Full (modal)

let currentItem = null;
let searchTimeout = null;
let selectedItemForModal = null;
let searchCache = {};
let gearSetsCache = null;
let currentView = localStorage.getItem('currentView') || 'inventory';
let currentGearSetsFilter = 'all';
let currentSelectedSet = 'ADP';
let loadedSets = {}; // Speichert geladene Sets
let favoriteGearSets = JSON.parse(localStorage.getItem('favoriteGearSets') || '[]'); // Array von "SetName Variant"

// NEU: Fuse.js Search Engine
let fuseInstance = null;
let allItemsForSearch = [];

// ÄNDERUNG 1: Initialwerte aus localStorage laden
let currentSortBy = localStorage.getItem('sortBy') || 'name';
let currentSortOrder = localStorage.getItem('sortOrder') || 'asc';
let currentCategoryFilter = localStorage.getItem('categoryFilter') || '';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // NEU: Anwendung der geladenen Einstellungen auf die UI
    applySavedSettingsToUI();
    
    // View-Switching einrichten
    setupViewSwitching();
    
    // Gespeicherte Ansicht laden
    switchToView(currentView);
    
    loadInventory();
    loadStats();
    // loadCategories muss NACH applySavedSettingsToUI laufen, 
    // da es currentCategoryFilter zur Bestimmung des aktiven Buttons nutzt
    loadCategories(); 
    setupEventListeners();
    loadSearchLimit();
    setupKeyboardShortcuts();
    setupStickyHeaderScrolling(); // NEU: Scroll-Detection für Compact-Modus
    
    // NEU: Initialisiere Fuse.js Search Engine
    initializeFuseSearch();
});

// VIEW SWITCHING SYSTEM
function setupViewSwitching() {
    const inventoryBtn = document.getElementById('view-btn-inventory');
    const gearsetsBtn = document.getElementById('view-btn-gearsets');
    
    inventoryBtn.addEventListener('click', () => switchToView('inventory'));
    gearsetsBtn.addEventListener('click', () => switchToView('gearsets'));
}

function switchToView(view) {
    currentView = view;
    localStorage.setItem('currentView', view);
    
    // Buttons updaten
    const inventoryBtn = document.getElementById('view-btn-inventory');
    const gearsetsBtn = document.getElementById('view-btn-gearsets');
    
    inventoryBtn.classList.remove('active');
    gearsetsBtn.classList.remove('active');
    
    // Views updaten
    const inventoryView = document.getElementById('inventory-view');
    const gearsetsView = document.getElementById('gearsets-view');
    
    inventoryView.classList.remove('active');
    gearsetsView.classList.remove('active');
    
    if (view === 'inventory') {
        inventoryBtn.classList.add('active');
        inventoryView.classList.add('active');
    } else if (view === 'gearsets') {
        gearsetsBtn.classList.add('active');
        gearsetsView.classList.add('active');
        
        // Gear Sets laden wenn noch nicht gecached
        if (!gearSetsCache) {
            loadGearSets();
        } else {
            // NEU: Prüfe invalidierte Sets und lade sie neu
            reloadInvalidatedSets();
        }
    }
}

// NEU: Lade alle invalidierten Sets neu beim View-Wechsel
async function reloadInvalidatedSets() {
    if (currentSelectedSet === 'ALL') {
        // "Alle Sets" View: Prüfe welche Sets fehlen
        const invalidatedSets = [];
        
        // Gehe durch gearSetsCache und prüfe welche nicht in loadedSets sind
        gearSetsCache.forEach(setInfo => {
            if (setInfo.variant_count > 0 && !loadedSets[setInfo.set_name]) {
                invalidatedSets.push(setInfo.set_name);
            }
        });
        
        if (invalidatedSets.length > 0) {
            console.log(`🔄 Lade ${invalidatedSets.length} invalidierte Sets neu...`);
            for (const setName of invalidatedSets) {
                await loadSingleSet(setName);
            }
        }
        
        displayGearSets();
    } else if (currentSelectedSet) {
        // Einzelnes Set: Prüfe ob es fehlt
        if (!loadedSets[currentSelectedSet]) {
            console.log(`🔄 Set ${currentSelectedSet} wurde invalidiert, lade neu...`);
            await loadSingleSet(currentSelectedSet);
        }
        
        displayGearSets();
    }
}

// FAVORITE GEAR SETS HELPERS
function getGearSetKey(setName, variant) {
    return `${setName}|||${variant}`;
}

function isGearSetFavorite(setName, variant) {
    const key = getGearSetKey(setName, variant);
    return favoriteGearSets.includes(key);
}

function toggleGearSetFavorite(setName, variant) {
    const key = getGearSetKey(setName, variant);
    const index = favoriteGearSets.indexOf(key);

    if (index >= 0) {
        // Remove from favorites
        favoriteGearSets.splice(index, 1);
    } else {
        // Add to favorites
        favoriteGearSets.push(key);
    }

    // Save to localStorage
    localStorage.setItem('favoriteGearSets', JSON.stringify(favoriteGearSets));
    console.log(`⭐ Gear Set ${setName} ${variant} favorite: ${index < 0}`);
}

// PLACEHOLDER ICON HELPER
function getPlaceholderIcon(itemType) {
    const validTypes = [
        'Arms', 'Backpack', 'Eyes', 'Hands', 'Hat', 'Helmet',
        'Jacket', 'Jumpsuit', 'Legs', 'Pants', 'Shirt', 'Shoes',
        'Torso', 'Undersuit'
    ];

    // Normalize item type (case-insensitive match)
    const normalizedType = validTypes.find(t =>
        t.toLowerCase() === (itemType || '').toLowerCase()
    );

    if (normalizedType) {
        return `/cache/Placeholder/${normalizedType}.png`;
    }

    return null; // Kein Placeholder verfügbar
}

// GET ITEM ICON - Intelligente Fallback-Logik
function getItemIcon(item, size = 'medium') {
    // size kann sein: 'thumb', 'medium', oder 'full'

    // 1. Prüfe ob lokales gecachtes Bild vorhanden (icon_url zeigt auf /cache/)
    if (item.icon_url && item.icon_url.startsWith('/cache/')) {
        let imageUrl = item.icon_url;

        // Konvertiere zu gewünschter Größe
        if (size === 'thumb' && imageUrl.endsWith('.png')) {
            return imageUrl.replace(/\.png$/, '_thumb.png');
        } else if (size === 'medium' && imageUrl.endsWith('.png')) {
            return imageUrl.replace(/\.png$/, '_medium.png');
        }

        return imageUrl;
    }

    // 2. Kein lokales Bild → Versuche Placeholder
    // (Auch wenn image_url existiert, wenn es nicht lokal gecacht ist, zeigen wir Placeholder)
    // Spezial-Fall: 'core' → 'Torso' für Gear-Sets
    let itemType = item.item_type || item.type;
    if (!itemType && item.partType) {
        itemType = item.partType === 'core' ? 'Torso' : item.partType;
    } else if (itemType && itemType.toLowerCase() === 'core') {
        itemType = 'Torso';
    }

    const placeholderPath = getPlaceholderIcon(itemType);
    if (placeholderPath) {
        return placeholderPath;
    }

    // 3. Kein Placeholder → null (Aufrufer zeigt dann 🎮)
    return null;
}

// GEAR SETS LADEN
async function loadGearSets() {
    try {
        const grid = document.getElementById('gearsets-grid');
        grid.innerHTML = '<p style="text-align: center; color: #888;">Lade Gear Sets...</p>';
        
        // Hole alle Sets vom Server (nur die Liste!)
        const response = await fetch('/api/get_all_gear_sets');
        const data = await response.json();
        
        if (!data.success) {
            grid.innerHTML = '<p style="text-align: center; color: #f44;">Fehler beim Laden!</p>';
            return;
        }
        
        gearSetsCache = data.sets;
        
        // Fülle Buttons mit Set-Namen
        populateSetButtons(gearSetsCache);
        
        // Lade NUR ADP beim Start
        await loadSingleSet('ADP');
        
        setupGearSetsControls();
        displayGearSets();
        
    } catch (error) {
        console.error('Error loading gear sets:', error);
        const grid = document.getElementById('gearsets-grid');
        grid.innerHTML = '<p style="text-align: center; color: #f44;">Fehler beim Laden!</p>';
    }
}

// BUTTONS MIT SET-NAMEN FÜLLEN
function populateSetButtons(sets) {
    const container = document.getElementById('set-buttons');
    const allButton = container.querySelector('.set-btn-all'); // Sichere den "Alle Sets" Button
    
    container.innerHTML = ''; // Leer machen
    
    // Füge jeden Set-Namen als Button hinzu
    sets.forEach(set => {
        if (set.variant_count > 0) {
            const btn = document.createElement('button');
            btn.className = 'set-btn';
            
            // ADP ist am Anfang aktiv
            if (set.set_name === 'ADP') {
                btn.classList.add('active');
            }
            
            btn.dataset.set = set.set_name;
            btn.textContent = `${set.set_name} (${set.variant_count})`;
            container.appendChild(btn);
        }
    });
    
    // "Alle Sets" Button wieder ans Ende setzen
    if (allButton) {
        container.appendChild(allButton);
    }
}

// LADE NUR EIN EINZIGES SET
async function loadSingleSet(setName) {
    // Schon geladen? Dann nicht nochmal!
    if (loadedSets[setName]) {
        console.log(`✨ ${setName} schon geladen!`);
        return;
    }
    
    const grid = document.getElementById('gearsets-grid');
    grid.innerHTML = '<p style="text-align: center; color: #888;">Lade ' + setName + '...</p>';
    
    // Finde das Set in der Liste
    const setInfo = gearSetsCache.find(s => s.set_name === setName);
    if (!setInfo) return;
    
    const variants = [];
    
    // Lade ALLE Farben von diesem Set
    for (const variant of setInfo.variants) {
        try {
            const response = await fetch(`/api/get_gear_set_details?set_name=${encodeURIComponent(setName)}&variant=${encodeURIComponent(variant)}`);
            const data = await response.json();
            
            if (data.success) {
                variants.push(data.set);
            }
        } catch (error) {
            console.error(`Fehler bei ${setName} ${variant}:`, error);
        }
    }
    
    // Speichere die geladenen Varianten
    loadedSets[setName] = variants;
    
    console.log(`✅ ${setName} geladen: ${variants.length} Farben`);
}

// LADE ALLE SETS (für "Alle Sets" Button)
async function loadAllSets() {
    const grid = document.getElementById('gearsets-grid');
    grid.innerHTML = '<p style="text-align: center; color: #888;">Lade alle Sets... Das kann etwas dauern!</p>';
    
    // Gehe durch alle Sets
    for (const set of gearSetsCache) {
        if (set.variant_count === 0) continue;
        
        // Lade nur wenn noch NICHT geladen
        if (!loadedSets[set.set_name]) {
            await loadSingleSet(set.set_name);
        }
    }
    
    console.log('✅ Alle Sets geladen!');
}

// CONTROLS EINRICHTEN (Buttons + Filter)
function setupGearSetsControls() {
    // Set-Buttons
    const setButtons = document.querySelectorAll('.set-btn');
    setButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            // Alle Buttons: nicht aktiv
            setButtons.forEach(b => b.classList.remove('active'));
            // Dieser Button: aktiv!
            this.classList.add('active');
            
            currentSelectedSet = this.dataset.set;
            
            // Spezial-Fall: "Alle Sets"
            if (currentSelectedSet === 'ALL') {
                await loadAllSets();
            } else {
                // Normales Set: Lade das Set (falls noch nicht geladen)
                await loadSingleSet(currentSelectedSet);
            }
            
            // Zeige es an
            displayGearSets();
        });
    });
    
    // Filter Buttons
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            currentGearSetsFilter = this.dataset.filter;
            displayGearSets();
        });
    });
}

// GEAR SETS ANZEIGEN
function displayGearSets() {
    const grid = document.getElementById('gearsets-grid');
    grid.innerHTML = '';
    
    let variants = [];
    
    // Spezial-Fall: "Alle Sets"
    if (currentSelectedSet === 'ALL') {
        // Sammle alle geladenen Sets zusammen
        Object.keys(loadedSets).forEach(setName => {
            variants = variants.concat(loadedSets[setName]);
        });
    } else {
        // Normaler Fall: Nur ein Set
        variants = loadedSets[currentSelectedSet] || [];
    }
    
    if (!variants || variants.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #888;">Keine Sets gefunden.</p>';
        return;
    }
    
    let variantsToShow = variants;

    // Filter nach Completion-Status oder Favorites
    if (currentGearSetsFilter !== 'all') {
        variantsToShow = variantsToShow.filter(v => {
            const ownedCount = v.owned_count;

            // Favorites Filter: Set muss in localStorage favorites sein
            if (currentGearSetsFilter === 'favorites') {
                return isGearSetFavorite(v.set_name, v.variant);
            }

            if (currentGearSetsFilter === 'none') return ownedCount === 0;
            if (currentGearSetsFilter === '1') return ownedCount === 1;
            if (currentGearSetsFilter === '2') return ownedCount === 2;
            if (currentGearSetsFilter === '3') return ownedCount === 3;
            if (currentGearSetsFilter === 'all-parts') return ownedCount === 4;

            return true;
        });
    }
    
    // Zeige gefilterte Sets an
    if (variantsToShow.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #888;">Keine Sets mit diesem Filter gefunden.</p>';
        return;
    }
    
    variantsToShow.forEach(setData => {
        const card = createGearSetCard(setData);
        grid.appendChild(card);
    });
    
    // NEU: Update Filter-Button Counts
    updateFilterButtonCounts(variants);
    
    console.log(`✅ Zeige ${variantsToShow.length} Sets`);
}

// NEU: Berechne und update Filter-Button Counts
function updateFilterButtonCounts(variants) {
    // Zähle Sets nach Kategorie
    const counts = {
        all: variants.length,
        favorites: 0,
        none: 0,
        one: 0,
        two: 0,
        three: 0,
        complete: 0
    };

    variants.forEach(v => {
        const owned = v.owned_count;
        if (owned === 0) counts.none++;
        else if (owned === 1) counts.one++;
        else if (owned === 2) counts.two++;
        else if (owned === 3) counts.three++;
        else if (owned === 4) counts.complete++;

        // Count favorites (aus localStorage)
        if (isGearSetFavorite(v.set_name, v.variant)) {
            counts.favorites++;
        }
    });

    // Update Button-Texte
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        const filter = btn.dataset.filter;
        let count = 0;
        let baseText = '';

        switch(filter) {
            case 'all':
                count = counts.all;
                baseText = 'Alle';
                break;
            case 'favorites':
                count = counts.favorites;
                baseText = '⭐ Favorites';
                break;
            case 'none':
                count = counts.none;
                baseText = '🔴 None (0/4)';
                break;
            case '1':
                count = counts.one;
                baseText = '🔵 1/4';
                break;
            case '2':
                count = counts.two;
                baseText = '🔵 2/4';
                break;
            case '3':
                count = counts.three;
                baseText = '🔵 3/4';
                break;
            case 'all-parts':
                count = counts.complete;
                baseText = '🟢 ALL (4/4)';
                break;
        }

        // Update Button-Text mit Count
        btn.textContent = `${baseText} (${count})`;
    });

    console.log(`✅ Filter Counts: Alle=${counts.all}, Favorites=${counts.favorites}, None=${counts.none}, 1/4=${counts.one}, 2/4=${counts.two}, 3/4=${counts.three}, 4/4=${counts.complete}`);
}

// NEU: Refresh ein spezifisches Set nach Item-Änderung (OPTIMIERT)
async function refreshGearSetIfNeeded(itemName) {
    // Versuche Set-Name UND Variante aus Item-Name zu extrahieren
    // Beispiele: 
    // "ADP Arms Black" → Set: ADP, Variant: Black
    // "ADP-mk4 Helmet (Modified)" → Set: ADP, Variant: Modified
    // "Overlord Helmet Heavy Orange" → Set: Overlord, Variant: Orange
    
    let foundItems = []; // [{setName, variant}]
    
    // Gehe durch ALLE Sets
    if (gearSetsCache) {
        gearSetsCache.forEach(setInfo => {
            const setName = setInfo.set_name;
            
            // Prüfe ob Set-Name im Item-Name vorkommt (case-insensitive)
            if (itemName.toLowerCase().includes(setName.toLowerCase())) {
                // Set gefunden! Jetzt versuche Variante zu finden
                const variants = setInfo.variants || [];
                
                // Prüfe jede Variante
                variants.forEach(variant => {
                    // Prüfe ob Varianten-Name im Item-Name vorkommt
                    if (itemName.toLowerCase().includes(variant.toLowerCase())) {
                        foundItems.push({
                            setName: setName,
                            variant: variant
                        });
                    }
                });
                
                // Falls keine spezifische Variante gefunden: Markiere ganzes Set
                if (foundItems.length === 0) {
                    foundItems.push({
                        setName: setName,
                        variant: null // Ganzes Set muss neu geladen werden
                    });
                }
            }
        });
    }
    
    // Aktualisiere gefundene Items
    if (foundItems.length > 0) {
        for (const item of foundItems) {
            if (item.variant) {
                // OPTIMIERT: Nur diese eine Variante neu laden
                console.log(`🔄 Lade nur ${item.setName} ${item.variant} neu (Item: ${itemName})`);
                await reloadSingleVariant(item.setName, item.variant);
            } else {
                // Ganzes Set neu laden (Fallback)
                console.log(`🗑️ Cache invalidiert für Set: ${item.setName} (Item: ${itemName})`);
                delete loadedSets[item.setName];
            }
        }
        
        // Display aktualisieren wenn in Gear-Sets View
        if (currentView === 'gearsets') {
            displayGearSets();
        }
    }
}

// NEU: Lade nur eine einzelne Variante eines Sets neu
async function reloadSingleVariant(setName, variant) {
    try {
        const response = await fetch(`/api/get_gear_set_details?set_name=${encodeURIComponent(setName)}&variant=${encodeURIComponent(variant)}`);
        const data = await response.json();
        
        if (data.success) {
            // Stelle sicher dass loadedSets[setName] existiert
            if (!loadedSets[setName]) {
                loadedSets[setName] = [];
            }
            
            // Finde und ersetze die Variante
            const variants = loadedSets[setName];
            const index = variants.findIndex(v => v.variant === variant);
            
            if (index !== -1) {
                // Ersetze existierende Variante
                variants[index] = data.set;
                console.log(`✅ ${setName} ${variant} aktualisiert`);
            } else {
                // Füge neue Variante hinzu
                variants.push(data.set);
                console.log(`➕ ${setName} ${variant} hinzugefügt`);
            }
        }
    } catch (error) {
        console.error(`Fehler beim Laden von ${setName} ${variant}:`, error);
    }
}
function createGearSetCard(setData) {
    const card = document.createElement('div');
    card.className = 'gearset-card';
    
    const ownedCount = setData.owned_count;
    
    // Rahmenfarbe
    if (ownedCount === 4) {
        card.classList.add('complete');
    } else if (ownedCount === 0) {
        card.classList.add('none');
    } else {
        card.classList.add('partial');
    }
    
    // Header
    const header = document.createElement('div');
    header.className = 'gearset-header';

    const name = document.createElement('div');
    name.className = 'gearset-name';
    name.textContent = `${setData.set_name} ${setData.variant}`;

    const status = document.createElement('div');
    status.className = 'gearset-status';

    if (ownedCount === 4) {
        status.classList.add('status-complete');
        status.textContent = 'ALL (4/4)';
    } else if (ownedCount === 0) {
        status.classList.add('status-none');
        status.textContent = 'None (0/4)';
    } else {
        status.classList.add('status-partial');
        status.textContent = `${ownedCount}/4`;
    }

    header.appendChild(name);
    header.appendChild(status);

    // Favorite Button for the whole set
    const setFavBtn = document.createElement('button');
    setFavBtn.className = 'favorite-btn gearset-favorite-btn';

    // Check if set is favorite (from localStorage)
    const isFavorite = isGearSetFavorite(setData.set_name, setData.variant);

    if (isFavorite) {
        setFavBtn.classList.add('is-favorite');
        setFavBtn.textContent = '⭐';
    } else {
        setFavBtn.textContent = '☆';
    }

    // Toggle favorite for this set (localStorage only, no API calls)
    setFavBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleGearSetFavorite(setData.set_name, setData.variant);

        // Re-render the sets to update UI
        displayGearSets();
    });

    header.appendChild(setFavBtn);
    card.appendChild(header);
    
    // Parts Grid (2x2)
    const partsGrid = document.createElement('div');
    partsGrid.className = 'gearset-parts';
    
    const partOrder = ['helmet', 'core', 'arms', 'legs'];
    
    partOrder.forEach(partType => {
        const piece = setData.pieces[partType];
        const partDiv = document.createElement('div');
        partDiv.className = 'gearset-part';
        
        if (piece && piece.exists) {
            // Teil existiert in DB
            if (piece.owned) {
                partDiv.classList.add('owned');
            } else {
                partDiv.classList.add('missing');
            }
            
            // Bild mit Placeholder-Fallback
            // Füge partType zum piece-Objekt hinzu für getItemIcon
            piece.partType = partType;
            const iconUrl = getItemIcon(piece, 'medium');
            if (iconUrl) {
                const img = document.createElement('img');
                img.src = iconUrl;
                img.alt = partType;
                img.onerror = function() {
                    // Wenn Bild fehlt, zeige nichts (Placeholder wurde bereits versucht)
                    this.style.display = 'none';
                };
                partDiv.appendChild(img);
            } else {
                // Kein Bild und kein Placeholder verfügbar
                // Zeige einen generischen Placeholder
                const placeholderDiv = document.createElement('div');
                placeholderDiv.style.height = '100px';
                placeholderDiv.style.display = 'flex';
                placeholderDiv.style.alignItems = 'center';
                placeholderDiv.style.justifyContent = 'center';
                placeholderDiv.style.fontSize = '32px';
                placeholderDiv.style.color = '#666';
                placeholderDiv.textContent = '🎮';
                partDiv.appendChild(placeholderDiv);
            }
            
            // Name
            const partName = document.createElement('div');
            partName.className = 'part-name';
            partName.textContent = partType.toUpperCase();
            partDiv.appendChild(partName);

            // KLICKBAR MACHEN!
            if (piece.name) {
                partDiv.style.cursor = 'pointer';
                partDiv.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    // Öffne Modal mit diesem Item
                    try {
                        const itemData = await api.get_item(piece.name);
                        if (itemData) {
                            await showItemModal(itemData);
                        }
                    } catch (error) {
                        console.error('Fehler beim Laden des Items:', error);
                    }
                });
            }
            
        } else {
            // Teil existiert nicht in DB
            partDiv.classList.add('missing');
            const partName = document.createElement('div');
            partName.className = 'part-name';
            partName.textContent = partType.toUpperCase();
            partName.style.color = '#666';
            partDiv.appendChild(partName);
        }
        
        partsGrid.appendChild(partDiv);
    });
    
    card.appendChild(partsGrid);
    
    return card;
}

// NEUE FUNKTION: Speichert Sortierung und Filter
function saveSortAndFilterSettings() {
    localStorage.setItem('sortBy', currentSortBy);
    localStorage.setItem('sortOrder', currentSortOrder);
    localStorage.setItem('categoryFilter', currentCategoryFilter);
    console.log(`✅ Saved settings: SortBy=${currentSortBy}, SortOrder=${currentSortOrder}, CategoryFilter=${currentCategoryFilter}`);
}

// NEUE FUNKTION: Wendet gespeicherte Einstellungen auf UI-Elemente an
function applySavedSettingsToUI() {
    // Sortierungs-Buttons
    document.querySelectorAll('.sort-btn').forEach(b => {
        b.classList.remove('active');
        if (b.dataset.sort === currentSortBy) {
            b.classList.add('active');
        }
    });

    // Sortierreihenfolge-Button
    const sortOrderBtn = document.getElementById('sort-order-btn');
    if (sortOrderBtn) {
        if (currentSortOrder === 'asc') {
            sortOrderBtn.textContent = '⬇️ Aufsteigend';
        } else {
            sortOrderBtn.textContent = '⬆️ Absteigend';
        }
    }
}

function setupEventListeners() {
    // Search input with debounce
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            handleSearch(e.target.value);
        }, 150);
    });
    
    // NEU: Tab-Taste für Autocomplete
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // ESC löscht den Suchtext
            e.preventDefault();
            searchInput.value = '';
            hideAutocomplete();
            hideSearchResults();
            hideItemPreview();
        } else if (e.key === 'Tab') {
            const autocompleteDiv = document.getElementById('autocomplete-dropdown');
            if (autocompleteDiv && !autocompleteDiv.classList.contains('hidden')) {
                e.preventDefault(); // Verhindert Standard Tab-Verhalten

                // Wähle ersten Eintrag aus
                const firstItem = autocompleteDiv.querySelector('.autocomplete-item');
                if (firstItem && selectedAutocompleteIndex === -1) {
                    // Index 0 auswählen
                    selectedAutocompleteIndex = 0;
                    highlightAutocompleteItem(selectedAutocompleteIndex);
                }

                // Übernehme den ausgewählten Eintrag
                if (selectedAutocompleteIndex >= 0) {
                    const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
                    if (items[selectedAutocompleteIndex]) {
                        const itemIndex = parseInt(items[selectedAutocompleteIndex].dataset.index);
                        // Finde das Item aus den Suchergebnissen
                        const query = searchInput.value;
                        const results = fuseInstance ? fuseInstance.search(query).map(r => r.item) : [];
                        if (results[itemIndex]) {
                            selectAutocompleteItem(results[itemIndex]);
                        }
                    }
                }
            }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            navigateAutocomplete(1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            navigateAutocomplete(-1);
        } else if (e.key === 'Enter') {
            const autocompleteDiv = document.getElementById('autocomplete-dropdown');
            if (autocompleteDiv && !autocompleteDiv.classList.contains('hidden') && selectedAutocompleteIndex >= 0) {
                e.preventDefault();
                const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
                if (items[selectedAutocompleteIndex]) {
                    const itemIndex = parseInt(items[selectedAutocompleteIndex].dataset.index);
                    const query = searchInput.value;
                    const results = fuseInstance ? fuseInstance.search(query).map(r => r.item) : [];
                    if (results[itemIndex]) {
                        selectAutocompleteItem(results[itemIndex]);
                    }
                }
            }
        } else if (e.key === 'Escape') {
            hideAutocomplete();
        }
    });

    // Filter inventory (text filter)
    const filterInput = document.getElementById('filter-input');
    filterInput.addEventListener('input', function(e) {
        filterInventory(e.target.value);
    });

    // Sort buttons (if they exist)
    document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active from all sort buttons
            document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
            // Make this button active
            this.classList.add('active');
            // Update sort
            currentSortBy = this.dataset.sort;
            // ÄNDERUNG 2: Sortierung speichern
            saveSortAndFilterSettings();
            loadInventory();
        });
    });

    // Sort order toggle button
    const sortOrderBtn = document.getElementById('sort-order-btn');
    if (sortOrderBtn) {
        sortOrderBtn.addEventListener('click', function() {
            currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            // Update button text
            if (currentSortOrder === 'asc') {
                const text = t('sortAscending') || '⬇️ Aufsteigend';
                this.textContent = '⬇️ ' + (typeof text === 'string' ? text.replace('⬇️ ', '') : 'Aufsteigend');
            } else {
                const text = t('sortDescending') || '⬆️ Absteigend';
                this.textContent = '⬆️ ' + (typeof text === 'string' ? text.replace('⬆️ ', '') : 'Absteigend');
            }
            // ÄNDERUNG 3: Sortierreihenfolge speichern
            saveSortAndFilterSettings();
            loadInventory();
        });
    }

    // Category buttons are set up in loadCategories()
    // No event listener needed here

    // Add button
    const addButton = document.getElementById('add-button');
    addButton.addEventListener('click', addItemToInventory);

    // MODAL CLOSE EVENTS
    setupModalCloseEvents();
    
    // Search limit selector
    const searchLimitSelect = document.getElementById('search-limit');
    searchLimitSelect.addEventListener('change', function(e) {
        saveSearchLimit(parseInt(e.target.value));
        // Trigger search again without clearing the input
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value) {
            handleSearch(searchInput.value);
        }
    });
}

function setupModalCloseEvents() {
    const modal = document.getElementById('item-modal');
    const closeBtn = document.querySelector('.close');
    const modalContent = document.querySelector('.modal-content');
    
    // 1. X-Button klicken
    if (closeBtn) {
        closeBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Close button clicked');
            closeModal();
            return false;
        };
    }
    
    // 2. Außerhalb des Modal-Contents klicken (auf den dunklen Hintergrund)
    if (modal) {
        modal.onclick = function(e) {
            if (e.target === modal) {
                console.log('Clicked outside modal content');
                closeModal();
            }
        };
    }
    
    // 3. Verhindern dass Klicks im Modal-Content das Modal schließen
    if (modalContent) {
        modalContent.onclick = function(e) {
            e.stopPropagation();
        };
    }
    
    // 4. ESC-Taste drücken
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' || e.keyCode === 27) {
            const modal = document.getElementById('item-modal');
            if (modal && !modal.classList.contains('hidden')) {
                console.log('ESC pressed - closing modal');
                closeModal();
            }
        }
    });
}

async function loadCategories() {
    try {
        const categories = await api.get_categories();
        const buttonGrid = document.getElementById('category-buttons');
        
        if (!buttonGrid) {
            console.error('Category buttons container not found');
            return;
        }
        
        // Clear loading message
        buttonGrid.innerHTML = '';
        
        // 1. Add "All" button first
        const allBtn = document.createElement('button');
        allBtn.className = 'category-btn';
        // ÄNDERUNG 4: Aktiver Zustand durch currentCategoryFilter gesteuert
        if (currentCategoryFilter === '') allBtn.classList.add('active');
        allBtn.textContent = '📦 Alle';
        allBtn.dataset.category = '';
        allBtn.addEventListener('click', function() {
            updateCategoryActiveState(this);
            currentCategoryFilter = '';
            // ÄNDERUNG 5: Kategorie speichern
            saveSortAndFilterSettings();
            loadInventory();
        });
        buttonGrid.appendChild(allBtn);

        // 2. NEU: Add "Favorites" button directly after All
        const favBtn = document.createElement('button');
        favBtn.className = 'category-btn';
        // ÄNDERUNG 6: Aktiver Zustand durch currentCategoryFilter gesteuert
        if (currentCategoryFilter === 'Favorites') favBtn.classList.add('active');
        favBtn.textContent = '⭐ Favoriten';
        favBtn.dataset.category = 'Favorites';
        // Spezielles Styling für Favoriten-Button (optional via CSS data-category selector)
        favBtn.addEventListener('click', function() {
            updateCategoryActiveState(this);
            currentCategoryFilter = 'Favorites';
            // ÄNDERUNG 7: Kategorie speichern
            saveSortAndFilterSettings();
            loadInventory();
        });
        buttonGrid.appendChild(favBtn);
        
        // 3. Add dynamic category buttons
        categories.forEach(category => {
            const btn = document.createElement('button');
            btn.className = 'category-btn';
            // ÄNDERUNG 8: Aktiver Zustand durch currentCategoryFilter gesteuert
            if (currentCategoryFilter === category) btn.classList.add('active');
            btn.textContent = category;
            btn.dataset.category = category;
            btn.addEventListener('click', function() {
                updateCategoryActiveState(this);
                currentCategoryFilter = category;
                // ÄNDERUNG 9: Kategorie speichern
                saveSortAndFilterSettings();
                loadInventory();
            });
            buttonGrid.appendChild(btn);
        });
        
        console.log(`✅ Loaded ${categories.length} category buttons + Favorites`);
    } catch (error) {
        console.error('Error loading categories:', error);
        const buttonGrid = document.getElementById('category-buttons');
        if (buttonGrid) {
            buttonGrid.innerHTML = `<div style="color: #f44; padding: 10px;">${t('categoryLoadError')}</div>`;
        }
    }
}

// Helper to handle active state switching
function updateCategoryActiveState(clickedBtn) {
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    clickedBtn.classList.add('active');
}

function loadSearchLimit() {
    const savedLimit = localStorage.getItem('searchLimit');
    const searchLimitSelect = document.getElementById('search-limit');
    
    if (savedLimit) {
        searchLimitSelect.value = savedLimit;
    } else {
        searchLimitSelect.value = '25';
    }
}

function saveSearchLimit(limit) {
    localStorage.setItem('searchLimit', limit);
    console.log(`Search limit set to: ${limit}`);
}

function getSearchLimit() {
    const searchLimitSelect = document.getElementById('search-limit');
    return parseInt(searchLimitSelect.value) || 25;
}

function resetSearchLimit() {
    const searchLimitSelect = document.getElementById('search-limit');
    searchLimitSelect.value = '25';
    saveSearchLimit(25);
    console.log('Search limit reset to 25');
    showNotification(t('searchLimitReset'));
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.background = '#00d9ff';
    notification.style.color = '#000';
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '4px';
    notification.style.zIndex = '10000';
    notification.style.fontWeight = 'bold';
    notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.5)';
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+Shift+R - Reset search limit
        if (e.ctrlKey && e.shiftKey && e.key === 'R') {
            e.preventDefault();
            resetSearchLimit();
        }
    });
}

// ==============================================
// FUSE.JS SMART SEARCH
// ==============================================

// Initialisiere Fuse.js mit allen Items aus der Datenbank
async function initializeFuseSearch() {
    try {
        console.log('🔍 Initialisiere Fuse.js...');
        
        // Hole alle Items aus der DB
        const response = await fetch('/api/search_items_local?query=');
        const items = await response.json();
        
        if (items && items.length > 0) {
            allItemsForSearch = items;
            
            // Fuse.js Konfiguration - OPTIMIERT
            const fuseOptions = {
                keys: [
                    { name: 'name', weight: 0.7 },      // Name höchste Priorität
                    { name: 'category', weight: 0.2 },  // Kategorie mittlere Priorität
                    { name: 'notes', weight: 0.1 }      // Notes niedrigste Priorität
                ],
                threshold: 0.6,              // Lockerer - findet auch Items mit extra Wörtern (Arms, Legs, etc.)
                distance: 100,               // Maximale Distanz für Matches
                minMatchCharLength: 2,       // Minimum 2 Zeichen
                ignoreLocation: true,        // Position im String egal
                findAllMatches: true,        // NEU: Findet alle Matches (wichtig für Multi-Token)
                includeScore: true,          // Score für Ranking
                includeMatches: true,        // Für Highlighting
                shouldSort: true,            // NEU: Automatische Sortierung nach Score
                useExtendedSearch: false     // Standard-Suche ausreichend
            };
            
            fuseInstance = new Fuse(allItemsForSearch, fuseOptions);
            console.log(`✅ Fuse.js bereit mit ${items.length} Items (Multi-Token aktiv)`);
        }
    } catch (error) {
        console.error('Fehler beim Initialisieren von Fuse.js:', error);
    }
}

let selectedAutocompleteIndex = -1;

// NEU: Token-basierte Suche
function tokenSearch(query, items) {
    // Schritt 1: Query in Tokens aufteilen
    const tokens = query.toLowerCase().split(/\s+/).filter(t => t.length >= 2);
    
    if (tokens.length === 0) return [];
    
    // Schritt 2: Items durchsuchen
    const results = [];
    
    items.forEach(item => {
        const itemName = item.name.toLowerCase();
        let score = 0;
        let matchedTokens = 0;
        
        // Prüfe jeden Token
        tokens.forEach(token => {
            if (itemName.includes(token)) {
                matchedTokens++;
                // Bonus: Token am Anfang = besser
                if (itemName.startsWith(token)) {
                    score += 3;
                } else {
                    score += 1;
                }
            }
        });
        
        // NUR Items die ALLE Tokens haben!
        if (matchedTokens === tokens.length) {
            results.push({ item, score });
        }
    });
    
    // Schritt 3: Sortiere nach Score (höher = besser)
    results.sort((a, b) => b.score - a.score);
    
    return results.map(r => r.item);
}

async function handleSearch(query) {
    // Trim whitespace from query
    query = query ? query.trim() : '';
    
    if (!query || query.length < 2) {
        hideSearchResults();
        hideItemPreview();
        hideAutocomplete();
        return;
    }

    try {
        console.time('Token Search');
        
        let results = [];
        
        // NEU: Token-Suche statt Fuse.js
        if (allItemsForSearch && allItemsForSearch.length > 0) {
            results = tokenSearch(query, allItemsForSearch);
            console.log(`🎯 Token-Suche gefunden: ${results.length} Items`);
        } else {
            // Fallback: normale Suche
            console.log('⚠️ Items nicht geladen, Fallback-Suche...');
            results = await api.search_items_local(query);
        }
        
        const limit = getSearchLimit();
        const limitedResults = results ? results.slice(0, limit) : [];
        
        // NUR Search Results anzeigen (KEIN Autocomplete mehr!)
        displaySearchResults(limitedResults, results ? results.length : 0);
        
        // Autocomplete wird NICHT mehr angezeigt
        hideAutocomplete();
        
        console.timeEnd('Token Search');
    } catch (error) {
        console.error('Search error:', error);
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.innerHTML = `<div style="padding: 10px; color: #f44;">${t('searchError')}</div>`;
        resultsDiv.classList.remove('hidden');
    }
}

// Autocomplete Dropdown anzeigen
function displayAutocomplete(items, query) {
    let autocompleteDiv = document.getElementById('autocomplete-dropdown');
    
    if (!autocompleteDiv) {
        // Erstelle Autocomplete Dropdown
        autocompleteDiv = document.createElement('div');
        autocompleteDiv.id = 'autocomplete-dropdown';
        autocompleteDiv.className = 'autocomplete-dropdown';
        
        // Append zum search-controls Container (hat position: relative)
        const searchControls = document.querySelector('.search-controls');
        if (searchControls) {
            searchControls.appendChild(autocompleteDiv);
        }
    }
    
    if (!items || items.length === 0) {
        hideAutocomplete();
        return;
    }
    
    autocompleteDiv.innerHTML = '';
    selectedAutocompleteIndex = -1;
    
    items.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'autocomplete-item';
        div.dataset.index = index;
        
        // Highlight matched text
        const itemName = item.name;
        const lowerName = itemName.toLowerCase();
        const lowerQuery = query.toLowerCase();
        
        let highlightedName = itemName;
        const matchIndex = lowerName.indexOf(lowerQuery);
        
        if (matchIndex !== -1) {
            const before = itemName.substring(0, matchIndex);
            const match = itemName.substring(matchIndex, matchIndex + query.length);
            const after = itemName.substring(matchIndex + query.length);
            highlightedName = `${before}<strong>${match}</strong>${after}`;
        }
        
        div.innerHTML = highlightedName;
        
        div.addEventListener('click', () => {
            selectAutocompleteItem(item);
        });
        
        autocompleteDiv.appendChild(div);
    });
    
    autocompleteDiv.classList.remove('hidden');
}

function hideAutocomplete() {
    const autocompleteDiv = document.getElementById('autocomplete-dropdown');
    if (autocompleteDiv) {
        autocompleteDiv.classList.add('hidden');
        selectedAutocompleteIndex = -1;
    }
}

function selectAutocompleteItem(item) {
    const searchInput = document.getElementById('search-input');
    searchInput.value = item.name;
    hideAutocomplete();
    handleSearch(item.name);
}

// NEU: Navigiere durch Autocomplete mit Pfeiltasten
function navigateAutocomplete(direction) {
    const autocompleteDiv = document.getElementById('autocomplete-dropdown');
    if (!autocompleteDiv || autocompleteDiv.classList.contains('hidden')) return;
    
    const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
    if (items.length === 0) return;
    
    // Berechne neuen Index
    let newIndex = selectedAutocompleteIndex + direction;
    
    // Wrap around
    if (newIndex < 0) newIndex = items.length - 1;
    if (newIndex >= items.length) newIndex = 0;
    
    selectedAutocompleteIndex = newIndex;
    highlightAutocompleteItem(selectedAutocompleteIndex);
}

// NEU: Highlight ausgewähltes Autocomplete-Item
function highlightAutocompleteItem(index) {
    const autocompleteDiv = document.getElementById('autocomplete-dropdown');
    if (!autocompleteDiv) return;
    
    const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
    
    // Entferne alle Highlights
    items.forEach(item => item.classList.remove('selected'));
    
    // Setze neues Highlight
    if (items[index]) {
        items[index].classList.add('selected');
        // Scrolle ins View
        items[index].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
}

function displaySearchResults(localResults, totalCount) {
    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '';

    if (localResults && localResults.length > 0) {
        // NEU: Nur Info-Text anzeigen wenn wir wirklich mehr haben als angezeigt
        if (totalCount && totalCount > localResults.length) {
            const infoDiv = document.createElement('div');
            infoDiv.style.padding = '8px';
            infoDiv.style.background = '#333';
            infoDiv.style.color = '#ffa500';
            infoDiv.style.fontSize = '12px';
            infoDiv.style.borderBottom = '1px solid #444';
            
            // FIXED: Fallback für t() Funktion
            let infoText = `Zeige ${localResults.length} von ${totalCount} Ergebnissen`;
            if (typeof t === 'function') {
                try {
                    const translated = t('searchShowingResults', {shown: localResults.length, total: totalCount});
                    // Prüfe ob Übersetzung ein String ist (nicht ein Objekt oder Funktion)
                    if (typeof translated === 'string') {
                        infoText = translated;
                    }
                } catch (e) {
                    console.warn('Translation error:', e);
                }
            }
            
            infoDiv.textContent = infoText;
            resultsDiv.appendChild(infoDiv);
        }
        
        localResults.forEach(item => {
            try {
                const resultItem = createSearchResultItem(item);
                resultsDiv.appendChild(resultItem);
            } catch (error) {
                console.error('Error creating search result item:', error);
            }
        });
        
        resultsDiv.classList.remove('hidden');
    } else {
        // FIXED: Fallback für t() Funktion
        let noResultsText = 'Keine Ergebnisse gefunden';
        if (typeof t === 'function') {
            try {
                const translated = t('searchNoResults');
                if (typeof translated === 'string') {
                    noResultsText = translated;
                }
            } catch (e) {
                console.warn('Translation error:', e);
            }
        }
        
        resultsDiv.innerHTML = `<div style="padding: 10px; color: #888;">${noResultsText}</div>`;
        resultsDiv.classList.remove('hidden');
    }
}

function createSearchResultItem(item) {
    const div = document.createElement('div');
    div.className = 'search-result-item';
    div.style.display = 'flex';
    div.style.alignItems = 'center';
    div.style.gap = '5px';

    // Use THUMB for search results (klein, schnell) - JETZT ZUERST!
    const iconUrl = getItemIcon(item, 'thumb');
    if (iconUrl) {
        const img = document.createElement('img');
        img.src = iconUrl;
        img.className = 'search-item-thumbnail';
        img.alt = item.name;
        img.style.width = '32px';
        img.style.height = '32px';
        img.style.objectFit = 'contain';
        img.style.marginLeft = '8px';
        img.style.marginRight = '8px';
        img.loading = 'lazy';
        img.onerror = function() {
            // Fallback zum Gamecontroller wenn Bild fehlt
            const icon = document.createElement('span');
            icon.style.fontSize = '24px';
            icon.style.marginLeft = '8px';
            icon.style.marginRight = '8px';
            icon.textContent = '🎮';
            this.replaceWith(icon);
        };
        div.appendChild(img);
    } else {
        const icon = document.createElement('span');
        icon.style.fontSize = '24px';
        icon.style.marginLeft = '8px';
        icon.style.marginRight = '8px';
        icon.textContent = '🎮';
        div.appendChild(icon);
    }

    // Minus button
    const minusBtn = document.createElement('button');
    minusBtn.textContent = '−';
    minusBtn.className = 'search-quick-btn search-btn-minus';
    minusBtn.disabled = item.count === 0;
    minusBtn.style.opacity = item.count === 0 ? '0.3' : '1';
    minusBtn.style.cursor = item.count === 0 ? 'not-allowed' : 'pointer';
    minusBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (item.count > 0) {
            // Finde die Zahl-Anzeige DIREKT (im gleichen div)
            const parentDiv = e.target.closest('.search-result-item');
            const countSpan = parentDiv.querySelector('.search-item-count');

            await quickUpdateCount(item, -1, countSpan, minusBtn);
        }
    });
    div.appendChild(minusBtn);

    // Plus button
    const plusBtn = document.createElement('button');
    plusBtn.textContent = '+';
    plusBtn.className = 'search-quick-btn search-btn-plus';
    plusBtn.addEventListener('click', async (e) => {
        e.stopPropagation();

        // Finde die Zahl-Anzeige DIREKT (im gleichen div)
        const parentDiv = e.target.closest('.search-result-item');
        const countSpan = parentDiv.querySelector('.search-item-count');
        const minusBtnInDiv = parentDiv.querySelector('.search-btn-minus');

        await quickUpdateCount(item, 1, countSpan, minusBtnInDiv);
    });
    div.appendChild(plusBtn);
    
    // Item name
    const nameSpan = document.createElement('span');
    nameSpan.className = 'search-item-name';
    nameSpan.textContent = item.name;
    nameSpan.style.flex = '1';
    nameSpan.style.cursor = 'pointer';
    nameSpan.addEventListener('click', async () => {
        hideSearchResults();
        await showItemModal(item);
    });
    div.appendChild(nameSpan);
    
    // Count display (RECHTS)
    const countSpan = document.createElement('span');
    countSpan.className = 'search-item-count';
    countSpan.textContent = `${item.count}x`;
    countSpan.style.marginRight = '10px';
    countSpan.style.color = item.count > 0 ? '#00d9ff' : '#666';
    countSpan.style.fontWeight = 'bold';
    countSpan.style.minWidth = '40px';
    countSpan.style.textAlign = 'right';
    div.appendChild(countSpan);
    
    return div;
}

async function quickUpdateCount(item, delta, countSpan = null, minusBtn = null) {
    try {
        // Item-Daten sind schon da - kein get_item() mehr nötig!
        const itemName = item.name;
        const oldCount = item.count;
        const newCount = Math.max(0, oldCount + delta);
        await api.update_count(itemName, newCount);
        
        // WICHTIG: Item-Objekt aktualisieren für nächsten Klick!
        item.count = newCount;
        
        // SOFORT: UI updaten (falls Elemente übergeben wurden)
        if (countSpan) {
            countSpan.textContent = `${newCount}x`;
            countSpan.style.color = newCount > 0 ? '#00d9ff' : '#666';
            // Visueller Effekt
            countSpan.style.transition = 'transform 0.15s';
            countSpan.style.transform = 'scale(1.3)';
            setTimeout(() => {
                countSpan.style.transform = 'scale(1)';
            }, 150);
        }
        
        // Minus-Button Status updaten (falls übergeben)
        if (minusBtn) {
            minusBtn.disabled = newCount === 0;
            minusBtn.style.opacity = newCount === 0 ? '0.3' : '1';
            minusBtn.style.cursor = newCount === 0 ? 'not-allowed' : 'pointer';
        }
        
        // Clear cache
        searchCache = {};
        
        // NEU: Refresh Gear-Set falls betroffen
        await refreshGearSetIfNeeded(itemName);
        
        // OPTIMIERUNG: Nur bei echten Inventar-Änderungen neu laden
        // Fall 1: Item wird ins Inventar hinzugefügt (0 -> 1+)
        if (oldCount === 0 && newCount > 0) {
            await loadInventory();
            await loadStats();
        }
        // Fall 2: Item wird aus Inventar entfernt (1+ -> 0) 
        else if (oldCount > 0 && newCount === 0) {
            await loadInventory();
            await loadStats();
        }
        // Fall 3: Nur Count-Änderung - KEIN RELOAD, nur UI update
        else {
            // Update im Inventar-Grid (wenn sichtbar)
            const inventoryItem = document.querySelector(`.inventory-item[data-name="${CSS.escape(itemName)}"]`);
            if (inventoryItem) {
                const countElement = inventoryItem.querySelector('.count');
                if (countElement) {
                    countElement.textContent = `${newCount}x`;
                    // Optionaler visueller Effekt
                    countElement.style.transition = 'transform 0.2s';
                    countElement.style.transform = 'scale(1.2)';
                    setTimeout(() => {
                        countElement.style.transform = 'scale(1)';
                    }, 200);
                }
            }
            
            // Update in Suchergebnissen
            const searchResults = document.querySelectorAll('.search-result-item');
            searchResults.forEach(result => {
                const nameSpan = result.querySelector('.search-item-name');
                if (nameSpan && nameSpan.textContent === itemName) {
                    const countSpan = result.querySelector('.search-item-count');
                    if (countSpan) {
                        countSpan.textContent = `${newCount}x`;
                        countSpan.style.color = newCount > 0 ? '#00d9ff' : '#666';
                    }
                    
                    // Minus-Button Status updaten
                    const minusBtn = result.querySelector('.search-btn-minus');
                    if (minusBtn) {
                        minusBtn.disabled = newCount === 0;
                        minusBtn.style.opacity = newCount === 0 ? '0.3' : '1';
                        minusBtn.style.cursor = newCount === 0 ? 'not-allowed' : 'pointer';
                    }
                }
            });
            
            // Stats verzögert updaten (nicht blockierend)
            setTimeout(() => loadStats(), 500);
        }
        
        // FOKUS ZURÜCKSETZEN - Wichtig für schnelles Arbeiten!
        // Prüfe welches Feld aktiv war und setze Fokus zurück
        const searchInput = document.getElementById('search-input');
        const filterInput = document.getElementById('filter-input');
        
        if (searchInput && searchInput.value && searchInput.value.length >= 2) {
            // Wenn in der Suche etwas steht, Fokus zurück auf Suche
            searchInput.focus();
            // Cursor ans Ende setzen
            searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
        } else if (filterInput && filterInput.value) {
            // Wenn im Inventar-Filter etwas steht, Fokus zurück auf Filter
            filterInput.focus();
            filterInput.setSelectionRange(filterInput.value.length, filterInput.value.length);
        } else if (searchInput) {
            // Sonst Standard: Fokus auf Suchfeld
            searchInput.focus();
        }
    } catch (error) {
        console.error('Error updating count:', error);
        alert(t('errorUpdating'));
    }
}

async function addItemToInventory() {
    if (!currentItem) return;

    try {
        const result = await api.add_item(
            currentItem.name,
            currentItem.item_type || null,
            currentItem.image_url || null,
            null,
            1
        );

        if (result.success) {
            // NEU: Refresh Gear-Set falls betroffen
            await refreshGearSetIfNeeded(currentItem.name);
            
            await loadInventory();
            await loadStats();
            await loadCategories();
            
            document.getElementById('search-input').value = '';
            hideSearchResults();
            hideItemPreview();
            
            alert(t('itemAdded', {name: currentItem.name}));
        } else {
            alert(t('errorAdding') + ': ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error adding item:', error);
        alert(t('errorAdding'));
    }
}

// NEU: Toggle Favorite Function
async function toggleFavorite(itemName, isFavorite) {
    try {
        const response = await fetch('/api/toggle_favorite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: itemName, is_favorite: isFavorite })
        });

        const result = await response.json();
        
        if (result.success) {
            // NEU: Refresh Gear-Set falls betroffen (auch wenn nur Favorite geändert wird)
            await refreshGearSetIfNeeded(itemName);
            
            // Reload inventory to update view (especially if in Favorites category)
            await loadInventory();
            
            // Optional: Auch Stats updaten, da sich die Favorites-Kategorie geändert hat
            await loadStats();
        } else {
            alert(t('errorUpdating') + ': ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
        alert(t('errorUpdating'));
    }
}

async function loadInventory() {
    try {
        console.time('Load Inventory');
        
        // Build query parameters
        const params = new URLSearchParams({
            sort_by: currentSortBy,
            sort_order: currentSortOrder
        });
        
        // NEU: Filter Logik für Favorites vs Normale Kategorien
        if (currentCategoryFilter === 'Favorites') {
            params.append('is_favorite', '1');
        } else if (currentCategoryFilter) {
            // Achtung: Backend erwartet 'category', Frontend verwendete früher 'category_filter'
            // Wir senden 'category' passend zum neuen Backend
            params.append('category', currentCategoryFilter);
        }
        
        // NOTE: Wir nutzen hier direkt fetch, da api-adapter.js ggf. nicht flexibel genug für Custom Params ist
        const response = await fetch(`/api/get_inventory_items?${params}`);
        if (!response.ok) {
            throw new Error('Failed to load inventory');
        }
        const items = await response.json();
        
        console.log(`✅ Loaded ${items.length} inventory items (${currentSortBy} ${currentSortOrder}, Filter: ${currentCategoryFilter})`);
        displayInventory(items);
        console.timeEnd('Load Inventory');
    } catch (error) {
        console.error('Error loading inventory:', error);
        const grid = document.getElementById('inventory-grid');
        grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #f44;">${t('inventoryLoadError')}</p>`;
    }
}

function displayInventory(items) {
    const grid = document.getElementById('inventory-grid');
    grid.innerHTML = '';

    if (!items || items.length === 0) {
        const message = currentCategoryFilter 
            ? t('inventoryCategoryEmpty', {category: currentCategoryFilter})
            : t('inventoryEmpty');
        grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #888;">${message}</p>`;
        return;
    }

    items.forEach(item => {
        const itemDiv = createInventoryItem(item);
        grid.appendChild(itemDiv);
    });
}

function createInventoryItem(item) {
    const div = document.createElement('div');
    div.className = 'inventory-item';
    div.dataset.name = item.name;
    div.style.position = 'relative';
    
    // Use MEDIUM for inventory grid with intelligent fallback
    const iconUrl = getItemIcon(item, 'medium');
    if (iconUrl) {
        const img = document.createElement('img');
        img.src = iconUrl;
        img.alt = item.name;
        img.style.width = '100%';
        img.style.height = '120px';
        img.style.objectFit = 'contain';
        img.style.background = '#222';
        img.loading = 'lazy';
        img.onerror = function() {
            this.style.display = 'none';
            const placeholder = document.createElement('div');
            placeholder.style.height = '120px';
            placeholder.style.background = '#333';
            placeholder.style.display = 'flex';
            placeholder.style.alignItems = 'center';
            placeholder.style.justifyContent = 'center';
            placeholder.style.fontSize = '48px';
            placeholder.textContent = '🎮';
            div.insertBefore(placeholder, div.firstChild);
        };
        div.appendChild(img);
    } else {
        const placeholder = document.createElement('div');
        placeholder.className = 'item-placeholder';
        placeholder.style.background = '#333';
        placeholder.style.height = '120px';
        placeholder.style.display = 'flex';
        placeholder.style.alignItems = 'center';
        placeholder.style.justifyContent = 'center';
        placeholder.style.color = '#666';
        placeholder.style.fontSize = '48px';
        placeholder.textContent = '🎮';
        div.appendChild(placeholder);
    }
    
    // NEU: Favorite Button (Oben Links)
    const favBtn = document.createElement('button');
    favBtn.className = 'favorite-btn';
    if (item.is_favorite) {
        favBtn.classList.add('is-favorite');
        favBtn.title = 'Unfavorite'; // Tooltip
    } else {
        favBtn.title = 'Favorite'; // Tooltip
    }
    favBtn.innerHTML = '★'; // Stern Unicode
    
    // Event Listener für Favoriten-Button
    favBtn.addEventListener('click', async (e) => {
        e.stopPropagation(); // Verhindert das Öffnen des Modals
        await toggleFavorite(item.name, !item.is_favorite);
    });
    div.appendChild(favBtn);
    
    // Quick action buttons (Oben Rechts)
    const quickActions = document.createElement('div');
    quickActions.style.position = 'absolute';
    quickActions.style.top = '5px';
    quickActions.style.right = '5px';
    quickActions.style.display = 'flex';
    quickActions.style.flexDirection = 'column';
    quickActions.style.gap = '3px';
    quickActions.style.zIndex = '10';
    
    // Plus button
    const plusBtn = document.createElement('button');
    plusBtn.textContent = '+';
    plusBtn.style.width = '30px';
    plusBtn.style.height = '30px';
    plusBtn.style.fontSize = '18px';
    plusBtn.style.fontWeight = 'bold';
    plusBtn.style.border = 'none';
    plusBtn.style.borderRadius = '4px';
    plusBtn.style.background = '#00d9ff';
    plusBtn.style.color = '#000';
    plusBtn.style.cursor = 'pointer';
    plusBtn.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
    plusBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        await quickUpdateCount(item, 1, null, null);
    });
    
    // Minus button
    const minusBtn = document.createElement('button');
    minusBtn.textContent = '−';
    minusBtn.style.width = '30px';
    minusBtn.style.height = '30px';
    minusBtn.style.fontSize = '18px';
    minusBtn.style.fontWeight = 'bold';
    minusBtn.style.border = 'none';
    minusBtn.style.borderRadius = '4px';
    minusBtn.style.background = '#ff4444';
    minusBtn.style.color = '#fff';
    minusBtn.style.cursor = 'pointer';
    minusBtn.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
    minusBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        await quickUpdateCount(item, -1, null, null);
    });
    
    quickActions.appendChild(plusBtn);
    quickActions.appendChild(minusBtn);
    div.appendChild(quickActions);
    
    // Name
    const name = document.createElement('h3');
    name.textContent = item.name;
    div.appendChild(name);
    
    // Count
    const count = document.createElement('div');
    count.className = 'count';
    count.textContent = `${item.count}x`;
    div.appendChild(count);
    
    // Click to open modal
    div.addEventListener('click', () => showItemModal(item));
    
    return div;
}

function filterInventory(query) {
    // Trim query
    query = query ? query.trim() : '';
    
    const items = document.querySelectorAll('.inventory-item');
    
    // Wenn leer: alles zeigen
    if (!query || query.length < 2) {
        items.forEach(item => item.style.display = 'block');
        return;
    }
    
    // NEU: Token-Suche statt Fuse.js
    if (allItemsForSearch && allItemsForSearch.length > 0) {
        const results = tokenSearch(query, allItemsForSearch);
        const matchedNames = new Set(results.map(r => r.name));
        
        items.forEach(item => {
            const name = item.dataset.name;
            if (matchedNames.has(name)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
        
        console.log(`🎯 Token-Filter: ${matchedNames.size} von ${items.length} Items gefunden`);
    } else {
        // Fallback: Simples String-Matching
        const lowerQuery = query.toLowerCase();
        items.forEach(item => {
            const name = (item.dataset.name || '').toLowerCase();
            if (name.includes(lowerQuery)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
}

async function showItemModal(item) {
    selectedItemForModal = item;
    
    console.log('Opening modal for:', item.name);
    console.time('Modal Load');
    
    // Show modal immediately
    document.getElementById('modal-name').textContent = item.name;
    const modalImage = document.getElementById('modal-image');
    const countInput = document.getElementById('modal-count');
    const notesInput = document.getElementById('modal-notes');
    
    // Placeholder
    modalImage.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="512" height="512"%3E%3Crect fill="%23333" width="512" height="512"/%3E%3Ctext x="50%25" y="50%25" font-size="64" text-anchor="middle" dy=".3em" fill="%23666"%3E🎮%3C/text%3E%3C/svg%3E';
    
    countInput.value = item.count || 0;
    notesInput.value = '';
    
    const modal = document.getElementById('item-modal');
    modal.classList.remove('hidden');
    
    // Load full item data asynchronously
    try {
        const itemData = await api.get_item(item.name);
        if (!itemData) {
            console.timeEnd('Modal Load');
            return;
        }
        
        countInput.value = itemData.count;
        notesInput.value = itemData.notes || '';
        
        // Use FULL/ORIGINAL image for modal
        if (itemData.full_url) {
            modalImage.src = itemData.full_url;
            console.log('✅ Full image loaded from:', itemData.full_url);
        } else if (itemData.thumb_url) {
            // Fallback to thumb if full doesn't exist
            modalImage.src = itemData.thumb_url;
            console.log('⚠️ Using thumb as fallback:', itemData.thumb_url);
        }
        
        console.timeEnd('Modal Load');
    } catch (error) {
        console.error('Error loading item data:', error);
        console.timeEnd('Modal Load');
    }
    
    // AUTO-SAVE setup
    // Remove old event listeners by replacing the elements
    const newCountInput = countInput.cloneNode(true);
    const newNotesInput = notesInput.cloneNode(true);
    countInput.parentNode.replaceChild(newCountInput, countInput);
    notesInput.parentNode.replaceChild(newNotesInput, notesInput);
    
    const itemName = item.name;
    
    // Count auto-save
    let countSaveTimeout;
    newCountInput.addEventListener('input', () => {
        clearTimeout(countSaveTimeout);
        countSaveTimeout = setTimeout(async () => {
            const newCount = parseInt(newCountInput.value) || 0;
            
            if (newCount <= 0) {
                const confirmed = confirm(t('modalConfirmZero', {name: itemName}));
                if (!confirmed) {
                    newCountInput.value = item.count;
                    return;
                }
            }
            
            await autoSaveCount(itemName, newCount);
        }, 500);
    });
    
    // Notes auto-save
    let notesSaveTimeout;
    newNotesInput.addEventListener('input', () => {
        clearTimeout(notesSaveTimeout);
        notesSaveTimeout = setTimeout(async () => {
            await autoSaveNotes(itemName, newNotesInput.value);
        }, 1000);
    });
}

async function autoSaveCount(itemName, newCount) {
    try {
        await api.update_count(itemName, newCount);
        searchCache = {};
        
        // NEU: Refresh Gear-Set falls betroffen
        await refreshGearSetIfNeeded(itemName);
        
        await loadInventory();
        await loadStats();
        console.log(`✅ Auto-saved count for ${itemName}: ${newCount}`);
    } catch (error) {
        console.error('Error auto-saving count:', error);
        alert(t('errorAutoSave'));
    }
}

async function autoSaveNotes(itemName, newNotes) {
    try {
        await api.update_notes(itemName, newNotes);
        console.log(`✅ Auto-saved notes for ${itemName}`);
    } catch (error) {
        console.error('Error auto-saving notes:', error);
    }
}

function closeModal() {
    console.log('Closing modal');
    const modal = document.getElementById('item-modal');
    modal.classList.add('hidden');
    selectedItemForModal = null;
}

function changeCount(delta) {
    const countInput = document.getElementById('modal-count');
    let newValue = parseInt(countInput.value) + delta;
    if (newValue < 0) newValue = 0;
    countInput.value = newValue;
    countInput.dispatchEvent(new Event('input'));
}

async function deleteItem() {
    if (!selectedItemForModal) return;
    
    if (confirm(t('modalConfirmDelete', {name: selectedItemForModal.name}))) {
        try {
            const itemName = selectedItemForModal.name;
            await api.delete_item(itemName);
            
            // NEU: Refresh Gear-Set falls betroffen
            await refreshGearSetIfNeeded(itemName);
            
            await loadInventory();
            await loadStats();
            await loadCategories();
            closeModal();
        } catch (error) {
            console.error('Error deleting item:', error);
            alert(t('errorDeleting'));
        }
    }
}

async function loadStats() {
    try {
        const stats = await api.get_stats();
        
        // Haupt-Statistiken
        document.getElementById('total-items-db').textContent = stats.total_items_in_db;
        document.getElementById('inventory-unique-items').textContent = stats.inventory_unique_items;
        document.getElementById('total-count').textContent = stats.total_item_count;
        document.getElementById('cache-size').textContent = stats.cache_size_mb + ' MB';
        
        // Kategorie-Statistiken
        const categoryStatsDiv = document.getElementById('category-stats');
        if (categoryStatsDiv && stats.category_counts) {
            categoryStatsDiv.innerHTML = '';
            
            // Sortiere Kategorien alphabetisch
            const sortedCategories = Object.keys(stats.category_counts).sort();
            
            if (sortedCategories.length > 0) {
                // Titel für Kategorie-Stats
                const title = document.createElement('h3');
                title.textContent = t('statsByCategory');
                title.style.color = '#00d9ff';
                title.style.fontSize = '1.2em';
                title.style.marginTop = '20px';
                title.style.marginBottom = '10px';
                categoryStatsDiv.appendChild(title);
                
                // Grid für Kategorie-Stats
                const grid = document.createElement('div');
                grid.className = 'category-stats-grid';
                
                sortedCategories.forEach(category => {
                    const count = stats.category_counts[category];
                    if (count > 0) {
                        const statItem = document.createElement('div');
                        statItem.className = 'category-stat-item';
                        
                        const label = document.createElement('span');
                        label.className = 'category-stat-label';
                        label.textContent = category + ':';
                        
                        const value = document.createElement('span');
                        value.className = 'category-stat-value';
                        value.textContent = count;
                        
                        statItem.appendChild(label);
                        statItem.appendChild(value);
                        grid.appendChild(statItem);
                    }
                });
                
                categoryStatsDiv.appendChild(grid);
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function hideSearchResults() {
    document.getElementById('search-results').classList.add('hidden');
}

function hideItemPreview() {
    document.getElementById('item-preview').classList.add('hidden');
    currentItem = null;
}

// ==============================================
// STICKY HEADER SCROLL-DETECTION
// Ziehharmonika-Effekt beim Scrollen der gesamten Seite
// ==============================================

function setupStickyHeaderScrolling() {
    const viewNavigation = document.querySelector('.view-navigation');
    const searchSection = document.querySelector('.search-section');
    const inventoryHeader = document.querySelector('.inventory-header');
    const gearsetsHeader = document.querySelector('.gearsets-header');
    
    // Lausche auf window-Scroll (gesamte Seite)
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Bei >50px Scroll: Compact-Modus aktivieren
        if (scrollTop > 50) {
            // View-Navigation kompakter machen
            if (viewNavigation) {
                viewNavigation.classList.add('compact');
            }
            
            // Search-Section kompakter machen
            if (searchSection) {
                searchSection.classList.add('compact');
            }
            
            // Inventar-Header kompakter machen (wenn sichtbar)
            if (inventoryHeader) {
                inventoryHeader.classList.add('compact');
            }
            
            // Gear-Sets-Header kompakter machen (wenn sichtbar)
            if (gearsetsHeader) {
                gearsetsHeader.classList.add('compact');
            }
        } else {
            // Zurück zum Normal-Zustand
            if (viewNavigation) {
                viewNavigation.classList.remove('compact');
            }
            
            if (searchSection) {
                searchSection.classList.remove('compact');
            }
            
            if (inventoryHeader) {
                inventoryHeader.classList.remove('compact');
            }
            
            if (gearsetsHeader) {
                gearsetsHeader.classList.remove('compact');
            }
        }
    });
    
    console.log('✅ Ziehharmonika-Effekt (Sticky Header + Search) aktiviert');
}