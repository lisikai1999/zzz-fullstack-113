/**
 * Control panel UI: TLE input, ground station config, scheduling parameters.
 */
const Controls = {
    currentTle: null,
    groundStation: null,
    satellites: [],

    init() {
        const container = document.getElementById('controls-content');
        container.innerHTML = `
            <div class="control-group">
                <label>Satellite TLE</label>
                <textarea id="tle-input" placeholder="Paste TLE (3 lines: name, line1, line2)"></textarea>
                <button class="btn btn-primary" onclick="Controls.loadIssTle()">Load ISS TLE</button>
            </div>

            <div class="control-group">
                <label>Ground Station Latitude</label>
                <input type="number" id="gs-lat" value="40.7128" step="0.001">
            </div>
            <div class="control-group">
                <label>Ground Station Longitude</label>
                <input type="number" id="gs-lon" value="-74.0060" step="0.001">
            </div>
            <div class="control-group">
                <label>Altitude (km)</label>
                <input type="number" id="gs-alt" value="0.01" step="0.001">
            </div>

            <div class="control-group">
                <label>Prediction Days</label>
                <input type="number" id="pred-days" value="3" min="1" max="14">
            </div>
            <div class="control-group">
                <label>Min Elevation (deg)</label>
                <input type="number" id="min-el" value="10" min="0" max="90">
            </div>

            <div class="control-group">
                <label>Number of Antennas</label>
                <input type="number" id="num-antennas" value="2" min="1" max="10">
            </div>

            <div class="control-group">
                <label>N2YO API Key</label>
                <input type="text" id="n2yo-key" placeholder="Optional: for validation">
            </div>

            <hr style="border-color: var(--border); margin: 12px 0;">

            <div class="control-group">
                <label>Actions</label>
                <button class="btn btn-success" onclick="App.startTracking()">Start Tracking</button>
                <button class="btn btn-danger" onclick="App.stopTracking()">Stop</button>
                <button class="btn btn-primary" onclick="App.predictPasses()">Predict Passes</button>
                <button class="btn btn-primary" onclick="App.runScheduler()">Schedule</button>
                <button class="btn btn-primary" onclick="App.startValidation()">Validate vs N2YO</button>
            </div>

            <hr style="border-color: var(--border); margin: 12px 0;">

            <div class="control-group">
                <label>Multi-Satellite Config</label>
                <div id="multi-sat-list"></div>
                <button class="btn btn-primary" onclick="Controls.addSatellite()">+ Add Satellite</button>
            </div>
        `;
    },

    async loadIssTle() {
        try {
            const tle = await API.getIssTle();
            if (tle.error) {
                const fallback = await API.getFallbackTle();
                document.getElementById('tle-input').value = `${fallback.name}\n${fallback.line1}\n${fallback.line2}`;
            } else {
                document.getElementById('tle-input').value = `${tle.name}\n${tle.line1}\n${tle.line2}`;
            }
        } catch (e) {
            const fallback = await API.getFallbackTle();
            document.getElementById('tle-input').value = `${fallback.name}\n${fallback.line1}\n${fallback.line2}`;
        }
    },

    getTle() {
        const raw = document.getElementById('tle-input').value.trim();
        const lines = raw.split('\n').map(l => l.trim()).filter(l => l);
        if (lines.length >= 3) {
            return { name: lines[0], line1: lines[1], line2: lines[2] };
        } else if (lines.length === 2) {
            return { name: 'SATELLITE', line1: lines[0], line2: lines[1] };
        }
        return null;
    },

    getGroundStation() {
        return {
            lat: parseFloat(document.getElementById('gs-lat').value),
            lon: parseFloat(document.getElementById('gs-lon').value),
            alt_km: parseFloat(document.getElementById('gs-alt').value),
        };
    },

    getConfig() {
        return {
            days: parseFloat(document.getElementById('pred-days').value),
            minElevation: parseFloat(document.getElementById('min-el').value),
            numAntennas: parseInt(document.getElementById('num-antennas').value),
        };
    },

    addSatellite() {
        const idx = this.satellites.length;
        this.satellites.push({ name: '', tle: null, priority: idx + 1 });
        this._renderMultiSatList();
    },

    _renderMultiSatList() {
        const container = document.getElementById('multi-sat-list');
        container.innerHTML = this.satellites.map((sat, i) => `
            <div style="border: 1px solid var(--border); padding: 6px; margin: 4px 0; border-radius: 4px;">
                <input type="text" placeholder="Name" value="${sat.name}"
                    onchange="Controls.satellites[${i}].name = this.value" style="width: 60%; margin-bottom: 4px;">
                <input type="number" placeholder="Priority" value="${sat.priority}" min="1"
                    onchange="Controls.satellites[${i}].priority = parseInt(this.value)" style="width: 35%;">
                <textarea placeholder="TLE (line1&#10;line2)" rows="2" style="width: 100%; margin-top: 4px;"
                    onchange="Controls._parseSatTle(${i}, this.value)"></textarea>
            </div>
        `).join('');
    },

    _parseSatTle(idx, raw) {
        const lines = raw.trim().split('\n').map(l => l.trim()).filter(l => l);
        if (lines.length >= 2) {
            this.satellites[idx].tle = { name: this.satellites[idx].name, line1: lines[0], line2: lines[1] };
        }
    },

    getSatellites() {
        // Include main TLE as first satellite
        const mainTle = this.getTle();
        const result = [];
        if (mainTle) {
            result.push({
                name: mainTle.name,
                tle: mainTle,
                priority: 1,
                norad_id: null,
            });
        }
        this.satellites.forEach(sat => {
            if (sat.tle) {
                result.push({
                    name: sat.name || 'SAT',
                    tle: sat.tle,
                    priority: sat.priority,
                    norad_id: null,
                });
            }
        });
        return result;
    }
};
