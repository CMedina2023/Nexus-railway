/**
 * Nexus AI - CSV Parser Module
 * Handles CSV parsing logic.
 */

(function (window) {
    'use strict';

    window.NexusModules = window.NexusModules || {};
    window.NexusModules.Jira = window.NexusModules.Jira || {};
    window.NexusModules.Jira.BulkUpload = window.NexusModules.Jira.BulkUpload || {};

    function parseCSV(text) {
        const rows = [];
        let currentRow = [];
        let currentField = '';
        let insideQuotes = false;

        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            const nextChar = text[i + 1];

            if (char === '"') {
                if (insideQuotes && nextChar === '"') {
                    currentField += '"';
                    i++;
                } else {
                    insideQuotes = !insideQuotes;
                }
            } else if (char === ',' && !insideQuotes) {
                currentRow.push(currentField.trim());
                currentField = '';
            } else if ((char === '\n' || char === '\r') && !insideQuotes) {
                if (currentField || currentRow.length > 0) {
                    currentRow.push(currentField.trim());
                    rows.push(currentRow);
                    currentRow = [];
                    currentField = '';
                }
                if (char === '\r' && nextChar === '\n') {
                    i++;
                }
            } else {
                currentField += char;
            }
        }

        if (currentField || currentRow.length > 0) {
            currentRow.push(currentField.trim());
            rows.push(currentRow);
        }

        return rows;
    }

    /**
     * Reads a File object and returns parsed CSV data
     * @param {File} file - The CSV file to read
     * @returns {Promise<{headers: string[], data: object[], rawParsed: string[][]}>}
     */
    function readCsvFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const csvText = e.target.result;
                    const parsed = parseCSV(csvText);
                    const result = {
                        headers: [],
                        data: [],
                        rawParsed: parsed
                    };

                    if (parsed.length > 0) {
                        result.headers = parsed[0].map(col => col.trim().replace(/^"|"$/g, ''));

                        for (let i = 1; i < parsed.length; i++) {
                            if (parsed[i] && parsed[i].length > 0) {
                                const row = {};
                                result.headers.forEach((h, idx) => {
                                    row[h] = parsed[i][idx] || '';
                                });
                                result.data.push(row);
                            }
                        }
                    }
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            };
            reader.onerror = () => reject(new Error('Error reading file'));
            reader.readAsText(file, 'UTF-8');
        });
    }

    window.NexusModules.Jira.BulkUpload.CsvParser = {
        parse: parseCSV,
        readFile: readCsvFile
    };

})(window);
