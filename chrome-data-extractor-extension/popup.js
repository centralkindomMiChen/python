document.addEventListener('DOMContentLoaded', () => {
  // Main action buttons
  const viewImagesBtn = document.getElementById('viewImagesBtn');
  const viewJsBtn = document.getElementById('viewJsBtn');
  const viewTablesBtn = document.getElementById('viewTablesBtn');
  const statusDiv = document.getElementById('status');

  // Preview Area Divs and their components
  const imagePreviewArea = document.getElementById('imagePreviewArea');
  const jsPreviewArea = document.getElementById('jsPreviewArea');
  const tablePreviewArea = document.getElementById('tablePreviewArea');

  const imageListDiv = document.getElementById('imageList');
  const jsListDiv = document.getElementById('jsList');
  const tableListDiv = document.getElementById('tableList');

  const selectAllImagesCheckbox = document.getElementById('selectAllImages');
  const selectAllJsCheckbox = document.getElementById('selectAllJs');
  const selectAllTablesCheckbox = document.getElementById('selectAllTables');

  const downloadSelectedImagesBtn = document.getElementById('downloadSelectedImagesBtn');
  const downloadSelectedJsBtn = document.getElementById('downloadSelectedJsBtn');
  const downloadSelectedTablesBtn = document.getElementById('downloadSelectedTablesBtn');

  let currentTabId = null; 
  let currentHostname = "unknown_page"; // For filenames

  if (!statusDiv) {
    console.error("CRITICAL: Status display element not found.");
    [viewImagesBtn, viewJsBtn, viewTablesBtn, downloadSelectedImagesBtn, downloadSelectedJsBtn, downloadSelectedTablesBtn].forEach(btn => btn && (btn.disabled = true));
    return; 
  }
  statusDiv.textContent = 'Ready. Select an action.'; 

  function hideAllPreviewAreas() {
    [imagePreviewArea, jsPreviewArea, tablePreviewArea].forEach(area => area && (area.style.display = 'none'));
    [selectAllImagesCheckbox, selectAllJsCheckbox, selectAllTablesCheckbox].forEach(cb => cb && (cb.checked = false));
    updateAllSectionsState(); 
  }

  function updateSectionState(listDiv, downloadButton, selectAllCheckbox) {
    if (!listDiv || !downloadButton || !selectAllCheckbox) return;
    const checkboxes = listDiv.querySelectorAll('input[type="checkbox"]');
    const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
    downloadButton.disabled = checkedCount === 0;
    if (checkboxes.length > 0 && checkedCount === checkboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCount > 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
  }
  
  function updateAllSectionsState() {
      updateSectionState(imageListDiv, downloadSelectedImagesBtn, selectAllImagesCheckbox);
      updateSectionState(jsListDiv, downloadSelectedJsBtn, selectAllJsCheckbox);
      updateSectionState(tableListDiv, downloadSelectedTablesBtn, selectAllTablesCheckbox);
  }
  updateAllSectionsState();

  function suggestedFilename(url, defaultName = "download", itemHostname = "unknown_page") {
      if (url === 'data_url_preview_too_long' || url === 'invalid_url_or_base64_too_long' || !url) {
          return `${defaultName}_${Date.now()}.txt`; 
      }
      try {
          const urlObj = new URL(url);
          let filename = urlObj.pathname.substring(urlObj.pathname.lastIndexOf('/') + 1);
          if (filename) filename = decodeURIComponent(filename);
          if (!filename || urlObj.protocol === 'data:') {
              const prefix = itemHostname !== "unknown_page" ? itemHostname : defaultName;
              if (url.startsWith('data:image/')) {
                  const mimeType = url.substring(url.indexOf(':') + 1, url.indexOf(';'));
                  const extension = mimeType.split('/')[1] || 'png'; 
                  filename = `${prefix}_image.${extension}`;
              } else if (url.startsWith('data:')) {
                  filename = `${prefix}_data.txt`;
              } else { 
                  filename = `${prefix}_${urlObj.hostname.replace(/\./g, '_') || 'file'}.html`;
              }
          }
          return filename.replace(/[<>:"/\\|?*]+/g, '_').substring(0, 200);
      } catch (e) {
          if (url && url.startsWith('data:image/')) {
            const mimeType = url.substring(url.indexOf(':') + 1, url.indexOf(';'));
            const extension = mimeType.split('/')[1] || 'png'; 
            return `${defaultName}_image_data_url.${extension}`;
          }
          let simpleName = url.substring(url.lastIndexOf('/') + 1);
          if (simpleName.includes('?')) simpleName = simpleName.substring(0, simpleName.indexOf('?'));
          if (simpleName.includes('#')) simpleName = simpleName.substring(0, simpleName.indexOf('#'));
          return (simpleName || defaultName).replace(/[<>:"/\\|?*]+/g, '_').substring(0, 200);
      }
  }

  function injectAndSendMessage(action, userFriendlyName) {
    hideAllPreviewAreas(); 
    statusDiv.textContent = `Requesting ${userFriendlyName} from page...`;
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (chrome.runtime.lastError) {
        console.error(`Tab query error for ${userFriendlyName}:`, chrome.runtime.lastError.message);
        statusDiv.textContent = `Error: Could not query active tab. ${chrome.runtime.lastError.message}`;
        currentTabId = null; currentHostname = "unknown_page";
        return;
      }
      if (!tabs || tabs.length === 0 || !tabs[0].id) {
        console.error(`No active tab found for ${userFriendlyName}.`);
        statusDiv.textContent = `Error: No active tab found. Please ensure a page is active.`;
        currentTabId = null; currentHostname = "unknown_page";
        return;
      }
      currentTabId = tabs[0].id; 
      try { currentHostname = new URL(tabs[0].url).hostname || "unknown_page"; } 
      catch { currentHostname = "unknown_page_invalid_url"; }

      if (tabs[0].url?.startsWith('chrome://') || tabs[0].url?.startsWith('https://chrome.google.com')) {
          console.warn(`Cannot inject script into restricted URL: ${tabs[0].url} for ${userFriendlyName}.`);
          statusDiv.textContent = `Error: Cannot operate on restricted pages (e.g., chrome://, Web Store).`;
          return;
      }

      chrome.scripting.executeScript(
        { target: { tabId: currentTabId }, files: ['content_script.js'] },
        () => {
          if (chrome.runtime.lastError) {
            console.error(`Inject script error for ${userFriendlyName}:`, chrome.runtime.lastError.message);
            statusDiv.textContent = `Error injecting script. Try reloading the page. ${chrome.runtime.lastError.message}`;
            return;
          }
          chrome.tabs.sendMessage(currentTabId, { action: action }, (response) => {
            if (chrome.runtime.lastError) {
              console.error(`Send message error for ${userFriendlyName}:`, chrome.runtime.lastError.message);
              statusDiv.textContent = `Error communicating with content script: ${chrome.runtime.lastError.message}. The page might be restricted or not responding.`;
            } else if (response && response.status) {
              statusDiv.textContent = response.status; 
            } else if (response && response.errorStatus) {
              statusDiv.textContent = `Error from page: ${response.errorStatus}`;
            } else {
              console.warn(`No specific initial response or unexpected response from content script for ${userFriendlyName}. Action: ${action}`);
              statusDiv.textContent = `Awaiting data for ${userFriendlyName}...`;
            }
          });
        }
      );
    });
  }

  if (viewImagesBtn) viewImagesBtn.addEventListener('click', () => injectAndSendMessage("collectImages", "Images"));
  if (viewJsBtn) viewJsBtn.addEventListener('click', () => injectAndSendMessage("extractJsForPreview", "JavaScript Snippets"));
  if (viewTablesBtn) viewTablesBtn.addEventListener('click', () => injectAndSendMessage("extractTablesForPreview", "Tables"));

  function createItemCheckbox(itemValue, itemDataAttributes = {}) {
      const checkbox = document.createElement('input'); checkbox.type = 'checkbox';
      checkbox.value = itemValue;
      for (const key in itemDataAttributes) checkbox.dataset[key] = itemDataAttributes[key];
      checkbox.addEventListener('change', () => {
          if (itemDataAttributes.listId === 'imageList') updateSectionState(imageListDiv, downloadSelectedImagesBtn, selectAllImagesCheckbox);
          else if (itemDataAttributes.listId === 'jsList') updateSectionState(jsListDiv, downloadSelectedJsBtn, selectAllJsCheckbox);
          else if (itemDataAttributes.listId === 'tableList') updateSectionState(tableListDiv, downloadSelectedTablesBtn, selectAllTablesCheckbox);
      });
      return checkbox;
  }

  function displayImagePreviews(images) {
    hideAllPreviewAreas();
    if (!imageListDiv || !imagePreviewArea) return;
    imageListDiv.innerHTML = ''; 
    if (!images || images.length === 0) {
      imageListDiv.textContent = 'No images found on this page.';
      statusDiv.textContent = 'No images found on the page.';
    } else {
      images.forEach(image => {
        const itemDiv = document.createElement('div'); itemDiv.className = 'item';
        const checkbox = createItemCheckbox(image.id, { url: image.src, alt: image.alt || '', listId: 'imageList' });
        const imgTag = document.createElement('img'); imgTag.className = 'thumbnail';
        imgTag.onerror = function() { this.alt='Failed to load'; this.src=''; this.style.border='1px dashed red';};
        if (image.src === 'data_url_preview_too_long' || image.src === 'invalid_url_or_base64_too_long') {
            imgTag.alt = image.src; imgTag.src = ''; 
        } else { imgTag.src = image.src; imgTag.alt = image.alt || 'Preview';}
        const detailsDiv = document.createElement('div'); detailsDiv.className = 'item-details';
        const altText = image.alt ? `Alt: ${image.alt.substring(0,100)}${image.alt.length > 100 ? '...' : ''}` : 'Alt: (not set)';
        const urlText = image.src.startsWith('data:') ? 'Data URL' : `URL: ${image.src.substring(0,150)}${image.src.length > 150 ? '...' : ''}`;
        detailsDiv.textContent = `${altText}\n${urlText}`;
        itemDiv.appendChild(checkbox); itemDiv.appendChild(imgTag); itemDiv.appendChild(detailsDiv);
        imageListDiv.appendChild(itemDiv);
      });
      statusDiv.textContent = `Found ${images.length} images. Select to download.`;
    }
    imagePreviewArea.style.display = 'block';
    updateSectionState(imageListDiv, downloadSelectedImagesBtn, selectAllImagesCheckbox);
  }

  function displayJsPreviews(scripts) {
    hideAllPreviewAreas();
    if (!jsListDiv || !jsPreviewArea) return;
    jsListDiv.innerHTML = '';
    if (!scripts || scripts.length === 0) {
      jsListDiv.textContent = 'No JS snippets found on this page.'; statusDiv.textContent = 'No JS snippets found on the page.';
    } else {
      scripts.forEach(script => {
        const itemDiv = document.createElement('div'); itemDiv.className = 'item';
        const checkbox = createItemCheckbox(script.id, { type: script.type, src: script.src || '', listId: 'jsList' });
        const detailsDiv = document.createElement('div'); detailsDiv.className = 'item-details';
        let typeInfo = `Type: ${script.type}`;
        if (script.type === 'external') typeInfo += ` | Src: ${script.src.substring(0,150)}${script.src.length > 150 ? '...' : ''}`;
        else typeInfo += ` | Length: ${script.fullContentHint} chars`;
        const previewPre = document.createElement('pre'); previewPre.textContent = script.preview;
        detailsDiv.appendChild(document.createTextNode(typeInfo)); detailsDiv.appendChild(previewPre);
        itemDiv.appendChild(checkbox); itemDiv.appendChild(detailsDiv);
        jsListDiv.appendChild(itemDiv);
      });
      statusDiv.textContent = `Found ${scripts.length} JS snippets. Select to download.`;
    }
    jsPreviewArea.style.display = 'block';
    updateSectionState(jsListDiv, downloadSelectedJsBtn, selectAllJsCheckbox);
  }

  function displayTablePreviews(tables) {
    hideAllPreviewAreas();
    if (!tableListDiv || !tablePreviewArea) return;
    tableListDiv.innerHTML = '';
    if (!tables || tables.length === 0) {
      tableListDiv.textContent = 'No tables found on this page.'; statusDiv.textContent = 'No tables found on the page.';
    } else {
      tables.forEach(table => {
        const itemDiv = document.createElement('div'); itemDiv.className = 'item';
        const checkbox = createItemCheckbox(table.id, {listId: 'tableList'});
        const detailsDiv = document.createElement('div'); detailsDiv.className = 'item-details';
        detailsDiv.textContent = `${table.summary}`;
        const previewPre = document.createElement('pre'); previewPre.textContent = table.previewData;
        detailsDiv.appendChild(previewPre);
        itemDiv.appendChild(checkbox); itemDiv.appendChild(detailsDiv);
        tableListDiv.appendChild(itemDiv);
      });
      statusDiv.textContent = `Found ${tables.length} tables. Select to download.`;
    }
    tablePreviewArea.style.display = 'block';
    updateSectionState(tableListDiv, downloadSelectedTablesBtn, selectAllTablesCheckbox);
  }
  
  // Helper to check if content is just boilerplate (simple check based on line count after header)
  function isContentEffectivelyEmpty(content, expectedHeaderLines) {
      if (!content) return true;
      const lines = content.split('\n');
      // Check if content has more than just the header lines and some minimal actual content lines
      // This is a heuristic. A more robust check might involve checking for non-comment lines.
      return lines.length <= expectedHeaderLines + 2; // Allow for a couple of blank lines or minimal content
  }


  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || !message.action) { console.warn("Received an invalid message:", message); return; }
    let initialStatus = "";
    let proceedWithDownload = true;

    switch (message.action) {
      case "imageListForPreview": displayImagePreviews(message.images); break;
      case "jsListForPreview": displayJsPreviews(message.scripts); break;
      case "tableListForPreview": displayTablePreviews(message.tables); break;
      case "statusUpdate": statusDiv.textContent = message.text; break;
      
      case "combinedJsContentToDownload":
        if (message.errorStatus) {
            initialStatus = message.errorStatus;
            if (isContentEffectivelyEmpty(message.content, 3)) { // JS header is ~3 lines
                statusDiv.textContent = message.errorStatus + " No downloadable content generated.";
                proceedWithDownload = false;
            } else {
                statusDiv.textContent = message.errorStatus + " Proceeding with download of partial results...";
            }
        } else {
            statusDiv.textContent = `Preparing download for ${message.filename}...`;
        }

        if (proceedWithDownload && message.content && message.filename) {
          try {
            const blob = new Blob([message.content], { type: 'text/javascript;charset=utf-8' });
            const objectUrl = URL.createObjectURL(blob);
            chrome.downloads.download({ url: objectUrl, filename: message.filename, saveAs: true }, (downloadId) => {
              if (chrome.runtime.lastError) {
                statusDiv.textContent = initialStatus ? initialStatus + ` Download failed: ${chrome.runtime.lastError.message}` : `Download failed for ${message.filename}: ${chrome.runtime.lastError.message}`;
              } else if (downloadId === undefined) {
                statusDiv.textContent = initialStatus ? initialStatus + ` Download did not start. Check browser settings.` : `Download of ${message.filename} did not start. Check browser settings.`;
              } else {
                statusDiv.textContent = initialStatus ? initialStatus + ` Download started: ${message.filename}` : `Download started: ${message.filename}`;
              }
              URL.revokeObjectURL(objectUrl);
            });
          } catch (e) { statusDiv.textContent = initialStatus ? initialStatus + ` Error creating JS file: ${e.message}` : `Error creating JS file: ${e.message}`; }
        } else if (proceedWithDownload && (!message.content || !message.filename)) {
             statusDiv.textContent = initialStatus ? initialStatus + " Error: Missing content or filename for JS download." : "Error: Missing content or filename for JS download.";
        }
        break;

      case "combinedTableDataToDownload":
        if (message.errorStatus) {
            initialStatus = message.errorStatus;
            if (isContentEffectivelyEmpty(message.content, 3)) { // CSV header is ~3 lines
                statusDiv.textContent = message.errorStatus + " No downloadable content generated.";
                proceedWithDownload = false;
            } else {
                statusDiv.textContent = message.errorStatus + " Proceeding with download of partial results...";
            }
        } else {
            statusDiv.textContent = `Preparing download for ${message.filename}...`;
        }

        if (proceedWithDownload && message.content && message.filename) {
          try {
            const blob = new Blob([message.content], { type: 'text/csv;charset=utf-8' });
            const objectUrl = URL.createObjectURL(blob);
            chrome.downloads.download({ url: objectUrl, filename: message.filename, saveAs: true }, (downloadId) => {
              if (chrome.runtime.lastError) {
                statusDiv.textContent = initialStatus ? initialStatus + ` Download failed: ${chrome.runtime.lastError.message}` : `Download failed for ${message.filename}: ${chrome.runtime.lastError.message}`;
              } else if (downloadId === undefined) {
                statusDiv.textContent = initialStatus ? initialStatus + ` Download did not start. Check browser settings.` : `Download of ${message.filename} did not start. Check browser settings.`;
              } else {
                statusDiv.textContent = initialStatus ? initialStatus + ` Download started: ${message.filename}` : `Download started: ${message.filename}`;
              }
              URL.revokeObjectURL(objectUrl);
            });
          } catch (e) { statusDiv.textContent = initialStatus ? initialStatus + ` Error creating CSV file: ${e.message}` : `Error creating CSV file: ${e.message}`; }
        } else if (proceedWithDownload && (!message.content || !message.filename)) {
            statusDiv.textContent = initialStatus ? initialStatus + " Error: Missing content or filename for CSV download." : "Error: Missing content or filename for CSV download.";
        }
        break;
      default: console.warn("Received unknown message action in popup:", message.action, message); break;
    }
  });

  function setupSelectAll(masterCheckbox, listDiv, downloadButton) {
    if (masterCheckbox && listDiv && downloadButton) {
      masterCheckbox.addEventListener('change', (event) => {
        listDiv.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = event.target.checked);
        updateSectionState(listDiv, downloadButton, masterCheckbox);
      });
    }
  }
  setupSelectAll(selectAllImagesCheckbox, imageListDiv, downloadSelectedImagesBtn);
  setupSelectAll(selectAllJsCheckbox, jsListDiv, downloadSelectedJsBtn);
  setupSelectAll(selectAllTablesCheckbox, tableListDiv, downloadSelectedTablesBtn);

  if (downloadSelectedImagesBtn) {
    downloadSelectedImagesBtn.addEventListener('click', (event) => {
      event.preventDefault();
      const selectedCheckboxes = Array.from(imageListDiv.querySelectorAll('input[type="checkbox"]:checked'));
      if (selectedCheckboxes.length === 0) {
        statusDiv.textContent = "No images selected for download."; return;
      }
      statusDiv.textContent = `Downloading ${selectedCheckboxes.length} image(s)...`;
      let downloadedCount = 0; let failedCount = 0;
      selectedCheckboxes.forEach(cb => {
        const imageUrl = cb.dataset.url;
        if (imageUrl && imageUrl !== 'data_url_preview_too_long' && imageUrl !== 'invalid_url_or_base64_too_long') {
          chrome.downloads.download({ url: imageUrl, filename: suggestedFilename(imageUrl, 'image', currentHostname) }, (downloadId) => {
            if (chrome.runtime.lastError || downloadId === undefined) {
              failedCount++; console.warn(`Failed to download image: ${imageUrl}`, chrome.runtime.lastError?.message);
            } else { downloadedCount++; }
            if (downloadedCount + failedCount === selectedCheckboxes.length) {
              statusDiv.textContent = `Image downloads: ${downloadedCount} succeeded, ${failedCount} failed.`;
            }
          });
        } else {
            failedCount++; console.warn("Skipping download for invalid/placeholder image URL:", cb.dataset.alt || imageUrl);
             if (downloadedCount + failedCount === selectedCheckboxes.length) {
              statusDiv.textContent = `Image downloads: ${downloadedCount} succeeded, ${failedCount} failed.`;
            }
        }
      });
    });
  }

  if (downloadSelectedJsBtn) {
    downloadSelectedJsBtn.addEventListener('click', (event) => {
      event.preventDefault();
      if (!currentTabId) { statusDiv.textContent = "Error: Tab context lost. Please 'View JS Snippets' again."; return; }
      const selectedScriptIds = Array.from(jsListDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
      if (selectedScriptIds.length === 0) {
        statusDiv.textContent = "No JS snippets selected for download."; return;
      }
      statusDiv.textContent = `Fetching content for ${selectedScriptIds.length} selected JS snippet(s)...`;
      chrome.tabs.sendMessage(currentTabId, { action: "getFullJsContents", scriptIds: selectedScriptIds, hostname: currentHostname });
    });
  }

  if (downloadSelectedTablesBtn) {
    downloadSelectedTablesBtn.addEventListener('click', (event) => {
      event.preventDefault();
      if (!currentTabId) { statusDiv.textContent = "Error: Tab context lost. Please 'View Tables' again."; return; }
      const selectedTableIds = Array.from(tableListDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
      if (selectedTableIds.length === 0) {
        statusDiv.textContent = "No tables selected for download."; return;
      }
      statusDiv.textContent = `Fetching data for ${selectedTableIds.length} selected table(s)...`;
      chrome.tabs.sendMessage(currentTabId, { action: "getFullTableContentsAsCsv", tableIds: selectedTableIds, hostname: currentHostname });
    });
  }
});
