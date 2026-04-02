document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("images");
  const count = document.getElementById("selected-count");
  const list = document.getElementById("selected-files");
  const thumbnails = document.getElementById("thumbnail-list");
  const dropZone = document.getElementById("drop-zone");

  if (
    !(input instanceof HTMLInputElement) ||
    !count ||
    !list ||
    !thumbnails ||
    !(dropZone instanceof HTMLElement)
  ) {
    return;
  }

  let selectedFiles = [];
  let objectUrls = [];

  const revokeObjectUrls = () => {
    for (const objectUrl of objectUrls) {
      URL.revokeObjectURL(objectUrl);
    }
    objectUrls = [];
  };

  const syncInputFiles = () => {
    const dataTransfer = new DataTransfer();
    for (const file of selectedFiles) {
      dataTransfer.items.add(file);
    }
    input.files = dataTransfer.files;
  };

  const fileKey = (file) => `${file.name}:${file.size}:${file.lastModified}`;

  const renderSelectedFiles = () => {
    count.textContent = `${selectedFiles.length} 枚選択`;
    list.innerHTML = "";
    thumbnails.innerHTML = "";
    revokeObjectUrls();

    for (const [index, file] of selectedFiles.entries()) {
      const item = document.createElement("li");
      item.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;
      list.appendChild(item);

      const objectUrl = URL.createObjectURL(file);
      objectUrls.push(objectUrl);

      const thumbnailCard = document.createElement("article");
      thumbnailCard.className = "thumbnail-card";

      const image = document.createElement("img");
      image.className = "thumbnail-card__image";
      image.src = objectUrl;
      image.alt = file.name;

      const body = document.createElement("div");
      body.className = "thumbnail-card__body";

      const filename = document.createElement("p");
      filename.className = "thumbnail-card__name";
      filename.textContent = file.name;

      const meta = document.createElement("p");
      meta.className = "thumbnail-card__meta";
      meta.textContent = `${Math.round(file.size / 1024)} KB`;

      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.className = "thumbnail-card__remove";
      removeButton.textContent = "削除";
      removeButton.addEventListener("click", () => {
        selectedFiles = selectedFiles.filter((_, selectedIndex) => selectedIndex !== index);
        syncInputFiles();
        renderSelectedFiles();
      });

      body.append(filename, meta, removeButton);
      thumbnailCard.append(image, body);
      thumbnails.appendChild(thumbnailCard);
    }
  };

  const addFiles = (files) => {
    const nextFiles = Array.from(files).filter((file) => file.type.startsWith("image/"));
    const seen = new Set(selectedFiles.map(fileKey));

    for (const file of nextFiles) {
      const key = fileKey(file);
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      selectedFiles.push(file);
    }

    syncInputFiles();
    renderSelectedFiles();
  };

  input.addEventListener("change", () => {
    selectedFiles = [];
    addFiles(input.files ?? []);
  });

  dropZone.addEventListener("click", () => {
    input.click();
  });

  dropZone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      input.click();
    }
  });

  const setDropZoneActive = (isActive) => {
    dropZone.classList.toggle("is-dragover", isActive);
  };

  dropZone.addEventListener("dragenter", (event) => {
    event.preventDefault();
    setDropZoneActive(true);
  });

  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    setDropZoneActive(true);
  });

  dropZone.addEventListener("dragleave", (event) => {
    if (event.target === dropZone) {
      setDropZoneActive(false);
    }
  });

  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    setDropZoneActive(false);
    if (!event.dataTransfer) {
      return;
    }
    addFiles(event.dataTransfer.files);
  });

  renderSelectedFiles();
});

document.body.addEventListener("htmx:beforeRequest", (event) => {
  if (!(event.target instanceof HTMLFormElement)) {
    return;
  }
  if (!event.target.classList.contains("upload-form")) {
    return;
  }

  const errorArea = document.getElementById("error-area");
  if (errorArea) {
    errorArea.textContent = "現在エラーはありません。";
  }
});
