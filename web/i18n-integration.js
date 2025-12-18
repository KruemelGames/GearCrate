// i18n-integration.js - Integration of translations into GearCrate

// Initialize language selector
document.addEventListener('DOMContentLoaded', function() {
    const languageSelect = document.getElementById('language-select');
    
    if (languageSelect) {
        // Set current language in selector
        languageSelect.value = i18n.currentLanguage;
        
        // Language change handler
        languageSelect.addEventListener('change', function(e) {
            const newLang = e.target.value;
            i18n.setLanguage(newLang);
        });
    }
    //
    // Listen for language changes
    document.addEventListener('languageChanged', function(e) {
        console.log(`Language changed to: ${e.detail.language}`);

        // Update language selector dropdown
        if (languageSelect) {
            languageSelect.value = e.detail.language;
        }

        // Update dynamic content
        updateDynamicContent();
    });
});

// Update dynamic content that's not in HTML
function updateDynamicContent() {
    // Update sort order button (nur Emoji, kein Text)
    const sortOrderBtn = document.getElementById('sort-order-btn');
    if (sortOrderBtn) {
        if (currentSortOrder === 'asc') {
            sortOrderBtn.textContent = '🔼';
            sortOrderBtn.title = window.tr ? window.tr('sortAscending') : 'Sort Ascending';
        } else {
            sortOrderBtn.textContent = '🔽';
            sortOrderBtn.title = window.tr ? window.tr('sortDescending') : 'Sort Descending';
        }
    }

    // Reload categories with new language
    if (typeof loadCategories === 'function') {
        loadCategories();
    }

    // Reload inventory to update "no items" message
    if (typeof loadInventory === 'function') {
        loadInventory();
    }

    // Reload stats title
    if (typeof loadStats === 'function') {
        loadStats();
    }
}

// Override alert messages to use translations
window.showNotification = function(messageKey, params) {
    const message = (window.tr && params) ? window.tr(messageKey, params) : (window.tr ? window.tr(messageKey) : messageKey);
    
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
};

// Translated confirm dialogs
window.confirmTranslated = function(messageKey, params) {
    const message = (window.tr && params) ? window.tr(messageKey, params) : (window.tr ? window.tr(messageKey) : messageKey);
    return confirm(message);
};

// Translated alerts
window.alertTranslated = function(messageKey, params) {
    const message = (window.tr && params) ? window.tr(messageKey, params) : (window.tr ? window.tr(messageKey) : messageKey);
    return alert(message);
};
