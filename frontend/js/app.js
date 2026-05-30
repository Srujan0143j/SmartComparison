const API_BASE = window.location.protocol === "file:" || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : window.location.origin;

// App state
let currentCategory = "";
let currentQuery = "";
let compareList = []; // Array of product names
let storeChartInstance = null;
let crossChartInstance = null;

// DOM Elements
const pageWrapper = document.getElementById("page-wrapper");
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const categoryChips = document.getElementById("category-chips");
const resultsGrid = document.getElementById("results-grid");
const resultsSec = document.getElementById("results-sec");
const resultsCountText = document.getElementById("results-count-text");
const loadingSpinner = document.getElementById("loading-spinner");
const loadingText = document.getElementById("loading-text");
const heroSec = document.getElementById("hero-sec");

// Drawer
const compareDrawer = document.getElementById("compare-drawer");
const drawerItemsList = document.getElementById("drawer-items-list");
const drawerCompareBtn = document.getElementById("drawer-compare-btn");

// Modals
const storeModal = document.getElementById("store-modal");
const closeStoreModal = document.getElementById("close-store-modal");
const crossModal = document.getElementById("cross-modal");
const closeCrossModal = document.getElementById("close-cross-modal");

// Database Seeding
const seedDbBtn = document.getElementById("seed-db-btn");
const logoBtn = document.getElementById("nav-logo");
const homeBtn = document.getElementById("nav-home");

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
    init3DBackground();
    // Perform initial empty search to display some default listings
    searchProducts();
});

logoBtn.addEventListener("click", resetToHome);
homeBtn.addEventListener("click", resetToHome);

function resetToHome(e) {
    e.preventDefault();
    searchInput.value = "";
    currentQuery = "";
    currentCategory = "";
    document.querySelectorAll(".category-chip").forEach(chip => {
        chip.classList.remove("active");
        if (chip.dataset.category === "") chip.classList.add("active");
    });
    searchProducts();
}

searchBtn.addEventListener("click", () => {
    currentQuery = searchInput.value.trim();
    searchProducts();
});

searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        currentQuery = searchInput.value.trim();
        searchProducts();
    }
});

// Category Chips click handler
categoryChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".category-chip");
    if (!chip) return;
    
    document.querySelectorAll(".category-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    
    currentCategory = chip.dataset.category;
    searchProducts();
});

// Seed DB handler
if (seedDbBtn) {
    seedDbBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        if (confirm("Are you sure you want to reset and re-seed the MongoDB database?")) {
            showLoading("Re-seeding database...");
            try {
                const response = await fetch(`${API_BASE}/api/seed`, { method: "POST" });
                const data = await response.json();
                alert(data.message || "Database seeded!");
                searchProducts();
            } catch (err) {
                console.error(err);
                alert("Seeding failed: " + err.message);
            } finally {
                hideLoading();
            }
        }
    });
}

// Drawer compare button click
drawerCompareBtn.addEventListener("click", () => {
    if (compareList.length < 2) {
        alert("Please select at least 2 models to compare.");
        return;
    }
    openCrossModal();
});

// Close modals
closeStoreModal.addEventListener("click", () => {
    storeModal.classList.remove("show");
    pageWrapper.classList.remove("modal-active");
});
closeCrossModal.addEventListener("click", () => {
    crossModal.classList.remove("show");
    pageWrapper.classList.remove("modal-active");
});

// Close modal on overlay click (click outside)
document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", (e) => {
        if (e.target === overlay) {
            overlay.classList.remove("show");
            pageWrapper.classList.remove("modal-active");
        }
    });
});

// Functions
function showLoading(text = "Searching...") {
    loadingText.textContent = text;
    loadingSpinner.style.display = "flex";
    resultsSec.style.display = "none";
}

function hideLoading() {
    loadingSpinner.style.display = "none";
    resultsSec.style.display = "block";
}

