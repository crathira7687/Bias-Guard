/**
 * BiasGuard v2 - Interactive JavaScript
 * Handles file uploads, animations, charts, and user interactions
 */

// State management
const state = {
  file: null,
  results: null,
  charts: {}
};

// DOM Elements
const elements = {
  dropZone: document.getElementById('dropZone'),
  fileInput: document.getElementById('fileInput'),
  uploadSection: document.getElementById('uploadSection'),
  loadingSection: document.getElementById('loadingSection'),
  resultsSection: document.getElementById('resultsSection'),
  scoreCircle: document.getElementById('scoreCircle'),
  fairnessScore: document.getElementById('fairnessScore'),
  biasLevel: document.getElementById('biasLevel'),
  biasDescription: document.getElementById('biasDescription'),
  totalCandidates: document.getElementById('totalCandidates'),
  originalRate: document.getElementById('originalRate'),
  mitigatedRate: document.getElementById('mitigatedRate'),
  chartCanvas: document.getElementById('biasChart'),
  genderMetrics: document.getElementById('genderMetrics'),
  raceMetrics: document.getElementById('raceMetrics'),
  downloadBtn: document.getElementById('downloadBtn'),
  newAnalysisBtn: document.getElementById('newAnalysisBtn')
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);

function init() {
  setupDragAndDrop();
  setupFileInput();
  setupButtons();
  setupAnimations();
}

// Drag and Drop
function setupDragAndDrop() {
  if (!elements.dropZone) return;
  
  const dropZone = elements.dropZone;
  
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });
  
  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }
  
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
  });
  
  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
  });
  
  dropZone.addEventListener('drop', handleDrop, false);
  dropZone.addEventListener('click', () => elements.fileInput?.click());
}

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  handleFiles(files);
}

// File Input
function setupFileInput() {
  if (!elements.fileInput) return;
  
  elements.fileInput.addEventListener('change', function() {
    handleFiles(this.files);
  });
}

function handleFiles(files) {
  if (files.length > 0) {
    const file = files[0];
    if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
      state.file = file;
      uploadFile(file);
    } else {
      showError('Please upload a CSV file');
    }
  }
}

// Upload to server
async function uploadFile(file) {
  showLoading();
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (data.success) {
      state.results = data;
      displayResults(data);
    } else {
      showError(data.error || 'Analysis failed');
    }
  } catch (error) {
    console.error('Upload error:', error);
    showError('Failed to analyze file. Please try again.');
  }
}

// Show sections
function showLoading() {
  elements.uploadSection?.classList.add('hidden');
  elements.loadingSection?.classList.remove('hidden');
  elements.resultsSection?.classList.add('hidden');
}

function showUpload() {
  elements.uploadSection?.classList.remove('hidden');
  elements.loadingSection?.classList.add('hidden');
  elements.resultsSection?.classList.add('hidden');
}

function showResults() {
  elements.uploadSection?.classList.add('hidden');
  elements.loadingSection?.classList.add('hidden');
  elements.resultsSection?.classList.remove('hidden');
}

// Display Results
function displayResults(data) {
  showResults();
  
  // Animate score
  animateScore(data.fairness_score);
  
  // Update stats
  updateStats(data);
  
  // Update bias level
  updateBiasLevel(data);
  
  // Create charts
  createCharts(data);
  
  // Update detailed metrics
  updateMetrics(data);
  
  // Setup download
  if (data.download_url) {
    elements.downloadBtn.onclick = () => window.open(data.download_url, '_blank');
  }
}

function animateScore(targetScore) {
  const duration = 1500;
  const start = 0;
  const startTime = performance.now();
  
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Ease out
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (targetScore - start) * easeOut);
    
    if (elements.fairnessScore) {
      elements.fairnessScore.textContent = current;
    }
    
    // Update circle progress
    if (elements.scoreCircle) {
      const percent = current;
      elements.scoreCircle.style.setProperty('--score', `${percent}%`);
    }
    
    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }
  
  requestAnimationFrame(update);
}

function updateStats(data) {
  if (elements.totalCandidates) {
    elements.totalCandidates.textContent = data.report?.total_candidates || 0;
  }
  
  if (elements.originalRate) {
    const rate = (data.original_hiring_rate * 100).toFixed(1);
    elements.originalRate.textContent = `${rate}%`;
  }
  
  if (elements.mitigatedRate) {
    const rate = (data.mitigated_hiring_rate * 100).toFixed(1);
    elements.mitigatedRate.textContent = `${rate}%`;
  }
}

function updateBiasLevel(data) {
  const level = data.bias_level || 'Unknown';
  const description = getBiasDescription(data);
  
  if (elements.biasLevel) {
    elements.biasLevel.textContent = `${level} Bias Detected`;
    elements.biasLevel.className = level.toLowerCase();
  }
  
  if (elements.biasDescription) {
    elements.biasDescription.textContent = description;
  }
}

