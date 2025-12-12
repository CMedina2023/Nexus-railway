# PDF Generation Fix - Summary

## Problem
The PDF download feature was getting stuck ("loading forever") on Railway.

## Root Cause
The application was using **Playwright** to generate PDFs. Playwright requires a full browser (Chromium) to be installed in the server environment. On Railway's standard Python container, these browser dependencies are missing, causing the process to hang or fail silently while trying to launch the browser.

## Solution
Switched the PDF generation library from **Playwright** to **WeasyPrint**.

### Why WeasyPrint?
- **Lightweight:** Does not require a full browser installation.
- **Server-Friendly:** Designed specifically for generating PDFs from HTML/CSS on servers.
- **Easy Deployment:** Works out-of-the-box with standard Python environments on Railway.

## Changes Made
1. **requirements.txt**: 
   - Removed `playwright`
   - Added `weasyprint>=60.0.0`

2. **app/core/app.py**:
   - Replaced `playwright` imports with `weasyprint`
   - Refactored `jira_download_report` to use `HTML(string=...).write_pdf()`
   - Refactored `metrics_download_report` to use `HTML(string=...).write_pdf()`
   - Configured PDF output to use A4 Landscape format

## Verification
After deployment, clicking "Download PDF" should now generate and download the file quickly without hanging.
