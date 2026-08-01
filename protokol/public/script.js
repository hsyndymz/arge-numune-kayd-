let monthlyChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupTabSwitching();
    setupFormHandlers();
    setupAutoCalculations();
    await loadStats();
    await loadProtocols();
    await loadArchivedYears();
    await loadActiveMonths();
}

function setupTabSwitching() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');

            navItems.forEach(i => i.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            item.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

function setupAutoCalculations() {
    const setupForForm = (prefix = '') => {
        const baseCostInput = document.getElementById(prefix + 'base_cost');
        const secondaryCostInput = document.getElementById(prefix + 'secondary_keşif_with_kdv');
        const stampTaxInput = document.getElementById(prefix + 'stamp_tax');
        const kdvInput = document.getElementById(prefix + 'kdv_amount');
        const totalCostKdvInput = document.getElementById(prefix + 'total_cost_with_kdv');
        const turkakInput = document.getElementById(prefix + 'turkak_fee');
        const totalInput = document.getElementById(prefix + 'total_amount');

        const turkakActive = document.getElementById(prefix + 'turkak_active');

        if (!baseCostInput) return;

        const calculate = () => {
            const H = parseFloat(baseCostInput.value) || 0;
            const i = parseFloat(secondaryCostInput.value) || 0;
            const I = H * 0.20;

            // Check if calculation should be active
            const isTurkakActive = turkakActive ? turkakActive.checked : true;
            const K = isTurkakActive ? (H * 0.006) : 0;

            const stamp = H * 0.00948;
            const total = H + I + K + i + stamp;

            kdvInput.value = I.toFixed(2);
            totalCostKdvInput.value = (H + I).toFixed(2);
            turkakInput.value = K.toFixed(2);
            stampTaxInput.value = stamp.toFixed(2);
            totalInput.value = total.toFixed(2);
        };

        baseCostInput.addEventListener('input', calculate);
        secondaryCostInput.addEventListener('input', calculate);
        if (turkakActive) {
            turkakActive.addEventListener('change', calculate);
        }

        // Initial calculation
        calculate();
    };

    setupForForm('');      // Main Form
    setupForForm('edit_'); // Edit Form
}

function setupFormHandlers() {
    // New Protocol Form
    document.getElementById('protocol-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/api/protocols', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (response.ok) {
                showToast('Protokol başarıyla eklendi!', 'success');
                e.target.reset();
                await initApp();
                // Switch to list tab
                document.querySelector('.nav-item[data-tab="protocols"]').click();
            } else {
                showToast('Hata: Kayıt eklenemedi.', 'error');
            }
        } catch (error) {
            showToast('Bağlantı hatası.', 'error');
            console.error('Error saving protocol:', error);
        }
    });

    // Edit Form
    document.getElementById('edit-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        const id = data.id;

        try {
            const response = await fetch(`/api/protocols/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (response.ok) {
                showToast('Kayıt güncellendi.', 'success');
                closeModal();
                await initApp();
            } else {
                showToast('Güncelleme hatası.', 'error');
            }
        } catch (error) {
            showToast('Bağlantı hatası.', 'error');
            console.error('Error updating protocol:', error);
        }
    });

    document.querySelector('.cancel-btn').addEventListener('click', closeModal);
    document.querySelector('.delete-btn').addEventListener('click', async () => {
        const id = document.querySelector('#edit-form input[name="id"]').value;
        if (confirm('Bu kaydı silmek istediğinize emin misiniz?')) {
            try {
                const response = await fetch(`/api/protocols/${id}`, { method: 'DELETE' });
                if (response.ok) {
                    showToast('Kayıt silindi.', 'success');
                    closeModal();
                    await initApp();
                } else {
                    showToast('Silme hatası.', 'error');
                }
            } catch (error) {
                showToast('Bağlantı hatası.', 'error');
                console.error('Error deleting protocol:', error);
            }
        }
    });

    // Excel Export
    document.getElementById('export-excel-btn').addEventListener('click', () => {
        const monthFilter = document.getElementById('month-filter').value;
        let url = '/api/protocols/export';

        // If a month like "Ağustos" is selected, we need to map it to numerical month or 
        // handle the mapping. The user wants "dekont tarihine" (payment_date) which is YYYY-MM-DD.
        // I need to ensure the month filter yields something useful.

        if (monthFilter) {
            url += `?month=${monthFilter}`;
        }

        window.location.href = url;
        showToast('Excel dosyası indiriliyor...', 'success');
    });
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i data-lucide="${type === 'success' ? 'check-circle' : 'alert-circle'}"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('stat-total-count').innerText = stats.total_count;
        document.getElementById('stat-total-revenue').innerText = new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2 }).format(stats.total_revenue);

        renderChart(stats.chart_data);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function renderChart(chartData) {
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    if (monthlyChart) monthlyChart.destroy();

    monthlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Aylık Protokol Sayısı',
                data: chartData.values,
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } }
            }
        }
    });
}

async function loadProtocols() {
    try {
        const response = await fetch('/api/protocols?limit=100');
        const protocols = await response.json();

        renderRecentTable(protocols.slice(0, 10));
        renderFullTable(protocols);
    } catch (error) {
        console.error('Error loading protocols:', error);
    }
}

function renderRecentTable(protocols) {
    const tbody = document.querySelector('#recent-table tbody');
    tbody.innerHTML = '';

    protocols.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.sequence_no || '--'}</td>
            <td>${p.firm || '--'}</td>
            <td>${p.job_description || '--'}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.total_amount)} TL</td>
            <td>${p.protocol_date || '--'}</td>
            <td><span class="status-badge ${p.payment_date ? 'status-paid' : 'status-pending'}">${p.payment_date ? 'Ödendi' : 'Bekliyor'}</span></td>
            <td>
                <div class="table-actions">
                    <button class="action-btn edit-btn" onclick="openEditModal(${p.id})" title="Düzenle"><i data-lucide="edit-3"></i></button>
                    <button class="action-btn pdf-btn" onclick="downloadPDF(${p.id})" title="PDF"><i data-lucide="file-text"></i></button>
                    <button class="action-btn delete-icon-btn" onclick="quickDelete(${p.id})" title="Sil"><i data-lucide="trash-2"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
    lucide.createIcons();
}

function renderFullTable(protocols) {
    const tbody = document.querySelector('#full-protocol-table tbody');
    tbody.innerHTML = '';

    protocols.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.sequence_no || '--'}</td>
            <td>${p.office_record_no || '--'}</td>
            <td>${p.protocol_no || '--'}</td>
            <td>${p.region_no || '--'}</td>
            <td title="${p.firm}">${p.firm ? (p.firm.length > 20 ? p.firm.substring(0, 20) + '...' : p.firm) : '--'}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.base_cost || 0)}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.kdv_amount || 0)}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.secondary_keşif_with_kdv || 0)}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.turkak_fee || 0)}</td>
            <td class="highlight-column">${new Intl.NumberFormat('tr-TR').format(p.total_amount || 0)}</td>
            <td>${p.protocol_date || '--'}</td>
            <td>
                <div class="table-actions">
                    <button class="action-btn edit-btn" onclick="openEditModal(${p.id})" title="Düzenle"><i data-lucide="edit-3"></i></button>
                    <button class="action-btn pdf-btn" onclick="downloadPDF(${p.id})" title="PDF"><i data-lucide="file-text"></i></button>
                    <button class="action-btn delete-icon-btn" onclick="quickDelete(${p.id})" title="Sil"><i data-lucide="trash-2"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
    lucide.createIcons();
}

async function quickDelete(id) {
    if (confirm('Bu kaydı tamamen silmek istediğinize emin misiniz?')) {
        try {
            const response = await fetch(`/api/protocols/${id}`, { method: 'DELETE' });
            if (response.ok) {
                showToast('Kayıt silindi.', 'success');
                await initApp();
            } else {
                showToast('Hata: Kayıt silinemedi.', 'error');
            }
        } catch (error) {
            showToast('Bağlantı hatası.', 'error');
        }
    }
}

function downloadPDF(id) {
    window.location.href = `/api/protocols/${id}/pdf`;
    showToast('PDF Raporu hazırlanıyor...', 'success');
}

async function openEditModal(id) {
    try {
        const response = await fetch(`/api/protocols/${id}`);
        const p = await response.json();
        const form = document.getElementById('edit-form');

        form.querySelector('input[name="id"]').value = p.id;

        // Populate all fields
        const fields = [
            'sequence_no', 'office_record_no', 'protocol_no', 'region_no',
            'sender', 'firm', 'job_description', 'protocol_date',
            'base_cost', 'kdv_amount', 'total_cost_with_kdv', 'secondary_keşif_with_kdv',
            'turkak_fee', 'stamp_tax', 'total_amount', 'payment_date',
            'receipt_no', 'bank_info'
        ];

        fields.forEach(field => {
            const input = document.getElementById('edit_' + field);
            if (input) {
                input.value = p[field] || (input.type === 'number' ? 0 : '');
            }
        });

        // Set TÜRKAK checkbox state
        const turkakActive = document.getElementById('edit_turkak_active');
        if (turkakActive) {
            // Check if fee is explicitly 0 (unchecked) or has value (checked)
            // Default to checked if it's a new record logic, but here it is edit
            // If p.turkak_fee is > 0, check it. If 0, uncheck.
            const currentFee = parseFloat(p.turkak_fee) || 0;
            turkakActive.checked = currentFee > 0;
        }

        document.getElementById('edit-modal').style.display = 'flex';
    } catch (error) {
        console.error('Error fetching protocol for edit:', error);
    }
}

function closeModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

// Month Filter
document.getElementById('month-filter').addEventListener('change', async (e) => {
    const month = e.target.value;
    const response = await fetch(`/api/protocols?limit=100${month ? `&month=${month}` : ''}`);
    const data = await response.json();
    renderFullTable(data);
});

// Global Search
document.getElementById('global-search').addEventListener('input', async (e) => {
    const term = e.target.value;
    if (term.length > 2) {
        const response = await fetch(`/api/protocols?firm=${term}`);
        const data = await response.json();
        renderFullTable(data);
    } else if (term.length === 0) {
        await loadProtocols();
    }
});

// Arşivleme Sistemi
async function loadArchivedYears() {
    try {
        const response = await fetch('/api/protocols/archived-years');
        const years = await response.json();
        const filter = document.getElementById('archive-year-filter');
        filter.innerHTML = '<option value="">Yıl Seçin</option>';
        years.forEach(year => {
            const opt = document.createElement('option');
            opt.value = year;
            opt.textContent = year;
            filter.appendChild(opt);
        });
    } catch (error) {
        console.error('Error loading archived years:', error);
    }
}

async function loadActiveMonths() {
    try {
        const response = await fetch('/api/protocols/active-months');
        const months = await response.json();
        const filter = document.getElementById('month-filter');
        // Keep "Tüm Aylar"
        filter.innerHTML = '<option value="">Tüm Aylar</option>';

        const monthNames = {
            "01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan",
            "05": "Mayıs", "06": "Haziran", "07": "Temmuz", "08": "Ağustos",
            "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık"
        };

        months.forEach(m => {
            // m is YYYY-MM
            const [year, month] = m.split('-');
            const name = `${monthNames[month]} ${year}`;
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = name;
            filter.appendChild(opt);
        });
    } catch (error) {
        console.error('Error loading active months:', error);
    }
}

document.getElementById('archive-year-filter').addEventListener('change', async (e) => {
    const year = e.target.value;
    if (!year) {
        document.querySelector('#archive-protocol-table tbody').innerHTML = '';
        return;
    }
    const response = await fetch(`/api/protocols/archive/${year}`);
    const data = await response.json();
    renderArchiveTable(data);
});

function renderArchiveTable(protocols) {
    const tbody = document.querySelector('#archive-protocol-table tbody');
    tbody.innerHTML = '';

    protocols.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.sequence_no || '--'}</td>
            <td>${p.office_record_no || '--'}</td>
            <td>${p.protocol_no || '--'}</td>
            <td>${p.region_no || '--'}</td>
            <td title="${p.firm}">${p.firm ? (p.firm.length > 20 ? p.firm.substring(0, 20) + '...' : p.firm) : '--'}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.base_cost || 0)}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.kdv_amount || 0)}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.secondary_keşif_with_kdv || 0)}</td>
            <td>${new Intl.NumberFormat('tr-TR').format(p.turkak_fee || 0)}</td>
            <td class="highlight-column">${new Intl.NumberFormat('tr-TR').format(p.total_amount || 0)}</td>
            <td>${p.protocol_date || '--'}</td>
            <td>
                <div class="table-actions">
                    <button class="action-btn pdf-btn" onclick="downloadPDF(${p.id})" title="PDF"><i data-lucide="file-text"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
    lucide.createIcons();
}

document.getElementById('close-year-btn').addEventListener('click', async () => {
    const year = document.getElementById('close-year-input').value;
    if (!year) return showToast('Lütfen bir yıl girin.', 'error');

    if (confirm(`${year} yılına ait TÜM aktif kayıtlar arşivlendi olarak işaretlenecek ve ana listeden kaldırılacaktır. Devam etmek istiyor musunuz?`)) {
        try {
            const response = await fetch(`/api/protocols/close-year?year=${year}`, { method: 'POST' });
            if (response.ok) {
                const res = await response.json();
                showToast(res.message, 'success');
                await initApp();
            } else {
                const err = await response.json();
                showToast(err.detail || 'Hata oluştu.', 'error');
            }
        } catch (error) {
            showToast('Bağlantı hatası.', 'error');
        }
    }
});

// Yıllık Rapor İndirme
document.getElementById('download-annual-detailed').addEventListener('click', () => {
    const year = document.getElementById('archive-year-filter').value;
    if (!year) return showToast('Lütfen arşive eklenmiş bir yıl seçin.', 'error');
    window.location.href = `/api/reports/annual-detailed/${year}`;
});

document.getElementById('download-annual-simplified').addEventListener('click', () => {
    const year = document.getElementById('archive-year-filter').value;
    if (!year) return showToast('Lütfen arşive eklenmiş bir yıl seçin.', 'error');
    window.location.href = `/api/reports/annual-simplified/${year}`;
});
