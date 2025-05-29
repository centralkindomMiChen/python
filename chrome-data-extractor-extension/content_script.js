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

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "collectImages") {
      // console.log("Content script received collectImages action");
      const images = Array.from(document.querySelectorAll('img'));
      const imageUrls = images.map(img => {
        if (img.src) {
          try {
            return new URL(img.src, window.location.href).href;
          } catch (e) {
            console.warn("Invalid image URL:", img.src, e.message);
            return null;
          }
        }
        return null;
      }).filter(url => url !== null);
      
      chrome.runtime.sendMessage({ action: "downloadImagesBatch", urls: imageUrls });
      sendResponse({ status: "Image URLs collected, sending to popup.", count: imageUrls.length });
      return false; 
    }

    if (message.action === "extractAndPrettifyJs") {
      // console.log("Content script received extractAndPrettifyJs action");
      (async () => {
        let allScriptsContent = `// Extracted JavaScript from ${window.location.href}
// Extraction timestamp: ${new Date().toISOString()}

`;
        const scripts = Array.from(document.querySelectorAll('script'));
        const scriptPromises = [];
        const pageHostname = new URL(window.location.href).hostname || "unknown_page";

        for (const script of scripts) {
          if (script.src) {
            let scriptUrlStr = '';
            try {
                scriptUrlStr = new URL(script.src, window.location.href).href;
            } catch (e) {
                console.warn(`Invalid script URL encountered: ${script.src}`, e.message);
                allScriptsContent += `// --- Skipped invalid external script URL: ${script.src} ---
// Error: ${e.message}

`;
                continue;
            }
            const scriptUrl = scriptUrlStr;

            scriptPromises.push(
              fetch(scriptUrl)
                .then(response => {
                  if (!response.ok) throw new Error(`Failed to fetch ${scriptUrl}: ${response.status} ${response.statusText}`);
                  return response.text();
                })
                .then(text => {
                  let prettyText = text;
                  try {
                    // Attempt to parse as JSON only if it looks like JSON (heuristic)
                    if ((text.startsWith("{") && text.endsWith("}")) || (text.startsWith("[") && text.endsWith("]"))) {
                        prettyText = JSON.stringify(JSON.parse(text), null, 2);
                        allScriptsContent += `// --- Script from ${scriptUrl} (prettified as JSON) ---
${prettyText}

`;
                    } else {
                        throw new Error("Not JSON, using basic JS prettify."); // Go to basic prettify
                    }
                  } catch (e) {
                    prettyText = text.replace(/;/g, ';\n').replace(/{/g, '{\n').replace(/}/g, '}\n');
                    allScriptsContent += `// --- Script from ${scriptUrl} (basic formatting) ---
${prettyText}

`;
                  }
                })
                .catch(error => {
                  console.warn(`Error fetching or processing script ${scriptUrl}:`, error.message);
                  allScriptsContent += `// --- Failed to fetch or process script from ${scriptUrl}: ${error.message} ---

`;
                })
            );
          } else {
            let inlineContent = script.textContent || "";
            try {
              // Attempt to parse as JSON only if it looks like JSON (heuristic)
              if ((inlineContent.startsWith("{") && inlineContent.endsWith("}")) || (inlineContent.startsWith("[") && inlineContent.endsWith("]"))) {
                inlineContent = JSON.stringify(JSON.parse(inlineContent), null, 2);
                allScriptsContent += `// --- Inline Script (prettified as JSON) ---
${inlineContent}

`;
              } else {
                throw new Error("Not JSON, using basic JS prettify."); // Go to basic prettify
              }
            } catch (e) {
              inlineContent = inlineContent.replace(/;/g, ';\n').replace(/{/g, '{\n').replace(/}/g, '}\n');
              allScriptsContent += `// --- Inline Script (basic formatting) ---
${inlineContent}

`;
            }
          }
        }

        try {
            await Promise.all(scriptPromises);
        } catch (error) {
            // This catch block is for Promise.all itself, though individual catches should handle most.
            console.error("Error during Promise.all for script fetches:", error.message);
            allScriptsContent += `// --- Error during batch processing of script fetches: ${error.message} ---

`;
        }
        
        chrome.runtime.sendMessage({
          action: "downloadJsFile",
          content: allScriptsContent,
          filename: `extracted_scripts_${pageHostname}.js`
        });
        sendResponse({ status: "JS extraction initiated. Data will be sent." });
      })();
      return true; 
    }

    if (message.action === "extractTables") {
      // console.log("Content script received extractTables action");
      let allTablesText = `Extracted Tables from: ${window.location.href}
Timestamp: ${new Date().toISOString()}
Page Hostname: ${new URL(window.location.href).hostname || "unknown_page"}

`;
      const tables = document.querySelectorAll('table');
      const pageHostname = new URL(window.location.href).hostname || "unknown_page";

      if (tables.length === 0) {
        allTablesText += "No tables found on this page.";
      } else {
        tables.forEach((table, index) => {
          allTablesText += `--- Table ${index + 1} of ${tables.length} ---\n`;
          const rows = table.rows;
          for (let i = 0; i < rows.length; i++) {
            const cells = rows[i].cells;
            const rowData = [];
            for (let j = 0; j < cells.length; j++) {
              const cellText = cells[j].innerText !== undefined ? cells[j].innerText.trim() : (cells[j].textContent || "").trim();
              rowData.push(escapeCsvCell(cellText));
            }
            allTablesText += rowData.join(',') + '\n';
          }
          allTablesText += '\n\n'; 
        });
      }

      const filename = `extracted_tables_${pageHostname}.csv`;
      chrome.runtime.sendMessage({
        action: "downloadTableData",
        content: allTablesText,
        filename: filename
      });
      
      sendResponse({ status: "Table extraction processed, sending data.", tableCount: tables.length });
      return false; 
    }
  });
}
