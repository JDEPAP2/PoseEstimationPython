"""Constantes y configuraciones para keypoints y joints del rig."""

# --- Umbral de confianza mínimo para keypoints ---
KP_THRES = 0.25

# --- Conexiones entre keypoints para dibujar esqueleto ---
SKELETON = [
    (5, 7), (7, 9),
    (6, 8), (8, 10),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (5, 6), (11, 12), (5, 11), (6, 12),
]

# --- Índices COCO de 17 puntos ---
NOSE = 0
LEYE = 1
REYE = 2
LEAR = 3
REAR = 4
LSHO = 5
RSHO = 6
LELB = 7
RELB = 8
LWR = 9
RWR = 10
LHIP = 11
RHIP = 12
LKNE = 13
RKNE = 14
LANK = 15
RANK = 16

# --- Mapeo de joints en modelo Mixamo ---
JOINT_MAP = {
    "L_UPPERARM": "mixamorig:LeftArm",
    "R_UPPERARM": "mixamorig:RightArm",
    "L_FOREARM": "mixamorig:LeftForeArm",
    "R_FOREARM": "mixamorig:RightForeArm",
    "L_HIP": "mixamorig:LeftUpLeg",
    "R_HIP": "mixamorig:RightUpLeg",
    "L_KNEE": "mixamorig:LeftLeg",
    "R_KNEE": "mixamorig:RightLeg",
    "L_ANKLE": "mixamorig:LeftFoot",
    "R_ANKLE": "mixamorig:RightFoot",
    "SPINE": "mixamorig:Spine1",
    "HIPS": "mixamorig:Spine",
}

# --- Configuración de ejes por joint ---
# Formato: joint → (eje, signo, offset)
AXIS_CFG = {
    "mixamorig:LeftArm": ("P", -1, 0),
    "mixamorig:RightArm": ("P", +1, 180),
    "mixamorig:LeftForeArm": ("P", -1, 0),
    "mixamorig:RightForeArm": ("P", +1, 0),
    "mixamorig:LeftUpLeg": ("R", -1, 100),
    "mixamorig:RightUpLeg": ("R", -1, 100),
    "mixamorig:LeftLeg": ("P", 0, 0),
    "mixamorig:RightLeg": ("P", 0, 0),
    "mixamorig:LeftFoot": ("P", 0, 0),
    "mixamorig:RightFoot": ("P", 0, 0),
    "mixamorig:Spine1": ("R", +1, 0),
    "mixamorig:Spine": ("R", +1, 0),
}

# --- Overrides fijos (opcional) ---
FIXED_OVERRIDES = {}
