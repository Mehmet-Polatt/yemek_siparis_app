const API_URL = ""; // Relative path as it's served by the same server

let state = {
    token: localStorage.getItem("token") || null,
    user: JSON.parse(localStorage.getItem("user")) || null,
    cart: null
};

// --- API Helpers ---
async function api_call(endpoint, method = "GET", body = null) {
    const headers = {
        "Content-Type": "application/json"
    };
    if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
    }

    const config = {
        method,
        headers,
    };
    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, config);
        
        if (response.status === 401) {
            logout();
            return null;
        }

        // Response ok değilse hata mesajını almaya çalış
        if (!response.ok) {
            let errorMessage = "Bir hata oluştu";
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // JSON değilse ham metni dene
                const textError = await response.text();
                errorMessage = textError || errorMessage;
            }
            throw new Error(errorMessage);
        }

        if (method === "DELETE" || response.status === 204) return true;
        
        // Boş response kontrolü
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            return await response.json();
        }
        return true;
    } catch (err) {
        console.error("API Error:", err);
        alert(err.message);
        return null;
    }
}

// --- Auth ---
async function login(email, password) {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            body: formData
        });
        if (!response.ok) throw new Error("Giriş başarısız");
        const data = await response.json();
        state.token = data.access_token;
        localStorage.setItem("token", state.token);
        
        // Kullanıcı bilgilerini al
        const user = await api_call("/auth/me");
        state.user = user;
        localStorage.setItem("user", JSON.stringify(user));
        
        updateUI();
        refreshCart(); // Giriş yapınca sepeti çek
        showSection("restaurants-section");
    } catch (err) {
        alert(err.message);
    }
}

async function register(first_name, last_name, email, password, role) {
    const res = await api_call("/auth/register", "POST", {
        first_name,
        last_name,
        email,
        password,
        role
    });

    if (res) {
        alert("Kayıt başarılı! Şimdi giriş yapabilirsiniz.");
        showSection("login-section");
    }
}

function logout() {
    state.token = null;
    state.user = null;
    state.cart = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    updateUI();
    showSection("login-section");
}

// --- Navigation ---
function showSection(sectionId) {
    document.querySelectorAll("section").forEach(s => s.classList.remove("active"));
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.add("active");
        if (sectionId === "restaurants-section") loadRestaurants();
        if (sectionId === "orders-section") loadOrders();
        if (sectionId === "cart-section") loadCart();
        if (sectionId === "management-section") loadManagement();
    }
}

// --- Rendering ---
async function loadRestaurants(search = null) {
    let url = "/restaurants/";
    if (search) {
        url += `?search=${encodeURIComponent(search)}`;
    }
    const restaurants = await api_call(url);
    const container = document.getElementById("restaurants-grid");
    if (!container) return;
    
    if (restaurants.length === 0) {
        container.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:2rem; color:#718096">Aramanızla eşleşen restoran bulunamadı.</div>`;
        return;
    }

    container.innerHTML = restaurants.map(r => `
        <div class="card" onclick="loadMenu(${r.id}, '${r.name}')">
            <img src="${r.logo_url || ''}" class="card-img" onerror="this.src='https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80'">
            <div class="card-content">
                <div class="card-title">${r.name}</div>
                <div class="card-desc">${r.description || ''}</div>
                <div class="card-footer">
                    <span class="rating-badge">⭐ ${r.rating.toFixed(1)}</span>
                    <button class="btn btn-secondary">Menüye Git</button>
                </div>
            </div>
        </div>
    `).join("");
}

