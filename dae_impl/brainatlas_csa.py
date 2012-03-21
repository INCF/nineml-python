#!/usr/bin/env python
import os, sys, traceback, httplib, urllib, zipfile, StringIO
from time import localtime, strftime, time

import numpy as np
from enthought.mayavi import mlab
from enthought.tvtk.api import tvtk
from enthought.mayavi.sources.vrml_importer import VRMLImporter
from enthought.mayavi.api import Engine

import nineml
import nineml.connection_generator as connection_generator
import nineml.geometry as geometry
from nineml.user_layer_aux import ConnectionGenerator
from nineml.user_layer_aux import grids

from lxml import etree
from lxml.builder import E

import csa

class Neurone(object):
    def __init__(self, x, y, z, index):
        self.x           = x
        self.y           = y
        self.z           = z
        self.index       = index
        self.connections = []
        
class Projection(object):
    def __init__(self, xs, ys, zs, xt, yt, zt):
        self.xs = xs
        self.ys = ys
        self.zs = zs
        self.Ns = len(xs)
        self.xt = xt
        self.yt = yt
        self.zt = zt
        self.Nt = len(xt)
        self.figure = mlab.figure()
        self.connections = []
        
        source_grid = grids.UnstructuredGrid(zip(xs, ys, zs))
        target_grid = grids.UnstructuredGrid(zip(xt, yt, zt))
        
        geometry = grids.GeometryImplementation(source_grid, target_grid)
        print('Metric({0},{1}) = {2}'.format(0, 5, geometry.metric(0, 5)))
        
        p      = 0.10 # fraction
        weight = 0.04 # nS
        delay  = 0.20 # ms
        cset = csa.cset(csa.random(p), weight, delay)
        cg = csa.CSAConnectionGenerator(cset)
        mask = connection_generator.Mask([(0, self.Ns - 1)], [(0, self.Nt - 1)])
        cg.setMask(mask)
        print cg, len(cg), cg.arity
        self.createConnections(cg)
       
        '''
        xml = """
            <CSA xmlns="http://software.incf.org/software/csa/1.0">
            <bind>
                <closure/>
                <bvar><ci>p</ci></bvar>
                <bvar><ci>weight</ci></bvar>
                <bvar><ci>delay</ci></bvar>
                <apply>
                    <cset/>
                    <apply>
                        <randomMask/>
                        <ci>p</ci>
                    </apply>
                    <ci>weight</ci>
                    <ci>delay</ci>
                </apply>
            </bind>
            </CSA>
            """
        root = etree.fromstring(xml)
        print etree.tostring(root)
        
        cg = csa.connectionGeneratorClosureFromXML(root)
        print cg
        '''
        
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
            
            print connection
            self.addConnectionLine(source_index, target_index)

    def addConnectionLine(self, source_index, target_index):
        x1 = self.xs[source_index]
        y1 = self.ys[source_index]
        z1 = self.zs[source_index]
        x2 = self.xt[target_index]
        y2 = self.yt[target_index]
        z2 = self.zt[target_index]
        
        line = tvtk.LineSource(point1=(x1, y1, z1), point2=(x2, y2, z2))
        lineMapper = tvtk.PolyDataMapper(input=line.output)
        lineActor  = tvtk.Actor(mapper=lineMapper)
        self.figure.scene.add_actor(lineActor)
    
    def plot(self):
        mlab.points3d(self.xs, self.ys, self.zs, scale_mode='none', scale_factor=.05, color=(0, 1, 1), figure = self.figure)
        mlab.points3d(self.xt, self.yt, self.zt, scale_mode='none', scale_factor=.05, color=(0, 1, 0), figure = self.figure)
        mlab.show()
    
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

if __name__ == "__main__":
    """
    scene_Hyp = Projection.retreiveFrom_3dbar('whs_0.5', 'Hyp', 'high', 'vrml')
    scene_Cx  = Projection.retreiveFrom_3dbar('whs_0.5', 'Cx',  'high', 'vrml')
    
    hypothalamus = VRMLImporter()
    hypothalamus.initialize(scene_Hyp)
    cortex = VRMLImporter()
    cortex.initialize(scene_Cx)
    
    #print hypothalamus.render()
    #hypothalamus.add_actors()
    #print hypothalamus.print_traits()
    
    e = Engine()
    e.start()
    s = e.new_scene()
    e.add_source(hypothalamus)
    e.add_source(cortex)

    cortex.add_actors()
    hypothalamus.add_actors()
    #print cortex.actors[0].mapper.input.points.to_array()
    
    mlab.show()
    sys.exit()
    """
    N = 20
    
    x1 = np.zeros(N)
    y1 = np.zeros(N)
    z1 = np.linspace(0, 1, N)
    
    x2 = np.zeros(N) + 1
    y2 = np.zeros(N)
    z2 = np.linspace(0, 1, N)

    p = Projection(x1, y1, z1, x2, y2, z2)
    p.plot()
    
