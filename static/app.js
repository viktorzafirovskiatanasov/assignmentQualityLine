let dailyChart;
let partChart;
let statsCache = [];
let selectedPart = '001PN001';

const chartColors = ['#4f8cff', '#8a63ff', '#15c39a'];

const modalOverlay = document.getElementById('modal-overlay');
const manualTestBtn = document.getElementById('manual-test-btn');
const closeModalBtn = document.getElementById('close-modal-btn');
const manualForm = document.getElementById('manual-test-form');
const liveTimestamp = document.getElementById('live-timestamp');
const statusCheckbox = document.getElementById('status');
const statusLabel = document.getElementById('status-label');

manualTestBtn.addEventListener('click', () => modalOverlay.classList.remove('hidden'));
closeModalBtn.addEventListener('click', () => modalOverlay.classList.add('hidden'));
document.getElementById('view-api-btn').addEventListener('click', () => window.open('/docs', '_blank'));
document.getElementById('view-script-btn').addEventListener('click', () => window.open('/script', '_blank'));
statusCheckbox.addEventListener('change', () => {
    statusLabel.textContent = statusCheckbox.checked ? 'Pass' : 'Fail';
});

function updateClock() {
    liveTimestamp.textContent = new Date().toLocaleString();
}
setInterval(updateClock, 1000);
updateClock();

manualForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const payload = {
        serial_number: document.getElementById('serial_number').value.trim(),
        part_number: document.getElementById('part_number').value,
        status: document.getElementById('status').checked,
    };

    const response = await fetch('/tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const error = await response.json();
        alert(error.detail || 'Could not save record.');
        return;
    }

    manualForm.reset();
    statusCheckbox.checked = true;
    statusLabel.textContent = 'Pass';
    modalOverlay.classList.add('hidden');
    await loadDashboard();
});

async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed for ${url}`);
    }
    return response.json();
}

function renderDailyChart(data) {
    const labels = data.map(item => item.date.slice(5));
    const values = data.map(item => item.count);
    const ctx = document.getElementById('dailyChart');

    if (dailyChart) dailyChart.destroy();

    dailyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Units tested',
                data: values,
                backgroundColor: '#4f8cff',
                borderRadius: 10,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#d4ddf0' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { beginAtZero: true, ticks: { color: '#d4ddf0', precision: 0 }, grid: { color: 'rgba(255,255,255,0.05)' } },
            },
        },
    });
}

function renderPartLegend(stats) {
    const legend = document.getElementById('part-legend');
    legend.innerHTML = '';

    stats.forEach((item, index) => {
        const legendItem = document.createElement('button');
        legendItem.className = `legend-item ${item.part_number === selectedPart ? 'active' : ''}`;
        legendItem.type = 'button';
        legendItem.dataset.partNumber = item.part_number;
        legendItem.innerHTML = `
            <span class="legend-left">
                <span class="swatch" style="background:${chartColors[index]}"></span>
                <span>${item.part_number}</span>
            </span>
            <strong>${item.total_tested}</strong>
        `;
        legendItem.addEventListener('click', () => setSelectedPart(item.part_number));
        legend.appendChild(legendItem);
    });
}

function renderPartChart(stats) {
    const ctx = document.getElementById('partChart');
    const labels = stats.map(item => item.part_number);
    const values = stats.map(item => item.total_tested);

    if (partChart) partChart.destroy();

    partChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: chartColors,
                borderColor: '#101728',
                borderWidth: 3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            onClick: (_, elements) => {
                if (!elements.length) return;
                const clickedIndex = elements[0].index;
                setSelectedPart(labels[clickedIndex]);
            },
        },
    });

    renderPartLegend(stats);
}

function setSelectedPart(partNumber) {
    selectedPart = partNumber;
    renderPartLegend(statsCache);
    updateGauge();
}

function updateGauge() {
    const current = statsCache.find(item => item.part_number === selectedPart) || {
        part_number: selectedPart,
        total_tested: 0,
        passed_units: 0,
        failed_units: 0,
        yield_percentage: 0,
    };

    const value = Number(current.yield_percentage || 0);
    const degrees = Math.round((value / 100) * 360);
    const color = value >= 90 ? '#1fc16b' : value >= 80 ? '#f4c542' : '#ff5d73';

    const gaugeRing = document.getElementById('gauge-ring');
    gaugeRing.style.background = `conic-gradient(${color} ${degrees}deg, rgba(255,255,255,0.08) ${degrees}deg)`;

    document.getElementById('yield-value').textContent = `${Math.round(value)}%`;
    document.getElementById('selected-part-label').textContent = current.part_number;
    document.getElementById('gauge-part').textContent = current.part_number;
    document.getElementById('gauge-total').textContent = current.total_tested;
    document.getElementById('gauge-passed').textContent = current.passed_units;
    document.getElementById('gauge-failed').textContent = current.failed_units;
    document.getElementById('passed-units').textContent = current.passed_units;
    document.getElementById('failed-units').textContent = current.failed_units;

    const totalUnits = statsCache.reduce((sum, item) => sum + item.total_tested, 0);
    document.getElementById('total-units').textContent = totalUnits;
}

async function loadDashboard() {
    const [dailyData, statsData] = await Promise.all([
        fetchJson('/daily'),
        fetchJson('/stats'),
    ]);

    statsCache = statsData;
    const hasSelected = statsCache.some(item => item.part_number === selectedPart);
    if (!hasSelected && statsCache.length) {
        selectedPart = statsCache[0].part_number;
    }

    renderDailyChart(dailyData);
    renderPartChart(statsCache);
    updateGauge();
}

loadDashboard().catch((error) => {
    console.error(error);
    alert('Dashboard failed to load.');
});
