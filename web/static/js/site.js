for (const button of document.querySelectorAll(".reveal")) {
  button.addEventListener("click", () => {
    const input = button.previousElementSibling;
    const shown = input.type === "text";
    input.type = shown ? "password" : "text";
    button.textContent = shown ? "Show" : "Hide";
  });
}
