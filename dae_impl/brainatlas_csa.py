#!/usr/bin/env python
import os, sys, traceback, math, httplib, urllib, zipfile, StringIO
from time import localtime, strftime, time

import numpy
import numpy.random

import vtk
from vtk.hybrid import vtkVRMLImporter
try:
    import enthought.mayavi as mayavi
    from enthought.mayavi import mlab
    from enthought.tvtk.api import tvtk
    from enthought.mayavi.sources.vrml_importer import VRMLImporter
    from enthought.mayavi.api import Engine
    from enthought.mayavi.sources.vtk_data_source import VTKDataSource
    from enthought.mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
    from enthought.traits.api import HasTraits, Trait, Range, Instance, on_trait_change, Array, Tuple, Str
    from enthought.traits.ui.api import View, Item, HSplit, Group, HGroup
    from enthought.tvtk.pyface.picker import Picker, DefaultPickHandler, PickHandler
except ImportError as e:
    print "Error: Cannot load enthought module; trying to load mayavi module instead..."
    try:
        from mayavi import mlab
        from tvtk.api import tvtk
        from mayavi.sources.vrml_importer import VRMLImporter
        from mayavi.api import Engine
        from mayavi.sources.vtk_data_source import VTKDataSource
        from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
        from traits.api import HasTraits, Trait, Range, Instance, on_trait_change, Array, Tuple, Str
        from traitsui.api import View, Item, HSplit, Group, HGroup
        from tvtk.pyface.picker import Picker, DefaultPickHandler, PickHandler
    except ImportError as e:
        print str(e)
        print "Cannot load Mayavi module. Aborting..."
        sys.exit()

import nineml
import nineml.connection_generator as connection_generator
import nineml.geometry as geometry
from nineml.user_layer_aux import ConnectionGenerator
from nineml.user_layer_aux import grids

from lxml import etree
from lxml.builder import E

import csa

