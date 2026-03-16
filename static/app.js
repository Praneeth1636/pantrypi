document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  if (target.matches("[data-add-ingredient]")) {
    event.preventDefault();
    const root = target.closest("[data-ingredients-root]");
    if (!root) return;

    const row = document.createElement("div");
    row.className = "pp-ingredient-row";
    row.innerHTML = `
      <input name="ingredient_quantity" type="number" step="0.01" placeholder="Qty">
      <input name="ingredient_unit" placeholder="Unit">
      <input name="ingredient_name" placeholder="Ingredient" style="flex: 1;">
      <input name="ingredient_category" placeholder="Category">
    `;
    root.insertBefore(row, target);
  }
});

