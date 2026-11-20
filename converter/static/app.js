document.documentElement.classList.add("js-ready");

const form = document.querySelector("#url-form");
const input = document.querySelector("#media-url");
const status = document.querySelector("#submit-status");
const panel = document.querySelector("#youtube-panel");
const preview = document.querySelector("#video-preview");
const player = document.querySelector("#youtube-player");

function getYouTubeVideoId(value) {
  let url;

  try {
    url = new URL(value);
  } catch {
    return null;
  }

  if (url.protocol !== "https:" && url.protocol !== "http:") {
    return null;
  }

  const host = url.hostname.toLowerCase();
  let videoId = null;

  if (host === "youtu.be") {
    videoId = url.pathname.split("/").filter(Boolean)[0];
  } else if (
    host === "youtube.com" ||
    host === "www.youtube.com" ||
    host === "m.youtube.com"
  ) {
    const segments = url.pathname.split("/").filter(Boolean);

    if (url.pathname === "/watch") {
      videoId = url.searchParams.get("v");
    } else if (segments.length === 2 && ["embed", "shorts"].includes(segments[0])) {
      videoId = segments[1];
    }
  }

  return videoId && /^[A-Za-z0-9_-]{11}$/.test(videoId) ? videoId : null;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const videoId = getYouTubeVideoId(input.value.trim());
  if (!videoId) {
    player.src = "about:blank";
    preview.hidden = true;
    panel.classList.remove("has-preview");
    status.textContent = "Enter a valid YouTube video URL.";
    return;
  }

  player.src = `https://www.youtube-nocookie.com/embed/${videoId}`;
  preview.hidden = false;
  panel.classList.add("has-preview");
  status.textContent = "";
});

const uploadForm = document.querySelector("#upload-form");
const uploadStatus = document.querySelector("#upload-status");
const convertButton = document.querySelector("#convert-button");
const downloadLink = document.querySelector("#download-link");

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  uploadStatus.textContent = "Uploading and converting...";
  downloadLink.hidden = true;
  convertButton.disabled = true;

  try {
    const response = await fetch(uploadForm.action, {
      method: "POST",
      body: new FormData(uploadForm),
    });
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Unable to convert this file.");
    }

    downloadLink.href = result.download_url;
    downloadLink.download = result.filename;
    downloadLink.hidden = false;
    uploadStatus.textContent = "Conversion complete.";
  } catch (error) {
    uploadStatus.textContent =
      error instanceof Error ? error.message : "Unable to convert this file.";
  } finally {
    convertButton.disabled = false;
  }
});
