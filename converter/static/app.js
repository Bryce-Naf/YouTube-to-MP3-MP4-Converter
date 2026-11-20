document.documentElement.classList.add("js-ready");

document.querySelector("#url-form").addEventListener("submit", (event) => {
  event.preventDefault();
  document.querySelector("#submit-status").textContent =
    "URL submission is not available yet.";
});
