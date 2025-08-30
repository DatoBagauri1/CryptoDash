// Main JavaScript file for CryptoDash

// Global variables
let priceUpdateInterval;
let notificationQueue = [];

// Document ready initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    startPriceUpdates();
});

// Initialize the application
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize modals
    initializeModals();
    
    // Setup theme handling
    initializeTheme();
    
    // Initialize search functionality
    initializeSearch();
    
    // Show welcome message for new users
    showWelcomeMessage();
    
    console.log('CryptoDash initialized successfully');
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize Bootstrap modals
function initializeModals() {
    const modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(modalEl => {
        modalEl.addEventListener('hidden.bs.modal', function() {
            // Clear form data when modal is closed
            const forms = modalEl.querySelectorAll('form');
            forms.forEach(form => {
                if (form.dataset.clearOnClose !== 'false') {
                    form.reset();
                }
            });
        });
    });
}

// Initialize theme handling
function initializeTheme() {
    const theme = localStorage.getItem('cryptodash-theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', theme);
}

// Initialize search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[type="search"], .crypto-search');
    searchInputs.forEach(input => {
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    // Price refresh buttons
    document.addEventListener('click', function(e) {
        if (e.target.matches('.refresh-prices, .refresh-prices *')) {
            e.preventDefault();
            refreshPrices();
        }
    });
    
    // Copy to clipboard functionality
    document.addEventListener('click', function(e) {
        if (e.target.matches('.copy-to-clipboard, .copy-to-clipboard *')) {
            e.preventDefault();
            copyToClipboard(e.target.dataset.text || e.target.textContent);
        }
    });
    
    // Number formatting for large numbers
    document.addEventListener('input', function(e) {
        if (e.target.matches('.format-number')) {
            formatNumberInput(e.target);
        }
    });
    
    // Smooth scrolling for anchor links
    document.addEventListener('click', function(e) {
        if (e.target.matches('a[href^="#"]')) {
            e.preventDefault();
            const targetId = e.target.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        }
    });
}

// Start periodic price updates
function startPriceUpdates() {
    // Update prices every 30 seconds if on dashboard or portfolio pages
    if (window.location.pathname.includes('/dashboard') || 
        window.location.pathname.includes('/portfolio')) {
        priceUpdateInterval = setInterval(updatePrices, 30000);
    }
}

// Update cryptocurrency prices
function updatePrices() {
    const priceElements = document.querySelectorAll('[data-coin-id]');
    if (priceElements.length === 0) return;
    
    const coinIds = Array.from(priceElements).map(el => el.dataset.coinId);
    const uniqueCoinIds = [...new Set(coinIds)];
    
    // Show loading indicators
    showLoadingIndicators(priceElements);
    
    // Fetch updated prices (this would typically make an API call)
    fetchCoinPrices(uniqueCoinIds)
        .then(prices => {
            updatePriceElements(prices);
            hideLoadingIndicators(priceElements);
        })
        .catch(error => {
            console.error('Failed to update prices:', error);
            hideLoadingIndicators(priceElements);
            showNotification('Failed to update prices', 'error');
        });
}

// Show loading indicators
function showLoadingIndicators(elements) {
    elements.forEach(el => {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.setAttribute('data-loading', 'true');
        el.appendChild(spinner);
    });
}

// Hide loading indicators
function hideLoadingIndicators(elements) {
    elements.forEach(el => {
        const spinner = el.querySelector('[data-loading="true"]');
        if (spinner) {
            spinner.remove();
        }
    });
}

// Fetch coin prices (mock implementation)
async function fetchCoinPrices(coinIds) {
    // In a real implementation, this would make an API call
    // For now, return mock data
    return new Promise((resolve) => {
        setTimeout(() => {
            const mockPrices = {};
            coinIds.forEach(id => {
                mockPrices[id] = {
                    usd: Math.random() * 1000,
                    usd_24h_change: (Math.random() - 0.5) * 20
                };
            });
            resolve(mockPrices);
        }, 1000);
    });
}

// Update price elements with new data
function updatePriceElements(prices) {
    document.querySelectorAll('[data-coin-id]').forEach(el => {
        const coinId = el.dataset.coinId;
        const price = prices[coinId];
        
        if (price) {
            // Update price display
            if (el.classList.contains('price-display')) {
                el.textContent = formatPrice(price.usd);
            }
            
            // Update change percentage
            if (el.classList.contains('change-display')) {
                const change = price.usd_24h_change;
                el.textContent = formatPercentage(change);
                el.className = el.className.replace(/text-(success|danger)/, '');
                el.classList.add(change >= 0 ? 'text-success' : 'text-danger');
            }
        }
    });
}

// Format price for display
function formatPrice(price) {
    if (price >= 1) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(price);
    } else {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 6,
            maximumFractionDigits: 6
        }).format(price);
    }
}

