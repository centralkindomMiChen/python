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

            for (const scriptId of message.scriptIds) {
                const index = parseInt(scriptId.split('_')[1]);
                if (isNaN(index) || index < 0 || index >= allScriptsOnPage.length) {
                    combinedJsContent += `// --- Invalid Script ID: ${scriptId} ---

`;
                    console.warn("Invalid script ID requested:", scriptId);
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
                                combinedJsContent += `// --- Script from ${scriptIdentifier} ---
${basicJsPrettify(text)}

`;
                            })
                            .catch(error => {
                                console.warn(`Failed to fetch script ${scriptIdentifier}:`, error.message);
                                combinedJsContent += `// --- Failed to fetch script ${scriptIdentifier}: ${error.message} ---

`;
                            })
                    );
                } else { 
                    let inlineContent = script.textContent || "";
                    if (inlineContent.trim()) actualScriptContentAdded = true;
                    combinedJsContent += `// --- Inline Script #${index} ---
${basicJsPrettify(inlineContent)}

`;
                }
            }

            try {
                await Promise.all(scriptPromises);
            } catch (error) {
                console.error("Error awaiting script fetches for getFullJsContents:", error);
                combinedJsContent += `// --- Error occurred during batch fetching of scripts ---

`;
            }
            
            const responsePayload = {
                action: "combinedJsContentToDownload",
                content: combinedJsContent,
                filename: `selected_scripts_${message.hostname || "unknown_page"}.js`
            };

            if (!actualScriptContentAdded && message.scriptIds.length > 0) {
                 // Check if any script content was actually added, beyond headers/error comments
                const placeholderHeaderLength = (`// Selected JavaScript from ${window.location.href}\n// Extraction timestamp: ${new Date().toISOString()}\n// Page Hostname: ${message.hostname || "unknown_page"}\n\n`).length;
                let contentWithoutHeader = combinedJsContent.substring(placeholderHeaderLength);
                let onlyCommentsOrErrors = true;
                contentWithoutHeader.split("// ---").forEach(segment => {
                    if (segment.includes("---") && segment.split("\n").slice(1).join("\n").trim() !== "") {
                        // Check if the part after a separator line actually contains non-empty lines
                        if (segment.split("\n").slice(1).some(line => line.trim() !== "" && !line.trim().startsWith("//"))) {
                             onlyCommentsOrErrors = false;
                        }
                    } else if (!segment.includes("---") && segment.trim() !== "") {
                         onlyCommentsOrErrors = false;
                    }
                });
                if(onlyCommentsOrErrors && !scriptPromises.length){ // If only inline scripts and all were empty or only comments
                     // This part is tricky, might need more robust check if script content itself is just comments
                }


                // Simplified check: if no scriptPromises were successful and no inline scripts had substantial content
                // For now, rely on the actualScriptContentAdded flag. If it's false, it means no script had meaningful content.
                if (!actualScriptContentAdded) {
                     responsePayload.errorStatus = "No valid script content could be retrieved for the selected items. File may contain only headers or error messages.";
                }
            }


            chrome.runtime.sendMessage(responsePayload);
        })();
        sendResponse({status: "JS content processing initiated. Full content will be sent separately."});
        return true; 
    }

    if (message.action === "getFullTableContentsAsCsv") {
        let combinedCsvContent = `Selected Tables from: ${window.location.href}
Timestamp: ${new Date().toISOString()}
Page Hostname: ${message.hostname || "unknown_page"}

`;
        const allTablesOnPage = Array.from(document.querySelectorAll('table'));
        let actualTableDataAdded = false;

        for (const tableId of message.tableIds) {
            const index = parseInt(tableId.split('_')[1]);
            if (isNaN(index) || index < 0 || index >= allTablesOnPage.length) {
                combinedCsvContent += `--- Invalid Table ID: ${tableId} ---\n\n`;
                console.warn("Invalid table ID requested:", tableId);
                continue;
            }
            const table = allTablesOnPage[index];
            combinedCsvContent += `--- Table Index: ${index} (ID: ${tableId}) ---\n`;
            const rows = table.rows;
            if (rows.length > 0) {
                for (let i = 0; i < rows.length; i++) {
                    const cells = rows[i].cells;
                    if (cells.length > 0) { // Only consider a row if it has cells
                        actualTableDataAdded = true; // Mark that we've found some data
                        const rowData = [];
                        for (let j = 0; j < cells.length; j++) {
                            rowData.push(escapeCsvCell(cells[j].innerText !== undefined ? cells[j].innerText : cells[j].textContent));
                        }
                        combinedCsvContent += rowData.join(',') + '\n';
                    }
                }
            }
            combinedCsvContent += '\n\n';
        }
        
        const responsePayload = {
            action: "combinedTableDataToDownload",
            content: combinedCsvContent,
            filename: `selected_tables_${message.hostname || "unknown_page"}.csv`
        };

        if (!actualTableDataAdded && message.tableIds.length > 0) {
            responsePayload.errorStatus = "No valid table data (rows/cells) could be retrieved for the selected items. File may contain only headers or empty tables.";
        }

        chrome.runtime.sendMessage(responsePayload);
        sendResponse({status: "Table CSV processing completed and sent."});
        return false; 
    }

    return true;
  });
}
