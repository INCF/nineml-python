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

class sedmlUniformTimeCourseSimulation(sedmlBase):
    def __init__(self, id, name, initialTime, outputStartTime, outputEndTime, numberOfPoints, algorithm):
        sedmlBase.__init__(self, id, name)
        
        if float(initialTime) != 0.0:
            raise RuntimeError('')
        if float(outputStartTime) != 0.0:
            raise RuntimeError('')
        if float(outputEndTime) <= float(outputStartTime):
            raise RuntimeError('')
            
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

class sedmlModel(sedmlBase):
    def __init__(self, id, name, language, source):
        sedmlBase.__init__(self, id, name)
        
        self.language = str(language) # URN
        self.urn      = None
        self.ul_model = None
        
        if isinstance(source, str):
            self.urn = source # URN
        
        elif isinstance(source, nineml.user_layer.Model):
            self.ul_model = source # python NineML UL Model object
        else:
            raise RuntimeError('')
            
    def __repr__(self):
        return 'sedmlModel({0}, {1}, {2})'.format(sedmlBase.__repr__(self), 
                                                  self.language,
                                                  self.urn)
    
    def getUserLayerModel(self):
        if self.ul_model:
            return self.ul_model
        else:
            # Here we should load the UserLayer model using the supplied URN
            # However, the loading user layer xml files is not supported at the moment
            raise RuntimeError('')

class sedmlTask(sedmlBase):
    def __init__(self, id, name, model, simulation):
        sedmlBase.__init__(self, id, name)
        
        self.model      = model
        self.simulation = simulation
    
    def __repr__(self):
        return 'sedmlTask({0}, {1}, {2})'.format(sedmlBase.__repr__(self), 
                                                 self.model.name,
                                                 self.simulation.name)

class sedmlDataGenerator(sedmlBase):
    def __init__(self, id, name, variables):
        sedmlBase.__init__(self, id, name)
        
        self.variables = list(variables)
    
    def __repr__(self):
        return 'sedmlDataGenerator({0}, {1})'.format(sedmlBase.__repr__(self), self.variables)

class sedmlVariable(sedmlBase):
    def __init__(self, id, name, task, target = None, symbol = None):
        sedmlBase.__init__(self, id, name)
        
        self.task   = task
        self.target = None
        self.symbol = None
        
        if target == None and symbol == None:
            raise RuntimeError('')
        elif target != None and symbol != None:
            raise RuntimeError('')

        if target != None:
            self.target = str(target)
        elif symbol != None:
            self.symbol = str(symbol)

    def __repr__(self):
        return 'sedmlVariable({0}, {1}, {2}, {3})'.format(sedmlBase.__repr__(self), 
                                                          self.task.name,
                                                          self.target,
                                                          self.symbol)

class sedmlPlot2D(sedmlBase):
    def __init__(self, id, name, curves):
        sedmlBase.__init__(self, id, name)
        
        self.curves = list(curves)
    
    def __repr__(self):
        return 'sedmlPlot2D({0}, {1})'.format(sedmlBase.__repr__(self), self.curves)

class sedmlCurve(sedmlBase):
    def __init__(self, id, name, logX, logY, xDataRefference, yDataRefference):
        sedmlBase.__init__(self, id, name)
        
        self.logX            = bool(logX)
        self.logY            = bool(logY)
        self.xDataRefference = str(xDataRefference)
        self.yDataRefference = str(yDataRefference)
    
    def __repr__(self):
        return 'sedmlCurve({0}, {1}, {2}, {3}, {4})'.format(sedmlBase.__repr__(self), 
                                                            self.logX,
                                                            self.logY,
                                                            self.xDataRefference,
                                                            self.yDataRefference)

class sedmlExperiment:
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
    
    def to_xml(self):
        pass

    @classmethod
    def from_xml(cls):
        simulations     = []
        models          = []
        tasks           = []
        data_generators = []
        outputs         = []

        return cls(simulations, models, tasks, data_generators, outputs)
     
    def get_daetools_simulation_inputs(self):
        variables_to_report = []
        plots_to_generate   = []
        
        if len(self.simulations) != 1:
            raise RuntimeError('')
        if len(self.models) != 1:
            raise RuntimeError('')
        
        simulation        = self.simulations[0]
        ul_model          = self.models[0].getUserLayerModel()
        reportingInterval = float(simulation.outputEndTime - simulation.outputStartTime) / (simulation.numberOfPoints - 1)
        timeHorizon       = float(simulation.outputEndTime)
         
        return (ul_model, timeHorizon, reportingInterval, variables_to_report, plots_to_generate)
         
if __name__ == "__main__":
    sedml_simulation = sedmlUniformTimeCourseSimulation('Brette simulation', 'Brette 2007 simulation', 0.0, 0.0, 0.06, 600, 'KISAO:0000283')
    sedml_model      = sedmlModel('Brette model', 'Brette model', 'urn:sedml:language:nineml', 'urn:to:user_layer_model') 
    sedml_task       = sedmlTask('task1', 'task1', sedml_model, sedml_simulation)
    
    sedml_variable_time  = sedmlVariable('time', 'time',    sedml_task, symbol='urn:sedml:symbol:time')
    sedml_variable_excV  = sedmlVariable('excV', 'Voltage', sedml_task, target='Group 1/Excitatory population/V[0]')
    sedml_variable_inhV  = sedmlVariable('inhV', 'Voltage', sedml_task, target='Group 1/Inhibitory population/V[0]')

    sedml_data_generator_time = sedmlDataGenerator('DG time', 'DG time', [sedml_variable_time])
    sedml_data_generator_excV = sedmlDataGenerator('DG excV', 'DG excV', [sedml_variable_excV])
    sedml_data_generator_inhV = sedmlDataGenerator('DG inhV', 'DG inhV', [sedml_variable_inhV])

    curve_excV = sedmlCurve('ExcV', 'ExcV', False, False, sedml_data_generator_time, sedml_data_generator_excV)
    curve_inhV = sedmlCurve('InhV', 'InhV', False, False, sedml_data_generator_time, sedml_data_generator_inhV)

    plot_excV  = sedmlPlot2D('Plot excV', 'Plot excV', [curve_excV])
    plot_inhV  = sedmlPlot2D('Plot inhV', 'Plot inhV', [curve_inhV])

    sedml_experiment = sedmlExperiment([sedml_simulation], 
                                       [sedml_model], 
                                       [sedml_task], 
                                       [sedml_data_generator_time, sedml_data_generator_excV, sedml_data_generator_inhV],
                                       [plot_excV, plot_inhV])
    print sedml_experiment
