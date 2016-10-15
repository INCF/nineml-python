
from nineml.abstraction.dynamics import Dynamics
from nineml.abstraction.dynamics.testing_utils import RecordValue

import coba_synapse
import iaf


class ComponentMetaData(object):
    is_neuron_model = False

    supports_test_pynn_neuron_std = True

    parameters = {
        'iaf.cm': 1.0,
        'iaf.gl': 50.0,
        'iaf.taurefrac': 5.0,
        'iaf.vrest': -65.0,
        'iaf.vreset': -65.0,
        'iaf.vthresh': -50.0,
        'cobaExcit.tau': 2.0,
        'cobaInhib.tau': 5.0,
        'cobaExcit.vrev': 0.0,
        'cobaInhib.vrev': -70.0,
    }

    initial_values = {
        'iaf_V': parameters['iaf.vrest'],
        'tspike': -1e99,
        'regime': 1002,
    }

    synapse_components = [
        ('cobaInhib', 'q'),
        ('cobaExcit', 'q'),
    ]

    records = [
        RecordValue(what='iaf_V',       tag='Voltage [mV]',     label='Membrane Voltage'),
        RecordValue(what='cobaInhib_g', tag='Conductance [ns]', label='cobaInhib-g'),
        RecordValue(what='cobaExcit_g', tag='Conductance [ns]', label='cobaExcit-g'),
        RecordValue(what='regime',      tag='Regime',           label='Regime'),
    ]


def get_component():

    # Create a model, composed of an iaf neuron, and
    iaf_2coba_model = Dynamics(
        name="iaf_2coba",
        subnodes={"iaf": iaf.get_component(),
                  "cobaExcit": coba_synapse.get_component(),
                  "cobaInhib": coba_synapse.get_component()})

    # Connections have to be setup as strings, because we are deep-copying objects.
    iaf_2coba_model.connect_ports("iaf.V", "cobaExcit.V")
    iaf_2coba_model.connect_ports("iaf.V", "cobaInhib.V")
    iaf_2coba_model.connect_ports("cobaExcit.I", "iaf.ISyn")
    iaf_2coba_model.connect_ports("cobaInhib.I", "iaf.ISyn")

    return iaf_2coba_model
