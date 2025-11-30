// Translation System - Mehrsprachiges UI
// Unterstützte Sprachen: Deutsch, English, Français, Español

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
    }
    
    /**
     * Detect browser/OS language
     * Fallback to English if language not supported
     */
    detectLanguage() {
        // Check localStorage first
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
     * Change current language
     */
    setLanguage(langCode) {
        if (!this.supportedLanguages.includes(langCode)) {
            console.error(`Language "${langCode}" not supported`);
            return false;
        }
        
        this.currentLanguage = langCode;
        localStorage.setItem('language', langCode);
        console.log(`🌍 Language changed to: ${langCode}`);
        
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

// Helper function for quick translations
function t(key, params) {
    return i18n.t(key, params);
}

// Update UI when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    i18n.updateUI();
});
