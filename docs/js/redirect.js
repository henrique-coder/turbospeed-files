class TurboSpeedFiles {
  constructor() {
    this.availableFiles = [];
    this.loadAvailableFiles();
  }

  async loadAvailableFiles() {
    try {
      const response = await fetch("../file-sizes.yaml");
      const yamlText = await response.text();
      this.parseYamlFiles(yamlText);
      this.displayFiles();
    } catch (error) {
      console.error("Error loading files:", error);
      this.showError();
    }
  }

  parseYamlFiles(yamlText) {
    const lines = yamlText.split("\n");
    let inFilesSection = false;

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed === "files:") {
        inFilesSection = true;
        continue;
      }
      if (inFilesSection && trimmed.startsWith("- ")) {
        const size = trimmed.replace(/^- ["']?|["']?$/g, "");
        this.availableFiles.push(size.toLowerCase());
      } else if (inFilesSection && !trimmed.startsWith("-") && trimmed) {
        break;
      }
    }

    this.availableFiles.sort((a, b) => this.parseSize(a) - this.parseSize(b));
  }

  parseSize(sizeStr) {
    const match = sizeStr.match(/^(\d+(?:\.\d+)?)(kb|mb|gb)$/);
    if (!match) return 0;

    const [, value, unit] = match;
    const numValue = parseFloat(value);

    switch (unit) {
      case "kb":
        return numValue * 1024;
      case "mb":
        return numValue * 1024 * 1024;
      case "gb":
        return numValue * 1024 * 1024 * 1024;
      default:
        return 0;
    }
  }

  formatSize(sizeStr) {
    const sizeBytes = this.parseSize(sizeStr);
    if (sizeBytes >= 1024 * 1024 * 1024) {
      return `${(sizeBytes / (1024 * 1024 * 1024)).toFixed(1).replace(".0", "")} GB`;
    } else if (sizeBytes >= 1024 * 1024) {
      return `${(sizeBytes / (1024 * 1024)).toFixed(0)} MB`;
    } else {
      return `${(sizeBytes / 1024).toFixed(0)} KB`;
    }
  }

  displayFiles() {
    const loadingEl = document.getElementById("loading");
    const filesListEl = document.getElementById("files-list");

    if (loadingEl) loadingEl.style.display = "none";

    if (this.availableFiles.length === 0) {
      filesListEl.innerHTML = "<p>No files available at this time.</p>";
      return;
    }

    const filesHtml = this.availableFiles
      .map((size) => {
        const shortUrl = `${window.location.origin}${window.location.pathname}${size}`;
        const formattedSize = this.formatSize(size);

        return `
                <div class="file-card">
                    <div class="file-size">${formattedSize}</div>
                    <div class="file-url">
                        <input type="text" value="${shortUrl}" readonly onclick="this.select()">
                        <button onclick="copyToClipboard('${shortUrl}')" title="Copy URL">📋</button>
                        <a href="${shortUrl}" class="download-btn" title="Download file">⬇️</a>
                    </div>
                </div>
            `;
      })
      .join("");

    filesListEl.innerHTML = filesHtml;
  }

  showError() {
    const loadingEl = document.getElementById("loading");
    const filesListEl = document.getElementById("files-list");

    if (loadingEl) loadingEl.style.display = "none";
    filesListEl.innerHTML = `
            <div class="error-message">
                <p>Error loading available files. Please try refreshing the page.</p>
            </div>
        `;
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = "✅";
    setTimeout(() => {
      button.textContent = originalText;
    }, 1000);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  new TurboSpeedFiles();
});
