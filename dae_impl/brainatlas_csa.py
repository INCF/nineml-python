#!/usr/bin/env python
import os, sys, traceback, math, httplib, urllib, zipfile, StringIO
from time import localtime, strftime, time

import numpy

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
except ImportError:
    from mayavi import mlab
    from tvtk.api import tvtk
    from mayavi.sources.vrml_importer import VRMLImporter
    from mayavi.api import Engine
    from mayavi.sources.vtk_data_source import VTKDataSource
    from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
    from traits.api import HasTraits, Trait, Range, Instance, on_trait_change, Array, Tuple, Str
    from traitsui.api import View, Item, HSplit, Group, HGroup
    from tvtk.pyface.picker import Picker, DefaultPickHandler, PickHandler

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
    def __init__(self, source_vrml_filename, target_vrml_filename):
        self.figure = mlab.figure()
        self.figure.on_mouse_pick(self.picker_callback)

        self.lineActors = []
        
        self.source_vrml_filename = source_vrml_filename
        self.target_vrml_filename = target_vrml_filename
        
        source_actor, source_dataset, source_vtkpoints = Projection.loadVRMLFile(source_vrml_filename)
        target_actor, target_dataset, target_vtkpoints = Projection.loadVRMLFile(target_vrml_filename)
        
        cylinder = vtk.vtkCylinder()
        cylinder.SetRadius(1)
        cylinder.SetCenter(0, 0, 0)
        rotate = vtk.vtkTransform()
        rotate.RotateX(90)
        cylinder.SetTransform(rotate)
        
        plane = vtk.vtkPlane()
        plane.SetOrigin(0, 0, 2)
        plane.SetNormal(0, 0, 1)
        
        planeClipper = vtk.vtkClipPolyData()
        planeClipper.SetInput(target_dataset)
        planeClipper.SetClipFunction(plane)
        planeClipper.GenerateClipScalarsOn()
        planeClipper.GenerateClippedOutputOn()
        planeClipper.SetValue(0.5)
        
        #print planeClipper.GetOutput()
        cylinderClipper = vtk.vtkClipPolyData()
        cylinderClipper.SetInput(planeClipper.GetOutput())
        cylinderClipper.SetClipFunction(cylinder)
        cylinderClipper.GenerateClipScalarsOn()
        cylinderClipper.GenerateClippedOutputOn()
        cylinderClipper.SetValue(0.5)
        
        """
        cutStrips = vtk.vtkStripper()
        cutStrips.SetInputConnection(cylinderClipper.GetClippedOutputPort())
        cutStrips.Update()
        cutPoly = vtk.vtkPolyData()
        cutPoly.SetPoints(cutStrips.GetOutput().GetPoints())
        cutPoly.SetPolys(cutStrips.GetOutput().GetLines())
        """
        out = cylinderClipper.GetClippedOutput()
        out.Update()
        
        # ACHTUNG, ACHTUNG!!
        # Bounds are in milimeters
        # Get the cube enclosing the cut part and generate neurones uniformly, every 50um
        xl, xh, yl, yh, zl, zh = out.GetBounds()
        nx = int(abs(xh - xl) * 1E-3 / 50E-6)
        ny = int(abs(yh - yl) * 1E-3 / 50E-6)
        nz = int(abs(zh - zl) * 1E-3 / 50E-6)
        print xl, xh, yl, yh, zl, zh
        print nx, ny, nz
        #grid = numpy.mgrid[xl : xh : nx * 1j, yl : yh : ny * 1j, zl : zh : nz * 1j]
        #print grid.shape, grid
        
        poly = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        vertices = vtk.vtkCellArray()
        for x in range(0, nx+1):
            for y in range(0, ny+1):
                for z in range(0, nz+1):
                    pid = points.InsertNextPoint(xl + 50E-3*x, yl + 50E-3*y, zl + 50E-3*z)
                    vertices.InsertNextCell(1)
                    vertices.InsertCellPoint(pid)
        #print points
        poly.SetPoints(points)
        poly.SetVerts(vertices)
        
        neuronesMapper = vtk.vtkPolyDataMapper()
        neuronesMapper.SetInput(poly)
        
        neuronesActor = vtk.vtkActor()
        neuronesActor.SetMapper(neuronesMapper)
        neuronesActor.GetProperty().SetColor(vtk.util.colors.green)
        neuronesActor.GetProperty().SetRepresentationToPoints()
        
        clipMapper = vtk.vtkPolyDataMapper()
        clipMapper.SetInputConnection(cylinderClipper.GetClippedOutputPort())
        clipMapper.ScalarVisibilityOff()
        
        backProp = vtk.vtkProperty()
        backProp.SetDiffuseColor(vtk.util.colors.tomato)
        
        cylinderActor = vtk.vtkActor()
        cylinderActor.SetMapper(clipMapper)
        cylinderActor.GetProperty().SetColor(vtk.util.colors.peacock)
        cylinderActor.SetBackfaceProperty(backProp)

        #clippedMapper = vtk.vtkPolyDataMapper()
        #clippedMapper.SetInputConnection(clipper.GetOutputPort())
        #clippedMapper.ScalarVisibilityOff()
        #
        #cortexActor = vtk.vtkActor()
        #cortexActor.SetMapper(clippedMapper)
        #cortexActor.GetProperty().SetRepresentationToPoints()
        target_actor.GetProperty().SetRepresentationToPoints()

        """
        out = target_dataset
        out.Update()
        cellArray = out.GetPolys()
        cellArray.InitTraversal()
        print cellArray
        print cellArray.GetNumberOfCells() 

        extrude = vtk.vtkLinearExtrusionFilter()
        extrude.SetInput(target_dataset)
        extrude.SetScaleFactor(0.1)
        extrude.CappingOn()
        extrude.SetExtrusionTypeToNormalExtrusion()
        #extrude.SetVector(1, 0, 0)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(extrude.GetOutput())           
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetRepresentationToPoints()
        
        out = extrude.GetOutput()
        out.Update()
        cellArray = out.GetPolys()
        cellArray.InitTraversal()
        print cellArray
        print cellArray.GetNumberOfCells() 
        """

        self.source_actor  = tvtk.to_tvtk(source_actor)
        self.cylinderActor = tvtk.to_tvtk(cylinderActor)
        self.cortexActor   = tvtk.to_tvtk(target_actor)
        self.neuronesActor = tvtk.to_tvtk(neuronesActor)
        
        self.source_dataset = source_dataset
        self.target_dataset = target_dataset
        
        self.Ns = source_vtkpoints.GetNumberOfPoints()
        self.Nt = target_vtkpoints.GetNumberOfPoints()
        print('Ns = {0}, Nt = {1}'.format(self.Ns, self.Nt))
        
        self.geometry = vtkPointsGeometry(source_vtkpoints, target_vtkpoints)
        print('Metric({0},{1}) = {2}'.format(0, 5, self.geometry.metric(0, 5)))
        
        # This will generate connections for the source neurone with the index = 0
        # Can be anything within the range [0, self.Ns)
        self.createCSAConnections(0)
        self.plot()
        
    def picker_callback(self, picker_obj):
        picked = picker_obj.actors
        for obj in [o._vtk_obj for o in picked]:
            print type(obj)
    
    def createCSAConnections(self, source_index):
        if source_index >= self.Ns:
            raise RuntimeError('Source index out of bounds')
        
        p      = 0.002 # fraction
        weight = 0.040 # nS
        delay  = 0.200 # ms
        
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
        # Add CSA connection lines 
        #self.figure.scene.add_actors(self.lineActors)
        
        # Add the source volume 
        #self.figure.scene.add_actor(self.source_actor)
        
        # Add the target volume
        self.figure.scene.add_actor(self.cylinderActor)
        #self.figure.scene.add_actor(self.cortexActor)
        self.figure.scene.add_actor(self.neuronesActor)
        
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
    scene_Hyp = 'scene_Hyp.wrl'
    scene_Cx  = 'scene_Cx.wrl' #'extract.wrl'
    
    if not os.path.isfile(scene_Hyp):
        Projection.retreiveFrom_3dbar('whs_0.5', 'Hyp', 'high', 'vrml')
    
    if not os.path.isfile(scene_Cx):
        Projection.retreiveFrom_3dbar('whs_0.5', 'Cx',  'high', 'vrml')
    
    p = Projection(scene_Hyp, scene_Cx)
    p.plot()
    mlab.show()
    
