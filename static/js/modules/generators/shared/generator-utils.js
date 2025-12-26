/**
 * Nexus AI - Generator Utilities
 * Funciones de utilidad compartidas para los generadores.
 */
(function (window) {
    'use strict';

    const NexusModules = window.NexusModules || {};
    NexusModules.Generators = NexusModules.Generators || {};

    NexusModules.Generators.Utils = {
        /**
         * Escapa caracteres HTML para evitar XSS y problemas de renderizado
         * @param {string} text - Texto a escapar
         * @returns {string} Texto escapado
         */
        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        /**
         * Configura una zona de arrastre (DropZone)
         * @param {string} dropZoneId - ID del elemento dropzone
         * @param {string} fileInputId - ID del input file
         * @param {Function} onFileSelect - Callback cuando se selecciona un archivo
         */
        setupDropZone(dropZoneId, fileInputId, onFileSelect) {
            const dropZone = document.getElementById(dropZoneId);
            const fileInput = document.getElementById(fileInputId);

            if (!dropZone || !fileInput) return;

            // Click en la zona de arrastre
            dropZone.addEventListener('mousedown', (e) => {
                if (e.target === dropZone || e.target.closest('.drop-zone-content')) {
                    e.preventDefault();
                    fileInput.click();
                }
            });

            // Arrastrar sobre la zona
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('drag-over');
            });

            // Salir de la zona
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('drag-over');
            });

            // Soltar en la zona
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('drag-over');

                const files = e.dataTransfer.files;
                if (files.length > 0 && onFileSelect) {
                    onFileSelect(files[0]);
                }
            });

            // Cambio en el input
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0 && onFileSelect) {
                    onFileSelect(e.target.files[0]);
                }
            });
        },

        /**
         * Maneja el contador de caracteres para un textarea
         * @param {string} textareaId - ID del textarea
         * @param {string} counterId - ID del elemento contador
         * @param {number} maxLength - Máximo de caracteres
         */
        setupCharCounter(textareaId, counterId, maxLength = 2000) {
            const textarea = document.getElementById(textareaId);
            const counter = document.getElementById(counterId);

            if (!textarea || !counter) return;

            textarea.addEventListener('input', (e) => {
                const length = e.target.value.length;
                counter.textContent = `${length} / ${maxLength} caracteres`;
                counter.classList.remove('warning', 'error');

                if (length > maxLength * 0.9) {
                    counter.classList.add('error');
                } else if (length > maxLength * 0.8) {
                    counter.classList.add('warning');
                }
            });
        },

        /**
         * Configura un componente de búsqueda filtrable (Combobox)
         * @param {Object} options - Opciones de configuración
         * @param {string} options.inputId - ID del input de búsqueda
         * @param {string} options.dropdownId - ID del contenedor del dropdown
         * @param {string} options.hiddenId - ID del input hidden que guardará el valor seleccionado
         * @param {Array} options.dataArray - Array de objetos con {key, name}
         * @param {Function} [options.onSelect] - Callback opcional al seleccionar un elemento
         */
        setupSearchableCombo({ inputId, dropdownId, hiddenId, dataArray, onSelect }) {
            const input = document.getElementById(inputId);
            const dropdown = document.getElementById(dropdownId);
            const hidden = document.getElementById(hiddenId);

            if (!input || !dropdown || !hidden) return;

            // Limpiar listeners anteriores si existen (usando clones para limpiar)
            const newInput = input.cloneNode(true);
            input.parentNode.replaceChild(newInput, input);

            let highlightedIndex = -1;
            let filteredData = [...dataArray];

            const renderOptions = (data) => {
                dropdown.innerHTML = '';
                if (data.length === 0) {
                    dropdown.innerHTML = '<div class="combobox-option no-results">No se encontraron resultados</div>';
                    dropdown.style.display = 'block';
                    return;
                }

                data.forEach((item, index) => {
                    const option = document.createElement('div');
                    option.className = 'combobox-option';
                    option.textContent = item.displayText || `${item.name} (${item.key})`;
                    option.dataset.key = item.key;
                    option.dataset.name = item.name;

                    if (index === highlightedIndex) {
                        option.classList.add('highlighted');
                    }

                    option.onclick = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        selectItem(item);
                    };

                    dropdown.appendChild(option);
                });
                dropdown.style.display = 'block';
            };

            const selectItem = (item) => {
                newInput.value = item.displayText || `${item.name} (${item.key})`;
                hidden.value = item.key;
                dropdown.style.display = 'none';
                highlightedIndex = -1;

                // Disparar evento change manual para el input hidden
                const changeEvent = new Event('change', { bubbles: true });
                hidden.dispatchEvent(changeEvent);

                if (onSelect) onSelect(item);
            };

            const filterOptions = (text) => {
                const search = text.toLowerCase().trim();
                filteredData = dataArray.filter(item =>
                    item.name.toLowerCase().includes(search) ||
                    item.key.toLowerCase().includes(search) ||
                    (item.displayText && item.displayText.toLowerCase().includes(search))
                );
                renderOptions(filteredData);
            };

            const updateHighlight = (options) => {
                options.forEach((opt, i) => {
                    if (i === highlightedIndex) {
                        opt.classList.add('highlighted');
                        opt.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                    } else {
                        opt.classList.remove('highlighted');
                    }
                });
            };

            // Event Listeners
            newInput.addEventListener('focus', () => {
                highlightedIndex = -1;
                if (newInput.value.trim() === '') {
                    renderOptions(dataArray);
                    filteredData = [...dataArray];
                } else {
                    filterOptions(newInput.value);
                }
            });

            newInput.addEventListener('input', () => {
                highlightedIndex = -1;
                filterOptions(newInput.value);
            });

            newInput.addEventListener('keydown', (e) => {
                if (dropdown.style.display === 'none') {
                    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                        dropdown.style.display = 'block';
                        renderOptions(filteredData);
                    }
                    return;
                }

                const options = dropdown.querySelectorAll('.combobox-option:not(.no-results)');
                if (options.length === 0) return;

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    highlightedIndex = (highlightedIndex + 1) % options.length;
                    updateHighlight(options);
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    highlightedIndex = (highlightedIndex - 1 + options.length) % options.length;
                    updateHighlight(options);
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (highlightedIndex >= 0 && highlightedIndex < options.length) {
                        selectItem(filteredData[highlightedIndex]);
                    }
                } else if (e.key === 'Escape') {
                    dropdown.style.display = 'none';
                    highlightedIndex = -1;
                }
            });

            // Cerrar al hacer click fuera - usar delegación o un listener global manejado cuidadosamente
            const outsideClickListener = (e) => {
                if (!newInput.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.style.display = 'none';
                    highlightedIndex = -1;
                }
            };

            document.addEventListener('mousedown', outsideClickListener);

            // Retornar objeto para limpieza o actualización si es necesario
            return {
                destroy: () => {
                    document.removeEventListener('mousedown', outsideClickListener);
                },
                updateData: (newData) => {
                    dataArray = newData;
                    filteredData = [...dataArray];
                }
            };
        },

        /**
         * Resalta un campo con una animación de error
         * @param {HTMLElement|string} element - Elemento o ID del elemento
         */
        highlightError(element) {
            const el = typeof element === 'string' ? document.getElementById(element) : element;
            if (!el) return;

            el.style.border = '2px solid #ef4444';
            el.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
            el.style.animation = 'shake 0.5s';

            setTimeout(() => {
                el.style.border = '';
                el.style.boxShadow = '';
                el.style.animation = '';
            }, 3000);
        }
    };

    window.NexusModules = NexusModules;
})(window);
