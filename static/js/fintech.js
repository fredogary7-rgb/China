/* ============================================
   TOKENFLOW - Fintech JavaScript Utilities
   Charts, Animations & Interactivity
   ============================================ */

// ============================================
// APPLICATION STATE
// ============================================
const TokenFlow = {
  state: {
    balanceHidden: false,
    currentCurrency: 'XOF',
    isDarkMode: localStorage.getItem('theme') === 'dark',
    originalBalance: 0,
    originalRevenue: 0,
    notifications: [],
    wallet: {
      XOF: 0,
      USD: 0,
      EUR: 0
    }
  },

  // Exchange rates (XOF base)
  exchangeRates: {
    'XOF': { rate: 1, symbol: 'XOF', name: 'Franc CFA' },
    'USD': { rate: 0.0016, symbol: '$', name: 'US Dollar' },
    'EUR': { rate: 0.0015, symbol: '€', name: 'Euro' }
  },

  charts: {},
  observers: []
};

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  TokenFlow.init();
});

TokenFlow.init = function() {
  // Apply saved theme
  if (this.state.isDarkMode) {
    document.documentElement.setAttribute('data-theme', 'dark');
    this.updateDarkModeIcon(true);
  }

  // Initialize components
  this.initCharts();
  this.initSidebar();
  this.initNotifications();
  this.initModals();
  this.initScrollAnimations();
  this.initCopyButtons();
  this.initPaymentMethods();
  this.initFormValidation();
  this.initAutoLoaders();

  // Store original balances from DOM
  const balanceEl = document.getElementById('mainBalance');
  const revenueEl = document.getElementById('revenueValue');
  if (balanceEl) {
    this.state.originalBalance = parseFloat(balanceEl.textContent.replace(/\s/g, '')) || 0;
  }
  if (revenueEl) {
    this.state.originalRevenue = parseFloat(revenueEl.textContent.replace(/[\sXOF€$]/g, '')) || 0;
  }

  // Show welcome modal on first visit
  if (!localStorage.getItem('welcomeShown') && document.getElementById('welcomeModal')) {
    setTimeout(() => {
      document.getElementById('welcomeModal').classList.add('active');
    }, 500);
  }
};

// ============================================
// CHART.JS CONFIGURATION
// ============================================
TokenFlow.initCharts = function() {
  const chartCanvas = document.getElementById('progressionChart');
  if (!chartCanvas || typeof Chart === 'undefined') return;

  const ctx = chartCanvas.getContext('2d');
  const isDark = this.state.isDarkMode;

  // Create gradient
  const gradientFill = ctx.createLinearGradient(0, 0, 0, 200);
  gradientFill.addColorStop(0, isDark ? 'rgba(99, 102, 241, 0.4)' : 'rgba(99, 102, 241, 0.3)');
  gradientFill.addColorStop(1, isDark ? 'rgba(99, 102, 241, 0.0)' : 'rgba(99, 102, 241, 0.0)');

  // Sample data - can be replaced with real data from backend
  const defaultData = {
    labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin'],
    values: [12000, 19000, 30000, 25000, 32000, 45000]
  };

  this.charts.progression = new Chart(ctx, {
    type: 'line',
    data: {
      labels: defaultData.labels,
      datasets: [{
        label: 'Vos Gains',
        data: defaultData.values,
        borderColor: '#6366F1',
        backgroundColor: gradientFill,
        borderWidth: 3,
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#6366F1',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1E293B',
          titleColor: '#F1F5F9',
          bodyColor: '#CBD5E1',
          padding: 12,
          borderRadius: 12,
          displayColors: false,
          callbacks: {
            label: (context) => `${context.parsed.y.toLocaleString('fr-FR')} XOF`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: isDark ? '#64748B' : '#94A3B8',
            font: { family: 'Plus Jakarta Sans', size: 11 }
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(148, 163, 184, 0.12)',
            drawBorder: false
          },
          ticks: {
            color: isDark ? '#64748B' : '#94A3B8',
            font: { family: 'Plus Jakarta Sans', size: 11 },
            callback: (value) => value >= 1000 ? `${(value / 1000)}K` : value
          }
        }
      }
    }
  });
};