async function loadMenu(restaurantId, restaurantName, search = null) {
    document.getElementById("menu-title").innerText = restaurantName;
    showSection("menu-section");
    
    let url = `/products/restaurant/${restaurantId}`;
    if (search) {
        url += `?search=${encodeURIComponent(search)}`;
    }
    const products = await api_call(url);
    const container = document.getElementById("menu-grid");
    if (!container) return;
    
    if (products.length === 0) {
        container.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:2rem; color:#718096">Bu restoranda aramanızla eşleşen ürün bulunamadı.</div>`;
    } else {
        container.innerHTML = products.map(p => `
            <div class="card">
                <img src="${p.image_url || ''}" class="card-img" onerror="this.src='https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80'">
                <div class="card-content">
                    <div style="display:flex; justify-content:space-between; align-items:start">
                        <div class="card-title">${p.name}</div>
                        <button class="btn" style="padding:4px 8px; font-size:0.8rem; background:#EDF2F7" onclick="event.stopPropagation(); showReviewModal(${restaurantId}, ${p.id}, '${p.name}')">💬 Yorum Yap</button>
                    </div>
                    <div class="card-desc">${p.description}</div>
                    <div class="card-footer">
                        <span class="price">${p.price} TL</span>
                        <button class="btn btn-primary" onclick="addToCart(${p.id})">Sepete Ekle</button>
                    </div>
                </div>
            </div>
        `).join("");
    }

    // Yorumları yükle
    loadReviews(restaurantId);
    
    // Modal için restoran ID'sini sakla
    document.querySelector("#review-form input[name='restaurant_id']").value = restaurantId;
}

async function loadReviews(restaurantId) {
    const reviews = await api_call(`/reviews/restaurant/${restaurantId}`);
    const container = document.getElementById("reviews-list");
    if (!container) return;

    if (!reviews || reviews.length === 0) {
        container.innerHTML = `<p style="text-align:center; color:#718096; padding:1rem; border:1px dashed #E2E8F0; border-radius:12px;">Henüz yorum yapılmamış. İlk yorumu siz yapın!</p>`;
        return;
    }

    // Backend ReviewResponse'da product bilgisi yoksa product_id'den anlayacağız
    container.innerHTML = reviews.map(r => `
        <div class="review-card">
            <div class="review-header">
                <div>
                    <span class="review-user">Müşteri #${r.user_id}</span>
                    ${r.product_id ? `<span style="font-size:0.85rem; color:#718096; margin-left:10px"> (Ürün için)</span>` : ''}
                </div>
                <span class="review-rating">${'⭐'.repeat(r.rating)}</span>
            </div>
            <div class="review-comment">${r.comment}</div>
            <div class="review-date">${new Date(r.created_at).toLocaleDateString()}</div>
        </div>
    `).join("");
}

function showReviewModal(restaurantId = null, productId = null, targetName = "") {
    if (!state.token) {
        alert("Yorum yapabilmek için giriş yapmalısınız.");
        showSection("login-section");
        return;
    }
    
    const form = document.getElementById("review-form");
    form.reset();
    
    // Eğer parametre gelmediyse mevcut sayfadakileri kullan
    if (!restaurantId && !productId) {
        restaurantId = document.querySelector("#menu-section.active") ? form.restaurant_id.value : null;
    }

    form.restaurant_id.value = restaurantId || "";
    form.product_id.value = productId || "";
    
    document.querySelector("#review-modal h2").innerText = targetName ? `${targetName} - Yorum Yap` : "Yorum Yap & Puan Ver";
    document.getElementById("review-modal").style.display = "flex";
}

async function submitReview() {
    const form = document.getElementById("review-form");
    const restaurantId = form.restaurant_id.value ? parseInt(form.restaurant_id.value) : null;
    const productId = form.product_id.value ? parseInt(form.product_id.value) : null;

    const data = {
        rating: parseInt(form.rating.value),
        comment: form.comment.value
    };

    if (restaurantId) data.restaurant_id = restaurantId;
    if (productId) data.product_id = productId;

    const res = await api_call("/reviews/", "POST", data);
    if (res) {
        closeModal("review-modal");
        form.reset();
        alert("Yorumunuz için teşekkürler!");
        if (restaurantId) loadReviews(restaurantId);
    }
}

