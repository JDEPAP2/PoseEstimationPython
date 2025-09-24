// scene3d.js
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export function createScene(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene(); 
  scene.background = null;

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.set(0, 1.5, 3);

  // luces
  const dir = new THREE.DirectionalLight(0xffffff, 1.0);
  dir.position.set(2, 4, 3);
  scene.add(dir);
  scene.add(new THREE.AmbientLight(0xffffff, 0.5));

  // hack Safari/iOS GLTF + createImageBitmap
  if ('createImageBitmap' in window) {
    try { delete window.createImageBitmap; } catch (e) { window.createImageBitmap = undefined; }
  }

  const clock = new THREE.Clock();
  let mixer = null;
  let modelRoot = null;

  function frameObject(obj) {
    const box = new THREE.Box3().setFromObject(obj);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3()).add(new THREE.Vector3(0, 1, 0));
    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = THREE.MathUtils.degToRad(camera.fov);
    let dist = Math.abs(maxDim / (2 * Math.tan(fov / 2)));
    dist *= 7;
    camera.position.set(center.x, center.y + maxDim * 0.1, center.z + dist);
    camera.near = dist / 100;
    camera.far = dist * 100;
    camera.updateProjectionMatrix();
  }

  function resize() {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (w && h && (canvas.width !== w || canvas.height !== h)) {
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
  }

  async function loadModel(path, resourcePath = '/models/') {
    if (!path) {
      console.warn('Sin GLB. Coloca un .glb en assets/models/.');
      return null;
    }
    const loader = new GLTFLoader();
    loader.setCrossOrigin('anonymous');
    loader.setResourcePath(resourcePath);

    return new Promise((resolve, reject) => {
      loader.load(path, (gltf) => {
        modelRoot = gltf.scene;
        modelRoot.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
        scene.add(modelRoot);
        frameObject(modelRoot);
        if (gltf.animations && gltf.animations.length) {
          mixer = new THREE.AnimationMixer(modelRoot);
          mixer.clipAction(gltf.animations[0]).play();
        }
        resolve({ modelRoot, animations: gltf.animations ?? [] });
      }, undefined, (err) => reject(err));
    });
  }

  function update() {
    if (mixer) mixer.update(clock.getDelta());
  }

  function render() {
    resize();
    renderer.render(scene, camera);
  }

  return {
    scene,
    camera,
    renderer,
    loadModel,
    get model() { return modelRoot; },
    get mixer() { return mixer; },
    update,
    render,
  };
}
