/**
 * D3.js Antenna Scheduling Gantt Chart
 */
const GanttChart = {
    svg: null,
    width: 0,
    height: 0,
    margin: { top: 30, right: 20, bottom: 40, left: 80 },
    colors: ['#58a6ff', '#a371f7', '#3fb950', '#d29922', '#f85149', '#79c0ff', '#d2a8ff'],
    tooltip: null,

    init(containerId) {
        const container = document.getElementById(containerId);
        this.width = container.clientWidth - 20 || 600;
        this.height = 200;

        this.tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('display', 'none');
    },

    render(scheduleData) {
        const container = document.getElementById('gantt-chart');
        container.innerHTML = '';

        if (!scheduleData || !scheduleData.antennas) {
            container.innerHTML = '<p style="color: var(--text-secondary); padding: 20px;">No schedule data. Run pass prediction first.</p>';
            return;
        }

        const antennaIds = Object.keys(scheduleData.antennas).sort();
        if (antennaIds.length === 0) return;

        // Collect all passes to determine time range
        let allPasses = [];
        antennaIds.forEach(id => {
            scheduleData.antennas[id].forEach(p => {
                allPasses.push({ ...p, antenna: id });
            });
        });

        if (allPasses.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary); padding: 20px;">No passes scheduled.</p>';
            return;
        }

        const conflicts = scheduleData.conflicts || [];

        // Time range
        const minTime = d3.min(allPasses, d => d.aos_unix);
        const maxTime = d3.max(allPasses, d => d.los_unix);

        const height = antennaIds.length * 50 + this.margin.top + this.margin.bottom;
        this.height = height;

        const svg = d3.select(container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', height);

        // Scales
        const xScale = d3.scaleLinear()
            .domain([minTime, maxTime])
            .range([this.margin.left, this.width - this.margin.right]);

        const yScale = d3.scaleBand()
            .domain(antennaIds)
            .range([this.margin.top, height - this.margin.bottom])
            .padding(0.3);

        // Satellite color map
        const satNames = [...new Set(allPasses.map(p => p.satellite_name))];
        const colorMap = {};
        satNames.forEach((name, i) => {
            colorMap[name] = this.colors[i % this.colors.length];
        });

        // X axis (time)
        const timeExtent = maxTime - minTime;
        let tickFormat;
        if (timeExtent < 86400) {
            tickFormat = (d) => {
                const date = new Date(d * 1000);
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            };
        } else {
            tickFormat = (d) => {
                const date = new Date(d * 1000);
                return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit' });
            };
        }

        svg.append('g')
            .attr('class', 'gantt-axis')
            .attr('transform', `translate(0, ${height - this.margin.bottom})`)
            .call(d3.axisBottom(xScale).ticks(8).tickFormat(tickFormat));

        // Y axis (antennas)
        svg.append('g')
            .attr('class', 'gantt-axis')
            .attr('transform', `translate(${this.margin.left}, 0)`)
            .call(d3.axisLeft(yScale).tickFormat(d => `Antenna ${d}`));

        // Draw pass bars
        const self = this;
        svg.selectAll('.gantt-bar')
            .data(allPasses)
            .enter()
            .append('rect')
            .attr('class', 'gantt-bar')
            .attr('x', d => xScale(d.aos_unix))
            .attr('y', d => yScale(d.antenna))
            .attr('width', d => Math.max(2, xScale(d.los_unix) - xScale(d.aos_unix)))
            .attr('height', yScale.bandwidth())
            .attr('fill', d => colorMap[d.satellite_name] || '#58a6ff')
            .attr('opacity', 0.85)
            .on('mouseover', function(event, d) {
                self.tooltip
                    .style('display', 'block')
                    .html(`<b>${d.satellite_name}</b><br>
                           Priority: ${d.priority}<br>
                           Max El: ${d.max_elevation_deg.toFixed(1)} deg<br>
                           Duration: ${Math.round(d.duration_seconds)}s<br>
                           ${new Date(d.aos_unix * 1000).toLocaleTimeString()} - ${new Date(d.los_unix * 1000).toLocaleTimeString()}`);
            })
            .on('mousemove', function(event) {
                self.tooltip
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px');
            })
            .on('mouseout', function() {
                self.tooltip.style('display', 'none');
            });

        // Satellite name labels on bars
        svg.selectAll('.gantt-label')
            .data(allPasses.filter(d => xScale(d.los_unix) - xScale(d.aos_unix) > 30))
            .enter()
            .append('text')
            .attr('class', 'gantt-label')
            .attr('x', d => xScale(d.aos_unix) + 4)
            .attr('y', d => yScale(d.antenna) + yScale.bandwidth() / 2 + 3)
            .text(d => d.satellite_name)
            .style('font-size', '9px')
            .style('pointer-events', 'none');

        // Draw conflicts as dashed red marks on a "Conflicts" row
        if (conflicts.length > 0) {
            svg.append('text')
                .attr('x', 10)
                .attr('y', height - 5)
                .attr('class', 'gantt-label')
                .style('fill', 'var(--accent-red)')
                .text(`${conflicts.length} conflict(s) unscheduled`);
        }

        // Legend
        const legend = svg.append('g')
            .attr('transform', `translate(${this.margin.left + 10}, ${this.margin.top - 20})`);

        satNames.forEach((name, i) => {
            const g = legend.append('g')
                .attr('transform', `translate(${i * 100}, 0)`);
            g.append('rect')
                .attr('width', 10)
                .attr('height', 10)
                .attr('fill', colorMap[name]);
            g.append('text')
                .attr('x', 14)
                .attr('y', 9)
                .style('font-size', '10px')
                .style('fill', 'var(--text-secondary)')
                .text(name);
        });

        // Stats
        if (scheduleData.stats) {
            const stats = scheduleData.stats;
            container.insertAdjacentHTML('beforeend',
                `<div style="font-size: 11px; color: var(--text-secondary); padding: 4px 0;">
                    Scheduled: ${stats.scheduled}/${stats.total_passes} passes |
                    Conflicts: ${stats.conflicted} |
                    Utilization: ${stats.utilization_percent}%
                </div>`
            );
        }
    }
};
