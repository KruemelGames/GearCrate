/**
 * app_panels.js - Adapter für Dropdown-Panel Layout
 * Überschreibt spezifische Funktionen für das neue Panel-System
 */

// Override displaySearchResults() für linkes Panel mit Ergebniszähler
const originalDisplaySearchResults = displaySearchResults;

function displaySearchResults(localResults, totalCount) {
    const resultsDiv = document.getElementById('search-results');
    const resultsLabel = document.getElementById('searchResultsLabel');
    const resultsCount = document.getElementById('searchResultsCount');

    resultsDiv.innerHTML = '';

    if (localResults && localResults.length > 0) {
        // Show results count label
        if (resultsLabel && resultsCount) {
            resultsCount.textContent = localResults.length;
            resultsLabel.style.display = 'block';
        }

        // Expand panel
        window.expandSearchPanel(true);

        localResults.forEach(item => {
            try {
                const resultItem = createSearchResultItem(item);
                resultsDiv.appendChild(resultItem);
            } catch (error) {
                console.error('Error creating search result item:', error);
            }
        });

        resultsDiv.classList.remove('hidden');
        resultsDiv.classList.add('visible'); // Für Panel-CSS
    } else {
        // No results
        if (resultsLabel) {
            resultsLabel.style.display = 'none';
        }

        let noResultsText = 'Keine Ergebnisse gefunden';
        if (typeof tr === 'function') {
            try {
                const translated = tr('searchNoResults');
                if (typeof translated === 'string') {
                    noResultsText = translated;
                }
            } catch (e) {
                console.warn('Translation error:', e);
            }
        }

        resultsDiv.innerHTML = `<div class="no-results">${noResultsText}</div>`;
        resultsDiv.classList.remove('hidden');
        resultsDiv.classList.add('visible');
        window.expandSearchPanel(true);
    }
}

// Override hideSearchResults() für linkes Panel
const originalHideSearchResults = hideSearchResults;

function hideSearchResults() {
    const resultsDiv = document.getElementById('search-results');
    const resultsLabel = document.getElementById('searchResultsLabel');

    if (resultsDiv) {
        resultsDiv.innerHTML = '';
        resultsDiv.classList.add('hidden');
        resultsDiv.classList.remove('visible');
    }

    if (resultsLabel) {
        resultsLabel.style.display = 'none';
    }

    window.expandSearchPanel(false); // Collapse panel
}

// Override loadCategories() für rechtes Panel
async function loadCategories() {
    try {
        const categories = await api.get_categories();
        const buttonGrid = document.getElementById('category-buttons-panel'); // NEU: Rechtes Panel

        if (!buttonGrid) {
            console.error('Category buttons container not found');
            return;
        }

        // Clear loading message
        buttonGrid.innerHTML = '';

        // 1. Add "All" button first
        const allBtn = document.createElement('button');
        allBtn.className = 'category-btn-panel'; // NEU: Panel-Klasse
        if (currentCategoryFilter === '') allBtn.classList.add('active');
        allBtn.textContent = '📦';
        allBtn.title = tr('categoryAll');
        allBtn.dataset.category = '';
        allBtn.addEventListener('click', function() {
            updateCategoryActiveState(this);
            currentCategoryFilter = '';
            saveSortAndFilterSettings();
            loadInventory();
        });
        buttonGrid.appendChild(allBtn);

        // 2. Add "Favorites" button (muss 'Favorites' String verwenden, nicht Emoji!)
        const favBtn = document.createElement('button');
        favBtn.className = 'category-btn-panel'; // NEU: Panel-Klasse
        if (currentCategoryFilter === 'Favorites') favBtn.classList.add('active');
        favBtn.textContent = '⭐';
        favBtn.title = tr('categoryFavorites');
        favBtn.dataset.category = 'Favorites';
        favBtn.addEventListener('click', function() {
            updateCategoryActiveState(this);
            currentCategoryFilter = 'Favorites';
            saveSortAndFilterSettings();
            loadInventory();
        });
        buttonGrid.appendChild(favBtn);

        // 3. Sortiere Kategorien in gewünschter Reihenfolge
        const categoryOrder = [
            'Helmet', 'Arms',
            'Torso', 'Legs',
            'Undersuit', 'Backpack',
            'Hat', 'Shirt',
            'Hands', 'Eyes',
            'Jacket', 'Pants',
            'Shoes', 'Jumpsuit'
        ];

        // Erstelle sortierte Liste
        const sortedCategories = [];
        categoryOrder.forEach(catName => {
            if (categories.includes(catName)) {
                sortedCategories.push(catName);
            }
        });

        // Füge übrige Kategorien hinzu (falls welche nicht in der Order-Liste sind)
        categories.forEach(cat => {
            if (!sortedCategories.includes(cat)) {
                sortedCategories.push(cat);
            }
        });

        // 4. Add category buttons mit placeholder Bildern in sortierter Reihenfolge
        sortedCategories.forEach(category => {
            const btn = document.createElement('button');
            btn.className = 'category-btn-panel'; // NEU: Panel-Klasse
            if (currentCategoryFilter === category) btn.classList.add('active');

            // Placeholder Image mit Alpha-Fade
            const placeholderPath = `/images/Placeholder/${getCategoryPlaceholder(category)}.png`;
            btn.style.backgroundImage = `url('${placeholderPath}')`;
            btn.classList.add('has-image');
            btn.title = category;

            btn.dataset.category = category;
            btn.addEventListener('click', function() {
                updateCategoryActiveState(this);
                currentCategoryFilter = category;
                saveSortAndFilterSettings();
                loadInventory();
            });
            buttonGrid.appendChild(btn);
        });

        console.log(`✅ Loaded ${categories.length} category buttons + Favorites in right panel`);
    } catch (error) {
        console.error('Error loading categories:', error);
        const buttonGrid = document.getElementById('category-buttons-panel');
        if (buttonGrid) {
            buttonGrid.innerHTML = `<div style="color: #f44; padding: 10px; font-size: 11px;">${tr('categoryLoadError')}</div>`;
        }
    }
}

// Helper: Map category name to placeholder image filename
function getCategoryPlaceholder(category) {
    const mapping = {
        'Helmet': 'Helmet',
        'Core': 'Torso',
        'Torso': 'Torso',
        'Arms': 'Arms',
        'Legs': 'Legs',
        'Backpack': 'Backpack',
        'Undersuit': 'Undersuit',
        'Jacket': 'Jacket',
        'Pants': 'Pants',
        'Shirt': 'Shirt',
        'Shoes': 'Shoes',
        'Hat': 'Hat',
        'Hands': 'Hands',
        'Eyes': 'Eyes',
        'Jumpsuit': 'Jumpsuit'
    };
    return mapping[category] || 'Helmet'; // Default fallback
}

// Helper to handle active state switching (Panel-Version)
function updateCategoryActiveState(clickedBtn) {
    document.querySelectorAll('.category-btn-panel').forEach(btn => {
        btn.classList.remove('active');
    });
    clickedBtn.classList.add('active');
}

console.log('✅ app_panels.js loaded - Panel-specific functions overridden');