TokenFlow.updateChartTheme = function() {
  if (!this.charts.progression) return;

  const isDark = this.state.isDarkMode;
  const ctx = this.charts.progression.ctx;

  const gradientFill = ctx.createLinearGradient(0, 0, 0, 200);
  gradientFill.addColorStop(0, isDark ? 'rgba(99, 102, 241, 0.4)' : 'rgba(99, 102, 241, 0.3)');
  gradientFill.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

  this.charts.progression.data.datasets[0].backgroundColor = gradientFill;
  this.charts.progression.options.scales.x.ticks.color = isDark ? '#64748B' : '#94A3B8';
  this.charts.progression.options.scales.y.ticks.color = isDark ? '#64748B' : '#94A3B8';
  this.charts.progression.options.scales.y.grid.color = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(148, 163, 184, 0.12)';
  this.charts.progression.update();
};

// ============================================
// AUTO LOADERS FOR BUTTONS
// ============================================
TokenFlow.initAutoLoaders = function() {
  // Intercept all form submissions
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
      const submitBtn = this.querySelector('button[type="submit"], .btn-submit, .btn-buy');
      if (submitBtn) {
        submitBtn.classList.add('btn-loading');
      }
    });
  });

  // Intercept primary action buttons and links that look like buttons
  document.querySelectorAll('.btn-primary, .btn-buy, .btn-submit, .action-item, .btn-details').forEach(btn => {
    btn.addEventListener('click', function(e) {
      // Only add loader if it's not a simple toggle or internal modal trigger
      if (this.tagName === 'A' && this.getAttribute('href') !== '#' && !this.closest('form')) {
        this.classList.add('btn-loading');
      }
    });
  });
};

// ============================================
// BALANCE & CURRENCY
// ============================================
TokenFlow.toggleBalanceVisibility = function() {
  const balanceEl = document.getElementById('mainBalance');
  const toggleBtn = document.getElementById('toggleBalance');
  if (!balanceEl || !toggleBtn) return;

  this.state.balanceHidden = !this.state.balanceHidden;
  const icon = toggleBtn.querySelector('i');

  if (this.state.balanceHidden) {
    balanceEl.textContent = '••••••';
    icon.className = 'fa-solid fa-eye';
    balanceEl.classList.add('blurred');
  } else {
    this.updateBalanceDisplay();
    icon.className = 'fa-solid fa-eye-slash';
    balanceEl.classList.remove('blurred');
  }
};

TokenFlow.changeCurrency = function() {
  const selector = document.getElementById('currencySelector');
  if (!selector) return;

  this.state.currentCurrency = selector.value;
  this.updateBalanceDisplay();
  this.updateRevenueDisplay();
  this.updateChartLabel();
};

TokenFlow.updateBalanceDisplay = function() {
  const balanceEl = document.getElementById('mainBalance');
  const currencyEl = document.getElementById('walletCurrency');
  if (!balanceEl) return;

  if (this.state.balanceHidden) {
    balanceEl.textContent = '••••••';
    return;
  }

  const rate = this.exchangeRates[this.state.currentCurrency];
  const balance = this.state.originalBalance * rate.rate;

  balanceEl.textContent = balance.toLocaleString('fr-FR', {
    minimumFractionDigits: this.state.currentCurrency === 'XOF' ? 0 : 2,
    maximumFractionDigits: this.state.currentCurrency === 'XOF' ? 0 : 2
  });
  if (currencyEl) currencyEl.textContent = rate.symbol;
};

TokenFlow.updateRevenueDisplay = function() {
  const revenueEl = document.getElementById('revenueValue');
  if (!revenueEl) return;

  const rate = this.exchangeRates[this.state.currentCurrency];
  const revenue = this.state.originalRevenue * rate.rate;

  revenueEl.textContent = revenue.toLocaleString('fr-FR', {
    minimumFractionDigits: this.state.currentCurrency === 'XOF' ? 0 : 2,
    maximumFractionDigits: this.state.currentCurrency === 'XOF' ? 0 : 2
  }) + ' ' + rate.symbol;
};

TokenFlow.updateChartLabel = function() {
  if (!this.charts.progression) return;
  this.charts.progression.data.datasets[0].label = `Vos Gains (${this.state.currentCurrency})`;
  this.charts.progression.update();
};

// ============================================
// DARK MODE
// ============================================
TokenFlow.toggleDarkMode = function() {
  this.state.isDarkMode = !this.state.isDarkMode;
  document.documentElement.setAttribute('data-theme', this.state.isDarkMode ? 'dark' : 'light');
  localStorage.setItem('theme', this.state.isDarkMode ? 'dark' : 'light');
  this.updateDarkModeIcon(this.state.isDarkMode);
  this.updateChartTheme();
};

TokenFlow.updateDarkModeIcon = function(isDark) {
  const btn = document.getElementById('darkModeBtn');
  if (!btn) return;
  const icon = btn.querySelector('i');
  icon.className = isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
};

