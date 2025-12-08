// Translation System - Mehrsprachiges UI
// Unterstützte Sprachen: Deutsch, English, Français, Español
//
class TranslationSystem {
    constructor() {
        this.translations = {
            de: de,
            en: en,
            fr: fr,
            es: es
        };

        this.supportedLanguages = ['de', 'en', 'fr', 'es'];
        this.defaultLanguage = 'en';
        this.currentLanguage = this.detectLanguage();

        console.log(`🌍 Language detected: ${this.currentLanguage}`);
        console.log(`📦 localStorage language: ${localStorage.getItem('language')}`);
        console.log(`🌐 Browser language: ${navigator.language || navigator.userLanguage}`);
    }
    
    /**
     * Detect browser/OS language
     * Fallback to English if language not supported
     */
    detectLanguage() {
        // Check localStorage first (for browser mode compatibility)
        const saved = localStorage.getItem('language');
        if (saved && this.supportedLanguages.includes(saved)) {
            return saved;
        }

        // Get browser language
        const browserLang = navigator.language || navigator.userLanguage;

        // Extract primary language code (e.g., 'de' from 'de-DE', 'es' from 'es-MX')
        const langCode = browserLang.split('-')[0].toLowerCase();

        // Check if supported
        if (this.supportedLanguages.includes(langCode)) {
            return langCode;
        }

        // Fallback to English
        return this.defaultLanguage;
    }

    /**
     * Load saved language from backend (for pywebview persistence)
     */
    async loadSavedLanguage() {
        console.log('[DEBUG] loadSavedLanguage() called');
        console.log('[DEBUG] typeof api:', typeof api);

        try {
            // Try to get saved language from backend API
            if (typeof api !== 'undefined') {
                console.log('[DEBUG] Calling api.get_user_language()...');
                const result = await api.get_user_language();
                console.log('[DEBUG] Result:', result);

                if (result.success && result.language && this.supportedLanguages.includes(result.language)) {
                    console.log(`📂 Loaded saved language from config: ${result.language}`);
                    this.currentLanguage = result.language;
                    this.updateUI();
                } else {
                    console.log('[DEBUG] Not loading language. Success:', result.success, 'Language:', result.language, 'Supported:', this.supportedLanguages.includes(result.language));
                }
            } else {
                console.log('[DEBUG] api is undefined');
            }
        } catch (e) {
            console.error('ℹ️ Could not load saved language from backend:', e);
        }
    }
    
    /**
     * Change current language
     */
    setLanguage(langCode) {
        if (!this.supportedLanguages.includes(langCode)) {
            console.error(`Language "${langCode}" not supported`);
            return false;
        }

        this.currentLanguage = langCode;

        // Save to localStorage (for browser mode)
        try {
            localStorage.setItem('language', langCode);
            console.log(`🌍 Language changed to: ${langCode}`);
            console.log(`✅ Verified localStorage save: ${localStorage.getItem('language')}`);
        } catch (e) {
            console.error(`❌ Error saving to localStorage:`, e);
        }

        // Also save to backend config file (for pywebview persistence)
        if (typeof api !== 'undefined') {
            api.set_user_language(langCode).then(result => {
                if (result.success) {
                    console.log(`💾 Language saved to config file: ${langCode}`);
                } else {
                    console.error(`❌ Error saving language to config file:`, result.error);
                }
            }).catch(e => {
                console.log('ℹ️ Could not save to backend (normal in browser mode)');
            });
        }

        // Update UI
        this.updateUI();

        return true;
    }
    
    /**
     * Get translation for key
     * Supports placeholders: t('itemAdded', {name: 'Sword'})
     */
    t(key, params = {}) {
        const lang = this.translations[this.currentLanguage];
        
        if (!lang) {
            console.error(`Language "${this.currentLanguage}" not found`);
            return key;
        }
        
        let text = lang[key];
        
        if (!text) {
            console.warn(`Translation key "${key}" not found for language "${this.currentLanguage}"`);
            return key;
        }
        
        // Replace placeholders
        Object.keys(params).forEach(param => {
            text = text.replace(`{${param}}`, params[param]);
        });
        
        return text;
    }
    
    /**
     * Get all languages for language picker
     */
    getAvailableLanguages() {
        return this.supportedLanguages.map(code => ({
            code: code,
            name: this.translations[code].languageName
        }));
    }
    
    /**
     * Update all UI elements with current language
     */
    updateUI() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);

            // Check if element has data-i18n-html (allows HTML content)
            if (element.hasAttribute('data-i18n-html')) {
                element.innerHTML = translation;
            }
            // Check if element has data-i18n-attr (translate attribute instead of text)
            else if (element.hasAttribute('data-i18n-attr')) {
                const attr = element.getAttribute('data-i18n-attr');
                element.setAttribute(attr, translation);
            }
            // Default: update text content
            else {
                element.textContent = translation;
            }
        });

        // Update title attributes (tooltips)
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });

        // Update placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });

        // Trigger custom event for dynamic content
        document.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: this.currentLanguage }
        }));

        console.log('✅ UI updated with translations');
    }
}

// Initialize global translation system
const i18n = new TranslationSystem();

// Make i18n globally accessible
window.i18n = i18n;

/**
 * FIXED: Renamed global helper from 't' to 'tr' to avoid collision
 * with minified libraries (like Fuse.js) that use 't' internally.
 */
function tr(key, params) {
    return i18n.t(key, params);
}

// Make tr() globally accessible
window.tr = tr;

// Debug: Log that translation system is ready
console.log('🌍 Translation system loaded. tr() function available:', typeof window.tr);
    return i18n.t(key, params);
}

// Make tr() globally accessible
window.tr = tr;

// Debug: Log that translation system is ready
console.log('🌍 Translation system loaded. tr() function available:', typeof window.tr);
// Helper function for quick translations
function t(key, params) {
    return i18n.t(key, params);
}

// Make t() globally accessible
window.t = t;

// Debug: Log that translation system is ready
console.log('🌍 Translation system loaded. t() function available:', typeof window.t);

// Update UI when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    i18n.updateUI();

    // Load saved language from backend after a short delay
    // This ensures api-adapter.js is loaded first
    setTimeout(() => {
        i18n.loadSavedLanguage();
    }, 100);
});
