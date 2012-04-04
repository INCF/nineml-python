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

def closeSurface(meshin):
    meshout = vtk.vtkPolyData()
    
    poly = vtk.vtkCleanPolyData()
    poly.PointMergingOn()
    #poly.ConvertLinesToPointsOn() 
    #poly.ConvertPolysToLinesOn() 
    #poly.ConvertStripsToPolysOn()
    poly.SetInput(meshin)
    poly.Update()
    
    boundaryEdges = vtk.vtkFeatureEdges()
    boundaryEdges.SetInput(meshin)
    boundaryEdges.SetBoundaryEdges(1)
    boundaryEdges.SetFeatureEdges(0)
    boundaryEdges.SetNonManifoldEdges(0)
    boundaryEdges.SetManifoldEdges(0)
    boundaryEdges.Update()

    nombre = boundaryEdges.GetOutput().GetNumberOfLines()
    pointsNumber = nombre
    print 'Number of open lines 1: ', nombre
    
    """
    region  = vtk.vtkPolyDataConnectivityFilter()
    region.SetInput(poly.GetOutput())
    region.SetExtractionMode(1)
    region.Update()

    bouchon     = vtk.vtkStripper()
    bouchon.SetInput(region.GetOutput())
    """
    
    region      = vtk.vtkPolyDataConnectivityFilter()
    meshAppend  = vtk.vtkAppendPolyData()
    bouchon     = vtk.vtkStripper()
    bouchonPoly = vtk.vtkPolyData()
    bouchontri  = vtk.vtkTriangleFilter()

    meshAppend.AddInput(poly.GetOutput())
    meshAppend.AddInput(bouchontri.GetOutput())

    region.SetInput(boundaryEdges.GetOutput())
    region.SetExtractionModeToAllRegions() #SetExtractionMode(1)

    bouchon.SetInput(region.GetOutput())

    bouchontri.SetInput(bouchonPoly)

    poly.SetInput(meshAppend.GetOutput())
    poly.SetTolerance(0.0)
    poly.SetConvertLinesToPoints(0)
    poly.SetConvertPolysToLines(0)
    poly.SetConvertStripsToPolys(0)

    boundaryEdges.SetInput(poly.GetOutput())
    while nombre != 0:
        region.Update()
                                        
        # creating polygonal patches
        bouchon.Update()
        print 'ujaaaaaa'

        bouchonPoly.Initialize()
        bouchonPoly.SetPoints(bouchon.GetOutput().GetPoints())
        bouchonPoly.SetPolys(bouchon.GetOutput().GetLines())
        bouchonPoly.Update()
        print 'ujaaaaaa'

        # triangulate the polygonal patch 
        bouchontri.Update()

        # patch (add the patch to the mesh)
        meshAppend.Update()

        # remove duplicated edges and points
        poly.Update()

        # update the number of border edges
        boundaryEdges.Update()

        nombre = boundaryEdges.GetOutput().GetNumberOfLines()
        print 'Left {0}'.format((pointsNumber - nombre) / pointsNumber)

    meshout.DeepCopy(poly.GetOutput())
    return meshout
    
