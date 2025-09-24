// app.js
import { createScene } from './scene3d.js';
import { createRigDriver } from './rig_driver.js';

const canvas = document.getElementById('threeCanvas');
const scene = createScene(canvas);
const rig = createRigDriver({ minConf: 0.35 });

// Carga del modelo y acople del driver al root
(async () => {
  try {
    const glbPath = window.__GLB_PATH__;
    const { modelRoot } = await scene.loadModel(glbPath);
    rig.attach(modelRoot);
  } catch (err) {
    console.error('Error cargando GLB:', err);
  }
})();

// Escuchar poses (emitidas desde otro módulo/app)
window.addEventListener('pose', (ev) => {
  const poses = ev.detail?.poses || [];
  if (!poses.length) return;
  rig.driveFromPose(poses[0]);
});

// Loop
function animate() {
  requestAnimationFrame(animate);
  scene.update();
  scene.render();
}
animate();
