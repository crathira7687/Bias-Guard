// BiasGuard - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadSection = document.getElementById('uploadSection');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    const downloadBtn = document.getElementById('downloadBtn');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    const errorMessage = document.getElementById('errorMessage');

    // Drag and drop handlers
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // Handle file upload
    async function handleFile(file) {
        if (!file.name.endsWith('.csv')) {
            showError('Please upload a CSV file');
            return;
        }

        // Hide error
        hideError();
        
        // Show loading
        uploadSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        resultsSection.classList.add('hidden');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const contentType = response.headers.get('content-type');
            let data;
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                throw new Error('Server returned invalid response: ' + text.substring(0, 200));
            }

            if (data.success) {
                displayResults(data);
            } else {
                showError(data.error || 'An unknown error occurred');
                resetToUpload();
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Error: ' + error.message);
            resetToUpload();
        }
    }

    function showError(message) {
        const errorEl = document.getElementById('errorMessage');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
        } else {
            alert(message);
        }
    }

    function hideError() {
        const errorEl = document.getElementById('errorMessage');
        if (errorEl) {
            errorEl.classList.add('hidden');
            errorEl.textContent = '';
        }
    }

    // Display results
    function displayResults(data) {
        loadingSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');

        // Update fairness score
        const score = data.fairness_score;
        const scoreCircle = document.getElementById('scoreCircle');
        const fairnessScoreEl = document.getElementById('fairnessScore');
        const biasLevelEl = document.getElementById('biasLevel');
        const biasDescEl = document.getElementById('biasDescription');

        fairnessScoreEl.textContent = Math.round(score);

        // Set colors based on bias level
        let color;
        if (score >= 80) {
            color = '#22C55E'; // Green
            biasLevelEl.textContent = 'Low Bias Detected';
            biasDescEl.textContent = 'Your hiring algorithm shows minimal bias. Great job!';
        } else if (score >= 50) {
            color = '#F59E0B'; // Orange
            biasLevelEl.textContent = 'Moderate Bias Detected';
            biasDescEl.textContent = 'Some bias patterns detected. Consider using our mitigation.';
        } else {
            color = '#EF4444'; // Red
            biasLevelEl.textContent = 'High Bias Detected';
            biasDescEl.textContent = 'Significant bias detected. We recommend applying mitigation.';
        }

        scoreCircle.style.background = `conic-gradient(${color} ${score * 3.6}deg, #E2E8F0 ${score * 3.6}deg)`;

        // Update stats
        document.getElementById('totalCandidates').textContent = data.report.total_candidates;
        document.getElementById('originalRate').textContent = (data.original_hiring_rate * 100).toFixed(1) + '%';
        document.getElementById('mitigatedRate').textContent = (data.mitigated_hiring_rate * 100).toFixed(1) + '%';

        // Update chart
        if (data.chart_url) {
            const chartImg = document.getElementById('chartImage');
            if (chartImg) {
                chartImg.src = data.chart_url + '?t=' + Date.now();
                chartImg.style.display = 'inline-block';
            }
        }

        // Display detailed report
        displayDetailedReport(data.report);

        // Set download URL
        if (downloadBtn && data.download_url) {
            downloadBtn.onclick = () => {
                window.location.href = data.download_url;
            };
        }
    }

    // Display detailed report
    function displayDetailedReport(report) {
        // Gender metrics
        const genderDiv = document.getElementById('genderMetrics');
        if (genderDiv) {
            genderDiv.innerHTML = '';
            
            if (report.gender) {
                for (const [key, value] of Object.entries(report.gender)) {
                    if (key.startsWith('rate_')) {
                        const gender = key.replace('rate_', '');
                        const row = document.createElement('div');
                        row.className = 'metric-row';
                        
                        let valueClass = '';
                        if (value >= 0.35 && value <= 0.55) {
                            valueClass = 'good';
                        } else if (value >= 0.25 && value <= 0.65) {
                            valueClass = 'warning';
                        } else {
                            valueClass = 'danger';
                        }
                        
                        row.innerHTML = `
                            <span class="metric-label">${gender}</span>
                            <span class="metric-value ${valueClass}">${(value * 100).toFixed(1)}%</span>
                        `;
                        genderDiv.appendChild(row);
                    }
                }
            }
        }

        // Race metrics
        const raceDiv = document.getElementById('raceMetrics');
        if (raceDiv) {
            raceDiv.innerHTML = '';
            
            if (report.race) {
                for (const [key, value] of Object.entries(report.race)) {
                    if (key.startsWith('rate_')) {
                        const race = key.replace('rate_', '');
                        const row = document.createElement('div');
                        row.className = 'metric-row';
                        
                        let valueClass = '';
                        if (value >= 0.35 && value <= 0.55) {
                            valueClass = 'good';
                        } else if (value >= 0.25 && value <= 0.65) {
                            valueClass = 'warning';
                        } else {
                            valueClass = 'danger';
                        }
                        
                        row.innerHTML = `
                            <span class="metric-label">${race}</span>
                            <span class="metric-value ${valueClass}">${(value * 100).toFixed(1)}%</span>
                        `;
                        raceDiv.appendChild(row);
                    }
                }
            }
        }

        // Age metrics
        const ageDiv = document.getElementById('ageMetrics');
        if (ageDiv) {
            ageDiv.innerHTML = '';
            
            if (report.age) {
                for (const [key, value] of Object.entries(report.age)) {
                    if (key.startsWith('rate_')) {
                        const age = key.replace('rate_', '');
                        const row = document.createElement('div');
                        row.className = 'metric-row';
                        
                        let valueClass = '';
                        if (value >= 0.35 && value <= 0.55) {
                            valueClass = 'good';
                        } else if (value >= 0.25 && value <= 0.65) {
                            valueClass = 'warning';
                        } else {
                            valueClass = 'danger';
                        }
                        
                        row.innerHTML = `
                            <span class="metric-label">${age}</span>
                            <span class="metric-value ${valueClass}">${(value * 100).toFixed(1)}%</span>
                        `;
                        ageDiv.appendChild(row);
                    }
                }
            }
        }
    }

    // Reset to upload section
    function resetToUpload() {
        loadingSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        fileInput.value = '';
    }

    // New analysis button
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', resetToUpload);
    }
});