// Search
async function searchProducts() {
    showLoading("Fetching products and applying ML models...");
    
    let url = `${API_BASE}/api/search?`;
    if (currentQuery) url += `q=${encodeURIComponent(currentQuery)}&`;
    if (currentCategory) url += `category=${encodeURIComponent(currentCategory)}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        renderResults(data.results);
    } catch (err) {
        console.error("API error:", err);
        resultsGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem; background: var(--glass-bg); border-radius: var(--radius-md); border: 1px dashed var(--danger);">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 2.5rem; color: var(--danger); margin-bottom: 1rem;"></i>
                <h3>Backend API Unreachable</h3>
                <p style="color: var(--text-muted); margin-top: 0.5rem;">Please start the FastAPI backend server using <code>uvicorn main:app --reload</code> inside the backend folder.</p>
            </div>
        `;
        hideLoading();
    }
}

// Render Results Grid
function renderResults(products) {
    resultsGrid.innerHTML = "";
    
    if (!products || products.length === 0) {
        resultsGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem;">
                <i class="fa-regular fa-face-frown" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
                <h3>No products found</h3>
                <p style="color: var(--text-muted); margin-top: 0.5rem;">Try adjusting your query or category filters.</p>
            </div>
        `;
        resultsCountText.textContent = "0 Products Found";
        hideLoading();
        return;
    }
    
    resultsCountText.textContent = `${products.length} Models Found`;
    
    products.forEach((p, index) => {
        const card = document.createElement("div");
        card.className = "product-card";
        card.style.animationDelay = `${index * 50}ms`;
        
        // Badge class
        let badgeClass = "badge-rec";
        if (p.ml_label === "Best Value") badgeClass = "badge-best-value";
        else if (p.ml_label === "Budget Pick") badgeClass = "badge-budget";
        else if (p.ml_label === "Premium Choice") badgeClass = "badge-premium";
        
        const isAdded = compareList.includes(p.name);
        
        card.innerHTML = `
            <div class="card-glare"></div>
            <span class="card-badge ${badgeClass}">${p.ml_label}</span>
            <div class="card-img-wrapper">
                <img src="${p.image_url}" alt="${p.name}" onerror="this.src='https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=300&auto=format&fit=crop'">
            </div>
            <div class="card-content">
                <div class="card-category">${p.category}</div>
                <div class="card-title">${p.name}</div>
                <div class="rating-row">
                    <div class="stars">${renderStars(p.avg_rating)}</div>
                    <span class="reviews-cnt">(${p.total_reviews.toLocaleString()} reviews)</span>
                </div>
                <div class="price-row">
                    <div>
                        <div class="price-range-label">Price range</div>
                        <div class="price-range" style="font-size: 1.125rem;">₹${p.min_price.toLocaleString()} - ₹${p.max_price.toLocaleString()}</div>
                    </div>
                </div>
                
                <!-- Direct Website Comparison Table -->
                <div class="card-price-comparison" style="margin-bottom: 1.25rem; background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-sm); overflow: hidden;">
                    <div style="font-size: 0.75rem; font-weight: 700; padding: 0.4rem 0.6rem; background: rgba(255,255,255,0.03); border-bottom: 1px solid var(--glass-border); display: flex; justify-content: space-between;">
                        <span>Website Comparison</span>
                        <span style="color: var(--success); font-weight: 800;"><i class="fa-solid fa-arrow-down-wide-short"></i> Price</span>
                    </div>
                    <div style="max-height: 140px; overflow-y: auto;">
                        ${p.listings.map(l => `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0.6rem; border-bottom: 1px solid rgba(255,255,255,0.03); font-size: 0.8125rem;">
                                <span style="font-weight: 500; display: flex; align-items: center; gap: 0.25rem;">
                                    ${l.source} 
                                    ${l.source === p.best_deal_store ? '<span style="font-size: 0.65rem; padding: 0.05rem 0.2rem; background: var(--success-light); color: var(--success); border-radius: 3px; font-weight: 700;">Best</span>' : ''}
                                </span>
                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                    <strong style="color: var(--text-main);">₹${l.price.toLocaleString()}</strong>
                                    <a href="${l.url}" target="_blank" style="color: var(--accent); font-size: 0.8125rem; display: flex; align-items: center;" title="Buy on ${l.source}"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>
                                </div>
                            </div>
                        `).join("")}
                    </div>
                </div>

                <div class="card-actions">
                    <button class="compare-btn" onclick="openStoreModal('${encodeURIComponent(p.name)}')">Compare Stores</button>
                    <button class="add-compare-list-btn ${isAdded ? 'active' : ''}" onclick="toggleCompareItem(this, '${encodeURIComponent(p.name)}')">
                        <i class="fa-solid ${isAdded ? 'fa-check' : 'fa-plus'}"></i>
                    </button>
                </div>
            </div>
        `;
        resultsGrid.appendChild(card);
    });
    
    setupCardTiltListeners();
    hideLoading();
}

function renderStars(rating) {
    const clampedRating = Math.max(0, Math.min(5, rating));
    const full = Math.floor(clampedRating);
    const half = clampedRating % 1 >= 0.5 ? 1 : 0;
    const empty = Math.max(0, 5 - full - half);
    
    return `${'<i class="fa-solid fa-star"></i>'.repeat(full)}${half ? '<i class="fa-solid fa-star-half-stroke"></i>' : ''}${'<i class="fa-regular fa-star"></i>'.repeat(empty)}`;
}

// Compare List State Management
function toggleCompareItem(btn, encodedName) {
    const name = decodeURIComponent(encodedName);
    const idx = compareList.indexOf(name);
    
    if (idx > -1) {
        compareList.splice(idx, 1);
        btn.classList.remove("active");
        btn.innerHTML = '<i class="fa-solid fa-plus"></i>';
    } else {
        if (compareList.length >= 4) {
            alert("You can compare up to 4 models at a time.");
            return;
        }
        compareList.push(name);
        btn.classList.add("active");
        btn.innerHTML = '<i class="fa-solid fa-check"></i>';
    }
    
    updateCompareDrawer();
}

function updateCompareDrawer() {
    drawerItemsList.innerHTML = "";
    
    if (compareList.length > 0) {
        compareList.forEach(name => {
            const item = document.createElement("div");
            item.className = "drawer-item";
            item.innerHTML = `
                <span>${name}</span>
                <span class="drawer-item-remove" onclick="removeCompareItem('${encodeURIComponent(name)}')">&times;</span>
            `;
            drawerItemsList.appendChild(item);
        });
        compareDrawer.classList.add("show");
    } else {
        compareDrawer.classList.remove("show");
    }
}

function removeCompareItem(encodedName) {
    const name = decodeURIComponent(encodedName);
    const idx = compareList.indexOf(name);
    if (idx > -1) {
        compareList.splice(idx, 1);
        updateCompareDrawer();
        
        // Update checkmarks in grid
        searchProducts(); // Re-render to refresh buttons state
    }
}

// Open Modal 1: Store comparison (Amazon vs Flipkart vs Croma)
async function openStoreModal(encodedName) {
    const name = decodeURIComponent(encodedName);
    storeModal.classList.add("show");
    pageWrapper.classList.add("modal-active");
    
    // Set loading placeholders
    document.getElementById("store-modal-title").textContent = name;
    const listingsContainer = document.getElementById("store-listings-container");
    listingsContainer.innerHTML = '<div class="spinner-wrapper"><div class="spinner"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/compare/stores?name=${encodeURIComponent(name)}`);
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (!data || !data.listings || data.listings.length === 0) {
            throw new Error("No comparative listings found for this product.");
        }
        
        // 1. Render store cards
        listingsContainer.innerHTML = "";
        data.listings.forEach(listing => {
            const lCard = document.createElement("div");
            lCard.className = "listing-card";
            
            // Radial percentage for conic gradient
            const percent = Math.round(listing.ml_score);
            
            lCard.innerHTML = `
                <div class="listing-store-info">
                    <span class="listing-store-name"><i class="fa-solid fa-store" style="color: var(--accent);"></i> ${listing.source}</span>
                    <span style="font-size: 0.8125rem; color: var(--text-muted);">Rating: ${listing.rating} ⭐</span>
                </div>
                <div class="listing-price">₹${listing.price.toLocaleString()}</div>
                <div class="listing-ml-block">
                    <div class="score-radial" data-score="${percent}" style="--percentage: ${percent}%"></div>
                    <div style="font-size: 0.8125rem;">
                        <div style="font-weight: 700; color: ${listing.ml_label === 'Best Value' ? 'var(--success)' : 'var(--text-main)'};">${listing.ml_label}</div>
                        <div style="color: var(--text-muted);">Score</div>
                    </div>
                </div>
                <a href="${listing.url}" target="_blank" class="listing-visit-btn">Visit Store</a>
            `;
            listingsContainer.appendChild(lCard);
        });
        
        // 2. Render specs
        const specsContainer = document.getElementById("store-specs-container");
        specsContainer.innerHTML = "";
        Object.entries(data.specifications || {}).forEach(([k, v]) => {
            const sItem = document.createElement("div");
            sItem.className = "spec-item";
            sItem.innerHTML = `
                <div class="spec-name">${k}</div>
                <div class="spec-value">${v}</div>
            `;
            specsContainer.appendChild(sItem);
        });
        
        // 3. Render reviews
        const reviewsContainer = document.getElementById("reviews-list-container");
        reviewsContainer.innerHTML = "";
        
        // Extract all reviews from all listings
        let allReviews = [];
        (data.listings || []).forEach(l => {
            const reviews = l.reviews || [];
            reviews.forEach(r => {
                allReviews.push({ ...r, source: l.source });
            });
        });
        
        // Take top 4 random reviews to display
        allReviews.sort(() => 0.5 - Math.random());
        const displayReviews = allReviews.slice(0, 4);
        
        displayReviews.forEach(r => {
            const rItem = document.createElement("div");
            rItem.className = "review-item";
            rItem.innerHTML = `
                <div class="review-meta">
                    <span><strong>${r.author}</strong> via ${r.source}</span>
                    <span style="color: var(--warning);">${renderStars(r.rating || 4.0)}</span>
                </div>
                <div class="review-title">${r.title}</div>
                <div class="review-text">"${r.text}"</div>
            `;
            reviewsContainer.appendChild(rItem);
        });
        
        // 4. Update Sentiment analysis marker
        // Average sentiment score over listings (scaled from -1..1 to 0..100)
        const avgSentiment = data.listings.reduce((sum, current) => sum + (current.ml_sentiment || 0), 0) / data.listings.length;
        const sentPercent = Math.round(((avgSentiment + 1) / 2) * 100);
        
        const pointer = document.getElementById("sentiment-pointer-marker");
        pointer.style.left = `${sentPercent}%`;
        
        let sentimentWord = "Neutral";
        let sentimentColor = "var(--warning)";
        if (avgSentiment > 0.25) {
            sentimentWord = "Highly Positive";
            sentimentColor = "var(--success)";
        } else if (avgSentiment < -0.15) {
            sentimentWord = "Critical / Negative";
            sentimentColor = "var(--danger)";
        }
        
        document.getElementById("sentiment-desc").innerHTML = `NLP Sentiment Index: <strong style="color: ${sentimentColor};">${sentimentWord} (${Math.round(avgSentiment * 100) / 100})</strong> based on review logs.`;

        // 5. Draw comparison chart
        drawStoreChart(data.listings);
        
    } catch (err) {
        console.error(err);
        listingsContainer.innerHTML = `<p style="color: var(--danger); text-align: center; padding: 1rem;"><i class="fa-solid fa-triangle-exclamation"></i> Error: ${err.message || 'Failed to fetch comparative listings.'}</p>`;
    }
}

