const API_BASE = window.location.protocol === "file:" || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : window.location.origin;

// App state
let currentCategory = "";
let compareList = []; // Array of product names
let storeChartInstance = null;
let crossChartInstance = null;
let shouldScrollToResults = false;

// DOM Elements (assigned dynamically inside DOMContentLoaded)
let pageWrapper, searchInput, searchBtn, categoryChips, resultsGrid, resultsSec, resultsCountText, loadingSpinner, loadingText, heroSec;
let compareDrawer, drawerItemsList, drawerCompareBtn;
let storeModal, closeStoreModal, crossModal, closeCrossModal;
let seedDbBtn, logoBtn, homeBtn;

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
    // Initialize DOM elements
    pageWrapper = document.getElementById("page-wrapper");
    searchInput = document.getElementById("search-input");
    searchBtn = document.getElementById("search-btn");
    categoryChips = document.getElementById("category-chips");
    resultsGrid = document.getElementById("results-grid");
    resultsSec = document.getElementById("results-sec");
    resultsCountText = document.getElementById("results-count-text");
    loadingSpinner = document.getElementById("loading-spinner");
    loadingText = document.getElementById("loading-text");
    heroSec = document.getElementById("hero-sec");

    compareDrawer = document.getElementById("compare-drawer");
    drawerItemsList = document.getElementById("drawer-items-list");
    drawerCompareBtn = document.getElementById("drawer-compare-btn");

    storeModal = document.getElementById("store-modal");
    closeStoreModal = document.getElementById("close-store-modal");
    crossModal = document.getElementById("cross-modal");
    closeCrossModal = document.getElementById("close-cross-modal");

    seedDbBtn = document.getElementById("seed-db-btn");
    logoBtn = document.getElementById("nav-logo");
    homeBtn = document.getElementById("nav-home");

    // Bind event listeners only after DOM is fully constructed
    if (logoBtn) logoBtn.addEventListener("click", resetToHome);
    if (homeBtn) homeBtn.addEventListener("click", resetToHome);
    
    if (searchBtn) {
        searchBtn.addEventListener("click", () => {
            shouldScrollToResults = true;
            searchProducts();
        });
    }

    if (searchInput) {
        searchInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                shouldScrollToResults = true;
                searchProducts();
            }
        });
    }

    if (categoryChips) {
        categoryChips.addEventListener("click", (e) => {
            e.preventDefault();
            const chip = e.target.closest(".category-chip");
            if (!chip) return;
            
            console.log("Category chip clicked:", chip.textContent, "Category value:", chip.getAttribute("data-category"));
            const catName = chip.getAttribute("data-category") || "";
            selectCategory(catName);
        });
    }

    if (resultsGrid) {
        resultsGrid.addEventListener("click", (e) => {
            const cardCategory = e.target.closest(".card-category");
            if (cardCategory) {
                const catName = cardCategory.textContent.trim();
                console.log("Card category clicked:", catName);
                selectCategory(catName);
            }
        });
    }

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

    if (drawerCompareBtn) {
        drawerCompareBtn.addEventListener("click", () => {
            if (compareList.length < 2) {
                alert("Please select at least 2 models to compare.");
                return;
            }
            openCrossModal();
        });
    }

    if (closeStoreModal) {
        closeStoreModal.addEventListener("click", () => {
            if (storeModal) storeModal.classList.remove("show");
            if (pageWrapper) pageWrapper.classList.remove("modal-active");
        });
    }

    if (closeCrossModal) {
        closeCrossModal.addEventListener("click", () => {
            if (crossModal) crossModal.classList.remove("show");
            if (pageWrapper) pageWrapper.classList.remove("modal-active");
        });
    }

    document.querySelectorAll(".modal-overlay").forEach(overlay => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                overlay.classList.remove("show");
                if (pageWrapper) pageWrapper.classList.remove("modal-active");
            }
        });
    });

    init3DBackground();
    
    // Perform initial empty search to display some default listings
    searchProducts();
});

function selectCategory(catName) {
    if (searchInput) searchInput.value = "";
    currentCategory = catName;
    
    document.querySelectorAll(".category-chip").forEach(c => {
        c.classList.remove("active");
        if (c.getAttribute("data-category") === catName) {
            c.classList.add("active");
        }
    });
    
    shouldScrollToResults = true;
    searchProducts();
}

