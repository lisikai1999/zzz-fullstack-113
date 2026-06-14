/**
 * D3.js Polar (Azimuth/Elevation) Star Chart
 * Center = zenith (90 deg elevation), outer ring = horizon (0 deg).
 */
const PolarChart = {
    svg: null,
    width: 340,
    height: 340,
    margin: 30,
    radius: 0,
    trajectoryPoints: [],
    colors: ['#58a6ff', '#a371f7', '#3fb950', '#d29922', '#f85149', '#79c0ff'],
    colorIndex: 0,

    init(container) {
        const el = document.getElementById(container);
        this.width = el.clientWidth - 20 || 340;
        this.height = el.clientHeight - 20 || 340;
        const size = Math.min(this.width, this.height);
        this.radius = (size - 2 * this.margin) / 2;

        this.svg = d3.select(`#${container}`)
            .append('svg')
            .attr('width', size)
            .attr('height', size);

        const g = this.svg.append('g')
            .attr('transform', `translate(${size / 2}, ${size / 2})`)
            .attr('class', 'polar-group');

        this.g = g;
        this._drawGrid();
        this._drawLabels();

        // Trajectory path
        this.trajectoryPath = g.append('path')
            .attr('class', 'trajectory-arc')
            .attr('stroke', this.colors[0]);

        // Satellite dot
        this.satelliteDot = g.append('circle')
            .attr('class', 'satellite-dot')
            .attr('r', 5)
            .attr('cx', 0)
            .attr('cy', 0)
            .style('display', 'none');

        // Info text
        this.infoText = g.append('text')
            .attr('x', 0)
            .attr('y', this.radius + 20)
            .attr('text-anchor', 'middle')
            .attr('class', 'polar-label')
            .style('font-size', '11px');
    },

    _drawGrid() {
        const elevations = [0, 30, 60, 90];
        elevations.forEach(el => {
            const r = this.radius * (90 - el) / 90;
            this.g.append('circle')
                .attr('class', 'polar-ring')
                .attr('r', r);
        });

        // Cardinal lines
        for (let az = 0; az < 360; az += 45) {
            const rad = az * Math.PI / 180;
            this.g.append('line')
                .attr('class', 'polar-line')
                .attr('x1', 0)
                .attr('y1', 0)
                .attr('x2', this.radius * Math.sin(rad))
                .attr('y2', -this.radius * Math.cos(rad));
        }
    },

    _drawLabels() {
        const labels = [
            { az: 0, text: 'N' }, { az: 90, text: 'E' },
            { az: 180, text: 'S' }, { az: 270, text: 'W' }
        ];
        labels.forEach(l => {
            const rad = l.az * Math.PI / 180;
            const r = this.radius + 14;
            this.g.append('text')
                .attr('class', 'polar-label')
                .attr('x', r * Math.sin(rad))
                .attr('y', -r * Math.cos(rad))
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .text(l.text);
        });

        // Elevation labels
        [30, 60].forEach(el => {
            const r = this.radius * (90 - el) / 90;
            this.g.append('text')
                .attr('class', 'polar-label')
                .attr('x', 3)
                .attr('y', -r - 2)
                .style('font-size', '9px')
                .text(`${el}`);
        });
    },

    _toXY(azDeg, elDeg) {
        const r = this.radius * (90 - elDeg) / 90;
        const azRad = azDeg * Math.PI / 180;
        return {
            x: r * Math.sin(azRad),
            y: -r * Math.cos(azRad)
        };
    },

    update(azDeg, elDeg) {
        if (elDeg < -5) {
            this.satelliteDot.style('display', 'none');
            this.infoText.text(`Below horizon (El: ${elDeg.toFixed(1)})`);
            return;
        }

        const pos = this._toXY(azDeg, Math.max(0, elDeg));
        this.satelliteDot
            .style('display', 'block')
            .attr('cx', pos.x)
            .attr('cy', pos.y);

        this.trajectoryPoints.push(pos);
        if (this.trajectoryPoints.length > 500) {
            this.trajectoryPoints.shift();
        }

        // Draw trajectory
        if (this.trajectoryPoints.length > 1) {
            const line = d3.line().x(d => d.x).y(d => d.y);
            this.trajectoryPath.attr('d', line(this.trajectoryPoints));
        }

        this.infoText.text(`Az: ${azDeg.toFixed(1)} | El: ${elDeg.toFixed(1)}`);
    },

    clearTrajectory() {
        this.trajectoryPoints = [];
        this.trajectoryPath.attr('d', '');
    },

    drawPassTrajectory(points, color) {
        color = color || this.colors[this.colorIndex++ % this.colors.length];
        const xyPoints = points
            .filter(p => p.elevation_deg >= 0)
            .map(p => this._toXY(p.azimuth_deg, p.elevation_deg));

        if (xyPoints.length < 2) return;

        const line = d3.line().x(d => d.x).y(d => d.y).curve(d3.curveCatmullRom);
        this.g.append('path')
            .attr('class', 'trajectory-arc')
            .attr('d', line(xyPoints))
            .attr('stroke', color)
            .attr('opacity', 0.6);
    },

    clearAll() {
        this.g.selectAll('.trajectory-arc:not(:first-of-type)').remove();
        this.clearTrajectory();
        this.colorIndex = 0;
    }
};
