// rig_driver.js
import * as THREE from 'three';

// ===== Mapas del usuario =====
const JOINT_MAP = {
  "L_UPPERARM": "mixamorigLeftArm",
  "R_UPPERARM": "mixamorigRightArm",
  "L_FOREARM":  "mixamorigLeftForeArm",
  "R_FOREARM":  "mixamorigRightForeArm",
  "L_HIP":      "mixamorigLeftUpLeg",
  "R_HIP":      "mixamorigRightUpLeg",
  "L_KNEE":     "mixamorigLeftLeg",
  "R_KNEE":     "mixamorigRightLeg",
  "L_ANKLE":    "mixamorigLeftFoot",
  "R_ANKLE":    "mixamorigRightFoot",
  "SPINE":      "mixamorigSpine1",
  "HIPS":       "mixamorigSpine",
};

const AXIS_CFG = {
  "mixamorigLeftArm":      ["P", +1,  -90],
  "mixamorigRightArm":     ["P", -1,  -90],
  "mixamorigLeftForeArm":  ["P", -1,    0],
  "mixamorigRightForeArm": ["P", -1,    0],
  "mixamorigLeftUpLeg":    ["R", -1,  280],
  "mixamorigRightUpLeg":   ["R", -1,  280],
  "mixamorigLeftLeg":      ["P",  0,    0],
  "mixamorigRightLeg":     ["P",  0,    0],
  "mixamorigLeftFoot":     ["P",  0,    0],
  "mixamorigRightFoot":    ["P",  0,    0],
  "mixamorigSpine1":       ["R", -1,  -90],
  "mixamorigSpine":        ["R", -1,    0],
};

// COCO keypoints (17)
const KP = {
  NOSE:0, LEYE:1, REYE:2, LEAR:3, REAR:4,
  LSHO:5, RSHO:6, LELB:7, RELB:8, LWR:9, RWR:10,
  LHIP:11, RHIP:12, LKNE:13, RKNE:14, LANK:15, RANK:16
};

// ===== Helpers (solo de rig) =====
function vec(a, b) { return new THREE.Vector2(b[0]-a[0], b[1]-a[1]); }
function angleDeg(v) { return THREE.MathUtils.radToDeg(Math.atan2(v.y, v.x)); }
function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }

function angleBetween(u, v) {
  const nu = u.clone().normalize(), nv = v.clone().normalize();
  const dot = THREE.MathUtils.clamp(nu.dot(nv), -1, 1);
  return THREE.MathUtils.radToDeg(Math.acos(dot));
}
function unwrapToNear(prev, val) {
  let v = val;
  while (v - prev > 180) v -= 360;
  while (v - prev < -180) v += 360;
  return v;
}
function applyAxisRotation(bone, [mode, sign, offsetDeg], valueDeg) {
  const deg = sign * valueDeg + offsetDeg;
  const rad = THREE.MathUtils.degToRad(deg);
  if (mode === 'P') bone.rotation.x = rad;
  else if (mode === 'Y') bone.rotation.y = rad;
  else bone.rotation.z = rad; // 'R'
}

