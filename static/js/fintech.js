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
  this.initEnhancedFeatures();
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
// FLUID ANIMATIONS SYSTEM
// ============================================
TokenFlow.Animations = {
  // Smooth scroll to element
  scrollTo: function(element, offset = 0) {
    const target = typeof element === 'string' ? document.querySelector(element) : element;
    if (!target) return;

    const targetPosition = target.offsetTop - offset;
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    });
  },

  // Animate number counting
  animateNumber: function(element, start, end, duration = 1000, formatter = null) {
    if (!element) return;

    const startTime = performance.now();
    const difference = end - start;

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-out)
      const easedProgress = 1 - Math.pow(1 - progress, 3);

      const currentValue = start + (difference * easedProgress);
      const displayValue = formatter ? formatter(currentValue) : Math.round(currentValue);

      element.textContent = displayValue;

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  },

  // Stagger animation for multiple elements
  staggerAnimate: function(elements, animationClass, delay = 100) {
    elements.forEach((element, index) => {
      setTimeout(() => {
        element.classList.add(animationClass);
      }, index * delay);
    });
  },

  // Pulse animation
  pulse: function(element, duration = 500) {
    element.style.animation = `pulse ${duration}ms ease-in-out`;
    setTimeout(() => {
      element.style.animation = '';
    }, duration);
  },

  // Shake animation for errors
  shake: function(element, duration = 500) {
    element.style.animation = `shake ${duration}ms ease-in-out`;
    setTimeout(() => {
      element.style.animation = '';
    }, duration);
  },

  // Bounce animation
  bounce: function(element, duration = 500) {
    element.style.animation = `bounce ${duration}ms ease-in-out`;
    setTimeout(() => {
      element.style.animation = '';
    }, duration);
  },

  // Fade in with slide
  fadeInSlide: function(element, direction = 'up', duration = 600) {
    const directions = {
      up: 'translateY(20px)',
      down: 'translateY(-20px)',
      left: 'translateX(20px)',
      right: 'translateX(-20px)'
    };

    element.style.opacity = '0';
    element.style.transform = directions[direction];
    element.style.transition = `all ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;

    requestAnimationFrame(() => {
      element.style.opacity = '1';
      element.style.transform = 'translate(0, 0)';
    });
  },

  // Morphing loader
  createLoader: function(container, size = 40) {
    const loader = document.createElement('div');
    loader.className = 'morphing-loader';
    loader.style.cssText = `
      width: ${size}px;
      height: ${size}px;
      border: 3px solid var(--border-color);
      border-top: 3px solid var(--primary);
      border-radius: 50%;
      animation: morphing-spin 1s linear infinite;
      margin: 0 auto;
    `;

    if (container) {
      container.innerHTML = '';
      container.appendChild(loader);
    }

    return loader;
  },

  // Success checkmark animation
  showSuccess: function(element) {
    const checkmark = document.createElement('div');
    checkmark.innerHTML = '✓';
    checkmark.style.cssText = `
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%) scale(0);
      color: var(--success);
      font-size: 24px;
      font-weight: bold;
      animation: checkmark-pop 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
    `;

    element.style.position = 'relative';
    element.appendChild(checkmark);

    setTimeout(() => {
      checkmark.remove();
    }, 1000);
  },

  // Ripple effect for buttons
  createRipple: function(event, element) {
    const ripple = document.createElement('div');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    ripple.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      left: ${x}px;
      top: ${y}px;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      transform: scale(0);
      animation: ripple-effect 0.6s linear;
      pointer-events: none;
    `;

    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, 600);
  }
};

// Add CSS animations to document head
const animationStyles = `
  @keyframes morphing-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }

  @keyframes bounce {
    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-10px); }
    60% { transform: translateY(-5px); }
  }

  @keyframes checkmark-pop {
    0% { transform: translate(-50%, -50%) scale(0) rotate(0deg); }
    50% { transform: translate(-50%, -50%) scale(1.2) rotate(180deg); }
    100% { transform: translate(-50%, -50%) scale(1) rotate(360deg); }
  }

  @keyframes ripple-effect {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }

  .animate-on-scroll {
    opacity: 0;
    transform: translateY(30px);
    transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .animate-on-scroll.in-view {
    opacity: 1;
    transform: translateY(0);
  }

  .loading-skeleton {
    background: linear-gradient(90deg, var(--bg-card) 25%, var(--border-color) 50%, var(--bg-card) 75%);
    background-size: 200px 100%;
    animation: loading-shimmer 1.5s infinite;
  }

  @keyframes loading-shimmer {
    0% { background-position: -200px 0; }
    100% { background-position: calc(200px + 100%) 0; }
  }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = animationStyles;
document.head.appendChild(styleSheet);

// Initialize scroll animations
TokenFlow.initScrollAnimations = function() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
      }
    });
  }, observerOptions);

  // Observe elements with scroll animation classes
  document.querySelectorAll('.animate-on-scroll, .scroll-fade-in').forEach(el => {
    observer.observe(el);
  });

  this.observers.push(observer);
};

// Enhanced button interactions
TokenFlow.enhanceButtons = function() {
  document.querySelectorAll('.btn-primary, .btn-secondary, .action-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
      this.Animations.createRipple(e, btn);
    });
  });
};

// Initialize enhanced features
TokenFlow.initEnhancedFeatures = function() {
  this.initScrollAnimations();
  this.enhanceButtons();

  // Animate numbers on page load
  document.querySelectorAll('[data-animate-number]').forEach(el => {
    const target = parseInt(el.dataset.animateNumber);
    this.Animations.animateNumber(el, 0, target, 1500, (num) => Math.round(num).toLocaleString('fr-FR'));
  });

  // Add loading states to forms
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Traitement...';
      }
    });
  });
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