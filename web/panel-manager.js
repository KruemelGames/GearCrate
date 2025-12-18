/**
 * panel-manager.js
 * 
 * Provides a centralized system for managing the state of all UI panels
 * to ensure only one panel per side (left/right) can be open at a time.
 */

const panelManager = {
    panels: {}, // Stores panel data: { element, state, tab, side }
    
    /**
     * Registers a panel with the manager.
     * @param {string} id - A unique ID for the panel (e.g., 'left', 'right').
     * @param {HTMLElement} wrapperElement - The main wrapper element for the panel and its tab.
     * @param {HTMLElement} tabElement - The tab element that controls the panel.
     * @param {HTMLElement} panelElement - The panel element that opens/closes.
     * @param {string} side - The side the panel belongs to ('left-side' or 'right-side').
     */
    registerPanel(id, wrapperElement, tabElement, panelElement, side) {
        if (!id || !wrapperElement || !tabElement || !side) {
            console.error('Panel registration failed: Missing required parameters for ID:', id);
            return;
        }

        this.panels[id] = {
            id: id,
            wrapper: wrapperElement,
            tab: tabElement,
            panel: panelElement,
            isOpen: false,
            side: side,
        };

        this.addEventListeners(this.panels[id]);
        console.log(`✅ Panel '${id}' (${side}) registered with manager.`);
    },

    /**
     * Adds the necessary event listeners for a registered panel.
     * @param {object} panel - The panel object from the panels registry.
     */
    addEventListeners(panel) {
        // Hover to Peek
        panel.wrapper.addEventListener('mouseenter', () => {
            // Only peek if no panel on the same side is fully open
            const isSideOpen = Object.values(this.panels).some(p => p.side === panel.side && p.isOpen);
            if (!isSideOpen) {
                panel.wrapper.classList.add('peek');
            }
        });

        panel.wrapper.addEventListener('mouseleave', () => {
            panel.wrapper.classList.remove('peek');
        });

        // Click on tab toggles the panel
        panel.tab.addEventListener('click', () => {
            this.togglePanel(panel.id);
        });

        // Click on the panel area itself only opens it
        if (panel.panel) {
             panel.panel.addEventListener('click', () => {
                if (!panel.isOpen) {
                    this.openPanel(panel.id);
                }
            });
        }
    },

    /**
     * Toggles a specific panel's state.
     * @param {string} id - The ID of the panel to toggle.
     */
    togglePanel(id) {
        if (this.panels[id]) {
            if (this.panels[id].isOpen) {
                this.closePanel(id);
            } else {
                this.openPanel(id);
            }
        }
    },

    /**
     * Opens a specific panel and closes others on the same side.
     * @param {string} id - The ID of the panel to open.
     */
    openPanel(id) {
        if (!this.panels[id]) return;

        const panelToOpen = this.panels[id];
        const sideToOpen = panelToOpen.side;

        // Close all other panels ON THE SAME SIDE
        for (const panelId in this.panels) {
            const currentPanel = this.panels[panelId];
            if (currentPanel.side === sideToOpen && currentPanel.id !== id && currentPanel.isOpen) {
                this.closePanel(panelId);
            }
        }

        // Open the target panel
        panelToOpen.isOpen = true;
        panelToOpen.wrapper.classList.remove('peek');
        panelToOpen.wrapper.classList.add('open');

        // Special handling for bottom panels that need content updates
        if (id === 'bottom-left' && window.updatePopupStats) {
            window.updatePopupStats();
        }
    },

    /**
     * Closes a specific panel.
     * @param {string} id - The ID of the panel to close.
     */
    closePanel(id) {
        if (this.panels[id] && this.panels[id].isOpen) {
            const panel = this.panels[id];
            panel.isOpen = false;
            panel.wrapper.classList.remove('open');
        }
    },

    // Method to close all panels, can be called externally if needed
    closeAll() {
        for (const panelId in this.panels) {
            this.closePanel(panelId);
        }
    }
};

// Expose the manager to the window object to be accessible by other scripts
window.panelManager = panelManager;
