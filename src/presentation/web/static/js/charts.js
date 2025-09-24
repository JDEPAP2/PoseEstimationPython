const chartMsCtx = document.getElementById('chartMs');
const chartFpsCtx = document.getElementById('chartFps');
const chartMeanCtx = document.getElementById('chartMeanConf');

function mkChart(ctx, label) {
  return new Chart(ctx, {
    type: 'line',
    data: { labels: [], datasets: [{ label, data: [], tension: 0.2 }] },
    options: { animation: false, responsive: true, plugins: { legend: { display: true } }, scales: { x: { display: false } } }
  });
}

const chMs   = mkChart(chartMsCtx,   'Inference (ms)');
const chFps  = mkChart(chartFpsCtx,  'Server FPS');
const chMean = mkChart(chartMeanCtx, 'Mean kp conf');

async function pollMetrics() {
  try {
    const res = await fetch('/api/metrics?n=120', { cache: 'no-store' });
    const json = await res.json();
    const labels = json.map(x => new Date(x.t*1000).toLocaleTimeString());

    chMs.data.labels   = labels; chMs.data.datasets[0].data   = json.map(x => x.inference_ms);
    chFps.data.labels  = labels; chFps.data.datasets[0].data  = json.map(x => x.server_fps);
    chMean.data.labels = labels; chMean.data.datasets[0].data = json.map(x => x.mean_kp_conf ?? 0);

    chMs.update(); chFps.update(); chMean.update();
  } catch (e) { console.error(e); }
  setTimeout(pollMetrics, 1000);
}

pollMetrics();