// Format percentage for display
function formatPercentage(percentage) {
    const sign = percentage >= 0 ? '+' : '';
    return `${sign}${percentage.toFixed(2)}%`;
}

// Format large numbers
function formatLargeNumber(number) {
    if (number >= 1e12) {
        return (number / 1e12).toFixed(1) + 'T';
    } else if (number >= 1e9) {
        return (number / 1e9).toFixed(1) + 'B';
    } else if (number >= 1e6) {
        return (number / 1e6).toFixed(1) + 'M';
    } else if (number >= 1e3) {
        return (number / 1e3).toFixed(1) + 'K';
    }
    return number.toLocaleString();
}

// Format number input fields
function formatNumberInput(input) {
    let value = input.value.replace(/[^\d.]/g, '');
    
    // Ensure only one decimal point
    const parts = value.split('.');
    if (parts.length > 2) {
        value = parts[0] + '.' + parts.slice(1).join('');
    }
    
    input.value = value;
}

// Copy text to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard', 'success');
        }).catch(() => {
            showNotification('Failed to copy', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard', 'success');
        } catch (err) {
            showNotification('Failed to copy', 'error');
        }
        
        textArea.remove();
    }
}

// Show notification
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Perform search
function performSearch(query) {
    if (query.length < 2) return;
    
    // This would typically make an API call to search for cryptocurrencies
    console.log('Searching for:', query);
    
    // Show search suggestions (implementation depends on specific page)
    showSearchSuggestions(query);
}

// Show search suggestions
function showSearchSuggestions(query) {
    const suggestionsContainer = document.querySelector('.search-suggestions');
    if (!suggestionsContainer) return;
    
    // Mock suggestions - in real implementation, this would come from API
    const mockSuggestions = [
        { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC' },
        { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
        { id: 'binancecoin', name: 'BNB', symbol: 'BNB' }
    ].filter(coin => 
        coin.name.toLowerCase().includes(query.toLowerCase()) ||
        coin.symbol.toLowerCase().includes(query.toLowerCase())
    );
    
    suggestionsContainer.innerHTML = mockSuggestions.map(coin => `
        <div class="suggestion-item p-2 border-bottom" data-coin-id="${coin.id}">
            <strong>${coin.name}</strong> (${coin.symbol})
        </div>
    `).join('');
}

// Refresh prices manually
function refreshPrices() {
    showNotification('Refreshing prices...', 'info', 1000);
    updatePrices();
}

// Show welcome message for new users
function showWelcomeMessage() {
    const hasVisited = localStorage.getItem('cryptodash-visited');
    if (!hasVisited && window.location.pathname === '/') {
        setTimeout(() => {
            showNotification('Welcome to CryptoDash! 🚀', 'success', 5000);
            localStorage.setItem('cryptodash-visited', 'true');
        }, 1000);
    }
}

// Utility function to debounce function calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility function to throttle function calls
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause updates
        if (priceUpdateInterval) {
            clearInterval(priceUpdateInterval);
        }
    } else {
        // Page is visible, resume updates
        startPriceUpdates();
    }
});

// Handle network status changes
window.addEventListener('online', function() {
    showNotification('Connection restored', 'success');
    updatePrices();
});

window.addEventListener('offline', function() {
    showNotification('Connection lost', 'warning');
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (priceUpdateInterval) {
        clearInterval(priceUpdateInterval);
    }
});

// Export functions for use in other scripts
window.CryptoDash = {
    formatPrice,
    formatPercentage,
    formatLargeNumber,
    showNotification,
    copyToClipboard,
    updatePrices,
    refreshPrices
};