// ============================================
// SIDEBAR
// ============================================
TokenFlow.initSidebar = function() {
  const overlay = document.getElementById('sidebarOverlay');
  if (!overlay) return;

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      this.toggleSidebar();
    }
  });
};

TokenFlow.toggleSidebar = function() {
  const overlay = document.getElementById('sidebarOverlay');
  if (!overlay) return;

  const isActive = overlay.classList.contains('active');
  if (isActive) {
    overlay.classList.remove('active');
  } else {
    overlay.classList.add('active');
  }
};

// ============================================
// NOTIFICATIONS
// ============================================
TokenFlow.initNotifications = function() {
  // Setup click-outside handler
  document.addEventListener('click', (e) => {
    const notifBtn = document.getElementById('notificationBtn');
    const notifPanel = document.getElementById('notificationsPanel');
    if (notifBtn && notifPanel) {
      if (!notifBtn.contains(e.target) && !notifPanel.contains(e.target)) {
        notifPanel.classList.remove('active');
      }
    }
  });
};

TokenFlow.toggleNotifications = function() {
  const panel = document.getElementById('notificationsPanel');
  if (panel) panel.classList.toggle('active');
};

TokenFlow.clearNotifications = function() {
  const items = document.querySelectorAll('.notification-item.unread');
  items.forEach(item => item.classList.remove('unread'));
  const badge = document.querySelector('.icon-btn .badge');
  if (badge) badge.style.display = 'none';
};

TokenFlow.addNotification = function(title, message, type = 'info') {
  const panel = document.getElementById('notificationsPanel');
  if (!panel) return;

  const icons = {
    info: 'fa-info',
    success: 'fa-check',
    warning: 'fa-triangle-exclamation',
    error: 'fa-times'
  };

  const notification = document.createElement('div');
  notification.className = `notification-item unread`;
  notification.innerHTML = `
    <div class="notification-icon ${type}">
      <i class="fa-solid ${icons[type]}"></i>
    </div>
    <div class="notification-content">
      <b>${title}</b>
      <span>${message}</span>
    </div>
  `;

  panel.insertBefore(notification, panel.querySelector('.notifications-header').nextSibling);
  this.showToast(`${title}: ${message}`, type);
};

// ============================================
// MODALS
// ============================================
TokenFlow.initModals = function() {
  // Close modal on backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('active');
      }
    });
  });
};

TokenFlow.closeModal = function(modalId = 'welcomeModal') {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    if (modalId === 'welcomeModal') {
      localStorage.setItem('welcomeShown', 'true');
    }
  }
};

TokenFlow.openModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
};

// ============================================
// TOAST NOTIFICATIONS
// ============================================
TokenFlow.showToast = function(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = {
    success: 'fa-check-circle',
    error: 'fa-exclamation-circle',
    info: 'fa-info-circle',
    warning: 'fa-exclamation-triangle'
  };

  toast.innerHTML = `<i class="fa-solid ${icons[type]}"></i> ${message}`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
};

// ============================================
// COPY FUNCTIONALITY
// ============================================
TokenFlow.initCopyButtons = function() {
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.getAttribute('data-copy');
      this.copyToClipboard(text);
    });
  });
};

TokenFlow.copyToClipboard = function(text) {
  navigator.clipboard.writeText(text).then(() => {
    this.showToast('Copié dans le presse-papier !', 'success');
  }).catch(() => {
    // Fallback
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    this.showToast('Copié dans le presse-papier !', 'success');
  });
};

TokenFlow.copyReferralLink = function() {
  const linkText = document.getElementById('referralLink')?.textContent;
  if (linkText) {
    this.copyToClipboard(linkText);
  }
};

// ============================================
// PAYMENT METHODS
// ============================================
TokenFlow.initPaymentMethods = function() {
  document.querySelectorAll('.payment-method').forEach(method => {
    method.addEventListener('click', () => {
      document.querySelectorAll('.payment-method').forEach(m => m.classList.remove('selected'));
      method.classList.add('selected');
    });
  });
};

// ============================================
// FORM VALIDATION
// ============================================
TokenFlow.initFormValidation = function() {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
      const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
      let valid = true;

      inputs.forEach(input => {
        if (!input.value.trim()) {
          valid = false;
          input.classList.add('error');
          input.style.borderColor = '#EF4444';
        } else {
          input.classList.remove('error');
          input.style.borderColor = '';
        }
      });

      if (!valid) {
        e.preventDefault();
        this.showToast('Veuillez remplir tous les champs obligatoires', 'error');
      }
    });
  });
};