class vtkPointsGeometry(geometry.Geometry):
    """
    Implementation of the Geometry interface, vtkPoints objects wrapper.
    """
    def __init__(self, source_vtkpoints, target_vtkpoints):
        self.source_vtkpoints = source_vtkpoints
        self.target_vtkpoints = target_vtkpoints
    
    def metric(self, source_index, target_index):
        (x1, y1, z1) = self.source_vtkpoints.GetPoint(source_index)
        (x2, y2, z2) = self.target_vtkpoints.GetPoint(target_index)
        return math.sqrt( (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2 )
    
    def sourcePosition(self, index):
        return self.source_vtkpoints.GetPoint(index)
    
    def targetPosition(self, index):
        return self.target_vtkpoints.GetPoint(index)

class Projection(object):
    def __init__(self, target_vrml_filename):
        self.figure = mlab.figure()
        self.figure.on_mouse_pick(self.picker_callback)

        self.cube_d          = 0.10 # [mm]
        self.neurone_radius  = 0.01 # [mm]
        self.central_neurone = 0
        
        self.neurones   = []
        self.actors     = []
        self.lineActors = []
        
        self.target_vrml_filename = target_vrml_filename
        
        target_actor, target_dataset, target_vtkpoints = Projection.loadVRMLFile(target_vrml_filename)
        
        tomatoProp = vtk.vtkProperty()
        tomatoProp.SetDiffuseColor(vtk.util.colors.tomato)
        
        _radius     = 0.70 # [mm]
        _resolution = 30
        _x = 2
        _y = 0
        _z = 3.25
        
        sphere = vtk.vtkSphere()
        sphere.SetRadius(_radius)
        sphere.SetCenter(_x, _y, _z)
        
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetRadius(_radius)
        sphereSource.SetCenter(_x, _y, _z)
        sphereSource.SetThetaResolution(_resolution)
        sphereSource.SetPhiResolution(_resolution)
        
        sphereMapper = vtk.vtkPolyDataMapper()
        sphereMapper.SetInput(sphereSource.GetOutput())
        sphereMapper.ScalarVisibilityOff()
        
        sphereActor = vtk.vtkActor()
        sphereActor.SetMapper(sphereMapper)
        sphereActor.GetProperty().SetColor(vtk.util.colors.yellow)
        
        clipCortex = vtk.vtkClipPolyData()
        clipCortex.SetInput(target_dataset)
        clipCortex.SetClipFunction(sphere)
        clipCortex.GenerateClipScalarsOn()
        clipCortex.GenerateClippedOutputOn()
        #clipCortex.SetValue(0.5)
        
        clipPoly = clipCortex.GetClippedOutput()
        clipPoly.Update()

        cutMapper = vtk.vtkPolyDataMapper()
        cutMapper.SetInputConnection(clipCortex.GetClippedOutputPort())
        cutMapper.ScalarVisibilityOff()
        
        cutActor = vtk.vtkActor()
        cutActor.SetMapper(cutMapper)
        cutActor.GetProperty().SetColor(vtk.util.colors.peacock)
        cutActor.SetBackfaceProperty(tomatoProp)
       
        # ACHTUNG, ACHTUNG!!
        # All dimensions are in milimeters
        polySphere = sphereSource.GetOutput()
        polySphere.Update()
        
        xl, xh, yl, yh, zl, zh = polySphere.GetBounds()
        
        nx = int(abs(xh - xl) / self.cube_d) + 1
        ny = int(abs(yh - yl) / self.cube_d) + 1
        nz = int(abs(zh - zl) / self.cube_d) + 1
        
        print xl, xh, yl, yh, zl, zh
        print nx, ny, nz
        
        neuronesPoly = vtk.vtkPolyData()
        points       = vtk.vtkPoints()
        vertices     = vtk.vtkCellArray()
        
        rng = numpy.random.RandomState()
        rng.seed(100)
        
        for ix in range(0, nx):
            for iy in range(0, ny):
                for iz in range(0, nz):
                    x0 = xl + self.cube_d * (ix    ) + self.neurone_radius
                    x1 = xl + self.cube_d * (ix + 1) - self.neurone_radius
                    xc = rng.uniform(x0, x1)
                    
                    y0 = yl + self.cube_d * (iy    ) + self.neurone_radius
                    y1 = yl + self.cube_d * (iy + 1) - self.neurone_radius
                    yc = rng.uniform(y0, y1)
                    
                    z0 = zl + self.cube_d * (iz    ) + self.neurone_radius
                    z1 = zl + self.cube_d * (iz + 1) - self.neurone_radius
                    zc = rng.uniform(z0, z1)
                    
                    pid = points.InsertNextPoint(xc, yc, zc)
                    vertices.InsertNextCell(1)
                    vertices.InsertCellPoint(pid)
        
        neuronesPoly.SetPoints(points)
        neuronesPoly.SetVerts(vertices)
        neuronesPoly.Update()
        
        neuronesMapper = vtk.vtkPolyDataMapper()
        neuronesMapper.SetInput(neuronesPoly)
        
        neuronesActor = vtk.vtkActor()
        neuronesActor.SetMapper(neuronesMapper)
        neuronesActor.GetProperty().SetColor(vtk.util.colors.white)

        neuronesClipper = vtk.vtkClipPolyData()
        neuronesClipper.SetInput(neuronesPoly)
        neuronesClipper.SetClipFunction(sphere)
        neuronesClipper.GenerateClipScalarsOn()
        neuronesClipper.GenerateClippedOutputOn()
        
        clean = vtk.vtkCleanPolyData()
        clean.PointMergingOff()
        clean.ConvertLinesToPointsOff()
        clean.SetInputConnection(neuronesClipper.GetClippedOutputPort())
        clippedNeuronesPoly = clean.GetOutput()
        clippedNeuronesPoly.Update()
        
        neurone_points = clippedNeuronesPoly.GetPoints()
        N = neurone_points.GetNumberOfPoints()
        
        append = vtk.vtkAppendPolyData()
        for i in  xrange(0, neurone_points.GetNumberOfPoints()):
            x, y, z = neurone_points.GetPoint(i)
            
            self.neurones.append( (xc, yc, zc) )
            
            neuroneSource = vtk.vtkSphereSource()
            neuroneSource.SetRadius(self.neurone_radius)
            neuroneSource.SetCenter(x, y, z)
            append.AddInput(neuroneSource.GetOutput())
                
        extractedNeuronesMapper = vtk.vtkPolyDataMapper()
        extractedNeuronesMapper.SetInputConnection(append.GetOutputPort())
        
        extractedNeuronesActor = vtk.vtkActor()
        extractedNeuronesActor.SetMapper(extractedNeuronesMapper)
        extractedNeuronesActor.GetProperty().SetColor(vtk.util.colors.yellow)
        extractedNeuronesActor.SetBackfaceProperty(tomatoProp)
        
        neuronesActor.GetProperty().SetRepresentationToSurface()
        extractedNeuronesActor.GetProperty().SetRepresentationToSurface()
        cutActor.GetProperty().SetRepresentationToSurface()
        sphereActor.GetProperty().SetRepresentationToWireframe()
        target_actor.GetProperty().SetRepresentationToPoints()
        
        self.actors.append(tvtk.to_tvtk(target_actor))
        #self.actors.append(tvtk.to_tvtk(neuronesActor))
        self.actors.append(tvtk.to_tvtk(cutActor))
        #self.actors.append(tvtk.to_tvtk(sphereActor))
        self.actors.append(tvtk.to_tvtk(extractedNeuronesActor))
        
        self.Ns = neurone_points.GetNumberOfPoints()
        self.Nt = neurone_points.GetNumberOfPoints()
        print('Ns = {0}, Nt = {1}'.format(self.Ns, self.Nt))
        
        self.geometry = vtkPointsGeometry(neurone_points, neurone_points)
        print('Metric({0},{1}) = {2}'.format(0, 5, self.geometry.metric(0, 5)))
        
        # This will generate connections for the source neurone with the index = 0
        # Can be anything within the range [0, self.Ns)
        self.central_neurone = 0
        self.createCSAConnections(self.central_neurone)
        
    def picker_callback(self, picker_obj):
        picked = picker_obj.actors
        for obj in [o._vtk_obj for o in picked]:
            print type(obj)
    
    def createCSAConnections(self, source_index):
        if source_index >= self.Ns:
            raise RuntimeError('Source index out of bounds')
        
        p      = 0.02 # fraction
        weight = 0.04 # nS
        delay  = 0.20 # ms
        
        cset = csa.cset(csa.random(p), weight, delay)
        cgi  = csa.CSAConnectionGenerator(cset)
        mask = connection_generator.Mask([(source_index, source_index)], [(0, self.Nt - 1)])
        cgi.setMask(mask)
        print 'CG: length = {0}, arity = {1}'.format(len(cgi), cgi.arity)
        
        self.lineActors = []
        
        for connection in cgi:
            size = len(connection)
            if(size < 2):
                raise RuntimeError('Not enough data in the explicit lists of connections')
            
            source_index = int(connection[0])
            target_index = int(connection[1])
            weight       = 0.0
            delay        = 0.0
            parameters   = []
            
            if cgi.arity == 1:
                weight = float(connection[2]) * 1E-6 # nS -> S
            elif cgi.arity == 2:
                weight = float(connection[2]) * 1E-6 # nS -> S
                delay  = float(connection[3]) * 1E-3 # ms -> s
            elif cgi.arity >= 3:
                weight = float(connection[2]) * 1E-6 # nS -> S
                delay  = float(connection[3]) * 1E-3 # ms -> s
                for i in range(4, size):
                    parameters.append(float(connection[i]))           
            
            x1, y1, z1 = self.geometry.sourcePosition(source_index)
            x2, y2, z2 = self.geometry.targetPosition(target_index)
            
            line       = tvtk.LineSource(point1=(x1, y1, z1), point2=(x2, y2, z2))
            lineMapper = tvtk.PolyDataMapper(input=line.output)
            lineActor  = tvtk.Actor(mapper=lineMapper)
            
            self.lineActors.append(lineActor)

    def plot(self):
        # Add actors 
        self.figure.scene.add_actors(self.actors)
        self.figure.scene.add_actors(self.lineActors)
        
        # Fit everything into a window
        self.figure.scene.reset_zoom()
    
    @staticmethod
    def retreiveFrom_3dbar(cafDatasetName, structureName, qualityPreset = 'high', outputFormat = 'vrml'):
        dict_parameters = {'cafDatasetName' : str(cafDatasetName),
                           'structureName'  : str(structureName),
                           'qualityPreset'  : str(qualityPreset),
                           'outputFormat'   : str(outputFormat)
                          }
        headers = {'User-Agent'  : 'WebService Application/1.0',
                   'Accept'      : 'application/zip'}
        
        http_connection = httplib.HTTPConnection('www.3dbar.org', 8080)
        #http_connection.set_debuglevel(5)
        parameters = urllib.urlencode(dict_parameters)
        http_connection.request('GET', '/getReconstruction?%s' % parameters, None, headers)

        response = http_connection.getresponse()
        if(response.status != 200):
            raise RuntimeError('The http request to www.3dbar.org failed: {0} {1}'.format(response.status, response.reason))

        content_type = response.getheader('Content-type', '')
        content_disposition = response.getheader('content-disposition', '')
        #print("response: ", str(response.getheaders()))

        outputFileName = None
        if content_type == 'application/x-download':
            zip_file = StringIO.StringIO(response.read())
            z = zipfile.ZipFile(zip_file, 'r')
            for filename in z.namelist():
                if '.wrl' in filename:
                    outputFileName = filename
                    z.extract(filename)
                    print('From: [{0}]; extracted file: [{1}]'.format(content_disposition, filename))
                    break

        http_connection.close()
        return outputFileName

    @staticmethod
    def loadVRMLFile(wrl_filename):
        """
        Opens a .wrl file, reads the points from it,  
        and returns vtkActor, vtkPolyData and vtkPoints objects
        """
        vrml = vtkVRMLImporter()
        vrml.SetFileName(wrl_filename)
        vrml.Read()
        vrml.Update()
        actors = vrml.GetRenderer().GetActors()
        actors.InitTraversal()
        actor = actors.GetNextActor()
        dataset = actor.GetMapper().GetInput()
        dataset.Update()
        #print dataset
        vtkpoints = dataset.GetPoints() 
        Np = vtkpoints.GetNumberOfPoints()
        return actor, dataset, vtkpoints
    
if __name__ == "__main__":
    try:
        from incf.dai.utils import list_hub_names, get_hub_by_name
        #print sorted(list_hub_names())

        whs = get_hub_by_name('whs')
        print sorted(whs.capabilities)

        response = whs.GetStructureNamesByPOI(format=None, srsName="Mouse_paxinos_1.0", x='1', y='4.3', z='1.78')
        #print response.content
        structureTerm = response.data['wps_ProcessOutputs']['wps_Output']['wps_Data']['wps_ComplexData']['StructureTermsResponse']['StructureTerms']['StructureTerm']

        #print structureTerm.Code
        #print structureTerm.Description
        #print structureTerm.Feature
        print structureTerm.Feature.Url
    
    except Exception as e:
        print str(e)
    
    scene_Cx  = 'scene_Cx.wrl'
    if not os.path.isfile(scene_Cx):
        Projection.retreiveFrom_3dbar('whs_0.5', 'Cx',  'high', 'vrml')
    
    p = Projection(scene_Cx)
    p.plot()
    mlab.show()
    