// Chart.js helper for Store comparison
function drawStoreChart(listings) {
    if (typeof Chart === 'undefined') {
        console.warn("Chart.js not loaded. Skipping store chart.");
        const canvas = document.getElementById("store-comparison-chart");
        if (canvas) {
            canvas.parentNode.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); font-size: 0.875rem;">Chart.js offline</div>';
        }
        return;
    }
    const ctx = document.getElementById("store-comparison-chart").getContext("2d");
    
    if (storeChartInstance) {
        storeChartInstance.destroy();
    }
    
    const labels = listings.map(l => l.source);
    const scores = listings.map(l => l.ml_score);
    const pricesScaled = listings.map(l => l.price / 1000); // Scale down price to draw nicely
    
    storeChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "ML Score (out of 100)",
                    data: scores,
                    backgroundColor: "rgba(99, 102, 241, 0.7)",
                    borderColor: "rgb(99, 102, 241)",
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: "Price (k INR)",
                    data: pricesScaled,
                    backgroundColor: "rgba(16, 185, 129, 0.7)",
                    borderColor: "rgb(16, 185, 129)",
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(255,255,255,0.05)" },
                    ticks: { color: "#94a3b8" }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: "#94a3b8" }
                }
            },
            plugins: {
                legend: {
                    labels: { color: "#f8fafc" }
                }
            }
        }
    });
}

