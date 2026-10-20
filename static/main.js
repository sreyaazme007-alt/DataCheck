// DataCheck Client-Side Interactions
document.addEventListener("DOMContentLoaded", function () {
  // --- File Upload & Dropzone Handling ---
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const fileInfo = document.getElementById("fileInfo");
  const fileNameDisplay = document.getElementById("fileNameDisplay");
  const uploadForm = document.getElementById("uploadForm");
  const submitBtn = document.getElementById("submitBtn");

  if (dropzone && fileInput) {
    // Click on dropzone opens file dialog
    dropzone.addEventListener("click", () => fileInput.click());

    // Highlight dropzone on drag over
    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragover");
      });
    });

    // Handle dropped files
    dropzone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        fileInput.files = files;
        updateFileInfo(files[0]);
      }
    });

    // Handle file selection from browse dialog
    fileInput.addEventListener("change", function () {
      if (this.files.length > 0) {
        updateFileInfo(this.files[0]);
      }
    });
  }

  function updateFileInfo(file) {
    if (!file) return;

    // Check extension
    if (!file.name.toLowerCase().endsWith(".csv")) {
      alert("Please select a valid CSV file (.csv)");
      fileInput.value = "";
      if (fileInfo) fileInfo.style.display = "none";
      return;
    }

    // Check size limit (16MB)
    const maxBytes = 16 * 1024 * 1024;
    if (file.size > maxBytes) {
      alert("File is too large. Maximum supported size is 16MB.");
      fileInput.value = "";
      if (fileInfo) fileInfo.style.display = "none";
      return;
    }

    const sizeKb = (file.size / 1024).toFixed(1);
    if (fileNameDisplay) {
      fileNameDisplay.textContent = `${file.name} (${sizeKb} KB)`;
    }
    if (fileInfo) {
      fileInfo.style.display = "block";
    }
  }

  if (uploadForm && submitBtn) {
    uploadForm.addEventListener("submit", function () {
      submitBtn.innerText = "Analyzing Dataset...";
    });
  }

  // --- Live Table Filtering for Error Report ---
  const searchInput = document.getElementById("tableSearch");
  const typeFilter = document.getElementById("errorTypeFilter");
  const errorRows = document.querySelectorAll("#errorTable tbody tr");
  const visibleCountSpan = document.getElementById("visibleErrorCount");

  if (searchInput || typeFilter) {
    function filterTable() {
      const query = (searchInput ? searchInput.value.toLowerCase().trim() : "");
      const selectedType = (typeFilter ? typeFilter.value.toLowerCase().trim() : "");

      let visible = 0;
      errorRows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        const rowType = (row.getAttribute("data-error-type") || "").toLowerCase();

        const matchesQuery = query === "" || text.includes(query);
        const matchesType = selectedType === "" || selectedType === "all" || rowType === selectedType;

        if (matchesQuery && matchesType) {
          row.style.display = "";
          visible++;
        } else {
          row.style.display = "none";
        }
      });

      if (visibleCountSpan) {
        visibleCountSpan.textContent = visible;
      }
    }

    if (searchInput) {
      searchInput.addEventListener("input", filterTable);
    }
    if (typeFilter) {
      typeFilter.addEventListener("change", filterTable);
    }
  }
});
