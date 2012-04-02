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

        self.neurones  = []
        self.lineActors = []
        
        self.source_vrml_filename = source_vrml_filename
        self.target_vrml_filename = target_vrml_filename
        
        source_actor, source_dataset, source_vtkpoints = Projection.loadVRMLFile(source_vrml_filename)
        target_actor, target_dataset, target_vtkpoints = Projection.loadVRMLFile(target_vrml_filename)
        
        print 'Np = ', target_vtkpoints.GetNumberOfPoints()
        
        target_actor.GetProperty().SetRepresentationToPoints()
        
        #print dir(target_dataset)
        #print dir(target_actor)
        targetNormals = vtk.vtkPolyDataNormals()
        targetNormals.SetInput(target_dataset)
        
        backProp = vtk.vtkProperty()
        backProp.SetDiffuseColor(vtk.util.colors.tomato)
        
        cylinder = vtk.vtkCylinder()
        cylinder.SetRadius(1)
        cylinder.SetCenter(0, 0, 0)
        rotate = vtk.vtkTransform()
        rotate.RotateX(90)
        rotate.RotateY(30)
        cylinder.SetTransform(rotate)
        
        plane = vtk.vtkPlane()
        plane.SetOrigin(0, 0, 1)
        plane.SetNormal(0, 0, 1)
        
        """
        cutPlane = vtk.vtkCutter()
        cutPlane.SetInputConnection(targetNormals.GetOutputPort())
        cutPlane.SetCutFunction(plane)
        cutPlane.GenerateCutScalarsOn()
        cutPlane.SetValue(0, 0.5)
        cutStrips = vtk.vtkStripper()
        cutStrips.SetInputConnection(cutPlane.GetOutputPort())
        cutStrips.Update()
        cutPolyPlane = vtk.vtkPolyData()
        cutPolyPlane.SetPoints(cutStrips.GetOutput().GetPoints())
        cutPolyPlane.SetPolys(cutStrips.GetOutput().GetLines())
        """
        
        planeClipper = vtk.vtkClipPolyData()
        planeClipper.SetInput(target_dataset)
        planeClipper.SetClipFunction(plane)
        planeClipper.GenerateClipScalarsOn()
        planeClipper.GenerateClippedOutputOn()
        planeClipper.SetValue(0.5)

        cutCylinder = vtk.vtkCutter()
        cutCylinder.SetInput(planeClipper.GetOutput())
        cutCylinder.SetCutFunction(cylinder)
        cutCylinder.GenerateCutScalarsOn()
        cutCylinder.SetValue(0, 0.5)
        
        cutStrips = vtk.vtkStripper()
        cutStrips.SetInputConnection(cutCylinder.GetOutputPort())
        cutStrips.Update()
        cutPolyCylinder = vtk.vtkPolyData()
        cutPolyCylinder.SetPoints(cutStrips.GetOutput().GetPoints())
        cutPolyCylinder.SetPolys(cutStrips.GetOutput().GetLines())
        #print cutPolyCylinder

        """
        dataset = vtk.vtkImplicitDataSet()
        dataset.SetDataSet(cutPolyCylinder)
        
        cylS = vtk.vtkCylinderSource()
        cylS.SetRadius(1)
        cylS.SetResolution(20)
        cylS.SetCenter(0, 0, 0)
        
        cylSMapper = vtk.vtkPolyDataMapper()
        cylSMapper.SetInputConnection(cylS.GetOutputPort())
        
        cylSActor = vtk.vtkActor()
        cylSActor.SetMapper(cylSMapper)
        cylSActor.GetProperty().SetColor(vtk.util.colors.yellow)
        cylSActor.RotateX(90)
        cylSActor.RotateY(30)
        
        cut = vtk.vtkCutter()
        cut.SetInput(cylSActor.GetMapper().GetInput())
        cut.SetCutFunction(dataset)
        cut.GenerateCutScalarsOn()
        cut.SetValue(0, 0.5)
        
        cutMapper = vtk.vtkPolyDataMapper()
        cutMapper.SetInputConnection(cut.GetOutputPort())
        cutcylActor = vtk.vtkActor()
        cutcylActor.SetMapper(cutMapper)
        cutcylActor.GetProperty().SetColor(vtk.util.colors.peacock)
        cutcylActor.SetBackfaceProperty(backProp)
        """
        
        # Triangle filter is robust enough to ignore the duplicate point at
        # the beginning and end of the polygons and triangulate them.
        cutTriangles = vtk.vtkTriangleFilter()
        cutTriangles.SetInput(cutPolyCylinder)
        
        cutMapper = vtk.vtkPolyDataMapper()
        cutMapper.SetInput(cutTriangles.GetOutput())
        #cutMapper.SetInputConnection(cutStrips.GetOutputPort())
        
        cutActor = vtk.vtkActor()
        cutActor.SetMapper(cutMapper)
        cutActor.GetProperty().SetColor(vtk.util.colors.peacock)
        cutActor.SetBackfaceProperty(backProp)
        
        """
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
        
        # ACHTUNG, ACHTUNG!!
        # Bounds are in milimeters
        # Get the cube enclosing the cut part and generate neurones uniformly, every 50um
        
        cutPolyCylinder.Update()
        
        xl, xh, yl, yh, zl, zh = target_dataset.GetBounds()
        delta = 1000E-3
        nx = int(abs(xh - xl) / delta) + 1
        ny = int(abs(yh - yl) / delta) + 1
        nz = int(abs(zh - zl) / delta) + 1
        
        print xl, xh, yl, yh, zl, zh
        print nx, ny, nz
        #grid = numpy.mgrid[xl : xh : nx * 1j, yl : yh : ny * 1j, zl : zh : nz * 1j]
        #print grid.shape, grid
        
        poly = vtk.vtkPolyData()
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
        poly.SetPoints(points)
        poly.SetVerts(vertices)
        poly.Update()
        print 'POLY = ', poly
        
        neuronesMapper = vtk.vtkPolyDataMapper()
        neuronesMapper.SetInput(poly)
        
        neuronesActor = vtk.vtkActor()
        neuronesActor.SetMapper(neuronesMapper)
        neuronesActor.GetProperty().SetColor(vtk.util.colors.green)
        neuronesActor.GetProperty().SetRepresentationToPoints()

        """
        clipMapper = vtk.vtkPolyDataMapper()
        clipMapper.SetInputConnection(cylinderClipper.GetClippedOutputPort())
        clipMapper.ScalarVisibilityOff()
        
        cylinderActor = vtk.vtkActor()
        cylinderActor.SetMapper(clipMapper)
        cylinderActor.GetProperty().SetColor(vtk.util.colors.peacock)
        cylinderActor.SetBackfaceProperty(backProp)
        """
        
        """
        box = vtk.vtkBox()
        box.SetBounds(xl, xh, yl, yh, zl, zh)
        
        select = vtk.vtkExtractGeometry()
        select.SetInputConnection(cutTriangles.GetOutputPort())
        select.SetImplicitFunction(box)
        #select.ExtractInsideOn()
        """
        
        #meshout = closeSurface(cutPolyCylinder)
        
        cleanPoly = vtk.vtkCleanPolyData()
        cleanPoly.PointMergingOn()
        cleanPoly.ConvertLinesToPointsOn() 
        cleanPoly.ConvertPolysToLinesOn() 
        cleanPoly.ConvertStripsToPolysOn()
        cleanPoly.SetInput(target_dataset)
        cleanPoly.Update()
        
        region  = vtk.vtkPolyDataConnectivityFilter()
        region.SetInput(cleanPoly.GetOutput())
        region.SetExtractionModeToLargestRegion()
        region.Update()
        out = region.GetOutput()
        out.Update()
        
        cutTriangles = vtk.vtkTriangleFilter()
        cutTriangles.SetInput(out)
        
        stripper = vtk.vtkStripper()
        stripper.SetInput(cutTriangles.GetOutput())
        stripper_out = stripper.GetOutput()
        stripper_out.Update()
        #print stripper_out
        
        strippedPoly = vtk.vtkPolyData()
        strippedPoly.Initialize()
        strippedPoly.SetPoints(stripper.GetOutput().GetPoints())
        strippedPoly.SetPolys(stripper.GetOutput().GetStrips())
        strippedPoly.Update()
        #print strippedPoly
        
        """
        feature = vtk.vtkFeatureEdges()
        feature.SetInput(strippedPoly)
        feature.SetBoundaryEdges(1)
        feature.SetFeatureEdges(0)
        feature.SetNonManifoldEdges(0)
        feature.SetManifoldEdges(0)
        feature.Update()
        featureOut = feature.GetOutput()
        featureOut.Update()
        lines = featureOut.GetLines()
        print lines
        nombre = featureOut.GetNumberOfLines()
        print 'Number of open lines: ', nombre
        """
        
        dataset = vtk.vtkImplicitDataSet()
        dataset.SetDataSet(strippedPoly)
        
        select = vtk.vtkSelectEnclosedPoints()
        select.SetInput(poly)
        select.SetSurface(strippedPoly)
        #select.CheckSurfaceOn()
        select.Update()
        selectOut = select.GetOutput()
        print selectOut.GetPoints()
        print selectOut.GetVerts()
        
        pointsInPoly = vtk.vtkPolyData()
        pointsInPoly.Initialize()
        pointsInPoly.SetPoints(selectOut.GetPoints())
        pointsInPoly.SetVerts(selectOut.GetVerts())
        pointsInPoly.Update()
        print pointsInPoly
       
        interMapper = vtk.vtkPolyDataMapper() #vtkDataSetMapper()
        interMapper.SetInput(selectOut) #feature.GetOutput())
        interMapper.ScalarVisibilityOff()
        
        interActor = vtk.vtkActor()
        interActor.SetMapper(interMapper)
        interActor.GetProperty().SetRepresentationToPoints()
        interActor.GetProperty().SetColor(vtk.util.colors.white)
        interActor.SetBackfaceProperty(backProp)
        
        self.source_actor  = tvtk.to_tvtk(source_actor)
        self.cylinderActor = tvtk.to_tvtk(cutActor)
        self.cortexActor   = tvtk.to_tvtk(target_actor)
        self.neuronesActor = tvtk.to_tvtk(neuronesActor)
        self.interActor    = tvtk.to_tvtk(interActor)
        
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
        
        self.figure.scene.add_actor(self.interActor)
        
        # Add the target volume
        #self.figure.scene.add_actor(self.cylinderActor)
        #self.figure.scene.add_actor(self.cortexActor)
        #self.figure.scene.add_actor(self.neuronesActor)
        
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
    
