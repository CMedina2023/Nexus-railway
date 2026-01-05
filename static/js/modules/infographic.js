/**
 * Nexus AI - Roadmap Module
 * Handles interactions for the Status/Roadmap page.
 */
(function (window) {
    'use strict';

    // Ensure namespace exists
    window.NexusModules = window.NexusModules || {};

    const Roadmap = {
        /**
         * Initialize roadmap interactions
         */
        init: function () {
            console.log('Roadmap module initialized');
            this.setupAnimations();
        },

        setupAnimations: function () {
            const items = document.querySelectorAll('.timeline-item');

            // Simple stagger animation on load
            items.forEach((item, index) => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(10px)';
                item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';

                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, index * 100);
            });
        }
    };

    // Public API
    window.NexusModules.Infographic = Roadmap; // Maintain old namespace for compatibility

})(window);
