/*
  PUT ME ON — admin.js
  --------------------
  Small quality-of-life touch for the admin dashboard: when you pick a new
  photo for a product, its filename is echoed under the file input so you
  can confirm you selected the right file before saving.
*/

document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener("change", () => {
    const existingNote = input.parentElement.querySelector(".file-chosen-note");
    if (existingNote) existingNote.remove();

    if (input.files && input.files.length > 0) {
      const note = document.createElement("p");
      note.className = "file-chosen-note";
      note.style.fontSize = "12px";
      note.style.color = "#9a9a9a";
      note.style.margin = "4px 0 0";
      note.textContent = `Selected: ${input.files[0].name}`;
      input.insertAdjacentElement("afterend", note);
    }
  });
});
