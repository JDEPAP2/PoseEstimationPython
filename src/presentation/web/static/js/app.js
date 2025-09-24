const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const ctx = overlay.getContext('2d');

// ===== Performance tuning =====
let INFER_INTERVAL_MS = 33;   // ~30 FPS objetivo
const INFER_WIDTH = 352;      // ancho enviado al backend (sube/baja según tu HW)
const JPEG_QUALITY = 0.6;    // compresión moderada
let lastInferW = null, lastInferH = null; // dimensiones exactamente enviadas

function uiError(msg) {
  console.error(msg);
  const pane = document.getElementById('videoPane');
  const div = document.createElement('div');
  Object.assign(div.style, {
    position: 'absolute', bottom: '12px', left: '12px', right: '12px',
    padding: '10px', background: '#2a2f3a', borderRadius: '8px', color: '#fff'
  });
  div.textContent = msg;
  pane.appendChild(div);
}

async function setupCam() {
  if (!('mediaDevices' in navigator) || !('getUserMedia' in navigator.mediaDevices)) {
    if (!window.isSecureContext) uiError('La cámara requiere HTTPS (usa https://localhost:5000).');
    else uiError('Este navegador no soporta getUserMedia.');
    throw new Error('getUserMedia not available');
  }
  const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false });
  video.srcObject = stream;
  await new Promise(r => video.onloadedmetadata = r);
  overlay.width  = Math.round(video.videoWidth  * 0.4);
  overlay.height = Math.round(video.videoHeight * 0.4);
}

// PARES (sin cara conectada: 0..4 solo puntos)
const pairs = [
  [5,7],[7,9], [6,8],[8,10], // brazos
  [5,6],                     // hombros
  [11,12],                   // caderas
  [11,13],[13,15],          // pierna izq
  [12,14],[14,16],          // pierna der
  [11,5],[12,6],            // torso->hombros
];

function drawPoses(poses, scale=1) {
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  ctx.lineWidth = 2; ctx.strokeStyle = '#ffffffff'; ctx.fillStyle = '#ff0000ff';
  for (const p of poses) {
    const k = p.keypoints;
    // líneas (sin cara)
    ctx.beginPath();
    for (const [a,b] of pairs) {
      const ka = k[a], kb = k[b];
      if (!ka || !kb || ka[2] < 0.3 || kb[2] < 0.3) continue;
      ctx.moveTo(ka[0]*scale, ka[1]*scale);
      ctx.lineTo(kb[0]*scale, kb[1]*scale);
    }
    ctx.stroke();
    // puntos (incluye cara sin conectar)
    for (let idx=0; idx<k.length; idx++) {
      const pt = k[idx];
      if (!pt || pt[2] < 0.3) continue;
      ctx.beginPath();
      ctx.arc(pt[0]*scale, pt[1]*scale, idx<=4 ? 2.5 : 3, 0, Math.PI*2);
      ctx.fill();
    }
  }
}

async function snapshotAndSend() {
  // Reescalar al tamaño objetivo ANTES de subir
  const scale = INFER_WIDTH / video.videoWidth;
  lastInferW = Math.round(video.videoWidth  * scale);
  lastInferH = Math.round(video.videoHeight * scale);
  const c = document.createElement('canvas');
  c.width = lastInferW; c.height = lastInferH;
  const cx = c.getContext('2d');
  cx.drawImage(video, 0, 0, lastInferW, lastInferH);
  const blob = await new Promise(r => c.toBlob(r, 'image/jpeg', JPEG_QUALITY));

  try {
    const form = new FormData();
    form.append('frame', blob, 'frame.jpg');
    const res = await fetch('/api/infer', { method: 'POST', body: form });
    if (!res.ok) throw new Error('infer failed');
    const data = await res.json();

    // MUY IMPORTANTE: escalar desde tamaño de inferencia -> overlay
    const scaleOverlay = overlay.width / lastInferW;
    drawPoses(data.poses, scaleOverlay);

    document.getElementById('kpiFps').textContent = data.server_fps.toFixed(1);
    document.getElementById('kpiMs').textContent  = data.inference_ms.toFixed(1);
    document.getElementById('kpiMeanConf').textContent = (data.mean_kp_conf ?? 0).toFixed(2);

    // Notificar a Three.js para el rig
    window.dispatchEvent(new CustomEvent('pose', {
      detail: { poses: data.poses, scale: { inW: lastInferW, inH: lastInferH } }
    }));
  } catch (e) { console.error(e); }
}

async function loopInfer() {
  try { await snapshotAndSend(); } catch {}
  setTimeout(loopInfer, INFER_INTERVAL_MS);
}

setupCam().then(loopInfer).catch(() => {});
