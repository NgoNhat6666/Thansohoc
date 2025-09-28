class NumerusApp {
    constructor() {
        this.baseURL = '';
        this.currentAnalysis = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSystems();
        this.loadMetrics();
        this.initSmoothScrolling();
        this.initMobileMenu();
    }

    setupEventListeners() {
        const form = document.getElementById('numerologyForm');
        const exportBtn = document.getElementById('exportHTML');
        const shareBtn = document.getElementById('shareResult');

        if (form) {
            form.addEventListener('submit', (e) => this.handleAnalyze(e));
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportHTML());
        }

        if (shareBtn) {
            shareBtn.addEventListener('click', () => this.shareResult());
        }
    }

    async loadSystems() {
        try {
            const response = await fetch('/v1/systems');
            const data = await response.json();
            this.renderSystems(data.systems);
        } catch (error) {
            console.error('Error loading systems:', error);
        }
    }

    renderSystems(systems) {
        const grid = document.getElementById('systemsGrid');
        if (!grid) return;

        const systemDescriptions = {
            'pythagorean': 'Hệ thống phổ biến nhất, dựa trên các nguyên tắc của Pythagoras. Sử dụng số từ 1-9 để phân tích tính cách và vận mệnh.',
            'chaldean': 'Hệ thống cổ xưa từ Babylon, được coi là chính xác nhất. Sử dụng số từ 1-8, bỏ qua số 9.',
            'hebrew_gematria': 'Hệ thống truyền thống Do Thái, gán giá trị số cho các chữ cái Hebrew để giải thích ý nghĩa sâu xa.',
            'greek_isopsephy': 'Hệ thống Hy Lạp cổ đại, tương tự Gematria nhưng sử dụng bảng chữ cái Hy Lạp.',
            'arabic_abjad': 'Hệ thống truyền thống Ả Rập, sử dụng giá trị số của các chữ cái Ả Rập để phân tích.',
            'vietnamese_latin': 'Hệ thống được điều chỉnh đặc biệt cho tiếng Việt, xử lý dấu và ký tự đặc biệt.'
        };

        grid.innerHTML = systems.map(system => `
            <div class="system-card">
                <h3>${system.name}</h3>
                <p>${systemDescriptions[system.id] || 'Hệ thống thần số học chuyên biệt với phương pháp tính toán độc đáo.'}</p>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #eee;">
                    <small style="color: #666;">ID: ${system.id}</small>
                </div>
            </div>
        `).join('');
    }

    async loadMetrics() {
        try {
            const response = await fetch('/v1/metrics');
            const data = await response.json();
            this.updateMetrics(data);
        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }

    updateMetrics(metrics) {
        const totalRequestsEl = document.getElementById('totalRequests');
        const successRateEl = document.getElementById('successRate');
        const avgResponseTimeEl = document.getElementById('avgResponseTime');

        if (totalRequestsEl) {
            totalRequestsEl.querySelector('.stat-number').textContent = 
                metrics.requests?.total || 0;
        }

        if (successRateEl) {
            successRateEl.querySelector('.stat-number').textContent = 
                (metrics.requests?.success_rate_percent || 0) + '%';
        }

        if (avgResponseTimeEl) {
            avgResponseTimeEl.querySelector('.stat-number').textContent = 
                Math.round(metrics.response_time_ms?.average || 0) + 'ms';
        }
    }

    async handleAnalyze(event) {
        event.preventDefault();
        
        const data = {
            full_name: document.getElementById('fullName').value,
            date_of_birth: document.getElementById('dateOfBirth').value,
            gender: document.getElementById('gender').value || null,
            system: document.getElementById('system').value,
            detailed: document.getElementById('detailed').checked
        };

        console.log('Analyzing with data:', data); // Debug log

        if (!data.full_name || !data.date_of_birth || !data.system) {
            this.showError('Vui lòng điền đầy đủ thông tin bắt buộc!');
            return;
        }

        this.showLoading(true);
        this.hideResults();

        try {
            const response = await fetch('/v1/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.currentAnalysis = { data, result };
            this.showResults(result, data);
            this.loadMetrics(); // Refresh metrics

        } catch (error) {
            console.error('Analysis error:', error);
            this.showError('Có lỗi xảy ra trong quá trình phân tích. Vui lòng thử lại!');
        } finally {
            this.showLoading(false);
        }
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.classList.toggle('hidden', !show);
        }
    }

    hideResults() {
        const results = document.getElementById('results');
        if (results) {
            results.classList.add('hidden');
        }
    }

    showResults(result, inputData) {
        const resultsDiv = document.getElementById('results');
        const contentDiv = document.getElementById('resultsContent');
        
        if (!resultsDiv || !contentDiv) return;

        // Create number cards
        const numbers = result.numbers;
        const numberCards = `
            <div class="number-cards">
                <div class="number-card">
                    <h4>🛤️ Số Đường Đời</h4>
                    <div class="number">${numbers.life_path}</div>
                    <p>Con đường cuộc đời</p>
                </div>
                <div class="number-card">
                    <h4>🎭 Số Biểu Đạt</h4>
                    <div class="number">${numbers.expression}</div>
                    <p>Cách thể hiện bản thân</p>
                </div>
                <div class="number-card">
                    <h4>💫 Số Linh Hồn</h4>
                    <div class="number">${numbers.soul_urge}</div>
                    <p>Khao khát nội tâm</p>
                </div>
                <div class="number-card">
                    <h4>🎯 Số Cá Tính</h4>
                    <div class="number">${numbers.personality}</div>
                    <p>Ấn tượng đầu tiên</p>
                </div>
                <div class="number-card">
                    <h4>🌟 Số Trưởng Thành</h4>
                    <div class="number">${numbers.maturity}</div>
                    <p>Mục tiêu lớn trong đời</p>
                </div>
                <div class="number-card">
                    <h4>📅 Năm Cá Nhân</h4>
                    <div class="number">${numbers.personal_year}</div>
                    <p>Năm ${new Date().getFullYear()}</p>
                </div>
            </div>
        `;

        let reportContent = '';
        if (result.report) {
            const sections = [
                { key: 'overview', title: '📋 Tổng Quan', icon: '📋' },
                { key: 'life_path', title: '🛤️ Đường Đời', icon: '🛤️' },
                { key: 'expression', title: '🎭 Biểu Đạt', icon: '🎭' },
                { key: 'soul_urge', title: '💫 Linh Hồn', icon: '💫' },
                { key: 'personality', title: '🎯 Cá Tính', icon: '🎯' },
                { key: 'challenges', title: '⚡ Thử Thách', icon: '⚡' },
                { key: 'advice', title: '💡 Lời Khuyên', icon: '💡' }
            ];

            reportContent = sections
                .filter(section => result.report[section.key])
                .map(section => `
                    <div class="report-section">
                        <h4>${section.title}</h4>
                        <div class="report-content">${result.report[section.key]}</div>
                    </div>
                `).join('');
        }

        // Additional details
        const additionalInfo = `
            <div class="report-section">
                <h4>🔢 Chi Tiết Khác</h4>
                <div class="report-content">
                    <p><strong>Hệ thống:</strong> ${result.system}</p>
                    <p><strong>Đỉnh cao cuộc đời:</strong> ${numbers.pinnacles?.join(', ') || 'N/A'}</p>
                    <p><strong>Thử thách:</strong> ${numbers.challenges?.join(', ') || 'N/A'}</p>
                    ${numbers.karmic_lessons?.length ? `<p><strong>Bài học nghiệp:</strong> ${numbers.karmic_lessons.join(', ')}</p>` : ''}
                </div>
            </div>
        `;

        contentDiv.innerHTML = `
            <div style="margin-bottom: 2rem;">
                <h4 style="color: var(--primary); margin-bottom: 1rem;">🎯 Kết quả cho: ${inputData.full_name}</h4>
                <p style="color: #666;">Ngày sinh: ${inputData.date_of_birth} | Hệ thống: ${result.system}</p>
            </div>
            ${numberCards}
            ${reportContent}
            ${additionalInfo}
        `;

        resultsDiv.classList.remove('hidden');
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    async exportHTML() {
        if (!this.currentAnalysis) {
            this.showError('Không có dữ liệu để xuất!');
            return;
        }

        try {
            const response = await fetch('/v1/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentAnalysis.data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const htmlContent = await response.text();
            
            // Create and download file
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `numerology-report-${this.currentAnalysis.data.full_name.replace(/\s+/g, '-')}.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showSuccess('Báo cáo HTML đã được tải xuống!');

        } catch (error) {
            console.error('Export error:', error);
            this.showError('Có lỗi xảy ra khi xuất báo cáo!');
        }
    }

    shareResult() {
        if (!this.currentAnalysis) {
            this.showError('Không có dữ liệu để chia sẻ!');
            return;
        }

        const result = this.currentAnalysis.result;
        const data = this.currentAnalysis.data;
        const numbers = result.numbers;

        const shareText = `🔢 Kết quả thần số học của ${data.full_name}:
🛤️ Số Đường Đời: ${numbers.life_path}
🎭 Số Biểu Đạt: ${numbers.expression}
💫 Số Linh Hồn: ${numbers.soul_urge}
🎯 Số Cá Tính: ${numbers.personality}

Phân tích bằng Numerus - Ứng dụng thần số học chuyên nghiệp`;

        if (navigator.share) {
            navigator.share({
                title: 'Kết quả Thần Số Học',
                text: shareText,
                url: window.location.href
            }).catch(console.error);
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(shareText).then(() => {
                this.showSuccess('Đã sao chép kết quả vào clipboard!');
            }).catch(() => {
                this.showError('Không thể sao chép. Vui lòng thử lại!');
            });
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelectorAll('.notification');
        existing.forEach(el => el.remove());

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
        `;

        switch (type) {
            case 'success':
                notification.style.background = 'var(--accent)';
                break;
            case 'error':
                notification.style.background = 'var(--danger)';
                break;
            default:
                notification.style.background = 'var(--info)';
        }

        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    initSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    initMobileMenu() {
        const hamburger = document.querySelector('.hamburger');
        const navMenu = document.querySelector('.nav-menu');

        if (hamburger && navMenu) {
            hamburger.addEventListener('click', () => {
                hamburger.classList.toggle('active');
                navMenu.classList.toggle('active');
            });

            // Close menu when clicking on a link
            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', () => {
                    hamburger.classList.remove('active');
                    navMenu.classList.remove('active');
                });
            });
        }
    }
}

// Additional CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }

    .hamburger.active span:nth-child(1) {
        transform: rotate(-45deg) translate(-5px, 6px);
    }
    
    .hamburger.active span:nth-child(2) {
        opacity: 0;
    }
    
    .hamburger.active span:nth-child(3) {
        transform: rotate(45deg) translate(-5px, -6px);
    }
`;
document.head.appendChild(style);

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.numerusApp = new NumerusApp();
});

// Auto refresh metrics every 30 seconds
setInterval(() => {
    if (window.numerusApp) {
        window.numerusApp.loadMetrics();
    }
}, 30000);