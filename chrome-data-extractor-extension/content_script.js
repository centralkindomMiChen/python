// Guard for the entire listener setup
if (!window.hasRunContentScriptInitialized) {
  window.hasRunContentScriptInitialized = true;

  // Helper function for CSV cell escaping
  function escapeCsvCell(text) {
    if (text === null || text === undefined) {
        return "";
    }
    text = String(text); // Ensure text is a string
    text = text.replace(/\s+/g, " ").trim(); // Normalize whitespace
    if (text.includes(',') || text.includes('"') || text.includes('\n')) {
        text = text.replace(/"/g, '""');
        return `"${text}"`;
    }
    return text;
  }

  // Helper function for basic JS prettification
  function basicJsPrettify(jsString) {
    if (typeof jsString !== 'string') jsString = String(jsString);
    try {
      if ((jsString.startsWith("{") && jsString.endsWith("}")) || (jsString.startsWith("[") && jsString.endsWith("]"))) {
          return JSON.stringify(JSON.parse(jsString), null, 2);
      } else {
          throw new Error("Not JSON, using basic JS prettify.");
      }
    } catch (e) {
      return jsString.replace(/;/g, ';\n').replace(/{/g, '{\n').replace(/}/g, '}\n').replace(/,\s*/g, ',\n  ');
    }
  }


  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // --- Preview Handlers (Existing) ---
    if (message.action === "collectImages") {
      const images = Array.from(document.querySelectorAll('img'));
      const imageObjectsArray = images.map((img, index) => {
        let imgSrc = '';
        try { imgSrc = img.src ? new URL(img.src, window.location.href).href : ''; } 
        catch (e) {
          console.warn(`Invalid image URL for preview: ${img.src}`, e.message);
          imgSrc = (img.src && img.src.startsWith('data:image/') && img.src.length > 100) ? 'data_url_preview_too_long' : (img.src || 'invalid_url_or_base64_too_long');
        }
        return { id: "img_" + index, src: imgSrc, alt: img.alt || "" };
      });
      chrome.runtime.sendMessage({ action: "imageListForPreview", images: imageObjectsArray });
      sendResponse({ status: "Image list for preview sent", count: imageObjectsArray.length });
      return false; 
    }

    if (message.action === "extractJsForPreview") {
      const scripts = Array.from(document.querySelectorAll('script'));
      const jsSnippets = scripts.map((s, i) => {
        const id = "js_" + i;
        if (s.src) {
          let scriptSrc = '';
          try { scriptSrc = new URL(s.src, window.location.href).href; } 
          catch (e) { console.warn(`Invalid script URL for JS preview: ${s.src}`, e.message); scriptSrc = `Invalid URL: ${s.src}`; }
          return { id: id, type: "external", src: scriptSrc, preview: `External script: ${scriptSrc}` };
        } else {
          let content = s.textContent || "";
          return { id: id, type: "inline", preview: content.substring(0, 200) + (content.length > 200 ? "..." : ""), fullContentHint: content.length };
        }
      });
      chrome.runtime.sendMessage({ action: "jsListForPreview", scripts: jsSnippets });
      sendResponse({ status: "JS list for preview sent", count: jsSnippets.length });
      return false; 
    }

    if (message.action === "extractTablesForPreview") {
      const tables = Array.from(document.querySelectorAll('table'));
      const tablePreviews = tables.map((t, i) => {
        const id = "table_" + i;
        let rowCount = t.rows.length; let colCount = rowCount > 0 ? t.rows[0].cells.length : 0;
        let previewText = ""; const maxPreviewRows = 2; const maxPreviewCols = 3;
        for (let r = 0; r < Math.min(rowCount, maxPreviewRows); r++) {
          let rowText = "";
          for (let c = 0; c < Math.min(colCount, maxPreviewCols); c++) {
            if (t.rows[r] && t.rows[r].cells[c]) {
              const cellContent = (t.rows[r].cells[c].innerText || t.rows[r].cells[c].textContent || "").trim();
              rowText += cellContent.substring(0, 20) + (cellContent.length > 20 ? "..." : "") + " | ";
            }
          }
          previewText += rowText.slice(0, -3) + (colCount > maxPreviewCols ? " ..." : "") + "\n";
        }
        if (rowCount > maxPreviewRows) previewText += "...\n";
        return { id: id, rows: rowCount, cols: colCount, summary: `Table ${i + 1} (${rowCount} rows, ${colCount} cols)`, previewData: previewText.substring(0, 100) + (previewText.length > 100 ? "..." : "") };
      });
      chrome.runtime.sendMessage({ action: "tableListForPreview", tables: tablePreviews });
      sendResponse({ status: "Table list for preview sent", count: tablePreviews.length });
      return false; 
    }

    // --- Full Content Handlers ---
    if (message.action === "getFullJsContents") {
        (async () => {
            let combinedJsContent = `// Selected JavaScript from ${window.location.href}
// Extraction timestamp: ${new Date().toISOString()}
// Page Hostname: ${message.hostname || "unknown_page"}

`;
            const scriptPromises = [];
            const allScriptsOnPage = Array.from(document.querySelectorAll('script'));
            let actualScriptContentAdded = false;
            let successCount = 0;
            let failureCount = 0;
            let hasFetchFailure = false; // Flag to track if any fetch specifically failed

            for (const scriptId of message.scriptIds) {
                const index = parseInt(scriptId.split('_')[1]);
                if (isNaN(index) || index < 0 || index >= allScriptsOnPage.length) {
                    combinedJsContent += `// --- Invalid Script ID: ${scriptId} ---

`;
                    console.warn("Invalid script ID requested:", scriptId);
                    failureCount++;
                    continue;
                }
                const script = allScriptsOnPage[index];
                let scriptIdentifier = `inline_script_#${index}`;
                try {
                    if (script.src) {
                        scriptIdentifier = new URL(script.src, window.location.href).href;
                    }
                } catch (e) {
                    scriptIdentifier = `invalid_src_#${index}: ${script.src}`;
                    console.warn(`Error constructing URL for script ${scriptId}: ${script.src}`, e.message);
                    // This case might be considered a failure for the script itself, even if not a fetch failure yet.
                }

                if (script.src) {
                    scriptPromises.push(
                        fetch(scriptIdentifier) 
                            .then(response => {
                                if (!response.ok) throw new Error(`HTTP error ${response.status} for ${scriptIdentifier}`);
                                return response.text();
                            })
                            .then(text => {
                                if (text.trim()) actualScriptContentAdded = true;
                                successCount++;
                                combinedJsContent += `// --- Script from ${scriptIdentifier} ---
${basicJsPrettify(text)}

`;
                            })
                            .catch(error => {
                                failureCount++;
                                hasFetchFailure = true; // Mark that a fetch failed
                                console.warn(`Failed to fetch script ${scriptIdentifier}:`, error.message);
                                combinedJsContent += `// --- Failed to fetch script ${scriptIdentifier}: ${error.message || 'Network error or resource access denied (CSP/CORS)'} ---

`;
                            })
                    );
                } else { 
                    let inlineContent = script.textContent || "";
                    if (inlineContent.trim()) {
                        actualScriptContentAdded = true;
                        successCount++;
                    } else {
                        // Consider empty inline script as a "minor" issue, not necessarily a hard failure unless specified
                        // For now, we'll count it as processed if it's selected, even if empty.
                        // If empty inline scripts should be a failure, increment failureCount here.
                        // For this task, focusing on external fetch, let's assume empty inline is not a 'failure'.
                        // If an inline script was *expected* to have content and doesn't, it's a different kind of issue.
                    }
                    combinedJsContent += `// --- Inline Script #${index} ---
${basicJsPrettify(inlineContent)}

`;
                }
            }

            try {
                await Promise.all(scriptPromises);
            } catch (error) {
                // This catch is for Promise.all itself if it's configured to fail fast,
                // but individual catches above should handle and log specific errors.
                // It's unlikely to be hit if all promises have their own .catch.
                console.error("Error awaiting script fetches for getFullJsContents:", error);
                // failureCount might already account for this, but ensure it does if this path is possible.
                // combinedJsContent += `// --- Error occurred during batch fetching of scripts ---

//`;
            }
            
            let errorStatusMessage = null;
            if (failureCount > 0) {
                errorStatusMessage = `${failureCount} of ${message.scriptIds.length} selected scripts encountered issues. `;
                if (hasFetchFailure) {
                    errorStatusMessage += "Some external scripts could not be downloaded (reasons may include network errors, page's Content Security Policy, or CORS restrictions). ";
                }
                errorStatusMessage += "Check the downloaded file for details on which scripts failed.";
            }
            // If no *actual* script content was added (e.g., all selected scripts were empty or failed to fetch)
            // and there were no specific failures already reported, set a generic error.
            if (!actualScriptContentAdded && message.scriptIds.length > 0 && failureCount === 0) {
                 errorStatusMessage = "No valid script content could be retrieved for the selected items. They might be empty or inaccessible.";
            }


            const responsePayload = {
                action: "combinedJsContentToDownload",
                content: combinedJsContent,
                filename: `selected_scripts_${message.hostname || "unknown_page"}.js`,
                errorStatus: errorStatusMessage // This will be null if failureCount is 0 and actualScriptContentAdded is true
            };
            
            // Adjust errorStatus if everything was "successful" but no actual content was found
            if (successCount === message.scriptIds.length && !actualScriptContentAdded && message.scriptIds.length > 0 && !errorStatusMessage) {
                 responsePayload.errorStatus = "Selected scripts were processed, but all were empty or yielded no content.";
            }


            chrome.runtime.sendMessage(responsePayload);
        })();
        sendResponse({status: `JS content processing: ${successCount} success, ${failureCount} failures. Results will be sent.`});
        return true; 
    }

    if (message.action === "getFullTableContentsAsCsv") {
        let combinedCsvContent = `Selected Tables from: ${window.location.href}
Timestamp: ${new Date().toISOString()}
Page Hostname: ${message.hostname || "unknown_page"}

`;
        const allTablesOnPage = Array.from(document.querySelectorAll('table'));
        let actualTableDataAdded = false;
        let successCount = 0;
        let failureCount = 0;


        for (const tableId of message.tableIds) {
            const index = parseInt(tableId.split('_')[1]);
            if (isNaN(index) || index < 0 || index >= allTablesOnPage.length) {
                combinedCsvContent += `--- Invalid Table ID: ${tableId} ---\n\n`;
                console.warn("Invalid table ID requested:", tableId);
                failureCount++;
                continue;
            }
            const table = allTablesOnPage[index];
            combinedCsvContent += `--- Table Index: ${index} (ID: ${tableId}) ---\n`;
            const rows = table.rows;
            let tableHadData = false;
            if (rows.length > 0) {
                for (let i = 0; i < rows.length; i++) {
                    const cells = rows[i].cells;
                    if (cells.length > 0) { 
                        actualTableDataAdded = true; 
                        tableHadData = true;
                        const rowData = [];
                        for (let j = 0; j < cells.length; j++) {
                            rowData.push(escapeCsvCell(cells[j].innerText !== undefined ? cells[j].innerText : cells[j].textContent));
                        }
                        combinedCsvContent += rowData.join(',') + '\n';
                    }
                }
            }
            if (tableHadData) {
                successCount++;
            } else {
                // If the table itself had no rows/cells, it could be considered a "minor failure" or just an empty table.
                // For now, we only increment failureCount for invalid IDs.
                // If an empty table should be a failure, increment failureCount here.
                 combinedCsvContent += `(This table was empty or had no processable cells)\n`;
            }
            combinedCsvContent += '\n\n';
        }
        
        let errorStatusMessage = null;
        if (failureCount > 0) { // Only for invalid IDs for now
            errorStatusMessage = `${failureCount} of ${message.tableIds.length} selected table IDs were invalid. `;
        }
        if (!actualTableDataAdded && message.tableIds.length > 0 && failureCount < message.tableIds.length) { // Some tables were valid but all were empty
             const mainMsg = "No actual data (rows/cells) found in the valid selected tables. ";
             errorStatusMessage = errorStatusMessage ? errorStatusMessage + mainMsg : mainMsg;
        }
        if (errorStatusMessage) {
            errorStatusMessage += "Check the downloaded file for details.";
        }


        const responsePayload = {
            action: "combinedTableDataToDownload",
            content: combinedCsvContent,
            filename: `selected_tables_${message.hostname || "unknown_page"}.csv`,
            errorStatus: errorStatusMessage
        };

        chrome.runtime.sendMessage(responsePayload);
        sendResponse({status: `Table CSV processing: ${successCount} tables with data, ${failureCount} invalid IDs. Results sent.`});
        return false; 
    }

    return true;
  });
}