// ============================================
// SCROLL ANIMATIONS
// ============================================
TokenFlow.initScrollAnimations = function() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        
        // Animate progress bars
        const progressFill = entry.target.querySelector('.progress-fill');
        if (progressFill) {
          progressFill.style.transition = 'width 0.8s ease';
        }
        
        // Animate stat cards
        const statValue = entry.target.querySelector('.stat-value');
        if (statValue) {
          this.animateNumber(statValue);
        }
      }
    });
  }, observerOptions);

  // Observe elements
  document.querySelectorAll('.investment-item, .stat-card, .vip-card, .advantage-item').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
  });
};

// Add CSS for animation
const style = document.createElement('style');
style.textContent = `
  .animate-in {
    opacity: 1 !important;
    transform: translateY(0) !important;
  }
`;
document.head.appendChild(style);

TokenFlow.animateNumber = function(element) {
  const finalValue = element.textContent;
  const numericValue = parseFloat(finalValue.replace(/[\s,]/g, ''));
  if (isNaN(numericValue)) return;

  const duration = 1000;
  const startTime = performance.now();

  const animate = (currentTime) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // Ease out cubic
    const currentValue = Math.round(numericValue * eased);

    element.textContent = currentValue.toLocaleString('fr-FR');

    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      element.textContent = finalValue;
    }
  };

  requestAnimationFrame(animate);
};

// ============================================
// INVESTMENT CALCULATOR
// ============================================
TokenFlow.calculateInvestment = function(montant, taux, duree) {
  const revenuJournalier = montant * (taux / 100);
  const revenuTotal = revenuJournalier * duree;
  const roi = ((revenuTotal / montant) * 100).toFixed(2);

  return {
    revenuJournalier,
    revenuTotal,
    roi,
    montant,
    duree
  };
};

// ============================================
// WALLET CONVERSION
// ============================================
TokenFlow.convertAmount = function(amount, fromCurrency, toCurrency) {
  // Convert to XOF first, then to target
  const inXOF = fromCurrency === 'XOF' ? amount : amount / this.exchangeRates[fromCurrency].rate;
  const converted = toCurrency === 'XOF' ? inXOF : inXOF * this.exchangeRates[toCurrency].rate;

  return {
    original: amount,
    from: fromCurrency,
    to: toCurrency,
    result: converted
  };
};

// ============================================
// VIP LEVEL CALCULATOR
// ============================================
TokenFlow.getVIPLevel = function(totalInvested) {
  if (totalInvested >= 500000) return { level: 'Diamond', multiplier: 1.5, color: '#B9F2FF' };
  if (totalInvested >= 200000) return { level: 'Gold', multiplier: 1.3, color: '#FFD700' };
  if (totalInvested >= 50000) return { level: 'Silver', multiplier: 1.15, color: '#C0C0C0' };
  return { level: 'Bronze', multiplier: 1.0, color: '#CD7F32' };
};

// ============================================
// REFERRAL COMMISSION CALCULATOR
// ============================================
TokenFlow.calculateCommission = function(amount, level) {
  const rates = { 1: 0.27, 2: 0.02, 3: 0.01 };
  return amount * (rates[level] || 0);
};

// ============================================
// LIVE DATA UPDATES (Simulated)
// ============================================
TokenFlow.startLiveUpdates = function() {
  // Simulate live profit updates
  setInterval(() => {
    const profitEl = document.querySelector('.revenue-value');
    if (profitEl && !this.state.balanceHidden) {
      const currentValue = this.state.originalRevenue;
      const newValue = currentValue + Math.floor(Math.random() * 100);
      this.state.originalRevenue = newValue;
      this.updateRevenueDisplay();
    }
  }, 30000); // Update every 30 seconds
};

// ============================================
// EXPORT GLOBAL FUNCTIONS
// ============================================
// These are the functions called from HTML onclick handlers
window.toggleBalanceVisibility = () => TokenFlow.toggleBalanceVisibility();
window.changeCurrency = () => TokenFlow.changeCurrency();
window.toggleDarkMode = () => TokenFlow.toggleDarkMode();
window.toggleSidebar = () => TokenFlow.toggleSidebar();
window.toggleNotifications = () => TokenFlow.toggleNotifications();
window.clearNotifications = () => TokenFlow.clearNotifications();
window.closeModal = (id) => TokenFlow.closeModal(id);
window.copyReferralLink = () => TokenFlow.copyReferralLink();
window.showToast = (msg, type) => TokenFlow.showToast(msg, type);

// Make TokenFlow globally available
window.TokenFlow = TokenFlow;