// GearCrate - Frontend Logic with Sorting & Filtering
// Image sizes: Thumb (search) → Medium (inventory) → Full (modal)

let currentItem = null;
let searchTimeout = null;
let selectedItemForModal = null;
let searchCache = {};
// ÄNDERUNG 1: Initialwerte aus localStorage laden
let currentSortBy = localStorage.getItem('sortBy') || 'name';
let currentSortOrder = localStorage.getItem('sortOrder') || 'asc';
let currentCategoryFilter = localStorage.getItem('categoryFilter') || '';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // NEU: Anwendung der geladenen Einstellungen auf die UI
    applySavedSettingsToUI();
    
    loadInventory();
    loadStats();
    // loadCategories muss NACH applySavedSettingsToUI laufen, 
    // da es currentCategoryFilter zur Bestimmung des aktiven Buttons nutzt
    loadCategories(); 
    setupEventListeners();
    loadSearchLimit();
    setupKeyboardShortcuts();
});

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
            // Sicherstellen, dass der Text die aktuelle Sprache berücksichtigt (falls i18n geladen ist)
            const text = (typeof t === 'function' && t('sortAscending') !== 'sortAscending') 
                ? t('sortAscending') : '⬇️ Aufsteigend';
            sortOrderBtn.textContent = '⬇️ ' + text.replace('⬇️ ', '');
        } else {
            const text = (typeof t === 'function' && t('sortDescending') !== 'sortDescending') 
                ? t('sortDescending') : '⬆️ Absteigend';
            sortOrderBtn.textContent = '⬆️ ' + text.replace('⬆️ ', '');
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
                this.textContent = '⬇️ ' + t('sortAscending').replace('⬇️ ', '');
            } else {
                this.textContent = '⬆️ ' + t('sortDescending').replace('⬆️ ', '');
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
        allBtn.textContent = '📦 ' + t('categoryAll');
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
        // Versuche Übersetzung zu nutzen oder Fallback
        const favText = (typeof t === 'function' && t('categoryFavorites') !== 'categoryFavorites') ? t('categoryFavorites') : 'Favorites';
        favBtn.textContent = '⭐ ' + favText;
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

async function handleSearch(query) {
    // Trim whitespace from query
    query = query ? query.trim() : '';
    
    if (!query || query.length < 2) {
        hideSearchResults();
        hideItemPreview();
        return;
    }

    try {
        console.time('Search');
        
        // Check cache first
        let localResults;
        if (searchCache[query]) {
            console.log('✅ Using cached results for:', query);
            localResults = searchCache[query];
        } else {
            console.log('🔍 Searching database for:', query);
            localResults = await api.search_items_local(query);
            searchCache[query] = localResults;
        }
        
        const limit = getSearchLimit();
        const limitedResults = localResults ? localResults.slice(0, limit) : [];
        
        displaySearchResults(limitedResults, localResults ? localResults.length : 0);
        
        console.timeEnd('Search');
    } catch (error) {
        console.error('Search error:', error);
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.innerHTML = `<div style="padding: 10px; color: #f44;">${t('searchError')}</div>`;
        resultsDiv.classList.remove('hidden');
    }
}

function displaySearchResults(localResults, totalCount) {
    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '';

    if (localResults && localResults.length > 0) {
        if (totalCount && totalCount > localResults.length) {
            const infoDiv = document.createElement('div');
            infoDiv.style.padding = '8px';
            infoDiv.style.background = '#333';
            infoDiv.style.color = '#ffa500';
            infoDiv.style.fontSize = '12px';
            infoDiv.style.borderBottom = '1px solid #444';
            infoDiv.textContent = t('searchShowingResults', {shown: localResults.length, total: totalCount});
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
        resultsDiv.innerHTML = `<div style="padding: 10px; color: #888;">${t('searchNoResults')}</div>`;
        resultsDiv.classList.remove('hidden');
    }
}

function createSearchResultItem(item) {
    const div = document.createElement('div');
    div.className = 'search-result-item';
    div.style.display = 'flex';
    div.style.alignItems = 'center';
    div.style.gap = '5px';
    
    // Minus button (JETZT LINKS)
    const minusBtn = document.createElement('button');
    minusBtn.textContent = '−';
    minusBtn.className = 'search-quick-btn search-btn-minus';
    minusBtn.disabled = item.count === 0;
    minusBtn.style.opacity = item.count === 0 ? '0.3' : '1';
    minusBtn.style.cursor = item.count === 0 ? 'not-allowed' : 'pointer';
    minusBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (item.count > 0) {
            await quickUpdateCount(item.name, -1);
        }
    });
    div.appendChild(minusBtn);
    
    // Plus button (JETZT LINKS)
    const plusBtn = document.createElement('button');
    plusBtn.textContent = '+';
    plusBtn.className = 'search-quick-btn search-btn-plus';
    plusBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        await quickUpdateCount(item.name, 1);
    });
    div.appendChild(plusBtn);
    
    // Use THUMB for search results (256x256)
    if (item.icon_url) {
        const img = document.createElement('img');
        img.src = item.icon_url;
        img.className = 'search-item-thumbnail';
        img.alt = item.name;
        img.style.width = '32px';
        img.style.height = '32px';
        img.style.objectFit = 'contain';
        img.style.marginLeft = '8px';
        img.style.marginRight = '8px';
        img.loading = 'lazy';
        img.onerror = function() {
            this.style.display = 'none';
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

async function quickUpdateCount(itemName, delta) {
    try {
        const item = await api.get_item(itemName);
        if (!item) {
            console.error('Item not found:', itemName);
            return;
        }
        
        const newCount = Math.max(0, item.count + delta);
        await api.update_count(itemName, newCount);
        
        // Clear cache
        searchCache = {};
        
        await loadInventory();
        await loadStats();
        
        // Refresh search results
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value && searchInput.value.length >= 2) {
            await handleSearch(searchInput.value);
        }
        
        // FOKUS ZURÜCKSETZEN - Wichtig für schnelles Arbeiten!
        // Prüfe welches Feld aktiv war und setze Fokus zurück
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
    
    // Use MEDIUM for inventory grid (512x512)
    if (item.thumb_url) {
        const img = document.createElement('img');
        img.src = item.thumb_url;
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
        await quickUpdateCount(item.name, 1);
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
        await quickUpdateCount(item.name, -1);
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
    // Trim and normalize query
    query = query ? query.trim().toLowerCase() : '';
    
    const items = document.querySelectorAll('.inventory-item');
    
    items.forEach(item => {
        const name = (item.dataset.name || '').toLowerCase();
        if (!query || name.includes(query)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
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
            await api.delete_item(selectedItemForModal.name);
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