// Open Modal 2: Cross-Model Comparison
async function openCrossModal() {
    crossModal.classList.add("show");
    pageWrapper.classList.add("modal-active");
    
    const table = document.getElementById("cross-compare-table");
    table.innerHTML = '<tr><td style="text-align: center; padding: 4rem;"><div class="spinner"></div><p style="margin-top: 1rem;">Analyzing cross-model dataset...</p></td></tr>';
    
    const queryNames = compareList.join(",");
    
    try {
        const response = await fetch(`${API_BASE}/api/compare/models?names=${encodeURIComponent(queryNames)}`);
        const data = await response.json();
        const models = data.comparison;
        
        // Generate Specifications list across models
        // Get all unique specs keys
        const allSpecsKeys = new Set();
        models.forEach(m => {
            Object.keys(m.specifications || {}).forEach(k => allSpecsKeys.add(k));
        });
        
        // Build Table
        let tableHTML = `
            <thead>
                <tr>
                    <th>Feature</th>
                    ${models.map(m => `<th>${m.name}</th>`).join("")}
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="highlight">Best Offer Price</td>
                    ${models.map(m => `<td class="highlight" style="font-size: 1.125rem; font-weight: 700; color: var(--success);">₹${m.price.toLocaleString()} <span style="font-size: 0.75rem; font-weight: normal; color: var(--text-muted);">via ${m.source}</span></td>`).join("")}
                </tr>
                <tr>
                    <td>Brand</td>
                    ${models.map(m => `<td>${m.brand}</td>`).join("")}
                </tr>
                <tr>
                    <td>Store Rating</td>
                    ${models.map(m => `<td>${m.rating} / 5.0 ⭐</td>`).join("")}
                </tr>
                <tr>
                    <td>Reviews Analyzed</td>
                    ${models.map(m => `<td>${m.review_count.toLocaleString()}</td>`).join("")}
                </tr>
                <tr>
                    <td>NLP Sentiment Index</td>
                    ${models.map(m => `<td>${Math.round(m.ml_sentiment * 100) / 100}</td>`).join("")}
                </tr>
                <tr>
                    <td class="highlight">ML Final Rating</td>
                    ${models.map(m => `<td class="highlight" style="font-weight: 800; color: var(--accent);">${m.ml_score} / 100</td>`).join("")}
                </tr>
                <tr>
                    <td>Verdict Label</td>
                    ${models.map(m => `<td><span class="card-badge ${m.ml_label === 'Best Value' ? 'badge-best-value' : m.ml_label === 'Budget Pick' ? 'badge-budget' : m.ml_label === 'Premium Choice' ? 'badge-premium' : 'badge-rec'}" style="position: static; padding: 0.2rem 0.5rem; font-size: 0.7rem;">${m.ml_label}</span></td>`).join("")}
                </tr>
        `;
        
        // Append specifications rows
        allSpecsKeys.forEach(key => {
            tableHTML += `
                <tr>
                    <td>${key}</td>
                    ${models.map(m => `<td>${m.specifications[key] || "N/A"}</td>`).join("")}
                </tr>
            `;
        });
        
        tableHTML += "</tbody>";
        table.innerHTML = tableHTML;
        
        // Render ML summary cards
        const summaryContainer = document.getElementById("cross-ml-summary-cards");
        summaryContainer.innerHTML = "";
        models.forEach(m => {
            const card = document.createElement("div");
            card.className = "spec-item";
            card.style.display = "flex";
            card.style.justifyContent = "space-between";
            card.style.alignItems = "center";
            
            card.innerHTML = `
                <div>
                    <div style="font-weight: 700; font-size: 0.9375rem;">${m.name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${m.brand} (${m.category})</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 800; color: var(--success); font-size: 1.125rem;">${m.ml_score}</div>
                    <div style="font-size: 0.75rem; color: var(--text-dark); text-transform: uppercase;">ML Value Score</div>
                </div>
            `;
            summaryContainer.appendChild(card);
        });
        
        // Draw Radar or Grouped Bar Chart
        drawCrossChart(models);
        
    } catch (err) {
        console.error(err);
        table.innerHTML = '<tr><td style="text-align: center; padding: 4rem; color: var(--danger);">Failed to execute cross-model dataset query.</td></tr>';
    }
}

