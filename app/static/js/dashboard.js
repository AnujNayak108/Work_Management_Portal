/* Dashboard charts — Chart.js with muted palette */
document.addEventListener('DOMContentLoaded', () => {
  Chart.defaults.color = '#71717a';
  Chart.defaults.borderColor = '#222230';
  Chart.defaults.font.family = 'Inter, sans-serif';
  Chart.defaults.font.size = 11;

  const mutedColors = [
    'rgba(124,124,224,0.5)',
    'rgba(91,185,140,0.5)',
    'rgba(107,156,196,0.5)',
    'rgba(196,164,78,0.5)',
  ];
  const borderColors = ['#7c7ce0', '#5bb98c', '#6b9cc4', '#c4a44e'];

  // Department completion chart
  const deptCtx = document.getElementById('dept-chart');
  if (deptCtx) {
    fetch('/api/dashboard-data').then(r => r.json()).then(data => {
      new Chart(deptCtx, {
        type: 'bar',
        data: {
          labels: data.departments.map(d => d.name),
          datasets: [{
            label: 'Completion %',
            data: data.departments.map(d => d.rate),
            backgroundColor: mutedColors,
            borderColor: borderColors,
            borderWidth: 1,
            borderRadius: 4,
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, max: 100, grid: { color: '#1a1a25' }, ticks: { color: '#52525b' } },
            x: { grid: { display: false }, ticks: { color: '#52525b' } }
          }
        }
      });
    }).catch(() => {});
  }

  // QoQ Trends chart
  const trendsCtx = document.getElementById('trends-chart');
  if (trendsCtx) {
    fetch('/api/analytics/trends').then(r => r.json()).then(data => {
      new Chart(trendsCtx, {
        type: 'line',
        data: {
          labels: ['Q1', 'Q2', 'Q3', 'Q4'],
          datasets: [{
            label: 'Avg Score',
            data: [data.trends.Q1, data.trends.Q2, data.trends.Q3, data.trends.Q4],
            borderColor: '#7c7ce0',
            backgroundColor: 'rgba(124,124,224,0.05)',
            fill: true, tension: 0.4,
            pointRadius: 5, pointHoverRadius: 7,
            pointBackgroundColor: '#7c7ce0',
            pointBorderColor: '#16161c',
            pointBorderWidth: 2,
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#71717a' } } },
          scales: {
            y: { beginAtZero: true, grid: { color: '#1a1a25' }, ticks: { color: '#52525b' } },
            x: { grid: { display: false }, ticks: { color: '#52525b' } }
          }
        }
      });
    }).catch(() => {});
  }

  // Distribution doughnut
  const distCtx = document.getElementById('distribution-chart');
  if (distCtx) {
    fetch('/api/analytics/distribution').then(r => r.json()).then(data => {
      const labels = Object.keys(data.distribution);
      const values = Object.values(data.distribution);
      const colors = ['#7c7ce0', '#5bb98c', '#6b9cc4', '#c4a44e', '#c4616c', '#8b7cc4', '#9ca3af'];
      new Chart(distCtx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length), borderWidth: 0, borderColor: '#16161c' }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { color: '#71717a', padding: 12, font: { size: 11 } } } },
          cutout: '68%',
        }
      });
    }).catch(() => {});
  }

  // Heatmap table
  const heatmapEl = document.getElementById('heatmap-table');
  if (heatmapEl) {
    fetch('/api/analytics/heatmap').then(r => r.json()).then(data => {
      if (!data.heatmap || data.heatmap.length === 0) {
        heatmapEl.innerHTML = '<p class="empty-state">No data available.</p>';
        return;
      }
      let html = '<table><thead><tr><th>Employee</th><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th></tr></thead><tbody>';
      data.heatmap.forEach(row => {
        html += `<tr><td style="color:var(--text-primary);font-weight:500;">${row.employee}</td>`;
        ['Q1','Q2','Q3','Q4'].forEach(q => {
          const v = row.quarters[q];
          const cls = v >= 100 ? 'heat-100' : v >= 75 ? 'heat-75' : v >= 50 ? 'heat-50' : v > 0 ? 'heat-25' : 'heat-0';
          html += `<td><div class="heatmap-cell ${cls}">${v}%</div></td>`;
        });
        html += '</tr>';
      });
      html += '</tbody></table>';
      heatmapEl.innerHTML = html;
    }).catch(() => { heatmapEl.innerHTML = '<p class="empty-state">Failed to load.</p>'; });
  }
});
