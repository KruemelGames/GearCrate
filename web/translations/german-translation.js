// German Translation / Deutsche Übersetzung
const de = {
    // Navigation & Main
    appTitle: "GearCrate",
    search: "Suche",
    inventory: "Inventar",
    stats: "Statistiken",
    
    // Search Section
    searchPlaceholder: "Suche Items...",
    searchLimit: "Ergebnisse zeigen:",
    searchLimitReset: "Suchergebnis-Limit auf 25 zurückgesetzt",
    searchShowingResults: "Zeige {shown} von {total} Ergebnissen",
    searchNoResults: "Keine Ergebnisse gefunden",
    searchError: "Fehler bei der Suche",
    
    // Inventory Section
    inventoryFilter: "Inventar filtern...",
    inventoryEmpty: "Noch keine Items im Inventar",
    inventoryCategoryEmpty: "Keine Items in Kategorie \"{category}\" gefunden",
    inventoryLoadError: "Fehler beim Laden",
    
    // Categories
    categoryAll: "Alle",
    categoryFavorites: "Favoriten",
    categoryLoading: "Lade Kategorien...",
    categoryLoadError: "Fehler beim Laden",
    
    // Favorites
    favoriteItem: "Zu Favoriten hinzufügen",
    unfavoriteItem: "Aus Favoriten entfernen",

    // Sorting
    sortBy: "Sortieren nach:",
    sortName: "Name",
    sortCount: "Anzahl",
    sortDate: "Datum",
    sortAscending: "⬇️ Aufsteigend",
    sortDescending: "⬆️ Absteigend",
    
    // Buttons
    add: "Hinzufügen",
    delete: "Löschen",
    save: "Speichern",
    cancel: "Abbrechen",
    close: "Schließen",
    
    // Modal
    modalCount: "Anzahl:",
    modalNotes: "Notizen:",
    modalDelete: "Item löschen",
    modalConfirmDelete: "{name} wirklich löschen?",
    modalConfirmZero: "\"{name}\" auf 0 setzen?\n\nDas Item wird aus dem Inventar entfernt (bleibt in der DB).",
    
    // Stats Section
    statsTitle: "Statistiken",
    statsTotalInDb: "Items in Datenbank:",
    statsInInventory: "Items im Inventar:",
    statsTotalCount: "Gesamtanzahl:",
    statsCacheSize: "Cache-Größe:",
    statsByCategory: "📦 Nach Kategorien",
    
    // Actions
    clearInventory: "Inventar leeren",
    deleteAll: "Alle löschen",
    clearCache: "Cache leeren",
    confirmClearInventory: "Wirklich alle Counts auf 0 setzen?",
    confirmDeleteAll: "ACHTUNG: Wirklich ALLE Items aus der Datenbank löschen?",
    confirmClearCache: "Wirklich den kompletten Cache leeren?",
    
    // Notifications
    itemAdded: "{name} wurde hinzugefügt!",
    itemDeleted: "{name} wurde gelöscht!",
    inventoryCleared: "Inventar wurde geleert!",
    cacheCleared: "Cache wurde geleert!",
    errorAdding: "Fehler beim Hinzufügen",
    errorDeleting: "Fehler beim Löschen",
    errorUpdating: "Fehler beim Aktualisieren der Anzahl",
    errorAutoSave: "Fehler beim automatischen Speichern der Anzahl",
    
    // Units
    times: "x",
    
    // Language
    language: "Sprache:",
    languageName: "Deutsch",

    // Bottom Popups
    settingsTitle: "Einstellungen",

    // Footer Buttons
    footerClearCache: "Cache leeren",
    footerDebug: "Debug",
    footerClearInventory: "Inventar leeren",
    confirmClearCache: "Website-Cache leeren und neu laden? Dies entfernt alle zwischengespeicherten Daten.",
    cacheCleared: "Cache geleert! Seite wird neu geladen.",

    // Import from SC Section
    importTitle: "📥 Import from Star Citizen",
    importAdminRequired: "⚠️ Administrator-Rechte erforderlich",
    importAdminWarning1: "Der InvDetect Scanner benötigt Admin-Rechte für Tastatur-Hooks und Fenster-Switching.",
    importAdminWarning2: "<strong>Bitte verwende:</strong> <code>start-browser-admin.bat</code> oder <code>start-desktop-admin.bat</code>",
    importAdminWarning3: "Ohne Admin-Rechte wird der Scanner nicht funktionieren.",
    importSelectScanMode: "🎯 Scan Mode wählen:",
    importSelectResolution: '🖥️ Auflösung wählen:',
    importMode1Title: "1x1 Items",
    importMode1Desc: "Normal (Waffen, Rüstungen, etc.)",
    importMode2Title: "1x2 Items",
    importMode2Desc: "Undersuits",
    importInstructions: "📋 Anleitung:",
    importStep1: "Wähle den passenden Scan-Modus (1x1 oder 1x2)",
    importStep2: "Klicke auf \"Scan Now\"",
    importStep3: "Ein CMD-Fenster öffnet sich mit \"Press INSERT to start scan...\"",
    importStep4: "Wechsle zu Star Citizen und öffne dein Universal Inventory",
    importStep5: "Drücke INSERT zum Starten",
    importStep6: "Der Scanner arbeitet automatisch",
    importStep7: "<strong>Abbruch:</strong> Drücke DELETE oder bewege Maus in Bildschirmecke",
    importStep8: "Nach dem Scan werden die Ergebnisse hier angezeigt",
    importTip: "💡 <strong>Tipp:</strong> Stelle sicher, dass Star Citizen im Vollbild-Modus läuft (1920x1080) für beste Ergebnisse.",
    importScanNow: "🚀 Scan Now",
    importScanning: "⏳ Scan läuft...",
    importScannerActive: "Der Scanner ist aktiv. Bitte folge den Anweisungen im CMD-Fenster.",
    importCancelInfo: "<strong>Abbruch:</strong> DELETE-Taste oder Maus in Bildschirmecke",
    importCheckResults: "🔍 Ergebnisse prüfen",
    importScanComplete: "✅ Scan abgeschlossen",
    importCategoryFilter: "🏷️ Kategorie Filter:",
    importUndo: "↶ Rückgängig",
    importRedo: "↷ Wiederholen",
    importFoundItems: "✅ Gefundene Items",
    importNotFoundItems: "❓ Nicht erkannte Items",
    importOpenNotDetected: "📄 not_detected.md öffnen",
    importImportItems: "✅ Items importieren",
    importNewScan: "🔄 Neuer Scan"
};