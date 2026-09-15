/*
  PUT ME ON — cart.js
  -------------------
  Handles the shopping bag entirely in the browser (no backend cart/orders
  table — this site is designed around WhatsApp checkout, not online
  payment). The cart is stored in localStorage so it survives a page reload.

  WHATSAPP_NUMBER and BRAND_NAME are set as global variables in index.html
  (from the Flask template), just above where this file is loaded.
*/

const CART_STORAGE_KEY = "putmeon_cart";

function loadCart() {
  const raw = localStorage.getItem(CART_STORAGE_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw);
  } catch (e) {
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
}

let cart = loadCart();

// ---------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------

const cartToggle = document.getElementById("cartToggle");
const cartClose = document.getElementById("cartClose");
const cartOverlay = document.getElementById("cartOverlay");
const cartDrawer = document.getElementById("cartDrawer");
const cartItemsEl = document.getElementById("cartItems");
const cartEmptyMsg = document.getElementById("cartEmptyMsg");
const cartCountEl = document.getElementById("cartCount");
const cartTotalEl = document.getElementById("cartTotal");
const checkoutBtn = document.getElementById("checkoutBtn");

// ---------------------------------------------------------------------
// Drawer open / close
// ---------------------------------------------------------------------

function openCart() {
  cartDrawer.classList.add("open");
  cartOverlay.classList.add("open");
}

function closeCart() {
  cartDrawer.classList.remove("open");
  cartOverlay.classList.remove("open");
}

if (cartToggle) cartToggle.addEventListener("click", openCart);
if (cartClose) cartClose.addEventListener("click", closeCart);
if (cartOverlay) cartOverlay.addEventListener("click", closeCart);

// ---------------------------------------------------------------------
// Cart mutations
// ---------------------------------------------------------------------

function addToCart(product) {
  const existing = cart.find((item) => item.id === product.id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ ...product, qty: 1 });
  }
  saveCart(cart);
  renderCart();
  openCart();
}

function changeQty(id, delta) {
  const item = cart.find((i) => i.id === id);
  if (!item) return;
  item.qty += delta;
  if (item.qty <= 0) {
    cart = cart.filter((i) => i.id !== id);
  }
  saveCart(cart);
  renderCart();
}

function removeItem(id) {
  cart = cart.filter((i) => i.id !== id);
  saveCart(cart);
  renderCart();
}

// ---------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------

function renderCart() {
  const totalItems = cart.reduce((sum, item) => sum + item.qty, 0);
  cartCountEl.textContent = totalItems;

  cartItemsEl.innerHTML = "";

  if (cart.length === 0) {
    cartItemsEl.appendChild(cartEmptyMsg);
    checkoutBtn.disabled = true;
  } else {
    checkoutBtn.disabled = false;
    cart.forEach((item) => {
      const row = document.createElement("div");
      row.className = "cart-item";
      row.innerHTML = `
        <div class="cart-item-info">
          <p class="cart-item-name">${escapeHtml(item.name)}</p>
          <p class="cart-item-price">GHS ${item.price.toFixed(2)} each</p>
          <div class="cart-item-qty">
            <button class="qty-btn" data-action="dec" data-id="${item.id}">-</button>
            <span>${item.qty}</span>
            <button class="qty-btn" data-action="inc" data-id="${item.id}">+</button>
          </div>
          <button class="cart-item-remove" data-action="remove" data-id="${item.id}">Remove</button>
        </div>
      `;
      cartItemsEl.appendChild(row);
    });
  }

  const total = cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  cartTotalEl.textContent = `GHS ${total.toFixed(2)}`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// Delegate qty/remove button clicks (buttons are re-created on every render)
cartItemsEl.addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const id = Number(btn.dataset.id);
  const action = btn.dataset.action;
  if (action === "inc") changeQty(id, 1);
  if (action === "dec") changeQty(id, -1);
  if (action === "remove") removeItem(id);
});

// ---------------------------------------------------------------------
// Add-to-cart buttons on product cards
// ---------------------------------------------------------------------

document.querySelectorAll(".product-card").forEach((card) => {
  const btn = card.querySelector(".add-to-cart");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const product = {
      id: Number(card.dataset.id),
      name: card.dataset.name,
      price: parseFloat(card.dataset.price),
    };
    addToCart(product);
  });
});

// ---------------------------------------------------------------------
// WhatsApp checkout
// ---------------------------------------------------------------------

function buildWhatsAppMessage() {
  const lines = [`Hi ${BRAND_NAME}! I'd like to order:`, ""];
  cart.forEach((item) => {
    lines.push(`- ${item.name} x${item.qty} (GHS ${(item.price * item.qty).toFixed(2)})`);
  });
  const total = cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  lines.push("");
  lines.push(`Total: GHS ${total.toFixed(2)}`);
  lines.push("");
  lines.push("Please confirm availability and delivery details. Thank you!");
  return lines.join("\n");
}

if (checkoutBtn) {
  checkoutBtn.addEventListener("click", () => {
    if (cart.length === 0) return;
    const message = buildWhatsAppMessage();
    const url = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
    window.open(url, "_blank");
  });
}

// ---------------------------------------------------------------------
// Initial render
// ---------------------------------------------------------------------

renderCart();