function getBiasDescription(data) {
  const score = data.fairness_score;
  
  if (score >= 80) {
    return 'Great job! Your hiring process shows minimal bias. Candidates are evaluated fairly based on qualifications.';
  } else if (score >= 50) {
    return 'Some bias detected. While not extreme, there are opportunities to improve fairness in your hiring process.';
  } else {
    return 'Significant bias detected. We strongly recommend using BiasGuard\'s mitigation to ensure fair candidate evaluation.';
  }
}

// Charts
function createCharts(data) {
  if (!elements.chartCanvas) return;
  
  // Destroy existing chart
  if (state.charts.main) {
    state.charts.main.destroy();
  }
  
  const ctx = elements.chartCanvas.getContext('2d');
  
  // Prepare data
  const report = data.report || {};
  const gender = report.gender || {};
  const race = report.race || {};
  
  // Get labels and values
  const genderLabels = Object.keys(gender).filter(k => k.startsWith('rate_')).map(k => k.replace('rate_', ''));
  const genderValues = Object.keys(gender).filter(k => k.startsWith('rate_')).map(k => (gender[k] * 100).toFixed(1));
  
  const raceLabels = Object.keys(race).filter(k => k.startsWith('rate_')).map(k => k.replace('rate_', ''));
  const raceValues = Object.keys(race).filter(k => k.startsWith('rate_')).map(k => (race[k] * 100).toFixed(1));
  
  // Create combined chart
  state.charts.main = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [...genderLabels, ...raceLabels],
      datasets: [
        {
          label: 'Original Hiring Rate',
          data: [...Array(genderLabels.length).fill(0), ...raceValues.map(v => parseFloat(v))],
          backgroundColor: 'rgba(239, 68, 68, 0.7)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 1,
          borderRadius: 6
        },
        {
          label: 'Mitigated Rate',
          data: genderValues.map(() => (data.mitigated_hiring_rate * 100).toFixed(1)),
          backgroundColor: 'rgba(16, 185, 129, 0.7)',
          borderColor: 'rgba(16, 185, 129, 1)',
          borderWidth: 1,
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#cbd5e1',
            font: { family: 'Sora', size: 12 },
            padding: 20
          }
        },
        tooltip: {
          backgroundColor: 'rgba(30, 30, 45, 0.9)',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(139, 92, 246, 0.3)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#64748b',
            font: { family: 'Sora' }
          }
        },
        y: {
          beginAtZero: true,
          max: 100,
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#64748b',
            font: { family: 'Sora' },
            callback: value => value + '%'
          }
        }
      }
    }
  });
}

// Update detailed metrics
function updateMetrics(data) {
  const report = data.report || {};
  
  // Gender metrics
  if (elements.genderMetrics && report.gender) {
    const gender = report.gender;
    let html = '';
    
    Object.entries(gender).forEach(([key, value]) => {
      if (key.startsWith('rate_')) {
        const group = key.replace('rate_', '');
        const rate = (value * 100).toFixed(1);
        const isGood = value >= 0.4 && value <= 0.6;
        
        html += `
          <div class="metric-row">
            <span class="metric-label">${group}</span>
            <span class="metric-value ${isGood ? 'good' : ''}">${rate}%</span>
          </div>
          <div class="comparison-bar">
            <div class="comparison-fill original" style="width: ${rate}%"></div>
          </div>
        `;
      }
    });
    
    elements.genderMetrics.innerHTML = html;
  }
  
  // Race metrics
  if (elements.raceMetrics && report.race) {
    const race = report.race;
    let html = '';
    
    Object.entries(race).forEach(([key, value]) => {
      if (key.startsWith('rate_')) {
        const group = key.replace('rate_', '');
        const rate = (value * 100).toFixed(1);
        const isGood = value >= 0.4 && value <= 0.6;
        
        html += `
          <div class="metric-row">
            <span class="metric-label">${group}</span>
            <span class="metric-value ${isGood ? 'good' : ''}">${rate}%</span>
          </div>
          <div class="comparison-bar">
            <div class="comparison-fill original" style="width: ${rate}%"></div>
          </div>
        `;
      }
    });
    
    elements.raceMetrics.innerHTML = html;
  }
}

// Buttons
function setupButtons() {
  if (elements.newAnalysisBtn) {
    elements.newAnalysisBtn.addEventListener('click', resetApp);
  }
}

function resetApp() {
  state.file = null;
  state.results = null;
  
  // Destroy charts
  Object.values(state.charts).forEach(chart => {
    if (chart && chart.destroy) chart.destroy();
  });
  state.charts = {};
  
  // Reset file input
  if (elements.fileInput) {
    elements.fileInput.value = '';
  }
  
  showUpload();
}

// Animations
function setupAnimations() {
  // Add scroll animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
      }
    });
  }, observerOptions);
  
  document.querySelectorAll('.stat-card, .report-section').forEach(el => {
    observer.observe(el);
  });
}

// Error handling
function showError(message) {
  showUpload();
  alert(message);
}

// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + U to upload
  if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
    e.preventDefault();
    elements.fileInput?.click();
  }
  
  // Escape to reset
  if (e.key === 'Escape' && state.results) {
    resetApp();
  }
});

// Export for debugging
window.BiasGuard = {
  state,
  reset: resetApp,
  upload: uploadFile
};
