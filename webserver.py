# ============================================
# Web server to show saved 3D visualization of the model
# ============================================

# Modules import
# ============================================
from pathlib import Path # Crossplatform pathing
import vtk # Use 3D-visualization features
import pandas as pd # Use pandas for data processing
from trame.app import get_server # Use Trame for web-server
from trame.ui.vuetify import SinglePageLayout # Use Vuetify for web-interface
from trame.widgets import vuetify, vtk as vtk_widgets # Use VTK for 3D-visualization
import re # Use regular expressions
from vtkmodules.util import numpy_support

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition

# VTK objects
renderer = vtk.vtkRenderer()

# ============================================
# Vizualize points from .csv file with 3D-glyph, color and opacity
# ============================================
def VizualizePoints(fileP, glyph, color, opacity):
    # Read .csv file with points coordinates
    df = pd.read_csv(Path('.',cfg.folderOUTPUT,fileP))
    points = vtk.vtkPoints()
    # Convert pandas DataFrame to vtkDataArray without loop
    vtk_array = numpy_support.numpy_to_vtk(df[["x", "y", "z"]].to_numpy(), deep=True, array_type=vtk.VTK_FLOAT)
    # Set vtkDataArray to vtkPoints
    points.SetData(vtk_array)
    #for _, row in df.iterrows():
    #    points.InsertNextPoint(row["x"], row["y"], row["z"])
    # Put Voxels on intersection points
    polyData = vtk.vtkPolyData()
    polyData.SetPoints(points)
    glyphs = vtk.vtkGlyph3D()
    glyphs.SetInputData(polyData)
    glyphs.SetSourceConnection(glyph.GetOutputPort())
    glyphs.ScalingOff()
    glyphs.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(glyphs.GetOutputPort())
    mapper.ScalarVisibilityOff()
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    actor.GetProperty().SetOpacity(opacity)
    renderer.AddActor(actor)
    print(f"{fileP} loaded")

# Function to enforce y-axis as vertical
def enforce_y_axis_vertical(**kwargs):
    print("s\n")
    camera = renderer.GetActiveCamera()
    camera.SetViewUp(0, 1, 0)  # Ensure y-axis is vertical
    renderer.ResetCameraClippingRange()
    
# ============================================
# Read .vtp files with mesh of earth surface
# Generate VTK-objects of 3D-surface with textures
# ============================================
for fileP in Path('.',cfg.folderOUTPUT).glob("*.vtp", case_sensitive=False):
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(fileP)
    reader.Update()
    polydata = reader.GetOutput()

    # Find raster file name from .vtp file name
    file_name = fileP.stem  # Get the file name without extension
    match = re.match(r"(\d+)_?(.*)", file_name)
    if match:
        index = match.group(1)  # One or more digits
        fileR = Path('.',cfg.folderRASTER,match.group(2))  # All other characters after '_'

    imageReader = env.readerFactory.CreateImageReader2(str(fileR))
    imageReader.SetFileName(fileR)
    imageReader.Update()

    texture = vtk.vtkTexture()
    texture.SetInputConnection(imageReader.GetOutputPort())
    texture.InterpolateOn()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetTexture(texture)
    actor.GetProperty().SetOpacity(1)
    renderer.AddActor(actor)
    print(f"{fileR} loaded")