// Chart.js helper for Cross Model comparison
function drawCrossChart(models) {
    if (typeof Chart === 'undefined') {
        console.warn("Chart.js not loaded. Skipping cross chart.");
        const canvas = document.getElementById("cross-comparison-chart");
        if (canvas) {
            canvas.parentNode.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); font-size: 0.875rem;">Chart.js offline</div>';
        }
        return;
    }
    const ctx = document.getElementById("cross-comparison-chart").getContext("2d");
    
    if (crossChartInstance) {
        crossChartInstance.destroy();
    }
    
    // We will draw a Radar chart showing: Price Index (scaled), Rating (scaled to 100), Sentiment (scaled to 100), ML Score
    // But radar chart needs at least 3 dimensions. If we have 2 models, radar is perfect.
    
    const datasets = models.map((m, idx) => {
        // Compute dimensions:
        // 1. Rating score (scaled to 100)
        const d_rating = m.rating * 20; 
        
        // 2. Sentiment score (scaled 0 to 100)
        const d_sentiment = ((m.ml_sentiment + 1) / 2) * 100;
        
        // 3. Price Value index (the cheaper, the higher the index - we invert relative to max price in selection)
        const maxPrice = Math.max(...models.map(x => x.price));
        const d_price_index = maxPrice > 0 ? (1.0 - (m.price / maxPrice)) * 100 : 100;
        
        // 4. ML composite score
        const d_ml = m.ml_score;
        
        const colors = [
            { fill: "rgba(99, 102, 241, 0.2)", border: "rgb(99, 102, 241)" },
            { fill: "rgba(16, 185, 129, 0.2)", border: "rgb(16, 185, 129)" },
            { fill: "rgba(245, 158, 11, 0.2)", border: "rgb(245, 158, 11)" },
            { fill: "rgba(239, 68, 68, 0.2)", border: "rgb(239, 68, 68)" }
        ];
        const color = colors[idx % colors.length];
        
        return {
            label: m.name,
            data: [d_rating, d_sentiment, d_price_index, d_ml],
            backgroundColor: color.fill,
            borderColor: color.border,
            pointBackgroundColor: color.border,
            borderWidth: 2
        };
    });
    
    crossChartInstance = new Chart(ctx, {
        type: "radar",
        data: {
            labels: ["Rating Quotient", "Review Sentiment", "Price Advantage", "Value Score"],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: "rgba(255,255,255,0.05)" },
                    grid: { color: "rgba(255,255,255,0.05)" },
                    pointLabels: { color: "#94a3b8", font: { size: 10, weight: "bold" } },
                    ticks: { display: false, color: "#94a3b8" },
                    min: 0,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    labels: { color: "#f8fafc" }
                }
            }
        }
    });
}

