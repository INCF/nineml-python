import nineml
import nineml.user_layer
import urllib
from lxml import etree
from lxml.builder import E

class sedmlBase:
    def __init__(self, id, name):
        self.id   = str(id)
        self.name = str(name)

    def __repr__(self):
        return '{0}, {1}'.format(self.id, self.name)
        
    def to_xml(self, root):
        root.set('id',   self.id)
        root.set('name', self.name)
        
    def from_xml(self, root):
        pass

class sedmlUniformTimeCourseSimulation(sedmlBase):
    xmlTagName = 'uniformTimeCourse'
    
    def __init__(self, id, name, initialTime, outputStartTime, outputEndTime, numberOfPoints, algorithm):
        sedmlBase.__init__(self, id, name)
        
        if float(initialTime) != 0.0:
            raise RuntimeError('SED-ML: the initial time has to be 0.0')
        if float(outputStartTime) != 0.0:
            raise RuntimeError('SED-ML: the output start time has to be 0.0')
        if float(outputEndTime) <= float(outputStartTime):
            raise RuntimeError('SED-ML: the output start time is greater than the output end time')
            
        self.initialTime     = 0.0
        self.outputStartTime = 0.0
        self.outputEndTime   = float(outputEndTime)
        self.numberOfPoints  = int(numberOfPoints)
        self.algorithm       = str(algorithm)
    
    def __repr__(self):
        return 'sedmlSimulation({0}, {1}, {2}, {3}, {4}, {5})'.format(sedmlBase.__repr__(self), 
                                                                      self.initialTime,
                                                                      self.outputStartTime,
                                                                      self.outputEndTime,
                                                                      self.numberOfPoints,
                                                                      self.algorithm)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        root.set('initialTime',     str(self.initialTime))
        root.set('outputStartTime', str(self.outputStartTime))
        root.set('outputEndTime',   str(self.outputEndTime))
        root.set('numberOfPoints',  str(self.numberOfPoints))
        
        xml_algorithm = etree.SubElement(root, 'algorithm')
        xml_algorithm.set('kisaoID', str(self.algorithm))
        
    def from_xml(self, root):
        sedmlBase.from_xml(self, root)

class sedmlModel(sedmlBase):
    xmlTagName = 'model'
    
    def __init__(self, id, name, language, source):
        sedmlBase.__init__(self, id, name)
        
        self.language = str(language) # URN
        self.source   = None
        self.ul_model = None
        
        if isinstance(source, str):
            self.source = source # URN
        elif isinstance(source, nineml.user_layer.Model):
            self.ul_model = source # python NineML UL Model object
        else:
            raise RuntimeError('SED-ML: invalid user-layer reference')
            
    def __repr__(self):
        return 'sedmlModel({0}, {1}, {2})'.format(sedmlBase.__repr__(self), 
                                                  self.language,
                                                  self.source)
    
    def getUserLayerModel(self):
        if self.ul_model:
            return self.ul_model
        else:
            # Here we should load the UserLayer model using the supplied URN
            # However, loading user layer xml files is not supported at the moment
            raise RuntimeError('')
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        root.set('language', str(self.language))
        root.set('source',   str(self.source))
                
    def from_xml(self, root):
        sedmlBase.from_xml(self, root)

class sedmlTask(sedmlBase):
    xmlTagName = 'task'
    
    def __init__(self, id, name, model, simulation):
        sedmlBase.__init__(self, id, name)
        
        self.model      = model
        self.simulation = simulation
    
    def __repr__(self):
        return 'sedmlTask({0}, {1}, {2})'.format(sedmlBase.__repr__(self), 
                                                 self.model.name,
                                                 self.simulation.name)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        root.set('modelReference',      self.model.id)
        root.set('simulationReference', self.simulation.id)
        
    def from_xml(self, root):
        sedmlBase.from_xml(self, root)

