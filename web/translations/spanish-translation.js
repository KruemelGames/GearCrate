// Spanish Translation / Traducción española
const es = {
    // Navigation & Main
    appTitle: "GearCrate",
    search: "Búsqueda",
    inventory: "Inventario",
    stats: "Estadísticas",
    
    // Search Section
    searchPlaceholder: "Buscar objetos...",
    searchLimit: "Mostrar resultados:",
    searchLimitReset: "Límite de resultados restablecido a 25",
    searchShowingResults: "Mostrando {shown} de {total} resultados",
    searchNoResults: "No se encontraron resultados",
    searchError: "Error de búsqueda",
    
    // Inventory Section
    inventoryFilter: "Filtrar inventario...",
    inventoryEmpty: "Aún no hay objetos en el inventario",
    inventoryCategoryEmpty: "No se encontraron objetos en la categoría \"{category}\"",
    inventoryLoadError: "Error al cargar",
    
    // Categories
    categoryAll: "Todos",
    categoryFavorites: "Favoritos",
    categoryLoading: "Cargando categorías...",
    categoryLoadError: "Error al cargar",

    // Favorites
    favoriteItem: "Añadir a favoritos",
    unfavoriteItem: "Quitar de favoritos",
    
    // Sorting
    sortBy: "Ordenar por:",
    sortName: "Nombre",
    sortCount: "Cantidad",
    sortDate: "Fecha",
    sortAscending: "⬇️ Ascendente",
    sortDescending: "⬆️ Descendente",
    
    // Buttons
    add: "Añadir",
    delete: "Eliminar",
    save: "Guardar",
    cancel: "Cancelar",
    close: "Cerrar",
    
    // Modal
    modalCount: "Cantidad:",
    modalNotes: "Notas:",
    modalDelete: "Eliminar objeto",
    modalConfirmDelete: "¿Realmente eliminar {name}?",
    modalConfirmZero: "¿Establecer \"{name}\" a 0?\n\nEl objeto se eliminará del inventario (permanece en la BD).",
    
    // Stats Section
    statsTitle: "Estadísticas",
    statsTotalInDb: "Objetos en la base:",
    statsInInventory: "Objetos en inventario:",
    statsTotalCount: "Cantidad total:",
    statsCacheSize: "Tamaño del caché:",
    statsByCategory: "📦 Por Categoría",
    
    // Actions
    clearInventory: "Vaciar inventario",
    deleteAll: "Eliminar todo",
    clearCache: "Vaciar caché",
    confirmClearInventory: "¿Realmente establecer todos los contadores a 0?",
    confirmDeleteAll: "ADVERTENCIA: ¿Realmente eliminar TODOS los objetos de la base de datos?",
    confirmClearCache: "¿Realmente vaciar todo el caché?",
    
    // Notifications
    itemAdded: "¡{name} fue añadido!",
    itemDeleted: "¡{name} fue eliminado!",
    inventoryCleared: "¡El inventario fue vaciado!",
    cacheCleared: "¡El caché fue vaciado!",
    errorAdding: "Error al añadir",
    errorDeleting: "Error al eliminar",
    errorUpdating: "Error al actualizar la cantidad",
    errorAutoSave: "Error al guardar automáticamente",
    
    // Units
    times: "x",
    
    // Language
    language: "Idioma:",
    languageName: "Español",

    // Bottom Popups
    settingsTitle: "Configuración",

    // Footer Buttons
    footerClearCache: "Limpiar caché",
    footerDebug: "Depurar",
    footerClearInventory: "Limpiar inventario",
    confirmClearCache: "¿Limpiar caché del sitio y recargar? Esto eliminará todos los datos almacenados en caché.",
    cacheCleared: "¡Caché limpiado! La página se recargará.",

    // Import from SC Section
    importTitle: "📥 Importar de Star Citizen",
    importAdminRequired: "⚠️ Derechos de administrador requeridos",
    importAdminWarning1: "El escáner InvDetect requiere derechos de administrador para hooks de teclado y cambio de ventana.",
    importAdminWarning2: "<strong>Por favor use:</strong> <code>start-browser-admin.bat</code> o <code>start-desktop-admin.bat</code>",
    importAdminWarning3: "Sin derechos de administrador, el escáner no funcionará.",
    importSelectScanMode: '🎯 Seleccionar modo de escaneo:',
    importSelectResolution: '🖥️ Seleccionar resolución:',
    importMode1Title: "Objetos 1x1",
    importMode1Desc: "Normal (Armas, Armaduras, etc.)",
    importMode2Title: "Objetos 1x2",
    importMode2Desc: "Ropa interior",
    importInstructions: "📋 Instrucciones:",
    importStep1: "Seleccione el modo de escaneo apropiado (1x1 o 1x2)",
    importStep2: "Haga clic en \"Escanear ahora\"",
    importStep3: "Se abrirá una ventana CMD con \"Press INSERT to start scan...\"",
    importStep4: "Cambie a Star Citizen y abra su inventario universal",
    importStep5: "Presione INSERT para comenzar",
    importStep6: "El escáner funcionará automáticamente",
    importStep7: "<strong>Cancelar:</strong> Presione DELETE o mueva el mouse a la esquina de la pantalla",
    importStep8: "Después del escaneo, los resultados se mostrarán aquí",
    importTip: "💡 <strong>Consejo:</strong> Asegúrese de que Star Citizen se ejecute en modo de pantalla completa (1920x1080) para obtener mejores resultados.",
    importScanNow: "🚀 Escanear ahora",
    importScanning: "⏳ Escaneando...",
    importScannerActive: "El escáner está activo. Siga las instrucciones en la ventana CMD.",
    importCancelInfo: "<strong>Cancelar:</strong> Tecla DELETE o mueva el mouse a la esquina de la pantalla",
    importCheckResults: "🔍 Verificar resultados",
    importScanComplete: "✅ Escaneo completo",
    importCategoryFilter: "🏷️ Filtro de categoría:",
    importUndo: "↶ Deshacer",
    importRedo: "↷ Rehacer",
    importFoundItems: "✅ Objetos encontrados",
    importNotFoundItems: "❓ Objetos no reconocidos",
    importOpenNotDetected: "📄 Abrir not_detected.md",
    importImportItems: "✅ Importar objetos",
    importNewScan: "🔄 Nuevo escaneo"
};