// 3D Background Particle Animation
function init3DBackground() {
    const canvas = document.getElementById("bg-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const particleCount = 100;
    const maxDistance = 110;

    // Initialize 3D points
    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: (Math.random() - 0.5) * 800,
            y: (Math.random() - 0.5) * 800,
            z: (Math.random() - 0.5) * 800,
            vx: (Math.random() - 0.5) * 0.25,
            vy: (Math.random() - 0.5) * 0.25,
            vz: (Math.random() - 0.5) * 0.25
        });
    }

    let mouseX = 0;
    let mouseY = 0;
    let targetRotY = 0.0003;
    let targetRotX = 0.0002;
    let currentRotY = 0.0003;
    let currentRotX = 0.0002;

    window.addEventListener("mousemove", (e) => {
        // Normalize mouse positions to [-0.5, 0.5]
        mouseX = (e.clientX / width) - 0.5;
        mouseY = (e.clientY / height) - 0.5;
        
        // Dynamic target rotation speed based on cursor
        targetRotY = mouseX * 0.0015;
        targetRotX = mouseY * 0.0015;
    });

    function rotateX(p, angle) {
        const rad = angle;
        const cos = Math.cos(rad);
        const sin = Math.sin(rad);
        const y = p.y * cos - p.z * sin;
        const z = p.y * sin + p.z * cos;
        p.y = y;
        p.z = z;
    }

    function rotateY(p, angle) {
        const rad = angle;
        const cos = Math.cos(rad);
        const sin = Math.sin(rad);
        const x = p.x * cos - p.z * sin;
        const z = p.x * sin + p.z * cos;
        p.x = x;
        p.z = z;
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);

        // Interpolate rotation speed for smooth movement
        currentRotY += (targetRotY - currentRotY) * 0.05;
        currentRotX += (targetRotX - currentRotX) * 0.05;

        // Auto rotation offset
        const rotY = currentRotY + 0.0002;
        const rotX = currentRotX + 0.0001;

        const projected = [];
        const focus = 400;

        // Update, rotate and project particles
        for (let i = 0; i < particleCount; i++) {
            const p = particles[i];

            // Slowly drift particles in space
            p.x += p.vx;
            p.y += p.vy;
            p.z += p.vz;

            // Contain in virtual box boundaries
            if (Math.abs(p.x) > 400) p.vx *= -1;
            if (Math.abs(p.y) > 400) p.vy *= -1;
            if (Math.abs(p.z) > 400) p.vz *= -1;

            // Apply 3D rotation
            rotateY(p, rotY);
            rotateX(p, rotX);

            // Projection to 2D
            const scale = focus / (focus + p.z + 500);
            const sx = width / 2 + p.x * scale;
            const sy = height / 2 + p.y * scale;

            projected.push({ sx, sy, z: p.z, scale });
        }

        // Draw constellation lines
        for (let i = 0; i < particleCount; i++) {
            const pi = particles[i];
            const projI = projected[i];

            if (projI.sx < 0 || projI.sx > width || projI.sy < 0 || projI.sy > height) continue;

            for (let j = i + 1; j < particleCount; j++) {
                const pj = particles[j];
                const projJ = projected[j];

                // Calculate 3D distance
                const dx = pi.x - pj.x;
                const dy = pi.y - pj.y;
                const dz = pi.z - pj.z;
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

                if (dist < maxDistance) {
                    const alpha = (1 - dist / maxDistance) * 0.15;
                    ctx.beginPath();
                    ctx.moveTo(projI.sx, projI.sy);
                    ctx.lineTo(projJ.sx, projJ.sy);
                    
                    // Neon gradient lines
                    ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`;
                    ctx.lineWidth = projI.scale * 0.8;
                    ctx.stroke();
                }
            }
        }

        // Draw particle nodes
        for (let i = 0; i < particleCount; i++) {
            const proj = projected[i];
            if (proj.sx < 0 || proj.sx > width || proj.sy < 0 || proj.sy > height) continue;

            // Size based on Z depth
            const radius = (1.5 - proj.z / 400) * 1.5;
            const alpha = (1 - proj.z / 800) * 0.45;

            ctx.beginPath();
            ctx.arc(proj.sx, proj.sy, radius, 0, Math.PI * 2);
            
            // Neon teal or indigo nodes
            ctx.fillStyle = `rgba(16, 185, 129, ${alpha})`;
            if (i % 2 === 0) {
                ctx.fillStyle = `rgba(99, 102, 241, ${alpha})`;
            }
            ctx.fill();
        }

        requestAnimationFrame(animate);
    }

    animate();
}

// Setup 3D Card Tilt mouse trackers
function setupCardTiltListeners() {
    const cards = document.querySelectorAll(".product-card");
    cards.forEach(card => {
        card.addEventListener("mousemove", (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const w = rect.width;
            const h = rect.height;
            
            // Calculate tilt angle based on mouse coordinates relative to center (max 12 deg)
            const rotX = -((y - h / 2) / h) * 12;
            const rotY = ((x - w / 2) / w) * 12;
            
            card.style.transform = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(1.02, 1.02, 1.02)`;
            card.style.setProperty('--glare-x', `${(x / w) * 100}%`);
            card.style.setProperty('--glare-y', `${(y / h) * 100}%`);
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
        });
    });
}
