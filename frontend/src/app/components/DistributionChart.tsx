import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Filler,
    Tooltip,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register Chart.js components once
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

interface DistributionChartProps {
    percentiles: {
        p5: number;
        p25: number;
        p50: number;
        p75: number;
        p95: number;
    };
    mean: number;
}

const DistributionChart: React.FC<DistributionChartProps> = ({ percentiles, mean }) => {
    // Guard: if percentiles are missing or invalid, show text-only fallback
    if (
        !percentiles ||
        typeof percentiles.p5 !== 'number' ||
        typeof percentiles.p50 !== 'number' ||
        typeof percentiles.p95 !== 'number'
    ) {
        return (
            <div style={{
                padding: 'var(--space-xl)',
                textAlign: 'center',
                color: 'var(--color-text-muted)',
                fontStyle: 'italic'
            }}>
                No distribution data available for this analysis.
            </div>
        );
    }

    // Build a bell-curve-like shape from the 5 percentile points
    // Y values approximate relative density (higher near median)
    const labels = ['P5', 'P25', 'P50', 'P75', 'P95'];
    const xValues = [
        percentiles.p5,
        percentiles.p25,
        percentiles.p50,
        percentiles.p75,
        percentiles.p95,
    ].map((v) => (v * 100).toFixed(1) + '%');

    // Approximate density: peaks at P50, tapers at extremes
    const densityValues = [0.10, 0.55, 1.0, 0.55, 0.10];

    const data = {
        labels: labels.map((l, i) => `${l} (${xValues[i]})`),
        datasets: [
            {
                data: densityValues,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#6366f1',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600 } as const,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#e2e8f0',
                borderColor: 'rgba(99, 102, 241, 0.5)',
                borderWidth: 1,
                callbacks: {
                    label: (ctx: any) => {
                        const pctValues = [percentiles.p5, percentiles.p25, percentiles.p50, percentiles.p75, percentiles.p95];
                        return `Probability: ${(pctValues[ctx.dataIndex] * 100).toFixed(1)}%`;
                    },
                },
            },
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: 'rgba(255, 255, 255, 0.5)', font: { size: 11 } },
            },
            y: {
                display: false,
            },
        },
    };

    return (
        <div style={{ padding: 'var(--space-lg) 0' }}>
            <div style={{ height: '200px', position: 'relative' }}>
                <Line data={data} options={options} />
            </div>

            <p style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                textAlign: 'center',
                fontStyle: 'italic',
                marginTop: 'var(--space-md)'
            }}>
                Mean outcome: {(mean * 100).toFixed(1)}% probability — Spread:{' '}
                {((percentiles.p95 - percentiles.p5) * 100).toFixed(1)}pp
                ({percentiles.p95 - percentiles.p5 > 0.4 ? 'high' : percentiles.p95 - percentiles.p5 > 0.2 ? 'moderate' : 'low'} variance)
            </p>
        </div>
    );
};

export default DistributionChart;