class Projection(object):
    def __init__(self, source_vrml_filename, target_vrml_filename):
        self.figure = mlab.figure()
        self.figure.on_mouse_pick(self.picker_callback)

        self.neurones   = []
        self.actors     = []
        self.lineActors = []
        
        self.source_vrml_filename = source_vrml_filename
        self.target_vrml_filename = target_vrml_filename
        
        source_actor, source_dataset, source_vtkpoints = Projection.loadVRMLFile(source_vrml_filename)
        target_actor, target_dataset, target_vtkpoints = Projection.loadVRMLFile(target_vrml_filename)
        
        print 'Np = ', target_vtkpoints.GetNumberOfPoints()
        
        target_dataset.Update()
        #print "target_dataset", target_dataset
        
        #print dir(target_dataset)
        #print dir(target_actor)
        targetNormals = vtk.vtkPolyDataNormals()
        targetNormals.SetInput(target_dataset)
        
        dataset = vtk.vtkImplicitDataSet()
        dataset.SetDataSet(target_dataset)
        
        backProp = vtk.vtkProperty()
        backProp.SetDiffuseColor(vtk.util.colors.tomato)
        
        _radius = 0.8
        _x = 2
        _y = 0
        _z = 3.2
        sphere = vtk.vtkSphere()
        sphere.SetRadius(_radius)
        sphere.SetCenter(_x, _y, _z)
        
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetRadius(_radius)
        sphereSource.SetCenter(_x, _y, _z)
        sphereSource.SetThetaResolution(30)
        sphereSource.SetPhiResolution(30)
        
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
        cutMapper.SetInputConnection(clipCortex.GetClippedOutputPort()) #SetInput(strippedPoly)
        cutMapper.ScalarVisibilityOff()
        
        cutActor = vtk.vtkActor()
        cutActor.SetMapper(cutMapper)
        cutActor.GetProperty().SetColor(vtk.util.colors.peacock)
        cutActor.SetBackfaceProperty(backProp)
       
        # ACHTUNG, ACHTUNG!!
        # Bounds are in milimeters
        # Get the cube enclosing the cut part and generate neurones uniformly, every 100um
        xl, xh, yl, yh, zl, zh = clipPoly.GetBounds()
        delta = 0.1 # mm
        nx = int(abs(xh - xl) / delta) + 1
        ny = int(abs(yh - yl) / delta) + 1
        nz = int(abs(zh - zl) / delta) + 1
        
        print xl, xh, yl, yh, zl, zh
        print nx, ny, nz
        #grid = numpy.mgrid[xl : xh : nx * 1j, yl : yh : ny * 1j, zl : zh : nz * 1j]
        #print grid.shape, grid
        
        neuronesPoly = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        vertices = vtk.vtkCellArray()
        for x in range(0, nx):
            for y in range(0, ny):
                for z in range(0, nz):
                    self.neurones.append( (xl + delta*x, yl + delta*y, zl + delta*z) )
                    pid = points.InsertNextPoint(xl + delta*x, yl + delta*y, zl + delta*z)
                    vertices.InsertNextCell(1)
                    vertices.InsertCellPoint(pid)
        #print self.neurones
        neuronesPoly.SetPoints(points)
        neuronesPoly.SetVerts(vertices)
        neuronesPoly.Update()
        #print 'neuronesPoly = ', neuronesPoly
        
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
        #neuronesClipper.SetValue(0.5)
        
        dataset = vtk.vtkImplicitDataSet()
        dataset.SetDataSet(neuronesActor.GetMapper().GetInput())
        
        #sphereSource.SetRadius(0.75)
        neuronesClipper2 = vtk.vtkClipPolyData()
        neuronesClipper2.SetInput(sphereSource.GetOutput())
        neuronesClipper2.SetClipFunction(dataset)
        neuronesClipper2.GenerateClipScalarsOn()
        neuronesClipper2.GenerateClippedOutputOn()
        #neuronesClipper2.SetValue(0.5)
        
        """
        sf = vtk.vtkSurfaceReconstructionFilter()
        sf.SetInput(poly)
        
        cf = vtk.vtkContourFilter()
        cf.SetInputConnection(sf.GetOutputPort())
        cf.SetValue(0, 0.0)
        
        reverse = vtk.vtkReverseSense()
        reverse.SetInputConnection(cf.GetOutputPort())
        reverse.ReverseCellsOn()
        reverse.ReverseNormalsOn()
        """
        
        #outline = vtk.vtkOutlineFilter() 
        #outline.SetInputConnection(neuronesClipper.GetClippedOutputPort())

        extractedNeuronesMapper = vtk.vtkPolyDataMapper()
        extractedNeuronesMapper.SetInputConnection(neuronesClipper.GetClippedOutputPort())
        
        extractedNeuronesActor = vtk.vtkActor()
        extractedNeuronesActor.SetMapper(extractedNeuronesMapper)
        extractedNeuronesActor.GetProperty().SetColor(vtk.util.colors.white)
        
        neuronesActor.GetProperty().SetRepresentationToPoints()
        extractedNeuronesActor.GetProperty().SetRepresentationToPoints()
        cutActor.GetProperty().SetRepresentationToWireframe()
        sphereActor.GetProperty().SetRepresentationToWireframe()
        target_actor.GetProperty().SetRepresentationToSurface()
        
        #self.actors.append(tvtk.to_tvtk(source_actor))
        #self.actors.append(tvtk.to_tvtk(target_actor))
        self.actors.append(tvtk.to_tvtk(cutActor))
        #self.actors.append(tvtk.to_tvtk(sphereActor))
        self.actors.append(tvtk.to_tvtk(extractedNeuronesActor))
        
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
        # Add actors 
        self.figure.scene.add_actors(self.actors)
        
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
    
