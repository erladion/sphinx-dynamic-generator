/**
 * toc-persistence.js
 *
 * Custom script for the Furo Sphinx theme to save and restore the expanded state
 * of the global Table of Contents (TOC) sidebar navigation using localStorage.
 *
 * It uses the unique document path (href) of the navigation link as the key
 * to store its expanded state.
 */

 document.addEventListener('DOMContentLoaded', () => {
    console.debug("DOMContentLoaded");
    const STORAGE_KEY = 'furo-toc-state';
    const EXPANDED_CLASS = 'is-expanded'; // Class Furo uses for an expanded item
    const navContainer = document.querySelector('.sidebar-tree');

    if (!navContainer) {
        console.debug("Could not find navContainer");
        // No navigation container found on this page, exit.
        return;
    }

    /**
     * Helper to get the canonical path (root-relative) for consistent keying.
     * @param {HTMLElement} anchor - The <a> element.
     * @returns {string | null} The root-relative pathname, or null if href is missing.
     */
    function getCanonicalPath(anchor) {
        // Use anchor.pathname which provides the path relative to the domain root 
        // (e.g., /chapter1/index.html), making it consistent across all pages.
        // It's important to check that href exists, otherwise anchor.pathname will throw if href is missing.
        if (!anchor.href) return null;
        return anchor.pathname; 
    }

    // --- 1. State Management ---

    /**
     * Retrieves the saved state map from localStorage.
     * @returns {Map<string, boolean>} A Map of {href: isExpanded} states.
     */
    function loadSavedState() {
        console.debug("loadSavedState");
        try {
            const savedData = localStorage.getItem(STORAGE_KEY);
            return savedData ? new Map(JSON.parse(savedData)) : new Map();
        } catch (e) {
            console.warn('Error loading TOC state from localStorage:', e);
            return new Map();
        }
    }

    /**
     * Saves the current expanded state of all links to localStorage.
     * @param {Map<string, boolean>} stateMap - The current state map.
     */
    function saveState(stateMap) {
        console.debug("saveState");
        try {
            const dataToSave = JSON.stringify(Array.from(stateMap.entries()));
            localStorage.setItem(STORAGE_KEY, dataToSave);

            console.log("Saving", STORAGE_KEY, dataToSave);
        } catch (e) {
            console.error('Error saving TOC state to localStorage. Data too large?', e);
        }
    }

    /**
     * Scans the DOM for all collapsible list items and returns the current state.
     * This captures the initial state set by the theme (e.g., the active path).
     * @returns {Map<string, boolean>} A Map of {href: isExpanded} states based on current DOM.
     */
    function getCurrentExpandedState() {
        const stateMap = new Map();
        // Furo uses 'toc-tree-item' for navigation entries
        navContainer.querySelectorAll('li.toctree-l1, li.toctree-l2, li.toctree-l3, li.toctree-l4').forEach(li => {
            const anchor = li.querySelector('a');
            const input = li.querySelector('input');
            
            if (anchor && input) {
                const path = getCanonicalPath(anchor); // <-- Use canonical path
                const isExpanded = input.checked; // State is driven by the checkbox
                if (path) {
                    stateMap.set(path, isExpanded);
                }
            }
        });
        return stateMap;
    }


    // --- 2. Restoration (Run on Page Load) ---

    /**
     * Restores the expanded state of the sidebar based on the saved state.
     */
    function restoreExpandedState() {
        console.debug("restoreExpandedState");
        const savedState = loadSavedState();
        if (savedState.size === 0) return;

        // Iterate through all collapsible list items in the navigation.
        navContainer.querySelectorAll('li.toctree-l1, li.toctree-l2, li.toctree-l3, li.toctree-l4').forEach(li => {
            const anchor = li.querySelector('a');
            if (!anchor) return;

            // Use the canonical path of the link as the unique identifier.
            const path = getCanonicalPath(anchor); // <-- Use canonical path

            if (path && savedState.get(path) === true) {
                const input = li.querySelector('input');
                
                if(!input) return;

                // 1. Restore the functional state (checkbox)
                input.checked = true;
                
                // 2. Restore the visual state (parent <li> class)
                // This is crucial for Furo's styling/animations to work correctly.
                li.classList.add(EXPANDED_CLASS);
            }
        });

        console.log(savedState)
    }


    // --- 3. Event Handling (Run on Click) ---

    /**
     * Attaches click listeners to all expand/collapse toggles.
     */
    function setupToggleListeners() {
        console.debug("setupToggleListeners");
        // We listen specifically to the hidden checkbox as it is the source of truth for the state.
        const toggles = navContainer.querySelectorAll('.toctree-checkbox');

        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                // Find the closest parent <li>
                const li = toggle.closest('li');
                if (!li) return;

                const anchor = li.querySelector('a');
                if (!anchor) return;

                const path = getCanonicalPath(anchor); // <-- Use canonical path
                if (!path) return;
                
                // toggle.checked already holds the new state (true/false) because the
                // click event has modified the checkbox state before this listener runs.
                const isExpanded = toggle.checked;

                // Load existing state, update for the current item, and save.
                const currentState = loadSavedState();
                currentState.set(path, isExpanded);
                saveState(currentState);
            });
        });
    }

    // Initialize the script
    setupToggleListeners();

    // The restoration block is now executed synchronously on DOMContentLoaded.
    restoreExpandedState();
    
    // CRITICAL: Capture and save the final state after the theme's initial logic and 
    // our restoration logic has run. This ensures the current page's expanded path is saved.
    saveState(getCurrentExpandedState());
});