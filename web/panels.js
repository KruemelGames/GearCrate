/**
 * panels.js
 * Registers the top-left (search) and top-right (filter) panels
 * with the central panelManager.
 */

document.addEventListener('DOMContentLoaded', () => {
    if (window.panelManager) {
        // Register Left Panel
        const panelLeftWrapper = document.getElementById('panelLeftWrapper');
        const panelLeft = document.getElementById('panelLeft');
        const tabLeft = document.getElementById('tabLeft');
        window.panelManager.registerPanel('left', panelLeftWrapper, tabLeft, panelLeft, 'left-side');

        // Register Right Panel
        const panelRightWrapper = document.getElementById('panelRightWrapper');
        const panelRight = document.getElementById('panelRight');
        const tabRight = document.getElementById('tabRight');
        window.panelManager.registerPanel('right', panelRightWrapper, tabRight, panelRight, 'right-side');

    } else {
        console.error('Panel Manager is not available.');
    }

    // This function remains as it is called by other scripts, but it is not directly related to the open/close logic.
    function expandSearchPanel(hasResults) {
        const panelLeft = document.getElementById('panelLeft');
        if (hasResults) {
            panelLeft.classList.remove('compact');
            panelLeft.classList.add('expanded');
        } else {
            panelLeft.classList.remove('expanded');
            panelLeft.classList.add('compact');
        }
    }

    // Export for use in other scripts
    window.expandSearchPanel = expandSearchPanel;
});

console.log('✅ Top panels registered with Panel Manager.');
