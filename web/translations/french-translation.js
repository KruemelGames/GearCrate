// French Translation / Traduction française
const fr = {
    // Navigation & Main
    appTitle: "GearCrate",
    search: "Recherche",
    inventory: "Inventaire",
    stats: "Statistiques",
    
    // Search Section
    searchPlaceholder: "Rechercher des objets...",
    searchLimit: "Afficher les résultats:",
    searchLimitReset: "Limite de résultats réinitialisée à 25",
    searchShowingResults: "Affichage de {shown} sur {total} résultats",
    searchNoResults: "Aucun résultat trouvé",
    searchError: "Erreur de recherche",
    
    // Inventory Section
    inventoryFilter: "Filtrer l'inventaire...",
    inventoryEmpty: "Aucun objet dans l'inventaire",
    inventoryCategoryEmpty: "Aucun objet trouvé dans la catégorie \"{category}\"",
    inventoryLoadError: "Erreur de chargement",
    
    // Categories
    categoryAll: "Tous",
    categoryFavorites: "Favoris",
    categoryLoading: "Chargement des catégories...",
    categoryLoadError: "Erreur de chargement",

    // Favorites
    favoriteItem: "Ajouter aux favoris",
    unfavoriteItem: "Retirer des favoris",
    
    // Sorting
    sortBy: "Trier par:",
    sortName: "Nom",
    sortCount: "Quantité",
    sortDate: "Date",
    sortAscending: "⬇️ Croissant",
    sortDescending: "⬆️ Décroissant",
    
    // Buttons
    add: "Ajouter",
    delete: "Supprimer",
    save: "Enregistrer",
    cancel: "Annuler",
    close: "Fermer",
    
    // Modal
    modalCount: "Quantité:",
    modalNotes: "Notes:",
    modalDelete: "Supprimer l'objet",
    modalConfirmDelete: "Vraiment supprimer {name}?",
    modalConfirmZero: "Mettre \"{name}\" à 0?\n\nL'objet sera retiré de l'inventaire (reste dans la DB).",
    
    // Stats Section
    statsTitle: "Statistiques",
    statsTotalInDb: "Objets dans la base:",
    statsInInventory: "Objets dans l'inventaire:",
    statsTotalCount: "Nombre total:",
    statsCacheSize: "Taille du cache:",
    statsByCategory: "📦 Par Catégorie",
    
    // Actions
    clearInventory: "Vider l'inventaire",
    deleteAll: "Tout supprimer",
    clearCache: "Vider le cache",
    confirmClearInventory: "Vraiment mettre tous les comptes à 0?",
    confirmDeleteAll: "ATTENTION: Vraiment supprimer TOUS les objets de la base?",
    confirmClearCache: "Vraiment vider tout le cache?",
    
    // Notifications
    itemAdded: "{name} a été ajouté!",
    itemDeleted: "{name} a été supprimé!",
    inventoryCleared: "L'inventaire a été vidé!",
    cacheCleared: "Le cache a été vidé!",
    errorAdding: "Erreur lors de l'ajout",
    errorDeleting: "Erreur lors de la suppression",
    errorUpdating: "Erreur lors de la mise à jour",
    errorAutoSave: "Erreur lors de l'enregistrement automatique",
    
    // Units
    times: "x",
    
    // Language
    language: "Langue:",
    languageName: "Français",

    // Footer Buttons
    footerClearCache: "🗑️ Vider le cache",
    footerDebug: "🐛 Déboguer",
    footerClearInventory: "📦 Vider l'inventaire",
    confirmClearCache: "Vider le cache du site et recharger? Cela supprimera toutes les données mises en cache.",
    cacheCleared: "Cache vidé! La page va se recharger.",

    // Import from SC Section
    importTitle: "📥 Importer de Star Citizen",
    importAdminRequired: "⚠️ Droits administrateur requis",
    importAdminWarning1: "Le scanner InvDetect nécessite des droits administrateur pour les hooks clavier et le changement de fenêtre.",
    importAdminWarning2: "<strong>Veuillez utiliser:</strong> <code>start-browser-admin.bat</code> ou <code>start-desktop-admin.bat</code>",
    importAdminWarning3: "Sans droits administrateur, le scanner ne fonctionnera pas.",
    importSelectScanMode: "🎯 Sélectionner le mode de scan:",
    importMode1Title: "Objets 1x1",
    importMode1Desc: "Normal (Armes, Armures, etc.)",
    importMode2Title: "Objets 1x2",
    importMode2Desc: "Sous-vêtements",
    importInstructions: "📋 Instructions:",
    importStep1: "Sélectionnez le mode de scan approprié (1x1 ou 1x2)",
    importStep2: "Cliquez sur \"Scanner maintenant\"",
    importStep3: "Une fenêtre CMD s'ouvrira avec \"Press INSERT to start scan...\"",
    importStep4: "Basculez vers Star Citizen et ouvrez votre inventaire universel",
    importStep5: "Appuyez sur INSERT pour démarrer",
    importStep6: "Le scanner fonctionnera automatiquement",
    importStep7: "<strong>Annuler:</strong> Appuyez sur DELETE ou déplacez la souris vers le coin de l'écran",
    importStep8: "Après le scan, les résultats seront affichés ici",
    importTip: "💡 <strong>Astuce:</strong> Assurez-vous que Star Citizen fonctionne en mode plein écran (1920x1080) pour de meilleurs résultats.",
    importScanNow: "🚀 Scanner maintenant",
    importScanning: "⏳ Scan en cours...",
    importScannerActive: "Le scanner est actif. Veuillez suivre les instructions dans la fenêtre CMD.",
    importCancelInfo: "<strong>Annuler:</strong> Touche DELETE ou déplacez la souris vers le coin de l'écran",
    importCheckResults: "🔍 Vérifier les résultats",
    importScanComplete: "✅ Scan terminé",
    importCategoryFilter: "🏷️ Filtre de catégorie:",
    importUndo: "↶ Annuler",
    importRedo: "↷ Refaire",
    importFoundItems: "✅ Objets trouvés",
    importNotFoundItems: "❓ Objets non reconnus",
    importOpenNotDetected: "📄 Ouvrir not_detected.md",
    importImportItems: "✅ Importer les objets",
    importNewScan: "🔄 Nouveau scan"
};