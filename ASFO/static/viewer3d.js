/**
 * ASFO 3D Viewer - Multi-model viewer with manipulation controls
 * Optimized for performance and ease of use
 */

class ASFO3DViewer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.models = [];
        this.selectedModel = null;
        this.nextModelId = 1;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        this.init();
        this.setupEventListeners();
        this.animate();
    }

    init() {
        const container = this.canvas.parentElement;

        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0d0d0d);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            45,
            container.clientWidth / 500,
            0.1,
            10000
        );
        this.camera.position.set(150, 150, 150);

        // Renderer with optimizations
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: this.canvas, 
            antialias: true,
            alpha: false,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(container.clientWidth, 500);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Limit pixel ratio for performance

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight1.position.set(100, 100, 100);
        this.scene.add(directionalLight1);

        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
        directionalLight2.position.set(-100, -100, -100);
        this.scene.add(directionalLight2);

        // Build platform grid
        this.grid = new THREE.GridHelper(200, 20, 0x00bcd4, 0x333333);
        this.scene.add(this.grid);

        // Axes helper
        const axes = new THREE.AxesHelper(100);
        this.scene.add(axes);

        // OrbitControls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 10;
        this.controls.maxDistance = 1000;
        this.controls.target.set(0, 0, 0);
    }

    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Mouse click for selection
        this.canvas.addEventListener('click', (e) => this.onCanvasClick(e));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.onKeyDown(e));
    }

    onWindowResize() {
        const container = this.canvas.parentElement;
        const width = container.clientWidth;
        const height = 500;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    onCanvasClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const meshes = this.models.map(m => m.mesh);
        const intersects = this.raycaster.intersectObjects(meshes);

        if (intersects.length > 0) {
            const clickedMesh = intersects[0].object;
            const model = this.models.find(m => m.mesh === clickedMesh);
            if (model) {
                this.selectModel(model.id);
            }
        } else {
            this.deselectAll();
        }
    }

    onKeyDown(event) {
        if (!this.selectedModel) return;

        const step = event.shiftKey ? 10 : 1;
        const rotStep = event.shiftKey ? 45 : 15;

        switch(event.key) {
            case 'Delete':
            case 'Backspace':
                if (event.target.tagName !== 'INPUT') {
                    this.deleteSelected();
                    event.preventDefault();
                }
                break;
            case 'd':
            case 'D':
                if (event.ctrlKey || event.metaKey) {
                    this.duplicateSelected();
                    event.preventDefault();
                }
                break;
            case 'ArrowLeft':
                this.moveSelected(-step, 0, 0);
                event.preventDefault();
                break;
            case 'ArrowRight':
                this.moveSelected(step, 0, 0);
                event.preventDefault();
                break;
            case 'ArrowUp':
                this.moveSelected(0, step, 0);
                event.preventDefault();
                break;
            case 'ArrowDown':
                this.moveSelected(0, -step, 0);
                event.preventDefault();
                break;
        }
    }

    async loadSTL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (event) => {
                const loader = new THREE.STLLoader();
                const geometry = loader.parse(event.target.result);
                
                // Optimize geometry
                geometry.computeBoundingBox();
                geometry.computeVertexNormals();
                
                // Center geometry at origin and place on platform
                const center = new THREE.Vector3();
                geometry.boundingBox.getCenter(center);
                geometry.translate(-center.x, -center.y, -geometry.boundingBox.min.z);
                
                // Create mesh with material
                const material = new THREE.MeshPhongMaterial({
                    color: 0xff6b35, // Orange/coral
                    specular: 0x111111,
                    shininess: 30,
                    flatShading: false
                });
                
                const mesh = new THREE.Mesh(geometry, material);
                
                // Add model to scene
                const model = {
                    id: this.nextModelId++,
                    mesh: mesh,
                    name: file.name,
                    selected: false
                };
                
                this.models.push(model);
                this.scene.add(mesh);
                
                // Select newly added model
                this.selectModel(model.id);
                
                // Fit camera if first model
                if (this.models.length === 1) {
                    this.fitToView();
                }
                
                resolve(model);
            };
            
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsArrayBuffer(file);
        });
    }

    selectModel(id) {
        // Deselect all first
        this.models.forEach(m => {
            m.selected = false;
            m.mesh.material.emissive.setHex(0x000000);
        });
        
        // Select the target model
        const model = this.models.find(m => m.id === id);
        if (model) {
            model.selected = true;
            model.mesh.material.emissive.setHex(0x00bcd4);
            this.selectedModel = model;
            this.updateUI();
        }
    }

    deselectAll() {
        this.models.forEach(m => {
            m.selected = false;
            m.mesh.material.emissive.setHex(0x000000);
        });
        this.selectedModel = null;
        this.updateUI();
    }

    deleteSelected() {
        if (!this.selectedModel) return;
        
        const index = this.models.findIndex(m => m.id === this.selectedModel.id);
        if (index !== -1) {
            this.scene.remove(this.models[index].mesh);
            this.models[index].mesh.geometry.dispose();
            this.models[index].mesh.material.dispose();
            this.models.splice(index, 1);
        }
        
        this.selectedModel = null;
        this.updateUI();
        this.updateModelList();
    }

    deleteAll() {
        this.models.forEach(m => {
            this.scene.remove(m.mesh);
            m.mesh.geometry.dispose();
            m.mesh.material.dispose();
        });
        this.models = [];
        this.selectedModel = null;
        this.updateUI();
        this.updateModelList();
    }

    duplicateSelected() {
        if (!this.selectedModel) return;
        
        const original = this.selectedModel;
        const geometry = original.mesh.geometry.clone();
        const material = original.mesh.material.clone();
        const mesh = new THREE.Mesh(geometry, material);
        
        // Offset position slightly
        mesh.position.copy(original.mesh.position);
        mesh.position.x += 20;
        mesh.rotation.copy(original.mesh.rotation);
        mesh.scale.copy(original.mesh.scale);
        
        const model = {
            id: this.nextModelId++,
            mesh: mesh,
            name: original.name + ' (copy)',
            selected: false
        };
        
        this.models.push(model);
        this.scene.add(mesh);
        this.selectModel(model.id);
        this.updateModelList();
    }

    moveSelected(dx, dy, dz) {
        if (!this.selectedModel) return;
        
        this.selectedModel.mesh.position.x += dx;
        this.selectedModel.mesh.position.y += dy;
        this.selectedModel.mesh.position.z += dz;
        this.updateUI();
    }

    rotateSelected(axis, degrees) {
        if (!this.selectedModel) return;
        
        const radians = degrees * Math.PI / 180;
        switch(axis) {
            case 'x':
                this.selectedModel.mesh.rotation.x += radians;
                break;
            case 'y':
                this.selectedModel.mesh.rotation.y += radians;
                break;
            case 'z':
                this.selectedModel.mesh.rotation.z += radians;
                break;
        }
        this.updateUI();
    }

    scaleSelected(sx, sy, sz) {
        if (!this.selectedModel) return;
        
        this.selectedModel.mesh.scale.set(sx, sy, sz);
        this.updateUI();
    }

    centerSelected() {
        if (!this.selectedModel) return;
        
        this.selectedModel.mesh.position.set(0, 0, 0);
        this.updateUI();
    }

    resetSelectedTransform() {
        if (!this.selectedModel) return;
        
        this.selectedModel.mesh.position.set(0, 0, 0);
        this.selectedModel.mesh.rotation.set(0, 0, 0);
        this.selectedModel.mesh.scale.set(1, 1, 1);
        this.updateUI();
    }

    fitToView() {
        if (this.models.length === 0) return;
        
        // Calculate bounding box of all models
        const box = new THREE.Box3();
        this.models.forEach(m => {
            const modelBox = new THREE.Box3().setFromObject(m.mesh);
            box.union(modelBox);
        });
        
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = this.camera.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
        cameraZ *= 1.5;
        
        this.camera.position.set(cameraZ, cameraZ, cameraZ);
        this.camera.lookAt(center);
        this.controls.target.copy(center);
        this.controls.update();
    }

    updateUI() {
        if (!this.selectedModel) {
            document.getElementById('modelInfo').innerHTML = '<span style="color: #757575;">No model selected</span>';
            document.getElementById('transformControls').style.opacity = '0.5';
            document.getElementById('transformControls').style.pointerEvents = 'none';
            return;
        }
        
        const m = this.selectedModel.mesh;
        const info = `
            <div style="color: #00bcd4; font-weight: bold;">${this.selectedModel.name}</div>
            <div style="font-size: 0.85em; color: #9e9e9e; margin-top: 5px;">
                Position: (${m.position.x.toFixed(1)}, ${m.position.y.toFixed(1)}, ${m.position.z.toFixed(1)})<br>
                Rotation: (${(m.rotation.x * 180 / Math.PI).toFixed(0)}°, ${(m.rotation.y * 180 / Math.PI).toFixed(0)}°, ${(m.rotation.z * 180 / Math.PI).toFixed(0)}°)<br>
                Scale: (${m.scale.x.toFixed(2)}, ${m.scale.y.toFixed(2)}, ${m.scale.z.toFixed(2)})
            </div>
        `;
        document.getElementById('modelInfo').innerHTML = info;
        document.getElementById('transformControls').style.opacity = '1';
        document.getElementById('transformControls').style.pointerEvents = 'auto';
        
        // Update input fields
        document.getElementById('posX').value = m.position.x.toFixed(1);
        document.getElementById('posY').value = m.position.y.toFixed(1);
        document.getElementById('posZ').value = m.position.z.toFixed(1);
        
        document.getElementById('rotX').value = (m.rotation.x * 180 / Math.PI).toFixed(0);
        document.getElementById('rotY').value = (m.rotation.y * 180 / Math.PI).toFixed(0);
        document.getElementById('rotZ').value = (m.rotation.z * 180 / Math.PI).toFixed(0);
        
        document.getElementById('scaleVal').value = m.scale.x.toFixed(2);
    }

    updateModelList() {
        const list = document.getElementById('modelList');
        if (this.models.length === 0) {
            list.innerHTML = '<div class="empty-state">No models loaded</div>';
            return;
        }
        
        list.innerHTML = this.models.map(m => `
            <div class="model-item ${m.selected ? 'selected' : ''}" onclick="viewer.selectModel(${m.id})">
                <span class="model-name">${m.name}</span>
                <button class="btn-small" onclick="event.stopPropagation(); viewer.deleteModel(${m.id})">✕</button>
            </div>
        `).join('');
    }

    deleteModel(id) {
        const index = this.models.findIndex(m => m.id === id);
        if (index !== -1) {
            this.scene.remove(this.models[index].mesh);
            this.models[index].mesh.geometry.dispose();
            this.models[index].mesh.material.dispose();
            this.models.splice(index, 1);
        }
        
        if (this.selectedModel && this.selectedModel.id === id) {
            this.selectedModel = null;
            this.updateUI();
        }
        
        this.updateModelList();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    getModelsCount() {
        return this.models.length;
    }

    hasModels() {
        return this.models.length > 0;
    }
}