function resetToHome(e) {
    if (e) e.preventDefault();
    if (searchInput) searchInput.value = "";
    currentCategory = "";
    document.querySelectorAll(".category-chip").forEach(chip => {
        chip.classList.remove("active");
        if (chip.getAttribute("data-category") === "") chip.classList.add("active");
    });
    shouldScrollToResults = false;
    searchProducts();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// Functions
function showLoading(text = "Searching...") {
    loadingText.textContent = text;
    loadingSpinner.style.display = "flex";
    resultsSec.style.display = "none";
}

function hideLoading() {
    loadingSpinner.style.display = "none";
    resultsSec.style.display = "block";
    if (shouldScrollToResults) {
        setTimeout(() => {
            resultsSec.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);
        shouldScrollToResults = false;
    }
}

// Search
async function searchProducts() {
    showLoading("Fetching products and applying ML models...");
    
    const query = searchInput ? searchInput.value.trim() : "";
    let url = `${API_BASE}/api/search?`;
    if (query) url += `q=${encodeURIComponent(query)}&`;
    if (currentCategory) url += `category=${encodeURIComponent(currentCategory)}`;
    
    console.log("searchProducts: Fetching from URL:", url);
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        console.log("searchProducts: Fetch succeeded. Results count:", data.results ? data.results.length : 0);
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
                    <span class="reviews-cnt">(${(p.total_reviews || 0).toLocaleString()} reviews)</span>
                </div>

                
                <!-- Specifications List -->
                <div class="card-specs" style="margin-bottom: 1rem; display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; font-size: 0.75rem; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); padding: 0.5rem; border-radius: var(--radius-sm);">
                    ${Object.entries(p.specifications || {}).map(([key, val]) => `
                        <div style="color: var(--text-muted); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" title="${key}: ${val}">
                            <span style="font-weight: 600; color: var(--text-main);">${key}:</span> ${val}
                        </div>
                    `).join("")}
                </div>
                
                <!-- Direct Website Comparison Table -->
                <div class="card-price-comparison" style="margin-bottom: 1.25rem; background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-sm); overflow: hidden;">
                    <div style="font-size: 0.75rem; font-weight: 700; padding: 0.4rem 0.6rem; background: rgba(255,255,255,0.03); border-bottom: 1px solid var(--glass-border); display: flex; justify-content: space-between;">
                        <span>Store Listings</span>
                        <span style="color: var(--accent); font-weight: 800;"><i class="fa-solid fa-cart-shopping"></i> Visit</span>
                    </div>
                    <div style="max-height: 140px; overflow-y: auto;">
                        ${p.listings.map(l => `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0.6rem; border-bottom: 1px solid rgba(255,255,255,0.03); font-size: 0.8125rem;">
                                <span style="font-weight: 500; display: flex; align-items: center; gap: 0.25rem;">
                                    ${l.source} 
                                    ${l.source === p.best_deal_store ? '<span style="font-size: 0.65rem; padding: 0.05rem 0.2rem; background: var(--success-light); color: var(--success); border-radius: 3px; font-weight: 700;">Best</span>' : ''}
                                </span>
                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                    <a href="${l.url}" target="_blank" style="color: var(--accent); font-size: 0.75rem; display: flex; align-items: center; gap: 0.25rem; background: rgba(99, 102, 241, 0.15); padding: 0.2rem 0.45rem; border-radius: 3px; border: 1px solid rgba(99, 102, 241, 0.3); font-weight: 600; text-decoration: none;" title="Buy on ${l.source}">Visit <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.65rem;"></i></a>
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
    const parsed = parseFloat(rating);
    const clampedRating = Math.max(0, Math.min(5, isNaN(parsed) ? 0 : parsed));
    const full = Math.floor(clampedRating) || 0;
    const half = clampedRating % 1 >= 0.5 ? 1 : 0;
    const empty = Math.max(0, 5 - full - half) || 0;
    
    return `${'<i class="fa-solid fa-star"></i>'.repeat(full)}${half ? '<i class="fa-solid fa-star-half-stroke"></i>' : ''}${'<i class="fa-regular fa-star"></i>'.repeat(empty)}`;
}

function formatPriceRange(minPrice, maxPrice) {
    if (!minPrice || minPrice === 0) {
        if (!maxPrice || maxPrice === 0) return "Check Stores";
        return `₹${maxPrice.toLocaleString()}`;
    }
    if (!maxPrice || maxPrice === 0) {
        return `₹${minPrice.toLocaleString()}`;
    }
    if (minPrice === maxPrice) {
        return `₹${minPrice.toLocaleString()}`;
    }
    return `₹${minPrice.toLocaleString()} - ₹${maxPrice.toLocaleString()}`;
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
                    <td>Brand</td>
                    ${models.map(m => `<td>${m.brand}</td>`).join("")}
                </tr>
                <tr>
                    <td>Store Rating</td>
                    ${models.map(m => `<td>${m.rating ? m.rating + ' / 5.0 ⭐' : 'N/A'}</td>`).join("")}
                </tr>
                <tr>
                    <td>Reviews Analyzed</td>
                    ${models.map(m => `<td>${(m.review_count || 0).toLocaleString()}</td>`).join("")}
                </tr>
                <tr>
                    <td>NLP Sentiment Index</td>
                    ${models.map(m => `<td>${Math.round((m.ml_sentiment || 0) * 100) / 100}</td>`).join("")}
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
        
        // 3. ML composite score
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
            data: [d_rating, d_sentiment, d_ml],
            backgroundColor: color.fill,
            borderColor: color.border,
            pointBackgroundColor: color.border,
            borderWidth: 2
        };
    });
    
    crossChartInstance = new Chart(ctx, {
        type: "radar",
        data: {
            labels: ["Rating Quotient", "Review Sentiment", "Value Score"],
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
    const canvas = document.getElementById("bgCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let W, H;

    function resize() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    /* ── PARTICLES ── */
    const PARTICLE_COUNT = 120;
    const particles = [];
    const colors = ["rgba(37,99,235,", "rgba(6,182,212,", "rgba(129,140,248,", "rgba(255,255,255,"];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * 1920,
        y: Math.random() * 1080,
        vx: (Math.random() - .5) * .4,
        vy: (Math.random() - .5) * .4,
        r: Math.random() * 2.5 + .5,
        alpha: Math.random() * .6 + .1,
        color: colors[Math.floor(Math.random() * colors.length)]
      });
    }

    /* ── GRID FLOOR ── */
    let gridOffset = 0;

    function drawGrid() {
      const vp = { x: W / 2, y: H * .55 };
      const cols = 24, rows = 20;
      const spread = W * 1.4;

      gridOffset = (gridOffset + .5) % (H / rows);

      ctx.save();
      // vertical lines
      for (let i = 0; i <= cols; i++) {
        const bx = -spread / 2 + (i / cols) * spread;
        const alpha = .06 + .06 * Math.sin(Date.now() * .001 + i * .3);
        ctx.strokeStyle = `rgba(37,99,235,${alpha})`;
        ctx.lineWidth = .8;
        ctx.beginPath();
        ctx.moveTo(vp.x, vp.y);
        ctx.lineTo(W / 2 + bx, H + 20);
        ctx.stroke();
      }
      // horizontal lines
      for (let j = 0; j <= rows; j++) {
        const t = (j / rows + gridOffset / H) % 1;
        const y = vp.y + (H - vp.y) * t;
        const alpha = t * .18;
        const xL = vp.x - spread / 2 * t;
        const xR = vp.x + spread / 2 * t;
        ctx.strokeStyle = `rgba(37,99,235,${alpha})`;
        ctx.lineWidth = .6;
        ctx.beginPath();
        ctx.moveTo(xL, y);
        ctx.lineTo(xR, y);
        ctx.stroke();
      }
      ctx.restore();
    }

    /* ── 3D RINGS (canvas 2D perspective trick) ── */
    const rings = [
      { rx: .72, ry: 0,   rz: 0,   a: 0, speed: .006, r: Math.min(W,H)*.36, opacity: .12, color: "37,99,235" },
      { rx: .55, ry: .3,  rz: .1,  a: 1.1, speed: .004, r: Math.min(W,H)*.26, opacity: .1,  color: "6,182,212" },
      { rx: .8,  ry: -.2, rz: .2,  a: 2.3, speed: .003, r: Math.min(W,H)*.48, opacity: .07, color: "129,140,248" },
    ];

    function drawRing(ring) {
      const cx = W / 2, cy = H / 2;
      const segs = 80;
      const points = [];
      for (let i = 0; i <= segs; i++) {
        const angle = (i / segs) * Math.PI * 2 + ring.a;
        let x = Math.cos(angle) * ring.r;
        let y = Math.sin(angle) * ring.r;
        // apply tilt
        const y2 = y * Math.cos(ring.rx);
        const z  = y * Math.sin(ring.rx);
        const x2 = x * Math.cos(ring.ry) - z * Math.sin(ring.ry);
        const z2 = x * Math.sin(ring.ry) + z * Math.cos(ring.ry);
        // perspective
        const fov = 800;
        const scale = fov / (fov + z2 * .3);
        points.push({ sx: cx + x2 * scale, sy: cy + y2 * scale, z: z2 });
      }
      ctx.beginPath();
      ctx.moveTo(points[0].sx, points[0].sy);
      for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].sx, points[i].sy);
      ctx.strokeStyle = `rgba(${ring.color},${ring.opacity})`;
      ctx.lineWidth = 1;
      ctx.stroke();
      ring.a += ring.speed;
    }

    /* ── SHOOTING STARS ── */
    const shootingStars = [];
    function spawnStar() {
      shootingStars.push({
        x: Math.random() * W * .7,
        y: Math.random() * H * .5,
        len: 80 + Math.random() * 140,
        speed: 6 + Math.random() * 8,
        alpha: 1,
        angle: Math.PI / 6 + (Math.random() - .5) * .3
      });
    }
    const starInterval = setInterval(spawnStar, 1800);

    function drawShootingStars() {
      for (let i = shootingStars.length - 1; i >= 0; i--) {
        const s = shootingStars[i];
        const dx = Math.cos(s.angle) * s.len;
        const dy = Math.sin(s.angle) * s.len;
        const grad = ctx.createLinearGradient(s.x, s.y, s.x + dx, s.y + dy);
        grad.addColorStop(0, "rgba(79,195,247,0)");
        grad.addColorStop(.5, `rgba(79,195,247,${s.alpha * .8})`);
        grad.addColorStop(1, "rgba(255,255,255,0)");
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(s.x + dx, s.y + dy);
        ctx.stroke();
        s.x += Math.cos(s.angle) * s.speed;
        s.y += Math.sin(s.angle) * s.speed;
        s.alpha -= .018;
        if (s.alpha <= 0) shootingStars.splice(i, 1);
      }
    }

    /* ── MOUSE PARALLAX ── */
    let mx = 0, my = 0;
    document.addEventListener("mousemove", e => {
      mx = (e.clientX / window.innerWidth - .5) * 2;
      my = (e.clientY / window.innerHeight - .5) * 2;
    });

    /* ── HERO 3D TILT ── */
    const hero = document.querySelector(".hero");
    if (hero) {
        hero.addEventListener("mousemove", e => {
          const r = hero.getBoundingClientRect();
          const x = (e.clientX - r.left) / r.width - .5;
          const y = (e.clientY - r.top) / r.height - .5;
          hero.style.transform = `perspective(1000px) rotateY(${x * 5}deg) rotateX(${-y * 3}deg)`;
        });
        hero.addEventListener("mouseleave", () => {
          hero.style.transition = "transform .6s ease";
          hero.style.transform = "perspective(1000px) rotateY(0deg) rotateX(0deg)";
          setTimeout(() => hero.style.transition = "", 600);
        });
    }

    /* ── MAIN LOOP ── */
    function draw() {
      ctx.clearRect(0, 0, W, H);

      // deep space bg gradient
      const bg = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W*.8);
      bg.addColorStop(0, "rgba(10,20,60,.85)");
      bg.addColorStop(.5,"rgba(4,10,30,.9)");
      bg.addColorStop(1, "rgba(2,5,15,1)");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, W, H);

      // grid
      drawGrid();

      // 3D rings (with mouse parallax)
      ctx.save();
      ctx.translate(mx * 10, my * 6);
      rings.forEach(drawRing);
      ctx.restore();

      // particles
      ctx.save();
      ctx.translate(mx * 15, my * 10);
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x % W, p.y % H, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color + p.alpha + ")";
        ctx.fill();
      });
      // connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const d = Math.sqrt(dx*dx + dy*dy);
          if (d < 100) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(37,99,235,${(1 - d/100) * .08})`;
            ctx.lineWidth = .5;
            ctx.stroke();
          }
        }
      }
      ctx.restore();

      // shooting stars
      drawShootingStars();

      requestAnimationFrame(draw);
    }
    draw();
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
