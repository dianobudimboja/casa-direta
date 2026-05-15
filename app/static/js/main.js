const themeToggle = document.getElementById('themeToggle');
const htmlElement = document.documentElement;

// Get saved theme or default to dark
const savedTheme = localStorage.getItem('theme') || 'dark';
htmlElement.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

function updateThemeIcon(theme) {
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }
}

function toggleTheme() {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    htmlElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
}

// ============================================
// MOBILE NAVBAR TOGGLE
// ============================================

const navbarToggle = document.getElementById('navbarToggle');
const navbarMenu = document.getElementById('navbarMenu');

if (navbarToggle && navbarMenu) {
    navbarToggle.addEventListener('click', () => {
        navbarMenu.classList.toggle('active');
    });
}

// ============================================
// DROPDOWN MENUS
// ============================================

const dropdownTriggers = document.querySelectorAll('.dropdown-trigger');

dropdownTriggers.forEach(trigger => {
    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const dropdown = trigger.closest('.dropdown');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        // Close all other dropdowns
        document.querySelectorAll('.dropdown-menu.show').forEach(openMenu => {
            if (openMenu !== menu) {
                openMenu.classList.remove('show');
            }
        });
        
        menu.classList.toggle('show');
    });
});

// Close dropdowns when clicking outside
document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
    });
});

// ============================================
// ALERT DISMISS
// ============================================

const alertCloseButtons = document.querySelectorAll('.alert-close');

alertCloseButtons.forEach(button => {
    button.addEventListener('click', () => {
        const alert = button.closest('.alert');
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    });
});

// Auto-dismiss alerts after 5 seconds
document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
});

// ============================================
// FORM VALIDATION HELPERS
// ============================================

function validateEmail(email) {
    const re = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[0-9]{9,12}$/;
    return re.test(phone);
}

function showError(input, message) {
    const formGroup = input.closest('.form-group');
    const existingError = formGroup.querySelector('.error-message');
    
    if (existingError) existingError.remove();
    
    input.classList.add('error');
    const error = document.createElement('small');
    error.className = 'error-message';
    error.style.color = 'var(--danger)';
    error.style.fontSize = '0.75rem';
    error.style.marginTop = '0.25rem';
    error.textContent = message;
    formGroup.appendChild(error);
}

function clearError(input) {
    input.classList.remove('error');
    const formGroup = input.closest('.form-group');
    const error = formGroup.querySelector('.error-message');
    if (error) error.remove();
}

// ============================================
// LOADING STATES
// ============================================

function showLoading(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.dataset.originalText = originalText;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';
}

function hideLoading(button) {
    button.disabled = false;
    button.innerHTML = button.dataset.originalText || 'Continuar';
}

// ============================================
// IMAGE UPLOAD PREVIEW
// ============================================

function setupImagePreview(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (input && preview) {
        input.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

// ============================================
// PRICE FORMATTER
// ============================================

function formatPrice(price) {
    return new Intl.NumberFormat('pt-AO', {
        style: 'currency',
        currency: 'AOA',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

// ============================================
// SEARCH FUNCTIONALITY
// ============================================

function setupLiveSearch(inputId, resultsContainerId, searchUrl) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(resultsContainerId);
    let debounceTimer;
    
    if (input && container) {
        input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(async () => {
                const query = e.target.value;
                if (query.length >= 2) {
                    try {
                        const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);
                        const data = await response.json();
                        renderSearchResults(data, container);
                    } catch (error) {
                        console.error('Search error:', error);
                    }
                } else if (query.length === 0) {
                    container.innerHTML = '';
                }
            }, 300);
        });
    }
}

// ============================================
// INITIALIZE ALL
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) mainContent.classList.add('fade-in');
    
    // Setup image previews if they exist
    setupImagePreview('photo_input', 'photo_preview');
    
    console.log('Casa Direta - Plataforma carregada com sucesso! 🏠');
});


// Atualizar contagem de favoritos
function updateFavoritesCount() {
    fetch('/favorites/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('favoritesCount');
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        });
}

// Chamar ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('favoritesCount')) {
        updateFavoritesCount();
    }
});