class sedmlDataGenerator(sedmlBase):
    xmlTagName = 'dataGenerator'
    
    def __init__(self, id, name, variables):
        sedmlBase.__init__(self, id, name)
        
        self.variables  = list(variables)
        self.parameters = []
    
    def __repr__(self):
        return 'sedmlDataGenerator({0}, {1})'.format(sedmlBase.__repr__(self), self.variables)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        xml_variables = etree.SubElement(root, 'listOfVariables')
        for variable in self.variables:
            xml_variable = etree.SubElement(xml_variables, variable.xmlTagName)
            variable.to_xml(xml_variable)
        
        xml_parameters = etree.SubElement(root, 'listOfParameters')
        for parameter in self.parameters:
            xml_parameter = etree.SubElement(xml_parameters, parameter.xmlTagName)
            parameter.to_xml(xml_parameter)
        
        xml_math = etree.SubElement(root, 'math')
        xml_math.set('xmlns', 'http://www.w3.org/1998/Math/MathML')
        xml_ci = etree.SubElement(xml_math, 'ci')
        xml_ci.text = str(self.name)
        
    def from_xml(self, root):
        sedmlBase.from_xml(self, root)

class sedmlVariable(sedmlBase):
    xmlTagName = 'variable'
    
    def __init__(self, id, name, task, target = None, symbol = None):
        sedmlBase.__init__(self, id, name)
        
        self.task   = task
        self.target = None
        self.symbol = None
        
        if target == None and symbol == None:
            raise RuntimeError('SED-ML: both target abd symbol are None')
        elif target != None and symbol != None:
            raise RuntimeError('SED-ML: target and symbol cannot be specified at the same time')

        if target != None:
            self.target = str(target)
        elif symbol != None:
            self.symbol = str(symbol)

    def __repr__(self):
        return 'sedmlVariable({0}, {1}, {2}, {3})'.format(sedmlBase.__repr__(self), 
                                                          self.task.name,
                                                          self.target,
                                                          self.symbol)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        root.set('taskReference', self.task.id)
        if self.symbol:
            root.set('symbol', self.symbol)
        elif self.target:
            root.set('target', self.target)
        
    def from_xml(self, root):
        sedmlBase.from_xml(self, root)

"""
class sedmlDataSet(sedmlBase):
    def __init__(self, id, name, label, dataGenerator):
        sedmlBase.__init__(self, id, name)
        
        self.label         = str(label)
        self.dataGenerator = dataGenerator
    
    def __repr__(self):
        return 'sedmlDataSet({0}, {1}, {2})'.format(sedmlBase.__repr__(self), 
                                                    self.label, 
                                                    self.dataGenerator)
"""

class sedmlPlot2D(sedmlBase):
    xmlTagName = 'plot2D'
    
    def __init__(self, id, name, curves):
        sedmlBase.__init__(self, id, name)
        
        self.curves = list(curves)
    
    def __repr__(self):
        return 'sedmlPlot2D({0}, {1})'.format(sedmlBase.__repr__(self), self.curves)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        xml_curves = etree.SubElement(root, 'listOfModels')
        for curve in self.curves:
            xml_curve = etree.SubElement(xml_curves, curve.xmlTagName)
            curve.to_xml(xml_curve)
        
    def from_xml(self, root):
        sedmlBase.from_xml(self, root)

class sedmlCurve(sedmlBase):
    xmlTagName = 'curve'
    
    def __init__(self, id, name, logX, logY, xDataReference, yDataReference):
        sedmlBase.__init__(self, id, name)
        
        self.logX            = bool(logX)
        self.logY            = bool(logY)
        self.xDataReference = xDataReference
        self.yDataReference = yDataReference
    
    def __repr__(self):
        return 'sedmlCurve({0}, {1}, {2}, {3}, {4})'.format(sedmlBase.__repr__(self), 
                                                            self.logX,
                                                            self.logY,
                                                            self.xDataReference,
                                                            self.yDataReference)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        if self.logX:
            root.set('logX', 'true')
        else:
            root.set('logX', 'false')
        if self.logY:
            root.set('logY', 'true')
        else:
            root.set('logY', 'false')
        root.set('xDataReference', str(self.xDataReference.id))
        root.set('yDataReference', str(self.yDataReference.id))
        
    def from_xml(self, root):
        sedmlBase.from_xml(self, root)

