/**
 * Nexus AI - Upload File Handler
 * Handles file drop zone interactions and CSV reading.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    const CsvParser = window.NexusModules.Jira.BulkUpload.CsvParser;
    const State = window.NexusModules.Jira.BulkUpload.State;

    function setupDropZone(onFileProcessed, showStatusCallback) {
        const dropZone = document.getElementById('csv-drop-zone');
        const fileInput = document.getElementById('csv-file-input');

        if (!dropZone || !fileInput) return;

        dropZone.addEventListener('mousedown', (e) => {
            if (e.target === dropZone || e.target.closest('.drop-zone-content')) {
                e.preventDefault();
                fileInput.click();
            }
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0], onFileProcessed, showStatusCallback);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0], onFileProcessed, showStatusCallback);
            }
        });
    }

    async function handleFileSelect(file, onFileProcessed, showStatusCallback) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            if (showStatusCallback) showStatusCallback('error', 'Solo se permiten archivos CSV');
            return;
        }

        State.update({ selectedCsvFile: file });

        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('file-name');

        if (fileInfo && fileName) {
            fileName.textContent = file.name;
            fileInfo.style.display = 'flex';
        }

        try {
            const result = await CsvParser.readFile(file);
            State.update({
                csvColumns: result.headers,
                csvData: result.data
            });

            if (onFileProcessed) onFileProcessed();
        } catch (error) {
            console.error('Error al leer CSV:', error);
            if (showStatusCallback) showStatusCallback('error', 'Error al leer el archivo CSV');
        }
    }

    window.NexusModules.Jira.BulkUpload.FileHandler = {
        setupDropZone,
        handleFileSelect
    };

})(window);