// --- Search Logic ---
let searchTimeout = null;
function handleSearch(event) {
    if (event.key === "Enter") {
        performSearch();
    }
}

async function performSearch() {
    const query = document.getElementById("search-input").value.trim();
    
    // Eğer menu-section aktifse sadece o restoran içindeki ürünlerde ara
    const menuSection = document.getElementById("menu-section");
    if (menuSection.classList.contains("active")) {
        const restaurantId = document.querySelector("#review-form input[name='restaurant_id']").value;
        const restaurantName = document.getElementById("menu-title").innerText;
        loadMenu(restaurantId, restaurantName, query);
    } else {
        // Değilse restoranlarda ara ve restoran listesine dön
        showSection("restaurants-section");
        loadRestaurants(query);
    }
}

async function loadCart() {
    await refreshCart(); // Önce güncel sepeti çek
    const cart = state.cart;
    const container = document.getElementById("cart-items");
    const totalEl = document.getElementById("cart-total");
    
    if (!container) return;
    if (!cart || cart.items.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:2rem;">
                <p style="color:#718096; margin-bottom:1rem;">Sepetiniz henüz boş.</p>
                <button class="btn btn-primary" onclick="showSection('restaurants-section')">Alışverişe Başla</button>
            </div>
        `;
        if (totalEl) totalEl.innerText = "0 TL";
        return;
    }

    let total = 0;
    container.innerHTML = cart.items.map(item => {
        const itemTotal = item.product.price * item.quantity;
        total += itemTotal;
        return `
            <div class="cart-item">
                <div class="cart-item-info">
                    <strong>${item.product.name}</strong>
                    <span style="font-size:0.9rem; color:#718096">${item.product.price} TL / adet</span>
                </div>
                <div style="display:flex; align-items:center; gap:20px">
                    <div class="quantity-controls">
                        <button class="qty-btn" onclick="removeFromCart(${item.id})">-</button>
                        <span style="font-weight:600; min-width:20px; text-align:center">${item.quantity}</span>
                        <button class="qty-btn" onclick="addToCart(${item.product_id})">+</button>
                    </div>
                    <div style="min-width:80px; text-align:right">
                        <span style="font-weight:700; color:var(--primary-color)">${itemTotal} TL</span>
                    </div>
                </div>
            </div>
        `;
    }).join("");
    if (totalEl) totalEl.innerText = `${total} TL`;
}

async function addToCart(productId) {
    if (!state.token) return showSection("login-section");
    const res = await api_call("/cart/add", "POST", { product_id: productId, quantity: 1 });
    if (res) {
        // Sepet sayfasındaysak listeyi yenile, değilse sadece sayacı ve state'i güncelle
        if (document.getElementById("cart-section").classList.contains("active")) {
            loadCart();
        } else {
            refreshCart();
            alert("Ürün sepete eklendi!");
        }
    }
}

async function removeFromCart(itemId) {
    const res = await api_call(`/cart/item/${itemId}`, "DELETE");
    if (res) {
        // Sepet sayfasındaysak listeyi yenile
        if (document.getElementById("cart-section").classList.contains("active")) {
            loadCart();
        } else {
            refreshCart();
        }
    }
}

async function checkout() {
    if (!state.cart || state.cart.items.length === 0) {
        alert("Sepetiniz boş!");
        return;
    }

    const cardNum = prompt("Ödeme işlemini tamamlamak için kart numaranızı girin (Test için herhangi bir numara girebilirsiniz):", "4444 4444 4444 4444");
    if (!cardNum) return;

    // Loading state simülasyonu
    const checkoutBtn = document.querySelector("#cart-section .btn-secondary");
    let originalText = "Siparişi Tamamla";
    if (checkoutBtn) {
        originalText = checkoutBtn.innerText;
        checkoutBtn.innerText = "İşleniyor...";
        checkoutBtn.disabled = true;
    }

    try {
        const res = await api_call("/orders/checkout", "POST", {
            card_number: cardNum,
            expiry_date: "12/25",
            cvv: "123"
        });

        if (res) {
            alert("Siparişiniz başarıyla alındı! Afiyet olsun.");
            await refreshCart(); // Sepeti API'den tazeleyerek temizle
            showSection("orders-section");
        }
    } catch (err) {
        console.error("Checkout error:", err);
        alert("Sipariş tamamlanırken bir hata oluştu: " + err.message);
    } finally {
        if (checkoutBtn) {
            checkoutBtn.innerText = originalText;
            checkoutBtn.disabled = false;
        }
    }
}

async function loadOrders() {
    const orders = await api_call("/orders/me");
    const container = document.getElementById("orders-list");
    if (!container) return;

    if (!orders || orders.length === 0) {
        container.innerHTML = `<p style="text-align:center; padding:2rem; color:#718096">Henüz bir siparişiniz bulunmuyor.</p>`;
        return;
    }

    container.innerHTML = orders.map(o => `
        <div class="card" style="margin-bottom:1.5rem; border-left: 4px solid var(--primary-color)">
            <div class="card-content">
                <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:1rem">
                    <div>
                        <strong style="font-size:1.1rem">Sipariş #${o.id}</strong>
                        <div style="font-size:0.85rem; color:#718096; margin-top:4px">${new Date(o.created_at).toLocaleString()}</div>
                    </div>
                    <span class="badge" style="background:${o.status === 'teslim edildi' ? 'var(--secondary-color)' : 'var(--primary-color)'}">${o.status}</span>
                </div>
                
                <div style="margin:1rem 0; padding:1rem 0; border-top:1px solid #EDF2F7; border-bottom:1px solid #EDF2F7">
                    ${o.items.map(i => `
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem">
                            <span>${i.quantity}x ${i.product ? i.product.name : 'Ürün #' + i.product_id}</span>
                            <span style="color:#718096">${i.price} TL</span>
                        </div>
                    `).join("")}
                </div>
                
                <div style="display:flex; justify-content:space-between; align-items:center">
                    <span style="color:#718096; font-size:0.9rem">${o.items.length} ürün</span>
                    <div style="font-size:1.2rem; font-weight:bold; color:var(--primary-color)">
                        <span style="font-size:0.9rem; font-weight:normal; color:var(--text-color)">Toplam:</span> ${o.total_price} TL
                    </div>
                </div>
            </div>
        </div>
    `).join("");
}

function updateUI() {
    const navLinks = document.getElementById("nav-links");
    if (!navLinks) return;
    const searchBar = document.getElementById("search-bar");
    if (state.token) {
        if (searchBar) searchBar.style.display = "flex";
        let links = `
            <a href="#" onclick="showSection('restaurants-section')">Restoranlar</a>
            <a href="#" onclick="showSection('orders-section')">Siparişlerim</a>
        `;

        if (state.user && (state.user.role === 'admin' || state.user.role === 'restaurant_owner')) {
            links += `<a href="#" onclick="showSection('management-section')">Yönetim Paneli</a>`;
        }

        links += `
            <a href="#" onclick="showSection('cart-section')">Sepetim <span id="cart-badge" class="badge">${calculateCartCount()}</span></a>
            <button onclick="logout()">Çıkış Yap</button>
        `;
        navLinks.innerHTML = links;
    } else {
        if (searchBar) searchBar.style.display = "none";
        navLinks.innerHTML = `
            <a href="#" onclick="showSection('login-section')">Giriş Yap</a>
            <a href="#" onclick="showSection('register-section')">Kayıt Ol</a>
        `;
    }
}

async function refreshCart() {
    if (!state.token) return;
    const cart = await api_call("/cart/");
    if (cart) {
        state.cart = cart;
        updateCartBadge(calculateCartCount());
    }
}

function calculateCartCount() {
    if (!state.cart || !state.cart.items) return 0;
    return state.cart.items.reduce((sum, item) => sum + item.quantity, 0);
}

function updateCartBadge(count) {
    const badge = document.getElementById("cart-badge");
    if (badge) {
        badge.innerText = count;
        badge.style.display = count > 0 ? "inline-block" : "none";
    }
}

// --- Management ---
async function loadManagement() {
    const isOwner = state.user && state.user.role === 'restaurant_owner';
    const endpoint = isOwner ? "/restaurants/my" : "/restaurants/";
    
    const restaurants = await api_call(endpoint);
    const container = document.getElementById("management-grid");
    if (!container) return;

    if (!restaurants || restaurants.length === 0) {
        container.innerHTML = "<p style='grid-column:1/-1; text-align:center; padding:2rem;'>Henüz bir restoranınız yok.</p>";
        return;
    }

    container.innerHTML = restaurants.map(r => `
        <div class="card">
            <img src="${r.logo_url || ''}" class="card-img" onerror="this.src='https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80'">
            <div class="card-content">
                <div class="card-title">${r.name}</div>
                <div class="card-desc">${r.address}</div>
                <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:1rem">
                    <button class="btn btn-secondary" onclick="showAddProductModal(${r.id})">+ Ürün Ekle</button>
                    <button class="btn" style="background:#EDF2F7" onclick="editRestaurant(${JSON.stringify(r).replace(/"/g, '&quot;')})">Düzenle</button>
                    <button class="btn" style="background:#FED7D7; color:red" onclick="deleteRestaurant(${r.id})">Sil</button>
                </div>
            </div>
        </div>
    `).join("");
}

function showAddRestaurantModal() {
    const form = document.getElementById("restaurant-form");
    form.reset();
    form.id.value = "";
    document.getElementById("modal-title").innerText = "Yeni Restoran Ekle";
    document.getElementById("restaurant-modal").style.display = "flex";
}

function closeModal(id) {
    document.getElementById(id).style.display = "none";
}

async function saveRestaurant() {
    const form = document.getElementById("restaurant-form");
    const data = {
        name: form.name.value,
        address: form.address.value,
        description: form.description.value,
        logo_url: form.logo_url.value
    };
    const id = form.id.value;

    let res;
    if (id) {
        res = await api_call(`/restaurants/${id}`, "PUT", data);
    } else {
        res = await api_call("/restaurants/", "POST", data);
    }

    if (res) {
        closeModal('restaurant-modal');
        loadManagement();
    }
}

function editRestaurant(restaurant) {
    const form = document.getElementById("restaurant-form");
    form.id.value = restaurant.id;
    form.name.value = restaurant.name;
    form.address.value = restaurant.address;
    form.description.value = restaurant.description || "";
    form.logo_url.value = restaurant.logo_url || "";
    document.getElementById("modal-title").innerText = "Restoranı Düzenle";
    document.getElementById("restaurant-modal").style.display = "flex";
}

async function deleteRestaurant(id) {
    if (!confirm("Bu restoranı silmek istediğinize emin misiniz?")) return;
    const res = await api_call(`/restaurants/${id}`, "DELETE");
    if (res) loadManagement();
}

function showAddProductModal(restaurantId) {
    const form = document.getElementById("product-form");
    form.reset();
    form.restaurant_id.value = restaurantId;
    document.getElementById("product-modal").style.display = "flex";
}

async function saveProduct() {
    const form = document.getElementById("product-form");
    const data = {
        name: form.name.value,
        price: parseFloat(form.price.value),
        description: form.description.value,
        stock: parseInt(form.stock.value),
        image_url: form.image_url.value,
        restaurant_id: parseInt(form.restaurant_id.value)
    };

    const res = await api_call("/products/", "POST", data);
    if (res) {
        closeModal('product-modal');
        alert("Ürün başarıyla eklendi!");
    }
}

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
    updateUI();
    if (state.token) {
        refreshCart(); // Başlangıçta sepeti çek
        showSection("restaurants-section");
    } else {
        showSection("login-section");
    }
});
