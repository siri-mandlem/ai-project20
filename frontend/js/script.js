const state = { products: [], cart: null, category: "", query: "" };
const $ = (selector) => document.querySelector(selector);
const money = (value) => `$${Number(value || 0).toFixed(2)}`;

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Something went wrong.");
  return data;
}

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => element.classList.remove("show"), 2500);
}

function navigate(path) {
  history.pushState({}, "", path);
  renderRoute();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function productCard(product) {
  return `<article class="product-card"><a href="/product-detail?id=${product.id}" data-route="/product-detail?id=${product.id}"><div class="product-category">${product.category}</div><img src="${product.image_url}" alt="${product.name}" loading="lazy"></a><div class="product-card-body"><h3>${product.name}</h3><p>${product.description}</p><div class="product-meta"><span>${money(product.price)}</span><button type="button" data-add="${product.id}">Add to bag +</button></div></div></article>`;
}

async function loadProducts() {
  const params = new URLSearchParams();
  if (state.category) params.set("category", state.category);
  if (state.query) params.set("q", state.query);
  state.products = await api(`/products?${params}`);
  const grid = $("#products-grid");
  if (grid) grid.innerHTML = state.products.length ? state.products.map(productCard).join("") : `<div class="empty-state">No products matched your search.</div>`;
  const searchGrid = $("#search-results");
  if (searchGrid) searchGrid.innerHTML = state.products.length ? state.products.map(productCard).join("") : `<div class="empty-state">Try another search.</div>`;
}

async function loadFeatured() {
  const products = await api("/products?featured=true");
  const element = $("#featured-products");
  if (element) element.innerHTML = products.slice(0, 3).map(productCard).join("");
}

async function loadCategories() {
  const categories = await api("/categories");
  const element = $("#category-filters");
  if (!element) return;
  element.innerHTML = ["<button class='active' data-category=''>All products</button>", ...categories.map(category => `<button data-category="${category}">${category}</button>`)].join("");
}

async function refreshCart() {
  state.cart = await api("/cart");
  $("#cart-count").textContent = state.cart.count;
  if (location.pathname === "/cart") renderCart();
}

function renderCart() {
  const target = $("#cart-view");
  if (!target || !state.cart) return;
  if (!state.cart.items.length) {
    target.innerHTML = `<div class="empty-state"><h2>Your bag is waiting.</h2><p>Add something beautiful and useful to get started.</p><a class="button primary" href="/products" data-route="/products">Browse products →</a></div>`;
    return;
  }
  target.innerHTML = `<div class="cart-panel">${state.cart.items.map(item => `<div class="cart-item"><img src="${item.product.image_url}" alt="${item.product.name}"><div><h3>${item.product.name}</h3><p>${money(item.product.price)} each</p></div><div class="cart-item-actions"><button data-decrease="${item.product.id}">−</button><strong>${item.quantity}</strong><button data-increase="${item.product.id}">+</button><button data-remove="${item.product.id}">Remove</button></div></div>`).join("")}</div><aside class="cart-panel"><span class="eyebrow">Order summary</span><div class="summary-line"><span>Items</span><span>${state.cart.count}</span></div><div class="summary-line total"><span>Total</span><span>${money(state.cart.total)}</span></div><a class="button primary" href="/checkout" data-route="/checkout">Checkout <span>→</span></a></aside>`;
}

async function addToCart(productId) { await api("/cart", { method: "POST", body: JSON.stringify({ product_id: productId }) }); await refreshCart(); toast("Added to your bag."); }
async function changeCart(productId, quantity) { await api(`/cart/${productId}`, { method: "PATCH", body: JSON.stringify({ quantity }) }); await refreshCart(); }
async function removeCart(productId) { await api(`/cart/${productId}`, { method: "DELETE" }); await refreshCart(); toast("Removed from your bag."); }

async function renderProductDetail() {
  const id = new URLSearchParams(location.search).get("id");
  const product = await api(`/products/${id}`);
  $("#product-detail-view").innerHTML = `<div class="detail-layout"><img class="detail-image" src="${product.image_url}" alt="${product.name}"><div class="detail-copy"><span class="eyebrow">${product.category}</span><h1>${product.name}</h1><p>${product.description}</p><div class="price">${money(product.price)}</div><div class="quantity-control"><button data-detail-quantity="-1">−</button><strong id="detail-quantity">1</strong><button data-detail-quantity="1">+</button></div><button class="button primary" type="button" data-detail-add="${product.id}">Add to bag <span>+</span></button></div></div>`;
}

function renderCheckout() {
  const target = $("#checkout-view");
  if (!state.cart?.items.length) { target.innerHTML = `<div class="empty-state">Your bag is empty. <a href="/products" data-route="/products">Return to the collection →</a></div>`; return; }
  target.innerHTML = `<form class="checkout-panel" id="checkout-form"><div class="form-field"><label for="customer-name">Full name</label><input id="customer-name" name="customer_name" required placeholder="Alex Morgan"></div><div class="form-field"><label for="shipping-address">Shipping address</label><textarea id="shipping-address" name="shipping_address" required placeholder="Street, city, postal code"></textarea></div><button class="button primary" type="submit">Place order <span>→</span></button></form><aside class="cart-panel"><span class="eyebrow">Your order</span>${state.cart.items.map(item => `<div class="summary-line"><span>${item.product.name} × ${item.quantity}</span><span>${money(item.line_total)}</span></div>`).join("")}<div class="summary-line total"><span>Total</span><span>${money(state.cart.total)}</span></div></aside>`;
}

async function renderOrders() {
  const orders = await api("/orders");
  $("#orders-view").innerHTML = orders.length ? orders.map(order => `<article class="order-card"><div class="order-top"><div><strong>Order #${order.id}</strong><br><small>${new Date(order.created_at).toLocaleString()}</small></div><div><span class="order-status">${order.status}</span><br><strong>${money(order.total_price)}</strong></div></div><div class="order-items">${order.items.map(item => `<span>${item.quantity} × ${item.product_name} · ${money(item.unit_price)}</span>`).join("")}</div></article>`).join("") : `<div class="empty-state">No orders yet. Your future favorites will appear here.</div>`;
}

async function renderRoute() {
  const path = location.pathname;
  const viewName = path === "/" ? "home" : path.slice(1).split("/")[0] || "home";
  document.querySelectorAll(".view").forEach(view => { view.hidden = view.dataset.view !== viewName; });
  document.querySelectorAll("[data-route]").forEach(link => link.classList.toggle("active", link.getAttribute("data-route") === path));
  try {
    if (viewName === "home") await loadFeatured();
    if (viewName === "products") { state.query = ""; await loadCategories(); await loadProducts(); }
    if (viewName === "search") { state.query = new URLSearchParams(location.search).get("q") || ""; $("#global-search").value = state.query; await loadProducts(); }
    if (viewName === "product-detail") await renderProductDetail();
    if (viewName === "cart") { await refreshCart(); renderCart(); }
    if (viewName === "checkout") { await refreshCart(); renderCheckout(); }
    if (viewName === "order-history") await renderOrders();
  } catch (error) { toast(error.message); }
}

document.addEventListener("click", async event => {
  const route = event.target.closest("[data-route]");
  if (route) { event.preventDefault(); navigate(route.getAttribute("data-route")); return; }
  const add = event.target.closest("[data-add]");
  if (add) { try { await addToCart(Number(add.dataset.add)); } catch (error) { toast(error.message); } return; }
  const increase = event.target.closest("[data-increase]");
  const decrease = event.target.closest("[data-decrease]");
  if (increase || decrease) { const id = Number((increase || decrease).dataset[increase ? "increase" : "decrease"]); const item = state.cart.items.find(row => row.product.id === id); await changeCart(id, item.quantity + (increase ? 1 : -1)); return; }
  const remove = event.target.closest("[data-remove]");
  if (remove) { await removeCart(Number(remove.dataset.remove)); return; }
  const detailAdd = event.target.closest("[data-detail-add]");
  if (detailAdd) { const quantity = Number($("#detail-quantity").textContent); await api("/cart", { method: "POST", body: JSON.stringify({ product_id: Number(detailAdd.dataset.detailAdd), quantity }) }); await refreshCart(); toast("Added to your bag."); return; }
  const detailQuantity = event.target.closest("[data-detail-quantity]");
  if (detailQuantity) { const current = Number($("#detail-quantity").textContent); $("#detail-quantity").textContent = Math.max(1, current + Number(detailQuantity.dataset.detailQuantity)); }
});

document.addEventListener("click", event => {
  const category = event.target.closest("[data-category]");
  if (!category) return;
  state.category = category.dataset.category;
  document.querySelectorAll("[data-category]").forEach(button => button.classList.toggle("active", button === category));
  loadProducts().catch(error => toast(error.message));
});

document.addEventListener("input", event => {
  if (event.target.id === "shop-search") { state.query = event.target.value; loadProducts().catch(error => toast(error.message)); }
  if (event.target.id === "global-search") { const value = event.target.value; const url = value ? `/search?q=${encodeURIComponent(value)}` : "/search"; history.replaceState({}, "", url); state.query = value; loadProducts().catch(error => toast(error.message)); }
});

document.addEventListener("submit", async event => {
  if (event.target.id !== "checkout-form") return;
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.target));
  try { await api("/orders", { method: "POST", body: JSON.stringify(payload) }); await refreshCart(); toast("Order placed. Thank you."); setTimeout(() => navigate("/order-history"), 700); } catch (error) { toast(error.message); }
});

window.addEventListener("popstate", renderRoute);
loadCategories().catch(() => {});
refreshCart().catch(() => {});
renderRoute();
