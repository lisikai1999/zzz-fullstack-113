/**
 * Three.js 3D Globe with satellite orbits and ground stations.
 */
const Globe = {
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    earth: null,
    satellites: {},
    groundStations: [],
    orbitLines: {},
    animationId: null,

    init(containerId) {
        const container = document.getElementById(containerId);
        const width = container.clientWidth || 400;
        const height = container.clientHeight || 380;

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0d1117);

        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(0, 0, 35);

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 12;
        this.controls.maxDistance = 80;

        // Lighting
        const ambient = new THREE.AmbientLight(0x404040, 2);
        this.scene.add(ambient);
        const directional = new THREE.DirectionalLight(0xffffff, 1.5);
        directional.position.set(5, 3, 5);
        this.scene.add(directional);

        // Earth
        this._createEarth();

        // Stars background
        this._createStars();

        // Start animation loop
        this._animate();

        // Handle resize
        window.addEventListener('resize', () => this._onResize(container));
    },

    _createEarth() {
        const RE = 6.371; // scale: 1 unit = 1000 km
        const geometry = new THREE.SphereGeometry(RE, 64, 64);

        // Procedural earth material (no texture dependency)
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');

        // Ocean
        ctx.fillStyle = '#1a3a5c';
        ctx.fillRect(0, 0, 512, 256);

        // Simple continent outlines (approximate)
        ctx.fillStyle = '#2d5a3d';
        ctx.beginPath();
        // North America
        ctx.ellipse(120, 80, 40, 30, 0, 0, Math.PI * 2);
        ctx.fill();
        // South America
        ctx.beginPath();
        ctx.ellipse(150, 160, 20, 40, 0.2, 0, Math.PI * 2);
        ctx.fill();
        // Europe/Africa
        ctx.beginPath();
        ctx.ellipse(270, 90, 15, 20, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(270, 155, 20, 35, 0, 0, Math.PI * 2);
        ctx.fill();
        // Asia
        ctx.beginPath();
        ctx.ellipse(350, 80, 50, 30, 0, 0, Math.PI * 2);
        ctx.fill();
        // Australia
        ctx.beginPath();
        ctx.ellipse(400, 175, 20, 15, 0, 0, Math.PI * 2);
        ctx.fill();

        // Grid lines
        ctx.strokeStyle = 'rgba(100, 150, 200, 0.15)';
        ctx.lineWidth = 0.5;
        for (let i = 0; i < 512; i += 32) {
            ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 256); ctx.stroke();
        }
        for (let i = 0; i < 256; i += 32) {
            ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(512, i); ctx.stroke();
        }

        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.MeshPhongMaterial({
            map: texture,
            specular: 0x222222,
            shininess: 15,
        });

        this.earth = new THREE.Mesh(geometry, material);
        this.scene.add(this.earth);

        // Equator ring
        const eqGeom = new THREE.RingGeometry(RE + 0.01, RE + 0.02, 128);
        const eqMat = new THREE.MeshBasicMaterial({ color: 0x333333, side: THREE.DoubleSide });
        const equator = new THREE.Mesh(eqGeom, eqMat);
        equator.rotation.x = Math.PI / 2;
        this.scene.add(equator);
    },

    _createStars() {
        const starGeom = new THREE.BufferGeometry();
        const starCount = 2000;
        const positions = new Float32Array(starCount * 3);
        for (let i = 0; i < starCount * 3; i += 3) {
            const r = 200 + Math.random() * 100;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            positions[i] = r * Math.sin(phi) * Math.cos(theta);
            positions[i + 1] = r * Math.sin(phi) * Math.sin(theta);
            positions[i + 2] = r * Math.cos(phi);
        }
        starGeom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.3 });
        this.scene.add(new THREE.Points(starGeom, starMat));
    },

    _latLonToVec3(latDeg, lonDeg, altitude) {
        const RE = 6.371;
        const r = RE + (altitude || 0) / 1000; // altitude in km -> scale
        const lat = latDeg * Math.PI / 180;
        const lon = lonDeg * Math.PI / 180;
        return new THREE.Vector3(
            r * Math.cos(lat) * Math.cos(lon),
            r * Math.sin(lat),
            -r * Math.cos(lat) * Math.sin(lon)
        );
    },

    addGroundStation(latDeg, lonDeg, name, color) {
        color = color || 0xff4444;
        const pos = this._latLonToVec3(latDeg, lonDeg, 0);

        // Pin marker
        const coneGeom = new THREE.ConeGeometry(0.08, 0.3, 8);
        const coneMat = new THREE.MeshBasicMaterial({ color });
        const cone = new THREE.Mesh(coneGeom, coneMat);
        cone.position.copy(pos);
        cone.lookAt(0, 0, 0);
        cone.rotateX(Math.PI / 2);
        this.scene.add(cone);

        // Small glow sphere
        const glowGeom = new THREE.SphereGeometry(0.1, 8, 8);
        const glowMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.6 });
        const glow = new THREE.Mesh(glowGeom, glowMat);
        glow.position.copy(pos);
        this.scene.add(glow);

        this.groundStations.push({ cone, glow, lat: latDeg, lon: lonDeg, name });
    },

    updateSatellite(id, latDeg, lonDeg, altKm, color) {
        color = color || 0x58a6ff;
        const pos = this._latLonToVec3(latDeg, lonDeg, altKm);

        if (!this.satellites[id]) {
            const geom = new THREE.SphereGeometry(0.12, 8, 8);
            const mat = new THREE.MeshBasicMaterial({ color });
            const mesh = new THREE.Mesh(geom, mat);
            this.scene.add(mesh);
            this.satellites[id] = { mesh, trail: [] };
        }

        this.satellites[id].mesh.position.copy(pos);
        this.satellites[id].trail.push(pos.clone());

        // Keep trail limited
        if (this.satellites[id].trail.length > 300) {
            this.satellites[id].trail.shift();
        }
    },

    drawOrbit(id, positions, color) {
        color = color || 0x58a6ff;

        // Remove old orbit line
        if (this.orbitLines[id]) {
            this.scene.remove(this.orbitLines[id]);
        }

        const points = positions.map(p =>
            this._latLonToVec3(p.lat_deg, p.lon_deg, p.alt_km)
        );

        if (points.length < 2) return;

        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.6 });
        const line = new THREE.Line(geometry, material);
        this.scene.add(line);
        this.orbitLines[id] = line;
    },

    _animate() {
        this.animationId = requestAnimationFrame(() => this._animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    },

    _onResize(container) {
        const w = container.clientWidth;
        const h = container.clientHeight;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    },

    clearOrbits() {
        Object.keys(this.orbitLines).forEach(id => {
            this.scene.remove(this.orbitLines[id]);
        });
        this.orbitLines = {};
    }
};
