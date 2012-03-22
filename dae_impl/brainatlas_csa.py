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

from enthought.traits.api import HasTraits, Trait, Range, Instance, on_trait_change, Array, Tuple, Str
from enthought.traits.ui.api import View, Item, HSplit, Group, HGroup
from enthought.mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from enthought.tvtk.pyface.picker import Picker, DefaultPickHandler, PickHandler

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
"""        
class P(Picker):
    def __init__(self, renwin, **traits):
        super(P, self).__init__(renwin, **traits)
    def pick(self, x, y):
        super(P, self).pick(x, y)
        print x, y
        
class SceneModel(MlabSceneModel):
    picker = None
    def __init__(self, parent = None, **traits):
        super(SceneModel, self).__init__(parent, **traits)
"""

class Projection(HasTraits):
    source_index = Str('0', desc = 'Source neurone index', auto_set=False, enter_set=True)
    scene        = Instance(MlabSceneModel, ())
    
    def __init__(self, source_vrml_filename, target_vrml_filename):
        HasTraits.__init__(self)
        #self.scene.picker = P(self.scene.render_window)
        #self.picker.pick_handler = None #Trait(DefaultPickHandler(), Instance(PickHandler)) 
        #.pointpicker.add_observer('EndPickEvent', self.picker_callback)
        print self.scene
        print dir(self.scene)
        print self.scene.interactor
        #self.scene.scene.interactor.add_observer('EndPickEvent', self.picker_callback)
        
        self.source_vrml_filename = source_vrml_filename
        self.target_vrml_filename = target_vrml_filename
        
        source_actor, source_dataset, source_vtkpoints = Projection.loadVRMLFile(source_vrml_filename)
        target_actor, target_dataset, target_vtkpoints = Projection.loadVRMLFile(target_vrml_filename)
        
        self.source_actor = tvtk.to_tvtk(source_actor)
        self.target_actor = tvtk.to_tvtk(target_actor)
        
        self.source_dataset = source_dataset
        self.target_dataset = target_dataset
        
        #print vtk.IsSurfaceClosed()
        sep = vtk.vtkSelectEnclosedPoints()
        sep.SetSurface(self.source_dataset)
        print sep.IsInsideSurface(0.0, -0.4, -0.6)
        
        cell = self.source_dataset.FindPoint(0, 0, 0)
        print cell
        print source_vtkpoints.GetPoint(cell)
        
        self.Ns = source_vtkpoints.GetNumberOfPoints()
        self.Nt = target_vtkpoints.GetNumberOfPoints()
        
        self.lineActors = []
        self.geometry = vtkPointsGeometry(source_vtkpoints, target_vtkpoints)
        print('Metric({0},{1}) = {2}'.format(0, 5, self.geometry.metric(0, 5)))
        
        self.createConnections(0)
        self.plot()
        
    @on_trait_change('source_index')
    def update_plot(self):
        # Remove actors
        self.scene.remove_actors(self.lineActors)
        
        #self.scene.remove_actor(self.source_actor)
        self.scene.remove_actor(self.target_actor)
        
        # Get the index
        source_index = int(self.source_index)
        print 'source_index = {0}'.format(self.source_index)
        self.createConnections(source_index)
        self.plot()
        
    def picker_callback(self, picker_obj, evt):
        picked = picker_obj.actors
        if obj in [o._vtk_obj for o in picked]:
            print obj
    
    def createConnections(self, source_index):
        if source_index >= self.Ns:
            return
        
        p      = 0.0001 # fraction
        weight = 0.04 # nS
        delay  = 0.20 # ms
        cset = csa.cset(csa.random(p), weight, delay)
        cgi = csa.CSAConnectionGenerator(cset)
        mask = connection_generator.Mask([(source_index, source_index)], [(0, self.Nt - 1)])
        cgi.setMask(mask)
        print cgi, len(cgi), cgi.arity
        
        self.lineActors = []
        
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
            
            x1, y1, z1 = self.geometry.sourcePosition(source_index)
            x2, y2, z2 = self.geometry.targetPosition(target_index)
            
            line       = tvtk.LineSource(point1=(x1, y1, z1), point2=(x2, y2, z2))
            lineMapper = tvtk.PolyDataMapper(input=line.output)
            lineActor  = tvtk.Actor(mapper=lineMapper)
            
            self.lineActors.append(lineActor)

    def plot(self):
        self.scene.add_actors(self.lineActors)
        
        #self.figure.scene.add_actor(self.source_actor)
        self.scene.add_actor(self.target_actor)
        self.scene.reset_zoom()
        #self.scene.isometric_view()
    
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
        #print dataset
        dataset.Update()
        vtkpoints = dataset.GetPoints() 
        Np = vtkpoints.GetNumberOfPoints()
        return actor, dataset, vtkpoints
    
    # the layout of the dialog created
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                    height=600, width=800, show_label=False),
                    HGroup('_', 'source_index', ),
                )
    
if __name__ == "__main__":
    scene_Hyp = 'scene_Hyp.wrl' #Projection.retreiveFrom_3dbar('whs_0.5', 'Hyp', 'high', 'vrml')
    scene_Cx  = 'scene_Cx.wrl' #Projection.retreiveFrom_3dbar('whs_0.5', 'Cx',  'high', 'vrml')
    
    p = Projection(scene_Hyp, scene_Cx)
    p.configure_traits()