# ============================================
# Read .csv files with points coordinates
# Generate VTK-objects of squares, voxels and megaphones
# ============================================'''
planeSquare = vtk.vtkPlaneSource()
planeSquare.SetOrigin(0, 0, 0)
planeSquare.SetPoint1(cfg.sizeVoxel, 0, 0)
planeSquare.SetPoint2(0, 0, cfg.sizeVoxel)
VizualizePoints('sq_full.csv', planeSquare, env.Colors.GetColor3d("Green"), 0.5)
planeSquare = vtk.vtkPlaneSource()
planeSquare.SetOrigin(0, 0, 0)
planeSquare.SetPoint1(cfg.sizeVoxel, 0, 0)
planeSquare.SetPoint2(0, 0, cfg.sizeVoxel)
VizualizePoints('sq_only.csv', planeSquare, env.Colors.GetColor3d("Gold"), 0.5)
planeSquare = vtk.vtkPlaneSource()
planeSquare.SetOrigin(0, 0, 0)
planeSquare.SetPoint1(cfg.sizeVoxel, 0, 0)
planeSquare.SetPoint2(0, 0, cfg.sizeVoxel)
VizualizePoints('sq_no.csv', planeSquare, env.Colors.GetColor3d("Tomato"), 0.5)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_yes.csv', cubeVoxel, env.Colors.GetColor3d("Green"), 1.0)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_no.csv', cubeVoxel, env.Colors.GetColor3d("Tomato"), 1.0)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_industrial.csv', cubeVoxel, env.Colors.GetColor3d("Gray"), 1.0)
coneMegaphone = vtk.vtkConeSource()
coneMegaphone.SetDirection(0, 1, 0)
coneMegaphone.SetHeight(cfg.sizeVoxel)
coneMegaphone.SetRadius(cfg.sizeVoxel/4)
VizualizePoints('mgphn_buildings.csv', coneMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)
coneMegaphone = vtk.vtkConeSource()
coneMegaphone.SetDirection(0, 1, 0)
coneMegaphone.SetHeight(cfg.heightStansaloneMegaphone)
coneMegaphone.SetRadius(cfg.sizeVoxel)
VizualizePoints('mgphn_standalone.csv', coneMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)
sphereMegaphone = vtk.vtkSphereSource()
sphereMegaphone.SetRadius(cfg.sizeVoxel/4)
VizualizePoints('mgphn_spehres.csv', sphereMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)
'''
# Paths
output_dir = "OUTPUT"
vox_csv_path = os.path.join(output_dir, "vox_yes.csv")
result_txt_path = os.path.join(output_dir, "result.txt")


# VTK pipeline
reader = vtk.vtkXMLPolyDataReader()
glyph_source = vtk.vtkCubeSource()
glyph_mapper = vtk.vtkGlyph3DMapper()
glyph_actor = vtk.vtkActor()
renderer = vtk.vtkRenderer()

# Load .vtp files
for file in os.listdir(output_dir):
    if file.endswith(".vtp"):
        reader.SetFileName(os.path.join(output_dir, file))
        reader.Update()
        polydata = reader.GetOutput()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        renderer.AddActor(actor)

# Process vox_yes.csv for glyphs
if os.path.exists(vox_csv_path):
    df = pd.read_csv(vox_csv_path)
    points = vtk.vtkPoints()
    for _, row in df.iterrows():
        points.InsertNextPoint(row["x"], row["y"], row["z"])
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    glyph_mapper.SetInputData(polydata)
    glyph_mapper.SetSourceConnection(glyph_source.GetOutputPort())
    glyph_mapper.SetScaleFactor(2)
    glyph_actor.SetMapper(glyph_mapper)
    glyph_actor.GetProperty().SetColor(0, 1, 0)  # Green color
    renderer.AddActor(glyph_actor)

# Read result.txt for bottom text
result_text = ""
if os.path.exists(result_txt_path):
    with open(result_txt_path, "r") as file:
        result_text = file.read()
'''

#render_window = vtk.vtkRenderWindow()
#render_window.AddRenderer(renderer)

# Create VTK pipeline
#cone_source = vtk.vtkConeSource()
#mapper = vtk.vtkPolyDataMapper()
#mapper.SetInputConnection(cone_source.GetOutputPort())
#actor = vtk.vtkActor()
#actor.SetMapper(mapper)

# VTK Renderer
#renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
renderer.ResetCamera()
renderer.SetBackground(0.2, 0.3, 0.4)  # Dark blue background

# VTK Render Window
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)

interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)
#interactor.SetInteractorStyle(vtk.vtkInteractorStyleTerrain())
interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
renderer.ResetCamera()

# Initialize server
server = get_server(client_type="vue2")
#server.port = 5000
state, ctrl = server.state, server.controller

'''
def on_camera_change(**kwargs):
    """Called when camera changes"""
    print("Camera changed!")
    print("Position:", state.camera_position)
    print("Focal Point:", state.camera_focal_point)
    print("View Up:", state.camera_view_up)

# Listen to state changes for camera properties
state.change("camera_position")(on_camera_change)
state.change("camera_focal_point")(on_camera_change)
state.change("camera_view_up")(on_camera_change)
'''

# Configure Trame UI
with SinglePageLayout(server) as layout:
    #layout.title.set("3D Viewer")
    #with layout.content:
    #    vtk_widgets.VtkRemoteView(renderer)
    layout.title.set_text("Rotating Cone")
    with layout.content:
        with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
            view = vtk_widgets.VtkRemoteView(render_window)
            #ctrl.on_server_ready.add(enforce_y_axis_vertical)
            #ctrl.on_camera_update.add(enforce_y_axis_vertical)
            
    #with layout.footer:
    #    layout.footer.add_child(f"<div>{result_text}</div>")
   # Get VTK camera after view initialization

'''
@ctrl.trigger("on_server_ready")
def setup_camera_listener():
    renderer = render_window.GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    
    def camera_modified(obj, event):
        state.camera_position = obj.GetPosition()
        state.camera_focal_point = obj.GetFocalPoint()
        state.camera_view_up = obj.GetViewUp()
    
    camera.AddObserver(vtk.vtkCommand.ModifiedEvent, camera_modified)
'''
# Start server
if __name__ == "__main__":
    server.start()
