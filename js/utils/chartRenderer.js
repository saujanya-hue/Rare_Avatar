/**
 * Canvas Chart Drawing Utilities
 */
const ChartRenderer = {
    renderBiomarkerPlot(canvas, labMeasurement) {
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;

        ctx.clearRect(0, 0, w, h);

        const isDark = document.body.classList.contains('dark-theme');
        const bgPlot = isDark ? '#0a0f1d' : '#f8fafc';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(15, 23, 42, 0.08)';
        const textMain = isDark ? '#f0f4f8' : '#0f172a';
        const textMuted = isDark ? '#94a3b8' : '#64748b';
        const cyanColor = isDark ? '#94a3b8' : '#334155';
        const emeraldColor = isDark ? '#10b981' : '#059669';

        const padding = { top: 30, right: 40, bottom: 40, left: 60 };
        const plotW = w - padding.left - padding.right;
        const plotH = h - padding.top - padding.bottom;

        // Background grid
        ctx.fillStyle = bgPlot;
        ctx.fillRect(padding.left, padding.top, plotW, plotH);

        // Border around plot area in light theme
        if (!isDark) {
            ctx.strokeStyle = '#e2e8f0';
            ctx.lineWidth = 1;
            ctx.strokeRect(padding.left, padding.top, plotW, plotH);
        }

        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (plotH / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(padding.left + plotW, y);
            ctx.stroke();
        }

        if (!labMeasurement) {
            ctx.fillStyle = textMuted;
            ctx.font = '14px Plus Jakarta Sans';
            ctx.textAlign = 'center';
            ctx.fillText('Order this laboratory investigation to view trajectory plot', w / 2, h / 2);
            return;
        }

        const unc = labMeasurement.uncertainty;
        const val = labMeasurement.value;
        const ciLow = unc.ci_95_low;
        const ciHigh = unc.ci_95_high;
        const refLow = labMeasurement.ref_low;
        const refHigh = labMeasurement.ref_high;

        const maxScale = Math.max(ciHigh, refHigh) * 1.35;
        const minScale = Math.max(0, Math.min(ciLow, refLow) * 0.7);

        const getY = (v) => padding.top + plotH - ((v - minScale) / (maxScale - minScale)) * plotH;

        // Normal Reference Range Band
        const refY1 = getY(refLow);
        const refY2 = getY(refHigh);
        ctx.fillStyle = isDark ? 'rgba(16, 185, 129, 0.12)' : 'rgba(5, 150, 105, 0.1)';
        ctx.fillRect(padding.left, refY2, plotW, refY1 - refY2);

        ctx.strokeStyle = isDark ? 'rgba(16, 185, 129, 0.4)' : 'rgba(5, 150, 105, 0.4)';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padding.left, refY1); ctx.lineTo(padding.left + plotW, refY1);
        ctx.moveTo(padding.left, refY2); ctx.lineTo(padding.left + plotW, refY2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label reference range
        ctx.fillStyle = emeraldColor;
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'left';
        ctx.fillText(`Ref: ${refLow}-${refHigh} ${labMeasurement.unit}`, padding.left + 8, refY2 - 6);

        // Simulation points: month 0, month 3, month 6, month 12
        const points = [
            { m: 0, v: val, low: ciLow, high: ciHigh },
            { m: 3, v: val * 1.08, low: ciLow * 1.05, high: ciHigh * 1.1 },
            { m: 6, v: val * 1.15, low: ciLow * 1.1, high: ciHigh * 1.2 },
            { m: 12, v: val * 1.28, low: ciLow * 1.18, high: ciHigh * 1.35 }
        ];

        const getX = (m) => padding.left + (m / 12) * plotW;

        // Draw 95% Confidence Interval polygon
        ctx.beginPath();
        ctx.moveTo(getX(points[0].m), getY(points[0].high));
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(getX(points[i].m), getY(points[i].high));
        }
        for (let i = points.length - 1; i >= 0; i--) {
            ctx.lineTo(getX(points[i].m), getY(points[i].low));
        }
        ctx.closePath();
        ctx.fillStyle = isDark ? 'rgba(148, 163, 184, 0.15)' : 'rgba(51, 65, 85, 0.12)';
        ctx.fill();

        // Draw Trajectory Line
        ctx.beginPath();
        ctx.moveTo(getX(points[0].m), getY(points[0].v));
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(getX(points[i].m), getY(points[i].v));
        }
        ctx.strokeStyle = cyanColor;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Draw Nodes
        points.forEach((p, idx) => {
            const x = getX(p.m);
            const y = getY(p.v);

            ctx.fillStyle = isDark ? '#0a0f1d' : '#ffffff';
            ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2); ctx.fill();

            ctx.fillStyle = idx === 0 ? cyanColor : (isDark ? 'rgba(148, 163, 184, 0.6)' : 'rgba(51, 65, 85, 0.6)');
            ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();

            // Value text
            ctx.fillStyle = textMain;
            ctx.font = '10px JetBrains Mono';
            ctx.textAlign = 'center';
            ctx.fillText(`${p.v.toFixed(1)}`, x, y - 10);
        });

        // X-Axis Months
        ctx.fillStyle = textMuted;
        ctx.font = '11px Plus Jakarta Sans';
        ctx.textAlign = 'center';
        [0, 3, 6, 9, 12].forEach(m => {
            ctx.fillText(`M${m}`, getX(m), h - 14);
        });

        // Y-Axis Labels
        ctx.textAlign = 'right';
        ctx.font = '10px JetBrains Mono';
        ctx.fillStyle = textMuted;
        ctx.fillText(`${maxScale.toFixed(0)}`, padding.left - 8, padding.top + 10);
        ctx.fillText(`${minScale.toFixed(0)}`, padding.left - 8, padding.top + plotH);
    },

    renderScenariosPlot(canvas, scenarios) {
        if (!canvas || !scenarios || scenarios.length === 0) return;

        // Auto-detect container width for sharp, responsive rendering
        const parentW = canvas.parentElement ? canvas.parentElement.clientWidth : 0;
        if (parentW > 0) {
            canvas.width = Math.min(1000, Math.max(500, parentW - 32));
        }

        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;

        ctx.clearRect(0, 0, w, h);

        const isDark = document.body.classList.contains('dark-theme');
        const bgPlot = isDark ? '#080c14' : '#f8fafc';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(15, 23, 42, 0.08)';
        const textMuted = isDark ? '#94a3b8' : '#64748b';

        const padding = { top: 40, right: 36, bottom: 44, left: 118 };
        const plotW = w - padding.left - padding.right;
        const plotH = h - padding.top - padding.bottom;

        // Background
        ctx.fillStyle = bgPlot;
        ctx.fillRect(padding.left, padding.top, plotW, plotH);

        // Border around plot area in light theme
        if (!isDark) {
            ctx.strokeStyle = '#e2e8f0';
            ctx.lineWidth = 1;
            ctx.strokeRect(padding.left, padding.top, plotW, plotH);
        }

        // Grid
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (plotH / 4) * i;
            ctx.beginPath(); ctx.moveTo(padding.left, y); ctx.lineTo(padding.left + plotW, y); ctx.stroke();
        }

        const colors = isDark 
            ? ['#94a3b8', '#ef4444', '#f59e0b', '#9d4edd']
            : ['#334155', '#dc2626', '#d97706', '#7c3aed'];

        scenarios.forEach((scen, idx) => {
            if (!scen.trajectory || scen.trajectory.length === 0) return;
            const col = colors[idx % colors.length];

            const getX = (m) => padding.left + (m / 12) * plotW;
            const getY = (score) => padding.top + (1.0 - score) * plotH; // 0.0 bottom, 1.0 top (or severity score)

            // Draw line
            ctx.beginPath();
            scen.trajectory.forEach((pt, i) => {
                const x = getX(pt.month);
                const y = getY(pt.state_score);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.strokeStyle = col;
            ctx.lineWidth = scen.is_active ? 3 : 1.8;
            if (!scen.is_active) ctx.setLineDash([4, 4]);
            else ctx.setLineDash([]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Draw points
            scen.trajectory.forEach((pt) => {
                const x = getX(pt.month);
                const y = getY(pt.state_score);
                ctx.fillStyle = col;
                ctx.beginPath(); ctx.arc(x, y, scen.is_active ? 5 : 3, 0, Math.PI * 2); ctx.fill();
            });
        });

        // X-Axis labels
        ctx.fillStyle = textMuted;
        ctx.font = '11px Plus Jakarta Sans';
        ctx.textAlign = 'center';
        [0, 3, 6, 9, 12].forEach(m => {
            ctx.fillText(`Month ${m}`, padding.left + (m / 12) * plotW, h - 14);
        });

        // Y-Axis labels (Disease Severity Score 0.0 to 1.0)
        ctx.textAlign = 'right';
        ctx.font = '10px JetBrains Mono';
        ctx.fillStyle = '#dc2626';
        ctx.fillText('Severe (1.0)', padding.left - 10, padding.top + 10);
        ctx.fillStyle = textMuted;
        ctx.fillText('Moderate (0.5)', padding.left - 10, padding.top + plotH / 2 + 3);
        ctx.fillStyle = '#059669';
        ctx.fillText('Remission (0.0)', padding.left - 10, padding.top + plotH);

        // Y-Axis Label
        ctx.save();
        ctx.translate(14, padding.top + plotH / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.textAlign = 'center';
        ctx.font = '10px Plus Jakarta Sans';
        ctx.fillStyle = textMuted;
        ctx.fillText('Severity Score', 0, 0);
        ctx.restore();
    }
};
