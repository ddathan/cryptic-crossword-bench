/**
 * Cryptic Crossword Evaluation Dashboard
 * Loads and displays evaluation results with a chart and table.
 */

// Configuration
const RESULTS_URL = 'results.json';

// Chart colors
const CHART_COLORS = {
    bar: 'rgba(37, 99, 235, 0.8)',
    barHover: 'rgba(37, 99, 235, 1)',
    error: 'rgba(107, 114, 128, 0.8)',
    grid: 'rgba(229, 231, 235, 1)',
};

/**
 * Format accuracy as percentage
 */
function formatAccuracy(accuracy) {
    return (accuracy * 100).toFixed(1) + '%';
}

/**
 * Format stderr as percentage
 */
function formatStderr(stderr) {
    return (stderr * 100).toFixed(1) + '%';
}

/**
 * Format date for display
 */
function formatDate(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
    });
}

/**
 * Format model args for display
 */
function formatModelArgs(args) {
    if (!args || Object.keys(args).length === 0) return '';
    return Object.entries(args)
        .map(([k, v]) => `${k}=${v}`)
        .join(', ');
}

/**
 * Format token count for display
 */
function formatTokens(tokens) {
    if (!tokens || tokens === 0) return '-';
    return tokens.toLocaleString();
}

/**
 * Format cost in USD for display
 */
function formatCost(cost) {
    if (cost === null || cost === undefined) return '-';
    if (cost < 0.01) return '<$0.01';
    return '$' + cost.toFixed(2);
}

/**
 * Get rank class for styling
 */
function getRankClass(rank) {
    if (rank === 1) return 'rank rank-1';
    if (rank === 2) return 'rank rank-2';
    if (rank === 3) return 'rank rank-3';
    return 'rank';
}

/**
 * Create the results table
 */
function createTable(results) {
    const tbody = document.getElementById('results-body');
    tbody.innerHTML = '';

    results.forEach((result, index) => {
        const rank = index + 1;
        const row = document.createElement('tr');

        row.innerHTML = `
            <td class="${getRankClass(rank)}">${rank}</td>
            <td class="model-name" title="${result.model}">${result.model_display}</td>
            <td class="accuracy">
                <span class="accuracy-value">${formatAccuracy(result.accuracy)}</span>
                <span class="stderr">&plusmn; ${formatStderr(result.stderr)}</span>
            </td>
            <td class="tokens">${formatTokens(result.total_tokens)}</td>
            <td class="cost">${formatCost(result.cost_usd)}</td>
            <td class="date">${formatDate(result.timestamp)}</td>
        `;

        tbody.appendChild(row);
    });
}

/**
 * Create the accuracy chart with error bars
 */
function createChart(results) {
    const ctx = document.getElementById('accuracyChart').getContext('2d');

    // Prepare data
    const labels = results.map(r => r.model_display);
    const accuracies = results.map(r => r.accuracy * 100);
    const stderrs = results.map(r => r.stderr * 100);

    // Create chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Accuracy (%)',
                data: accuracies,
                backgroundColor: CHART_COLORS.bar,
                hoverBackgroundColor: CHART_COLORS.barHover,
                borderRadius: 4,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const idx = context.dataIndex;
                            const acc = accuracies[idx].toFixed(1);
                            const err = stderrs[idx].toFixed(1);
                            return `Accuracy: ${acc}% \u00B1 ${err}%`;
                        },
                        afterLabel: function(context) {
                            const result = results[context.dataIndex];
                            const args = formatModelArgs(result.model_args);
                            if (args) {
                                return `Args: ${args}`;
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Accuracy (%)',
                    },
                    grid: {
                        color: CHART_COLORS.grid,
                    },
                },
                x: {
                    grid: {
                        display: false,
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0,
                    }
                }
            },
        },
        plugins: [{
            // Custom plugin to draw error bars
            id: 'errorBars',
            afterDatasetsDraw: function(chart) {
                const ctx = chart.ctx;
                const meta = chart.getDatasetMeta(0);

                meta.data.forEach((bar, index) => {
                    const stderr = stderrs[index];
                    if (stderr <= 0) return;

                    const x = bar.x;
                    const y = bar.y;
                    const yScale = chart.scales.y;

                    // Calculate error bar positions
                    const errorTop = yScale.getPixelForValue(accuracies[index] + stderr);
                    const errorBottom = yScale.getPixelForValue(accuracies[index] - stderr);
                    const capWidth = 6;

                    // Draw error bar
                    ctx.save();
                    ctx.strokeStyle = CHART_COLORS.error;
                    ctx.lineWidth = 2;

                    // Vertical line
                    ctx.beginPath();
                    ctx.moveTo(x, errorTop);
                    ctx.lineTo(x, errorBottom);
                    ctx.stroke();

                    // Top cap
                    ctx.beginPath();
                    ctx.moveTo(x - capWidth, errorTop);
                    ctx.lineTo(x + capWidth, errorTop);
                    ctx.stroke();

                    // Bottom cap
                    ctx.beginPath();
                    ctx.moveTo(x - capWidth, errorBottom);
                    ctx.lineTo(x + capWidth, errorBottom);
                    ctx.stroke();

                    ctx.restore();
                });
            }
        }]
    });
}

/**
 * Update the generated timestamp
 */
function updateGeneratedAt(timestamp) {
    const elem = document.getElementById('generated-at');
    if (timestamp) {
        const date = new Date(timestamp);
        elem.textContent = `Results generated: ${date.toLocaleString()}`;
    }
}

/**
 * Show the results content
 */
function showResults(data) {
    document.getElementById('loading').style.display = 'none';

    if (!data.results || data.results.length === 0) {
        document.getElementById('no-results').style.display = 'block';
        return;
    }

    document.getElementById('results-content').style.display = 'block';

    createTable(data.results);
    createChart(data.results);
    updateGeneratedAt(data.generated_at);
}

/**
 * Show error state
 */
function showError(error) {
    console.error('Failed to load results:', error);
    document.getElementById('loading').style.display = 'none';
    document.getElementById('no-results').style.display = 'block';
}

/**
 * Initialize the dashboard
 */
async function init() {
    try {
        const response = await fetch(RESULTS_URL);

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();
        showResults(data);
    } catch (error) {
        showError(error);
    }
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
