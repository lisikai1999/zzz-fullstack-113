/**
 * Main application orchestration.
 */
const App = {
    eventSource: null,
    passesData: null,
    scheduleData: null,

    init() {
        Controls.init();
        PolarChart.init('polar-chart');
        Globe.init('globe-container');
        GanttChart.init('gantt-chart');
        ValidationPanel.init('validation-content');

        // Clock update
        setInterval(() => {
            document.getElementById('clock').textContent = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
        }, 1000);

        // Load ISS TLE by default
        Controls.loadIssTle();
    },

    startTracking() {
        const tle = Controls.getTle();
        const gs = Controls.getGroundStation();
        if (!tle) {
            alert('Please enter a valid TLE');
            return;
        }

        this.stopTracking();
        PolarChart.clearTrajectory();

        // Add ground station to globe
        Globe.addGroundStation(gs.lat, gs.lon, 'GS', 0xff4444);

        // Start SSE stream
        this.eventSource = API.startRealtimeStream(tle, gs,
            (data) => this._onPositionUpdate(data),
            (err) => console.error('SSE error:', err)
        );

        document.getElementById('tracking-status').textContent = 'Tracking';
        document.getElementById('tracking-status').classList.add('active');

        // Draw one full orbit on the globe
        this._drawFullOrbit(tle, gs);
    },

    stopTracking() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        document.getElementById('tracking-status').textContent = 'Idle';
        document.getElementById('tracking-status').classList.remove('active');
    },

    _onPositionUpdate(data) {
        if (data.error) return;

        // Update polar chart
        if (data.look_angles) {
            PolarChart.update(data.look_angles.azimuth_deg, data.look_angles.elevation_deg);
        }

        // Update globe
        if (data.geodetic) {
            Globe.updateSatellite('main', data.geodetic.lat_deg, data.geodetic.lon_deg, data.geodetic.alt_km);
        }
    },

    async _drawFullOrbit(tle, gs) {
        try {
            const now = Date.now() / 1000;
            const result = await API.propagateTrack(tle, now, now + 5400, 30, gs);
            if (result.positions) {
                Globe.drawOrbit('main', result.positions.map(p => p.geodetic));
            }
        } catch (e) {
            console.error('Failed to draw orbit:', e);
        }
    },

    async predictPasses() {
        const tle = Controls.getTle();
        const gs = Controls.getGroundStation();
        const config = Controls.getConfig();
        if (!tle) { alert('Please enter a valid TLE'); return; }

        try {
            const result = await API.predictPasses(tle, gs, config.days, config.minElevation);
            this.passesData = result;
            this._renderPassesTable(result);

            // Draw pass arcs on polar chart
            PolarChart.clearAll();
            for (const pass of result.passes.slice(0, 10)) {
                await this._drawPassOnPolar(tle, gs, pass);
            }
        } catch (e) {
            alert('Pass prediction failed: ' + e.message);
        }
    },

    _renderPassesTable(data) {
        const container = document.getElementById('passes-table');
        if (!data.passes || data.passes.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary); padding: 10px;">No passes found.</p>';
            return;
        }

        let html = `<table class="passes-list">
            <thead><tr><th>#</th><th>AOS</th><th>LOS</th><th>Max El</th><th>Duration</th><th>AOS Az</th></tr></thead>
            <tbody>`;

        data.passes.forEach((p, i) => {
            const aos = new Date(p.aos_unix * 1000).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
            const los = new Date(p.los_unix * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const dur = Math.round(p.duration_seconds);
            html += `<tr>
                <td>${i + 1}</td>
                <td>${aos}</td>
                <td>${los}</td>
                <td>${p.max_elevation_deg.toFixed(1)}</td>
                <td>${dur}s</td>
                <td>${p.aos_azimuth_deg.toFixed(0)}</td>
            </tr>`;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    },

    async _drawPassOnPolar(tle, gs, pass) {
        try {
            const result = await API.propagateTrack(tle, pass.aos_unix, pass.los_unix, 5, gs);
            if (result.positions) {
                const points = result.positions
                    .filter(p => p.look_angles)
                    .map(p => ({
                        azimuth_deg: p.look_angles.azimuth_deg,
                        elevation_deg: p.look_angles.elevation_deg,
                    }));
                PolarChart.drawPassTrajectory(points);
            }
        } catch (e) {
            console.error('Failed to draw pass arc:', e);
        }
    },

    async runScheduler() {
        const satellites = Controls.getSatellites();
        const gs = Controls.getGroundStation();
        const config = Controls.getConfig();

        if (satellites.length === 0) {
            alert('Please add at least one satellite (enter TLE)');
            return;
        }

        try {
            const result = await API.schedule(satellites, gs, config.numAntennas, config.days, config.minElevation);
            this.scheduleData = result;
            GanttChart.render(result);
        } catch (e) {
            alert('Scheduling failed: ' + e.message);
        }
    },

    async startValidation() {
        const tle = Controls.getTle();
        const gs = Controls.getGroundStation();
        if (!tle) { alert('Please enter a valid TLE'); return; }

        // Assume ISS for validation
        const noradId = 25544;
        ValidationPanel.startValidation(noradId, tle, gs);
    },

    stopValidation() {
        ValidationPanel.stopValidation();
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => App.init());