class sedmlExperiment:
    xmlTagName = 'sedML'
    
    def __init__(self, simulations, models, tasks, data_generators, outputs):
        self.simulations     = list(simulations)
        self.models          = list(models)
        self.tasks           = list(tasks)
        self.data_generators = list(data_generators)
        self.outputs         = list(outputs)

    def __repr__(self):
        res = 'sedmlExperiment('
        for o in self.simulations:
            res += repr(o) + '\n'
        for o in self.models:
            res += repr(o) + '\n'
        for o in self.tasks:
            res += repr(o) + '\n'
        for o in self.data_generators:
            res += repr(o) + '\n'
        for o in self.outputs:
            res += repr(o) + '\n'
        res += ')'
        return res
     
    def get_simulation(self):
        if len(self.simulations) != 1:
            raise RuntimeError('SED-ML: the number of simulations has to be zero')
        return self.simulations[0]
    
    def get_ul_model(self):
        if len(self.models) != 1:
            raise RuntimeError('SED-ML: the number of models has to be zero')
        return self.models[0].getUserLayerModel()
    
    def to_xml(self):
        sedML = etree.Element(self.xmlTagName)
        sedML.set('level',   '1')
        sedML.set('version', '1')
        sedML.set('xmlns',   'http://sed-ml.org/')
        
        xml_simulations = etree.SubElement(sedML, 'listOfSimulations')
        for simulation in self.simulations:
            xml_simulation = etree.SubElement(xml_simulations, simulation.xmlTagName)
            simulation.to_xml(xml_simulation)
        
        xml_models = etree.SubElement(sedML, 'listOfModels')
        for model in self.models:
            xml_model = etree.SubElement(xml_models, model.xmlTagName)
            model.to_xml(xml_model)

        xml_tasks = etree.SubElement(sedML, 'listOfTasks')
        for task in self.tasks:
            xml_task = etree.SubElement(xml_tasks, task.xmlTagName)
            task.to_xml(xml_task)

        xml_datagenerators = etree.SubElement(sedML, 'listOfDataGenerators')
        for datagenerator in self.data_generators:
            xml_datagenerator = etree.SubElement(xml_datagenerators, datagenerator.xmlTagName)
            datagenerator.to_xml(xml_datagenerator)

        xml_outputs = etree.SubElement(sedML, 'listOfOutputs')
        for output in self.outputs:
            xml_output = etree.SubElement(xml_outputs, output.xmlTagName)
            output.to_xml(xml_output)
        
        return sedML
        
    def from_xml(self, root):
        pass
         
if __name__ == "__main__":
    sedml_simulation = sedmlUniformTimeCourseSimulation('Brette_simulation', 'Brette_simulation', 0.0, 0.0, 0.06, 600, 'KISAO:0000283')
    sedml_model      = sedmlModel('Brette_model', 'Brette_model', 'urn:sedml:language:nineml', 'file://user_layer_model.xml') 
    sedml_task       = sedmlTask('task1', 'task1', sedml_model, sedml_simulation)
    
    sedml_variable_time  = sedmlVariable('time',  'time',    sedml_task, symbol='urn:sedml:symbol:time')
    sedml_variable_excV0 = sedmlVariable('excV0', 'Voltage', sedml_task, target='Group 1.Excitatory population[0].V')
    sedml_variable_excV4 = sedmlVariable('excV4', 'Voltage', sedml_task, target='Group 1.Excitatory population[4].V')
    sedml_variable_inhV  = sedmlVariable('inhV',  'Voltage', sedml_task, target='Group 1.Inhibitory population[0].V')

    sedml_data_generator_time = sedmlDataGenerator('DG_time', 'DG_time', [sedml_variable_time])
    sedml_data_generator_excV = sedmlDataGenerator('DG_excV', 'DG_excV', [sedml_variable_excV0, sedml_variable_excV4])
    sedml_data_generator_inhV = sedmlDataGenerator('DG_inhV', 'DG_inhV', [sedml_variable_inhV])

    curve_excV = sedmlCurve('ExcV', 'ExcV', False, False, sedml_data_generator_time, sedml_data_generator_excV)
    curve_inhV = sedmlCurve('InhV', 'InhV', False, False, sedml_data_generator_time, sedml_data_generator_inhV)

    plot_excV  = sedmlPlot2D('Plot_excV', 'Plot_excV', [curve_excV])
    plot_inhV  = sedmlPlot2D('Plot_inhV', 'Plot_inhV', [curve_inhV])

    sedml_experiment = sedmlExperiment([sedml_simulation], 
                                       [sedml_model], 
                                       [sedml_task], 
                                       [sedml_data_generator_time, sedml_data_generator_excV, sedml_data_generator_inhV],
                                       [plot_excV, plot_inhV])
    #print sedml_experiment

    filename = 'sample_sedml.xml'
    etree.ElementTree(sedml_experiment.to_xml()).write(filename, encoding="utf-8", pretty_print=True, xml_declaration=True)
