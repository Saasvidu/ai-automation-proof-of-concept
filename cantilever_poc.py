# cantilever_poc.py - A minimal Abaqus Python Scripting PoC

# -----------------------------------------------------
# --- 1. Import Modules and Constants ---
# -----------------------------------------------------
from abaqus import *
from abaqusConstants import *
# Note: This is required to access the Model and Session objects

# -----------------------------------------------------
# --- 2. Define Parametric Input (Future IR Target) ---
# -----------------------------------------------------
MODEL_NAME = 'Cantilever_PoC'
PART_LENGTH = 1.0  # meters
PART_WIDTH = 0.1  # meters
PART_HEIGHT = 0.1  # meters
YOUNGS_MODULUS = 200.0E9  # Pa (Pascals - typical for Steel)
POISSON_RATIO = 0.3
TIP_LOAD = 1000.0  # Newtons

# -----------------------------------------------------
# --- 3. Create Model & Part ---
# -----------------------------------------------------
# Create a new model
model = mdb.Model(name=MODEL_NAME)

# Create a sketch for the cross-section
sketch = model.ConstrainedSketch(name='beamProfile', sheetSize=1.0)
sketch.rectangle(point1=(-PART_WIDTH/2, -PART_HEIGHT/2), point2=(PART_WIDTH/2, PART_HEIGHT/2))

# Create a 3D, deformable part by extruding the sketch
part = model.Part(name='Beam', dimensionality=THREE_D, type=DEFORMABLE_BODY)
part.BaseSolidExtrude(sketch=sketch, depth=PART_LENGTH)

# -----------------------------------------------------
# --- 4. Material and Section ---
# -----------------------------------------------------
# Create a simple Elastic material
material = model.Material(name='Steel')
material.Elastic(table=((YOUNGS_MODULUS, POISSON_RATIO), ))

# Create a homogeneous solid section and assign it to the part
section = model.HomogeneousSolidSection(name='BeamSection', material='Steel')
region = (part.cells,)
part.SectionAssignment(region=region, sectionName='BeamSection')

# -----------------------------------------------------
# --- 5. Assembly ---
# -----------------------------------------------------
# Create a part instance in the assembly
assembly = model.rootAssembly
instance = assembly.Instance(name='BeamInstance', part=part, dependent=ON)

# -----------------------------------------------------
# --- 6. Step, Boundary Conditions (BCs), and Load ---
# -----------------------------------------------------
# Create a Static step
step = model.StaticStep(name='Step-1', previous='Initial')

# Define geometric sequences using coordinates
# Fixed end (x=0). Find the face.
fixed_face_geom = instance.faces.findAt(((0.0, 0.0, 0.0),)) 

# Loaded end (x=L). Find the vertex.
load_point_geom = instance.vertices.findAt(((PART_WIDTH/2, PART_HEIGHT/2, PART_LENGTH),))

# --- IMPORTANT FIX: Create Sets/Regions from Geometry Sequences ---
# Create a SET for the fixed face
assembly.Set(faces=fixed_face_geom, name='Set-FixedEnd')
fixed_region = model.rootAssembly.sets['Set-FixedEnd']

# Create a SET for the load point (vertex)
assembly.Set(vertices=load_point_geom, name='Set-LoadPoint')
load_region = model.rootAssembly.sets['Set-LoadPoint']

# Apply Fixed BC (ENCASTRE) using the newly created region object
model.EncastreBC(name='Fixed', createStepName='Initial', 
                 region=fixed_region, localCsys=None)

# Apply Concentrated Load (CF) at the tip vertex using the load region
model.ConcentratedForce(name='TipLoad', createStepName='Step-1', 
                        region=load_region, 
                        cf3= -TIP_LOAD, # Load in the -Z direction
                        distributionType=UNIFORM)

# -----------------------------------------------------
# --- 7. Mesh and Job Submission (Corrected) ---
# -----------------------------------------------------
# Seed the part instance
assembly.seedPartInstance(regions=(instance,), size=PART_HEIGHT/5.0) 
assembly.generateMesh(regions=(instance,))

# Create an analysis job and submit it
job = mdb.Job(name=MODEL_NAME, model=MODEL_NAME, type=ANALYSIS)
# NOTE: To run in non-GUI mode, you can use:
# job.submit(consistencyChecking=OFF)
# job.waitForCompletion() 

print(f"Abaqus model '{MODEL_NAME}' created successfully.")
print(f"Run the script in Abaqus/CAE using File > Run Script to execute the model creation.")