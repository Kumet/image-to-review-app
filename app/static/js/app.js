document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("images");
  const count = document.getElementById("selected-count");
  const list = document.getElementById("selected-files");

  if (!(input instanceof HTMLInputElement) || !count || !list) {
    return;
  }

  const renderSelectedFiles = () => {
    const files = Array.from(input.files ?? []);
    count.textContent = `${files.length} 件選択`;
    list.innerHTML = "";

    for (const file of files) {
      const item = document.createElement("li");
      item.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;
      list.appendChild(item);
    }
  };

  input.addEventListener("change", renderSelectedFiles);
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
