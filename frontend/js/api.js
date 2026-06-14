/**
 * Backend API client with SSE support.
 */
const API = {
    baseUrl: '',

    async request(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const resp = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!resp.ok) throw new Error(`API error: ${resp.status}`);
        return resp.json();
    },

    async propagate(tle, timestampUnix, groundStation) {
        return this.request('/api/propagate', {
            method: 'POST',
            body: JSON.stringify({
                tle,
                timestamp_unix: timestampUnix || null,
                ground_station: groundStation || null,
            }),
        });
    },

    async propagateTrack(tle, startUnix, endUnix, stepSeconds, groundStation) {
        return this.request('/api/propagate/track', {
            method: 'POST',
            body: JSON.stringify({
                tle,
                start_unix: startUnix,
                end_unix: endUnix,
                step_seconds: stepSeconds,
                ground_station: groundStation || null,
            }),
        });
    },

    async predictPasses(tle, groundStation, days, minElevation, startUnix) {
        return this.request('/api/passes/predict', {
            method: 'POST',
            body: JSON.stringify({
                tle,
                ground_station: groundStation,
                days,
                min_elevation_deg: minElevation,
                start_unix: startUnix || null,
            }),
        });
    },

    async predictMulti(satellites, groundStation, numAntennas, days, minElevation, startUnix) {
        return this.request('/api/passes/predict/multi', {
            method: 'POST',
            body: JSON.stringify({
                satellites,
                ground_station: groundStation,
                num_antennas: numAntennas,
                days,
                min_elevation_deg: minElevation,
                start_unix: startUnix || null,
            }),
        });
    },

    async schedule(satellites, groundStation, numAntennas, days, minElevation, startUnix) {
        return this.request('/api/schedule', {
            method: 'POST',
            body: JSON.stringify({
                satellites,
                ground_station: groundStation,
                num_antennas: numAntennas,
                days,
                min_elevation_deg: minElevation,
                start_unix: startUnix || null,
            }),
        });
    },

    async getIssTle() {
        return this.request('/api/tle/iss');
    },

    async getFallbackTle() {
        return this.request('/api/tle/fallback');
    },

    async validateCompare(noradId, tle, groundStation) {
        const params = new URLSearchParams({
            line1: tle.line1,
            line2: tle.line2,
            name: tle.name || 'SATELLITE',
            lat: groundStation.lat,
            lon: groundStation.lon,
            alt_km: groundStation.alt_km || 0,
        });
        return this.request(`/api/validate/compare/${noradId}?${params}`);
    },

    async getValidationStatus() {
        return this.request('/api/validate/status');
    },

    startRealtimeStream(tle, groundStation, onMessage, onError) {
        const params = new URLSearchParams({
            line1: tle.line1,
            line2: tle.line2,
            name: tle.name || 'SATELLITE',
            lat: groundStation.lat,
            lon: groundStation.lon,
            alt_km: groundStation.alt_km || 0,
        });
        const url = `${this.baseUrl}/api/realtime/stream?${params}`;
        const source = new EventSource(url);

        source.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (e) {
                if (onError) onError(e);
            }
        };

        source.onerror = (e) => {
            if (onError) onError(e);
        };

        return source;
    },
};
