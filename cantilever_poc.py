# cantilever_poc.py - A minimal Abaqus Python Scripting PoC

# -----------------------------------------------------
# --- 1. Import Modules and Constants ---
# -----------------------------------------------------
from abaqus import *
from abaqusConstants import *

# -----------------------------------------------------
# --- 2. Define Parametric Input (Future IR Target) ---
# -----------------------------------------------------
MODEL_NAME = 'Cantilever_PoC_3'
PART_LENGTH = 1.0   # meters
PART_WIDTH = 0.1    # meters
PART_HEIGHT = 0.1   # meters
YOUNGS_MODULUS = 200.0E9 # Pa (Pascals - typical for Steel)
POISSON_RATIO = 0.3
TIP_LOAD = 1000.0   # Newtons

# --- NEW: Mesh Control Parameters ---
# Define the *number* of elements along each dimension
N_ELEMENTS_LENGTH = 20  # Number of elements along the beam's length (Z-axis)
N_ELEMENTS_WIDTH = 4   # Number of elements across the beam's width (X-axis)
N_ELEMENTS_HEIGHT = 4  # Number of elements through the beam's height (Y-axis)

# --- NEW: Node Limit Calculator ---
# (N+1) nodes for N elements in each direction
total_nodes = (N_ELEMENTS_LENGTH + 1) * (N_ELEMENTS_WIDTH + 1) * (N_ELEMENTS_HEIGHT + 1)
total_elements = N_ELEMENTS_LENGTH * N_ELEMENTS_WIDTH * N_ELEMENTS_HEIGHT

print(f"--- MESH PRE-CHECK ---")
print(f"Elements: {N_ELEMENTS_LENGTH} (L) x {N_ELEMENTS_WIDTH} (W) x {N_ELEMENTS_HEIGHT} (H) = {total_elements} elements")
print(f"Nodes: {total_nodes} nodes")

if total_nodes > 1000:
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"WARNING: Node count ({total_nodes}) exceeds")
    print(f"Abaqus Learning Edition limit (1000 nodes).")
    print(f"The 'generateMesh' command will fail.")
    print(f"Reduce the N_ELEMENTS... variables.")
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
else:
    print(f"Node count ({total_nodes}) is within the 1000-node limit.")
print(f"------------------------")

# -----------------------------------------------------
# --- 3. Create Model & Part ---
# -----------------------------------------------------
# (No changes in this section)
model = mdb.Model(name=MODEL_NAME)
sketch = model.ConstrainedSketch(name='beamProfile', sheetSize=1.0)
sketch.rectangle(point1=(-PART_WIDTH/2, -PART_HEIGHT/2), point2=(PART_WIDTH/2, PART_HEIGHT/2))
part = model.Part(name='Beam', dimensionality=THREE_D, type=DEFORMABLE_BODY)
part.BaseSolidExtrude(sketch=sketch, depth=PART_LENGTH)

# -----------------------------------------------------
# --- 4. Material and Section ---
# -----------------------------------------------------
# (No changes in this section)
material = model.Material(name='Steel')
material.Elastic(table=((YOUNGS_MODULUS, POISSON_RATIO), ))
section = model.HomogeneousSolidSection(name='BeamSection', material='Steel')
region = (part.cells,)
part.SectionAssignment(region=region, sectionName='BeamSection')

# -----------------------------------------------------
# --- 5. Assembly ---
# -----------------------------------------------------
# (No changes in this section)
assembly = model.rootAssembly
instance = assembly.Instance(name='BeamInstance', part=part, dependent=ON)

# -----------------------------------------------------
# --- 6. Step, Boundary Conditions (BCs), and Load ---
# -----------------------------------------------------
# (No changes in this section)
step = model.StaticStep(name='Step-1', previous='Initial')
fixed_face_geom = instance.faces.findAt(((0.0, 0.0, 0.0),)) 
load_point_geom = instance.vertices.findAt(((PART_WIDTH/2, PART_HEIGHT/2, PART_LENGTH),))
assembly.Set(faces=fixed_face_geom, name='Set-FixedEnd')
fixed_region = model.rootAssembly.sets['Set-FixedEnd']
assembly.Set(vertices=load_point_geom, name='Set-LoadPoint')
load_region = model.rootAssembly.sets['Set-LoadPoint']
model.EncastreBC(name='Fixed', createStepName='Initial', region=fixed_region)
model.ConcentratedForce(name='TipLoad', createStepName='Step-1', 
                        region=load_region, cf3= -TIP_LOAD)

# -----------------------------------------------------
# --- 7. Mesh and Job Submission (Corrected) ---
# -----------------------------------------------------
# --- This section is heavily modified ---

# 1. Assign element controls for a structured hex mesh
part.setMeshControls(regions=part.cells, elemShape=HEX, technique=STRUCTURED)

# 2. Find all 12 edges and group them by direction
#    We use findAt() to grab the edges at their approximate mid-points.
W, H, L = PART_WIDTH, PART_HEIGHT, PART_LENGTH
W2, H2, L2 = W/2.0, H/2.0, L/2.0

# Find the 4 edges running along the LENGTH (Z-axis)
edges_len_1 = part.edges.findAt(coordinates=( W2,  H2, L2))
edges_len_2 = part.edges.findAt(coordinates=(-W2,  H2, L2))
edges_len_3 = part.edges.findAt(coordinates=(-W2, -H2, L2))
edges_len_4 = part.edges.findAt(coordinates=( W2, -H2, L2))
length_edges = (edges_len_1, edges_len_2, edges_len_3, edges_len_4)

# Find the 4 edges running along the WIDTH (X-axis)
edges_wid_1 = part.edges.findAt(coordinates=( 0,  H2, 0))
edges_wid_2 = part.edges.findAt(coordinates=( 0, -H2, 0))
edges_wid_3 = part.edges.findAt(coordinates=( 0,  H2, L))
edges_wid_4 = part.edges.findAt(coordinates=( 0, -H2, L))
width_edges = (edges_wid_1, edges_wid_2, edges_wid_3, edges_wid_4)

# Find the 4 edges running along the HEIGHT (Y-axis)
edges_hgt_1 = part.edges.findAt(coordinates=( W2, 0, 0))
edges_hgt_2 = part.edges.findAt(coordinates=(-W2, 0, 0))
edges_hgt_3 = part.edges.findAt(coordinates=( W2, 0, L))
edges_hgt_4 = part.edges.findAt(coordinates=(-W2, 0, L))
height_edges = (edges_hgt_1, edges_hgt_2, edges_hgt_3, edges_hgt_4)

# 3. Apply seeds by *number* to each group of edges
part.seedEdgeByNumber(edges=length_edges, number=N_ELEMENTS_LENGTH, constraint=FIXED)
part.seedEdgeByNumber(edges=width_edges, number=N_ELEMENTS_WIDTH, constraint=FIXED)
part.seedEdgeByNumber(edges=height_edges, number=N_ELEMENTS_HEIGHT, constraint=FIXED)

# 4. Generate the mesh on the part
part.generateMesh()
# 

# --- Job Submission ---
job = mdb.Job(name=MODEL_NAME, model=MODEL_NAME, type=ANALYSIS)

# NOTE: To run in non-GUI mode, uncomment these lines:
# job.submit(consistencyChecking=OFF)
# job.waitForCompletion() 

print(f"Abaqus model '{MODEL_NAME}' created and meshed successfully.")
print(f"Run the script in Abaqus/CAE using File > Run Script to execute.")