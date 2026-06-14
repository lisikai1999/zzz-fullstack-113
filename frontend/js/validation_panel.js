/**
 * N2YO Validation Panel — live comparison of computed vs N2YO positions.
 */
const ValidationPanel = {
    container: null,
    intervalId: null,
    deviationHistory: [],
    maxHistory: 60,
    chartSvg: null,

    init(containerId) {
        this.container = document.getElementById(containerId);
        this.render();
    },

    render() {
        this.container.innerHTML = `
            <div class="validation-table-container">
                <table class="validation-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Computed</th>
                            <th>N2YO</th>
                            <th>Delta</th>
                        </tr>
                    </thead>
                    <tbody id="validation-tbody">
                        <tr><td colspan="4" style="color: var(--text-secondary)">Click "Start Validation" to begin</td></tr>
                    </tbody>
                </table>
                <div id="validation-status" style="margin-top: 8px; font-size: 11px; color: var(--text-secondary)"></div>
            </div>
            <div class="deviation-chart" id="deviation-chart"></div>
        `;
    },

    async startValidation(noradId, tle, groundStation) {
        this.stopValidation();
        this.deviationHistory = [];

        const statusEl = document.getElementById('validation-status');
        statusEl.textContent = 'Validating...';

        const doCompare = async () => {
            try {
                const result = await API.validateCompare(noradId, tle, groundStation);

                if (result.error) {
                    statusEl.textContent = `Error: ${result.error}`;
                    return;
                }

                this._updateTable(result);
                this._addToHistory(result);
                this._renderChart();

                const status = result.deviation.within_tolerance
                    ? 'PASS (< 0.5 deg)'
                    : 'FAIL (> 0.5 deg)';
                statusEl.innerHTML = `Status: <span class="${result.deviation.within_tolerance ? 'delta-ok' : 'delta-error'}">${status}</span> | Updated: ${new Date().toLocaleTimeString()}`;
            } catch (e) {
                statusEl.textContent = `Error: ${e.message}`;
            }
        };

        await doCompare();
        this.intervalId = setInterval(doCompare, 2000);
    },

    stopValidation() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    },

    _updateTable(result) {
        const tbody = document.getElementById('validation-tbody');
        if (!tbody) return;

        const rows = [
            {
                param: 'Azimuth (deg)',
                computed: result.computed.azimuth_deg.toFixed(4),
                n2yo: result.n2yo.azimuth_deg.toFixed(4),
                delta: result.deviation.azimuth_deg,
            },
            {
                param: 'Elevation (deg)',
                computed: result.computed.elevation_deg.toFixed(4),
                n2yo: result.n2yo.elevation_deg.toFixed(4),
                delta: result.deviation.elevation_deg,
            },
            {
                param: 'Range (km)',
                computed: result.computed.range_km.toFixed(1),
                n2yo: result.n2yo.range_km.toFixed(1),
                delta: Math.abs(result.computed.range_km - result.n2yo.range_km).toFixed(1),
            },
        ];

        tbody.innerHTML = rows.map(r => {
            const deltaClass = r.delta < 0.5 ? 'delta-ok' : r.delta < 1.0 ? 'delta-warn' : 'delta-error';
            return `<tr>
                <td>${r.param}</td>
                <td>${r.computed}</td>
                <td>${r.n2yo}</td>
                <td class="${deltaClass}">${typeof r.delta === 'number' ? r.delta.toFixed(4) : r.delta}</td>
            </tr>`;
        }).join('');
    },

    _addToHistory(result) {
        this.deviationHistory.push({
            time: Date.now(),
            az_delta: result.deviation.azimuth_deg,
            el_delta: result.deviation.elevation_deg,
        });
        if (this.deviationHistory.length > this.maxHistory) {
            this.deviationHistory.shift();
        }
    },

    _renderChart() {
        const container = document.getElementById('deviation-chart');
        if (!container || this.deviationHistory.length < 2) return;

        container.innerHTML = '';
        const width = container.clientWidth || 300;
        const height = 120;
        const margin = { top: 15, right: 10, bottom: 25, left: 35 };

        const svg = d3.select(container).append('svg')
            .attr('width', width)
            .attr('height', height);

        const xScale = d3.scaleLinear()
            .domain([0, this.deviationHistory.length - 1])
            .range([margin.left, width - margin.right]);

        const maxDev = Math.max(
            0.6,
            d3.max(this.deviationHistory, d => Math.max(d.az_delta, d.el_delta))
        );

        const yScale = d3.scaleLinear()
            .domain([0, maxDev])
            .range([height - margin.bottom, margin.top]);

        // 0.5 degree threshold line
        svg.append('line')
            .attr('x1', margin.left)
            .attr('x2', width - margin.right)
            .attr('y1', yScale(0.5))
            .attr('y2', yScale(0.5))
            .attr('stroke', 'var(--accent-red)')
            .attr('stroke-dasharray', '4')
            .attr('opacity', 0.5);

        svg.append('text')
            .attr('x', width - margin.right + 2)
            .attr('y', yScale(0.5) + 3)
            .style('font-size', '8px')
            .style('fill', 'var(--accent-red)')
            .text('0.5');

        // Az line
        const azLine = d3.line()
            .x((d, i) => xScale(i))
            .y(d => yScale(d.az_delta));

        svg.append('path')
            .datum(this.deviationHistory)
            .attr('fill', 'none')
            .attr('stroke', '#58a6ff')
            .attr('stroke-width', 1.5)
            .attr('d', azLine);

        // El line
        const elLine = d3.line()
            .x((d, i) => xScale(i))
            .y(d => yScale(d.el_delta));

        svg.append('path')
            .datum(this.deviationHistory)
            .attr('fill', 'none')
            .attr('stroke', '#a371f7')
            .attr('stroke-width', 1.5)
            .attr('d', elLine);

        // Y axis
        svg.append('g')
            .attr('transform', `translate(${margin.left}, 0)`)
            .call(d3.axisLeft(yScale).ticks(4))
            .selectAll('text')
            .style('font-size', '9px')
            .style('fill', 'var(--text-secondary)');

        // Legend
        svg.append('text').attr('x', margin.left + 5).attr('y', margin.top - 3)
            .style('font-size', '9px').style('fill', '#58a6ff').text('Az');
        svg.append('text').attr('x', margin.left + 25).attr('y', margin.top - 3)
            .style('font-size', '9px').style('fill', '#a371f7').text('El');
        svg.append('text').attr('x', margin.left + 45).attr('y', margin.top - 3)
            .style('font-size', '9px').style('fill', 'var(--text-secondary)').text('Deviation (deg)');
    }
};
