const SmartHire = {
    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.loadApplications(); // NEW: load applications if on applications page
    },

    setupEventListeners() {
        // Existing form submissions
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit);
        });

        // File upload preview
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', this.handleFileChange);
        });

        // Resume upload
        this.setupResumeUpload();

        // Auto-hide alerts
        this.autoHideAlerts();

        // Mobile menu toggle
        this.setupMobileMenu();
    },

setupResumeUpload() {
  const resumeForm = document.getElementById("resumeForm");
  if (!resumeForm) return;

  resumeForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById("resumeFile");
    const file = fileInput?.files?.[0];
    if (!file) {
      alert("Please select a resume file");
      return;
    }

    // Get job_id: prefer a hidden input on the form; fallback to data attribute
    const jobId =
      resumeForm.querySelector('input[name="job_id"]')?.value ||
      resumeForm.dataset.jobId;

    if (!jobId) {
      alert("Missing job_id; add <input type='hidden' name='job_id' value='{{ job_id }}'> to the form.");
      return;
    }

    const formData = new FormData();
    formData.append("resumeFile", file); // <-- must match backend key
    formData.append("job_id", jobId);

    try {
      const res = await fetch("/upload-resume", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Upload failed");

      const score = data?.candidate?.score ?? data?.score ?? 0;
      const scoreResult = document.getElementById("scoreResult");
      if (scoreResult) scoreResult.textContent = "Your ATS Score: " + score;

      // Optional: refresh candidates list if present
      if (typeof loadCandidates === "function") loadCandidates();
    } catch (err) {
      alert("Error uploading file: " + err.message);
    }
  });
},

async loadApplications() {
    try {
        const response = await fetch('/api/my-applications');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const apps = await response.json();

        const container = document.getElementById("applications-container");
        container.innerHTML = "";

        apps.forEach(app => {
            const div = document.createElement("div");
            div.className = "p-4 border mb-2";
            div.textContent = `${app.job_title} - ${app.status}`;
            container.appendChild(div);
        });
    } catch (err) {
        console.error(err);
        document.getElementById("applications-container").innerHTML =
            `<p class="text-red-500">Error loading applications: ${err.message}</p>`;
    }
},

// Removed duplicate DOMContentLoaded event for loadApplications


    handleFormSubmit(event) {
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            const originalText = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
            
            // Re-enable button after 30 seconds as fallback
            setTimeout(() => {
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }, 30000);
        }
    },

    handleFileChange(event) {
        const input = event.target;
        const file = input.files[0];
        
        if (file) {
            const maxSize = 5 * 1024 * 1024; 
            if (file.size > maxSize) {
                alert('File size must be less than 5MB');
                input.value = '';
                return;
            }

            const allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            if (!allowedTypes.includes(file.type)) {
                alert('Please upload a PDF, TXT, DOC, or DOCX file');
                input.value = '';
                return;
            }

            const fileNameDisplay = document.getElementById('file-name');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = `Selected: ${file.name}`;
                fileNameDisplay.classList.remove('hidden');
            }
        }
    },

    autoHideAlerts() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (!alert.querySelector('.alert-close')) {
                const closeButton = document.createElement('button');
                closeButton.className = 'alert-close ml-auto text-lg hover:opacity-70';
                closeButton.innerHTML = '&times;';
                closeButton.addEventListener('click', () => {
                    alert.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => alert.remove(), 300);
                });
                alert.appendChild(closeButton);
            }

            setTimeout(() => {
                if (alert.parentNode) {
                    alert.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => {
                        if (alert.parentNode) alert.remove();
                    }, 300);
                }
            }, 5000);
        });
    },

    setupMobileMenu() {
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }
    },

    initializeComponents() {
        this.initProgressBars();
        this.initTooltips();
        this.initSearchFilters();
    },

    initProgressBars() {
        const progressBars = document.querySelectorAll('.progress-fill');
        progressBars.forEach(bar => {
            const value = bar.dataset.value || 0;
            const color = this.getScoreColor(value);
            bar.style.width = `${value}%`;
            bar.style.backgroundColor = color;
        });
    },

    getScoreColor(score) {
        if (score >= 80) return '#10b981'; 
        if (score >= 60) return '#f59e0b'; 
        if (score >= 40) return '#f97316'; 
        return '#ef4444'; 
    },

    initTooltips() {
        const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
        tooltipTriggers.forEach(trigger => {
            let tooltip;
            
            trigger.addEventListener('mouseenter', () => {
                const text = trigger.dataset.tooltip;
                tooltip = document.createElement('div');
                tooltip.className = 'absolute z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg pointer-events-none';
                tooltip.textContent = text;
                
                document.body.appendChild(tooltip);
                
                const rect = trigger.getBoundingClientRect();
                tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
                tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
            });
            
            trigger.addEventListener('mouseleave', () => {
                if (tooltip) {
                    tooltip.remove();
                    tooltip = null;
                }
            });
        });
    },

    initSearchFilters() {
        const searchInputs = document.querySelectorAll('[data-search]');
        searchInputs.forEach(input => {
            input.addEventListener('input', this.debounce((event) => {
                const query = event.target.value.toLowerCase();
                const targetSelector = event.target.dataset.search;
                const targets = document.querySelectorAll(targetSelector);
                
                targets.forEach(target => {
                    const text = target.textContent.toLowerCase();
                    const matches = text.includes(query);
                    target.style.display = matches ? '' : 'none';
                });
            }, 300));
        });
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    },

    formatScore(score) {
        return score ? `${score.toFixed(1)}` : 'N/A';
    },

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg max-w-sm ${this.getNotificationClass(type)}`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${this.getNotificationIcon(type)} mr-2"></i>
                <span>${message}</span>
                <button class="ml-auto text-lg hover:opacity-70" onclick="this.parentNode.parentNode.remove()">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    },

    getNotificationClass(type) {
        const classes = {
            success: 'bg-green-100 border border-green-200 text-green-800',
            error: 'bg-red-100 border border-red-200 text-red-800',
            warning: 'bg-yellow-100 border border-yellow-200 text-yellow-800',
            info: 'bg-blue-100 border border-blue-200 text-blue-800'
        };
        return classes[type] || classes.info;
    },

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }
};

// API utilities
const API = {
    async get(url) {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return response.json();
    },

    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return response.json();
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    SmartHire.init();
});

// Expose to global scope
window.SmartHire = SmartHire;
window.API = API;

// Animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-10px); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
`;
document.head.appendChild(style);

