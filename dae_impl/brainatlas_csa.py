#!/usr/bin/env python
import os, sys, traceback, math, httplib, urllib, zipfile, StringIO
from time import localtime, strftime, time

import numpy

import vtk
from vtk.hybrid import vtkVRMLImporter

from enthought.mayavi import mlab
from enthought.tvtk.api import tvtk
from enthought.mayavi.sources.vrml_importer import VRMLImporter
from enthought.mayavi.api import Engine
from enthought.mayavi.sources.vtk_data_source import VTKDataSource

from enthought.traits.api import HasTraits, Range, Instance, on_trait_change, Array, Tuple, Str
from enthought.traits.ui.api import View, Item, HSplit, Group, HGroup
from enthought.mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor

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
    Implementation of the Geometry interface. 
    It is a wrapper on top the vtkPoints objects.
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
        
class Projection(HasTraits):
    meridional = Range(1, 30,  6)
    transverse = Range(0, 30, 11)
    scene      = Instance(MlabSceneModel, ())
    
    def __init__(self, source_vrml_filename, target_vrml_filename):
        HasTraits.__init__(self)
        
        print self.scene
        print self.scene.mlab
        
        #self.figure = self.scene.mlab.figure()
        
        self.source_vrml_filename = source_vrml_filename
        self.target_vrml_filename = target_vrml_filename
        
        self.source_actor, self.source_vtkpoints = Projection.loadVRMLFile(source_vrml_filename)
        self.target_actor, self.target_vtkpoints = Projection.loadVRMLFile(target_vrml_filename)
        
        self.Ns = self.source_vtkpoints.GetNumberOfPoints()
        self.Nt = self.target_vtkpoints.GetNumberOfPoints()
        
        self.lines = []
        self.geometry = vtkPointsGeometry(self.source_vtkpoints, self.target_vtkpoints)
        print('Metric({0},{1}) = {2}'.format(0, 5, self.geometry.metric(0, 5)))
        
        p      = 0.0001 # fraction
        weight = 0.04 # nS
        delay  = 0.20 # ms
        cset = csa.cset(csa.random(p), weight, delay)
        cg = csa.CSAConnectionGenerator(cset)
        mask = connection_generator.Mask([(0, 1)], [(0, self.Nt - 1)])
        cg.setMask(mask)
        print cg, len(cg), cg.arity
        self.createConnections(cg)
        self.plot()
        
    @on_trait_change('meridional,transverse')
    def update_plot(self):
        print 'm = {0} t = {1}'.format(self.meridional, self.transverse)
    
    def createConnections(self, cgi):
        count = 0
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
            
            #print connection
            self.addConnectionLine(source_index, target_index)

    def addConnectionLine(self, source_index, target_index):
        x1, y1, z1 = self.geometry.sourcePosition(source_index)
        x2, y2, z2 = self.geometry.targetPosition(target_index)
        
        line       = tvtk.LineSource(point1=(x1, y1, z1), point2=(x2, y2, z2))
        lineMapper = tvtk.PolyDataMapper(input=line.output)
        lineActor  = tvtk.Actor(mapper=lineMapper)
        self.scene.add_actor(lineActor)
        
        #self.lines.append(([x1, x2], [y1, y2], [z1, z2]))
    
    def plot(self):
        #engine = Engine()
        #engine.start()
        #scene = engine.new_scene()
        #svrml = VRMLImporter()
        #svrml.initialize(self.source_vrml)
        #tvrml = VRMLImporter()
        #tvrml.initialize(self.target_vrml)
        #engine.add_source(svrml)
        #engine.add_source(tvrml)
        
        """
        x = numpy.zeros(self.Ns)
        y = numpy.zeros(self.Ns)
        z = numpy.zeros(self.Ns)
        for i in xrange(0, self.Ns):
            c = self.source_vtkpoints.GetPoint(i)
            x[i] = c[0]
            y[i] = c[1]
            z[i] = c[2]
        mlab.points3d(x, y, z, figure = self.figure)
        
        x = numpy.zeros(self.Nt)
        y = numpy.zeros(self.Nt)
        z = numpy.zeros(self.Nt)
        for i in xrange(0, self.Nt):
            c = self.target_vtkpoints.GetPoint(i)
            x[i] = c[0]
            y[i] = c[1]
            z[i] = c[2]
        mlab.points3d(x, y, z, figure = self.figure)
        """
        #for (x, y, z) in self.lines:
        #    print x, y, z
        #    engine.add_source( mlab.pipeline.line_source(x, y, z) )

        sa = tvtk.to_tvtk(self.source_actor)
        self.figure.scene.add_actor(sa)
        ta = tvtk.to_tvtk(self.target_actor)
        self.scene.add_actor(ta)
        #mlab.show()
    
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
        Opens a .wrl file, reads the points in it and returns 
        3 numpy arrays with x, y, z coordinates
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
        vtkpoints = dataset.GetPoints() 
        Np = vtkpoints.GetNumberOfPoints()
        return actor, vtkpoints
    
    # the layout of the dialog created
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                    height=250, width=300, show_label=False),
                    HGroup('_', 'meridional', 'transverse', ),
                )
    
if __name__ == "__main__":
    scene_Hyp = 'scene_Hyp.wrl' #Projection.retreiveFrom_3dbar('whs_0.5', 'Hyp', 'high', 'vrml')
    scene_Cx  = 'scene_Cx.wrl' #Projection.retreiveFrom_3dbar('whs_0.5', 'Cx',  'high', 'vrml')
    
    p = Projection(scene_Hyp, scene_Cx)
    p.configure_traits()