export function createRigDriver({ minConf = 0.35 } = {}) {
  let boneIndex = {}; // name -> bone
  let modelRoot = null;

  // Estados para suavizado
  const elbowState    = { L: { prev:null }, R: { prev:null } };
  const shoulderState = { L: { prev:null }, R: { prev:null } };
  const ema = {}; // EMA por hueso

  function indexBones(root) {
    boneIndex = {};
    root.traverse(obj => { if (obj.isBone) boneIndex[obj.name] = obj; });
    // console.log('Bones:', Object.keys(boneIndex));
  }

  function attach(root) {
    modelRoot = root;
    indexBones(modelRoot);
  }

  function smoothAngleLimited(stateObj, key, targetDeg, alpha = 0.35, maxStepDeg = 25) {
    const st = stateObj[key];
    if (st.prev == null) { st.prev = targetDeg; return targetDeg; }
    const unwrapped = unwrapToNear(st.prev, targetDeg);
    const delta = THREE.MathUtils.clamp(unwrapped - st.prev, -maxStepDeg, +maxStepDeg);
    const stepped = st.prev + delta;
    const out = (1 - alpha) * st.prev + alpha * stepped;
    st.prev = out;
    return out;
  }

  function upd(boneName, deg) {
    const bone = boneIndex[boneName];
    if (!bone) return;
    const cfg = AXIS_CFG[boneName] || ['R',1,0];
    applyAxisRotation(bone, cfg, deg);
  }

  function updSmooth(boneName, deg, a = 0.35) {
    const bone = boneIndex[boneName];
    if (!bone) return;
    const prev = ema[boneName] ?? deg;
    const out = prev * (1 - a) + deg * a;
    ema[boneName] = out;
    const cfg = AXIS_CFG[boneName] || ['R',1,0];
    applyAxisRotation(bone, cfg, out);
  }

  function driveFromPose(pose) {
    if (!pose || !pose.keypoints || !modelRoot) return;
    const k = pose.keypoints; // [[x,y,c], ...]

    // Torso (para hombros relativos)
    let torsoVec = null;
    if (k[KP.LHIP] && k[KP.RHIP] && k[KP.LSHO] && k[KP.RSHO]) {
      const hipMid = [(k[KP.LHIP][0]+k[KP.RHIP][0])/2, (k[KP.LHIP][1]+k[KP.RHIP][1])/2];
      const shoMid = [(k[KP.LSHO][0]+k[KP.RSHO][0])/2, (k[KP.LSHO][1]+k[KP.RSHO][1])/2];
      torsoVec = vec(hipMid, shoMid);
    }

    // Hombros
    if (k[KP.LSHO]?.[2] > minConf && k[KP.LELB]?.[2] > minConf) {
      const upper = vec(k[KP.LSHO], k[KP.LELB]);
      let ang;
      if (torsoVec) {
        const nu = torsoVec.clone().normalize();
        const nv = upper.clone().normalize();
        const dot = THREE.MathUtils.clamp(nu.dot(nv), -1, 1);
        const det = nu.x * nv.y - nu.y * nv.x;
        ang = THREE.MathUtils.radToDeg(Math.atan2(det, dot));
      } else { ang = angleDeg(upper); }
      const sang = smoothAngleLimited(shoulderState, 'L', ang, 0.35, 20);
      upd(JOINT_MAP.L_UPPERARM, sang);
    }
    if (k[KP.RSHO]?.[2] > minConf && k[KP.RELB]?.[2] > minConf) {
      const upper = vec(k[KP.RSHO], k[KP.RELB]);
      let ang;
      if (torsoVec) {
        const nu = torsoVec.clone().normalize();
        const nv = upper.clone().normalize();
        const dot = THREE.MathUtils.clamp(nu.dot(nv), -1, 1);
        const det = nu.x * nv.y - nu.y * nv.x;
        ang = THREE.MathUtils.radToDeg(Math.atan2(det, dot));
      } else { ang = angleDeg(upper); }
      const sang = smoothAngleLimited(shoulderState, 'R', ang, 0.35, 20);
      upd(JOINT_MAP.R_UPPERARM, sang);
    }

    // Codos (flexión 0..180)
    if (k[KP.LSHO]?.[2] > minConf && k[KP.LELB]?.[2] > minConf && k[KP.LWR ]?.[2] > minConf) {
      const upper = vec(k[KP.LSHO], k[KP.LELB]);
      const fore  = vec(k[KP.LELB], k[KP.LWR ]);
      let flex = angleBetween(upper, fore);
      flex = clamp(flex, 0, 160);
      const sflex = smoothAngleLimited(elbowState, 'L', flex, 0.65, 90);
      upd(JOINT_MAP.L_FOREARM, sflex);
    } else if (elbowState.L.prev != null) {
      upd(JOINT_MAP.L_FOREARM, elbowState.L.prev);
    }

    if (k[KP.RSHO]?.[2] > minConf && k[KP.RELB]?.[2] > minConf && k[KP.RWR ]?.[2] > minConf) {
      const upper = vec(k[KP.RSHO], k[KP.RELB]);
      const fore  = vec(k[KP.RELB], k[KP.RWR ]);
      let flex = angleBetween(upper, fore);
      flex = clamp(flex, 0, 160);
      const sflex = smoothAngleLimited(elbowState, 'R', flex, 0.35, 25);
      upd(JOINT_MAP.R_FOREARM, sflex);
    } else if (elbowState.R.prev != null) {
      upd(JOINT_MAP.R_FOREARM, elbowState.R.prev);
    }

    // Caderas/piernas (absoluto simple)
    if (k[KP.LHIP]?.[2] > minConf && k[KP.LKNE]?.[2] > minConf) {
      upd(JOINT_MAP.L_HIP, angleDeg(vec(k[KP.LHIP], k[KP.LKNE])));
    }
    if (k[KP.RHIP]?.[2] > minConf && k[KP.RKNE]?.[2] > minConf) {
      upd(JOINT_MAP.R_HIP, angleDeg(vec(k[KP.RHIP], k[KP.RKNE])));
    }
    if (k[KP.LKNE]?.[2] > minConf && k[KP.LANK]?.[2] > minConf) {
      upd(JOINT_MAP.L_KNEE, angleDeg(vec(k[KP.LKNE], k[KP.LANK])));
    }
    if (k[KP.RKNE]?.[2] > minConf && k[KP.RANK]?.[2] > minConf) {
      upd(JOINT_MAP.R_KNEE, angleDeg(vec(k[KP.RKNE], k[KP.RANK])));
    }

    // Spine superior con EMA suave
    if (k[KP.LHIP] && k[KP.RHIP] && k[KP.LSHO] && k[KP.RSHO]) {
      const hipMid = [(k[KP.LHIP][0]+k[KP.RHIP][0])/2, (k[KP.LHIP][1]+k[KP.RHIP][1])/2];
      const shoMid = [(k[KP.LSHO][0]+k[KP.RSHO][0])/2, (k[KP.LSHO][1]+k[KP.RSHO][1])/2];
      const angSpine = angleDeg(vec(hipMid, shoMid));
      updSmooth(JOINT_MAP.SPINE, angSpine, 0.55);
    }
  }

  return {
    attach,          // (modelRoot)
    driveFromPose,   // (pose)
    // opcional: exponer mapas por si quieres editarlos desde fuera
    JOINT_MAP,
    AXIS_CFG,
    KP,
  };
}
