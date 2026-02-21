// Chart.js Configuration and Utilities for EyeCare Admin Dashboard

// Initialize Risk Distribution Pie Chart
function initRiskPieChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low Risk', 'Moderate Risk', 'High Risk'],
            datasets: [{
                data: [data.low || 0, data.moderate || 0, data.high || 0],
                backgroundColor: ['#43A047', '#FB8C00', '#E53935'],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 13,
                            family: "'Segoe UI', sans-serif"
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Initialize Assessments Line Chart
function initAssessmentsLineChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = data.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const values = data.map(item => item.count);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Assessments',
                data: values,
                borderColor: '#1E88E5',
                backgroundColor: 'rgba(30, 136, 229, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#1E88E5',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Initialize Feature Importance Bar Chart
function initFeatureImportanceChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const features = Object.keys(data);
    const importance = Object.values(data);

    // Sort by importance
    const sorted = features.map((feature, i) => ({
        feature: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        importance: importance[i]
    })).sort((a, b) => b.importance - a.importance).slice(0, 10);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(item => item.feature),
            datasets: [{
                label: 'Importance',
                data: sorted.map(item => item.importance),
                backgroundColor: 'rgba(142, 36, 170, 0.8)',
                borderColor: '#8E24AA',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Importance: ${(context.parsed.x * 100).toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: Math.max(...sorted.map(item => item.importance)) * 1.1,
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(0) + '%';
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    ticks: {
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Initialize Confusion Matrix (using Chart.js matrix or custom rendering)
function renderConfusionMatrix(containerId, matrix) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const labels = ['Low', 'Moderate', 'High'];
    
    let html = '<table class="confusion-matrix-table">';
    html += '<thead><tr><th></th>';
    labels.forEach(label => {
        html += `<th>Predicted ${label}</th>`;
    });
    html += '</tr></thead><tbody>';

    matrix.forEach((row, i) => {
        html += `<tr><th>Actual ${labels[i]}</th>`;
        row.forEach((value, j) => {
            const isCorrect = i === j;
            const className = isCorrect ? 'correct' : 'incorrect';
            html += `<td class="${className}">${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    
    container.innerHTML = html;
}

// Initialize Activity Logs Chart
function initActivityChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = data.map(item => item.action);
    const counts = data.map(item => item.count);

    const colors = [
        '#1E88E5', '#E91E63', '#8E24AA', '#009688', 
        '#43A047', '#FB8C00', '#E53935', '#00BCD4'
    ];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Activity Count',
                data: counts,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 0,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        font: {
                            size: 10
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ML Metrics Gauge Chart
function initMetricGauge(canvasId, value, label) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const percentage = (value * 100).toFixed(1);

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [value, 1 - value],
                backgroundColor: ['#1E88E5', '#E9ECEF'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        },
        plugins: [{
            beforeDraw: function(chart) {
                const width = chart.width;
                const height = chart.height;
                const ctx = chart.ctx;
                ctx.restore();
                const fontSize = (height / 80).toFixed(2);
                ctx.font = fontSize + "em sans-serif";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#212529";
                const text = percentage + "%";
                const textX = Math.round((width - ctx.measureText(text).width) / 2);
                const textY = height / 2;
                ctx.fillText(text, textX, textY);
                
                // Draw label
                ctx.font = (fontSize * 0.5) + "em sans-serif";
                ctx.fillStyle = "#6C757D";
                const labelX = Math.round((width - ctx.measureText(label).width) / 2);
                const labelY = height / 2 + (fontSize * 20);
                ctx.fillText(label, labelX, labelY);
                ctx.save();
            }
        }]
    });
}

// Export chart data to CSV
function exportChartToCSV(data, filename) {
    let csv = '';
    
    if (Array.isArray(data) && data.length > 0) {
        // Get headers
        const headers = Object.keys(data[0]);
        csv += headers.join(',') + '\n';
        
        // Get rows
        data.forEach(row => {
            csv += headers.map(header => row[header]).join(',') + '\n';
        });
    }
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'chart_data.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Styles for Confusion Matrix
const style = document.createElement('style');
style.textContent = `
.confusion-matrix-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.confusion-matrix-table th,
.confusion-matrix-table td {
    padding: 16px;
    text-align: center;
    border: 1px solid #DEE2E6;
}

.confusion-matrix-table thead th {
    background: #F8F9FA;
    font-weight: 600;
    color: #495057;
}

.confusion-matrix-table tbody th {
    background: #F8F9FA;
    font-weight: 600;
    color: #495057;
}

.confusion-matrix-table td {
    font-weight: 600;
    font-size: 16px;
}

.confusion-matrix-table td.correct {
    background: rgba(67, 160, 71, 0.1);
    color: #43A047;
}

.confusion-matrix-table td.incorrect {
    background: rgba(229, 57, 53, 0.1);
    color: #E53935;
}
`;
document.head.appendChild(style);
