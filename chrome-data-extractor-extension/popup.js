document.addEventListener('DOMContentLoaded', () => {
  const downloadImagesBtn = document.getElementById('downloadImagesBtn');
  const extractJsBtn = document.getElementById('extractJsBtn');
  const extractTablesBtn = document.getElementById('extractTablesBtn');
  const statusDiv = document.getElementById('status');

  if (!statusDiv) {
    console.error("CRITICAL: Status display element not found.");
    if(downloadImagesBtn) downloadImagesBtn.disabled = true;
    if(extractJsBtn) extractJsBtn.disabled = true;
    if(extractTablesBtn) extractTablesBtn.disabled = true;
    return; 
  }
  statusDiv.textContent = 'Ready. Select an action.'; 

  function injectAndSendMessage(action, userFriendlyName) {
    statusDiv.textContent = `Processing ${userFriendlyName}... Please wait.`;
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (chrome.runtime.lastError) {
        console.error(`Tab query error for ${userFriendlyName}:`, chrome.runtime.lastError.message);
        statusDiv.textContent = `Error: Could not query active tab for ${userFriendlyName}.`;
        return;
      }
      if (!tabs || tabs.length === 0 || !tabs[0].id) {
        console.error(`No active tab found for ${userFriendlyName}.`);
        statusDiv.textContent = `Error: No active tab found for ${userFriendlyName}.`;
        return;
      }
      const tabId = tabs[0].id;

      if (tabs[0].url?.startsWith('chrome://') || tabs[0].url?.startsWith('https://chrome.google.com')) {
          console.warn(`Cannot inject script into restricted URL: ${tabs[0].url} for ${userFriendlyName}.`);
          statusDiv.textContent = `Error: Cannot operate on restricted pages (e.g., chrome://, Web Store) for ${userFriendlyName}.`;
          return;
      }

      chrome.scripting.executeScript(
        { target: { tabId: tabId }, files: ['content_script.js'] },
        () => {
          if (chrome.runtime.lastError) {
            console.error(`Inject script error for ${userFriendlyName}:`, chrome.runtime.lastError.message);
            statusDiv.textContent = `Error injecting script for ${userFriendlyName}. Try reloading the page.`;
            return;
          }
          chrome.tabs.sendMessage(tabId, { action: action }, (response) => {
            if (chrome.runtime.lastError) {
              console.error(`Send message error for ${userFriendlyName}:`, chrome.runtime.lastError.message);
              statusDiv.textContent = `Error communicating with content script for ${userFriendlyName}. The page might be restricted or not responding.`;
            } else if (response && response.status) {
              statusDiv.textContent = response.status; 
              // console.log(`Initial response from content script for ${userFriendlyName}:`, response); // Removed for cleaner console
            } else {
                console.warn(`No specific initial response or unexpected response from content script for ${userFriendlyName}.`);
            }
          });
        }
      );
    });
  }

  if (downloadImagesBtn) {
    downloadImagesBtn.addEventListener('click', () => {
      injectAndSendMessage("collectImages", "Images");
    });
  } else {
    console.error('Download Images button not found.');
  }

  if (extractJsBtn) {
    extractJsBtn.addEventListener('click', () => {
      injectAndSendMessage("extractAndPrettifyJs", "JavaScript");
    });
  } else {
    console.error('Extract JS button not found.');
  }

  if (extractTablesBtn) {
    extractTablesBtn.addEventListener('click', () => {
      injectAndSendMessage("extractTables", "Tables");
    });
  } else {
    console.error('Extract Tables button not found.');
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || !message.action) {
        console.warn("Received an invalid message:", message);
        return;
    }

    switch (message.action) {
      case "downloadImagesBatch":
        if (message.urls && message.urls.length > 0) {
          statusDiv.textContent = `Found ${message.urls.length} images. Starting downloads...`;
          let downloadedCount = 0;
          let failedCount = 0;
          const totalImages = message.urls.length;

          message.urls.forEach(url => {
            if (url) {
              chrome.downloads.download({ url: url }, (downloadId) => {
                if (chrome.runtime.lastError) {
                  failedCount++;
                  console.error("Download failed for image:", url, chrome.runtime.lastError.message);
                } else if (downloadId === undefined) {
                  failedCount++;
                  console.warn("Download did not start for image (downloadId undefined):", url);
                } else {
                  downloadedCount++;
                  // console.log("Downloading image:", url, "Download ID:", downloadId); // Can be verbose
                }
                
                if (downloadedCount + failedCount === totalImages) {
                  statusDiv.textContent = `Image downloads complete: ${downloadedCount} succeeded, ${failedCount} failed.`;
                } else {
                  statusDiv.textContent = `Downloading images... ${downloadedCount}/${totalImages} succeeded, ${failedCount} failed.`;
                }
              });
            } else {
              failedCount++; 
              if (downloadedCount + failedCount === totalImages) {
                statusDiv.textContent = `Image downloads complete: ${downloadedCount} succeeded, ${failedCount} failed.`;
              }
            }
          });
        } else {
          statusDiv.textContent = "No images found on this page.";
        }
        break;

      case "downloadJsFile":
        if (message.content && message.filename) {
          statusDiv.textContent = `JavaScript extracted (${message.filename}). Preparing download...`;
          try {
            const blob = new Blob([message.content], { type: 'text/javascript;charset=utf-8' });
            const objectUrl = URL.createObjectURL(blob);

            chrome.downloads.download({
              url: objectUrl,
              filename: message.filename,
              saveAs: true
            }, (downloadId) => {
              if (chrome.runtime.lastError) {
                statusDiv.textContent = `Error starting JS file download: ${chrome.runtime.lastError.message}`;
                console.error("Error starting JS file download:", chrome.runtime.lastError.message);
                URL.revokeObjectURL(objectUrl);
              } else if (downloadId === undefined) {
                statusDiv.textContent = 'JS file download did not start. Check browser settings or console.';
                console.warn('JS file download did not start (downloadId undefined). Filename:', message.filename);
                URL.revokeObjectURL(objectUrl);
              } else {
                statusDiv.textContent = `JS file download started: ${message.filename}.`;
                // console.log(`JS file download started. ID: ${downloadId}, Filename: ${message.filename}`); // Can be verbose
                URL.revokeObjectURL(objectUrl); // Revoke here as download has started
              }
            });
          } catch (e) {
            statusDiv.textContent = `Error creating JS file for download: ${e.message}`;
            console.error("Error creating JS file blob/URL:", e);
          }
        } else {
          statusDiv.textContent = "No JavaScript content found or filename missing.";
          console.warn("No content or filename in downloadJsFile message:", message);
        }
        break;

      case "downloadTableData":
        if (message.content && message.filename) {
          statusDiv.textContent = `Tables extracted (${message.filename}). Preparing download...`;
          try {
            const blob = new Blob([message.content], { type: 'text/csv;charset=utf-8' });
            const objectUrl = URL.createObjectURL(blob);

            chrome.downloads.download({
              url: objectUrl,
              filename: message.filename,
              saveAs: true
            }, (downloadId) => {
              if (chrome.runtime.lastError) {
                statusDiv.textContent = `Error starting table data download: ${chrome.runtime.lastError.message}`;
                console.error("Error starting table data download:", chrome.runtime.lastError.message);
                URL.revokeObjectURL(objectUrl);
              } else if (downloadId === undefined) {
                statusDiv.textContent = 'Table data download did not start. Check browser settings or console.';
                console.warn('Table data download did not start (downloadId undefined). Filename:', message.filename);
                URL.revokeObjectURL(objectUrl);
              } else {
                statusDiv.textContent = `Table data download started: ${message.filename}.`;
                // console.log(`Table data download started. ID: ${downloadId}, Filename: ${message.filename}`); // Can be verbose
                URL.revokeObjectURL(objectUrl); // Revoke here as download has started
              }
            });
          } catch (e) {
            statusDiv.textContent = `Error creating table data file for download: ${e.message}`;
            console.error("Error creating table data file blob/URL:", e);
          }
        } else {
          statusDiv.textContent = "No table data found or filename missing.";
          console.warn("No content or filename in downloadTableData message:", message);
        }
        break;
      
      default:
        console.warn("Received unknown message action:", message.action, message);
        break;
    }
  });
});
