/**
 * bottom-popups.js
 * Registers the bottom-left (stats) and bottom-right (settings) panels
 * with the central panelManager.
 */
document.addEventListener('DOMContentLoaded', function() {
    if (window.panelManager) {
        // Register Bottom-Left Panel (Stats)
        const statsWrapper = document.getElementById('popupStatsWrapper');
        const statsToggle = document.getElementById('tabStatsToggle');
        const statsPanel = document.getElementById('popupStats');
        window.panelManager.registerPanel('bottom-left', statsWrapper, statsToggle, statsPanel, 'left-side');

        // Register Bottom-Right Panel (Settings)
        const settingsWrapper = document.getElementById('popupSettingsWrapper');
        const settingsToggle = document.getElementById('tabSettingsToggle');
        const settingsPanel = document.getElementById('popupSettings');
        window.panelManager.registerPanel('bottom-right', settingsWrapper, settingsToggle, settingsPanel, 'right-side');
    } else {
        console.error('Panel Manager is not available.');
    }

    // This function remains as it is called externally
    function updatePopupStats() {
        const totalItemsDb = document.getElementById('total-items-db')?.textContent || '0';
        const inventoryUniqueItems = document.getElementById('inventory-unique-items')?.textContent || '0';
        const totalCount = document.getElementById('total-count')?.textContent || '0';
        const cacheSize = document.getElementById('cache-size')?.textContent || '0 MB';

        document.getElementById('popup-total-items-db').textContent = totalItemsDb;
        document.getElementById('popup-inventory-unique-items').textContent = inventoryUniqueItems;
        document.getElementById('popup-total-count').textContent = totalCount;
        document.getElementById('popup-cache-size').textContent = cacheSize;

        const categoryStats = document.getElementById('category-stats');
        const popupCategoryStats = document.getElementById('popup-category-stats');
        if (categoryStats && popupCategoryStats) {
            popupCategoryStats.innerHTML = categoryStats.innerHTML;
        }
    }

    // Export function so it can be called from app.js
    window.updatePopupStats = updatePopupStats;
});

console.log('✅ Bottom panels registered with Panel Manager.');
