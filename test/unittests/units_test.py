import unittest
from sympy import sympify
from nineml import Document, units as un

all_dims = [getattr(un, d) for d in dir(un)
            if isinstance(getattr(un, d), un.Dimension)]


class TestUnitsDimensions(unittest.TestCase):

    def test_xml_540degree_roundtrip(self):
        document1 = Document.load(units_xml_str)
        xml = document1.serialize()
        document2 = Document.load(xml)
        self.assertEquals(document1, document2)

    def test_sympy(self):
        for dim in (un.temperature, un.capacitance, un.resistance, un.charge,
                    un.voltage, un.specificCapacitance):
            sympy_dim = sympify(dim)
            new_dim = un.Dimension.from_sympy(sympy_dim)
            self.assertEquals(dim, new_dim,
                              "Sympy roundtrip failed for {}".format(dim))

    def test_accessors(self):

        for i, (abbrev, name) in enumerate((
            ('m', 'mass'), ('l', 'length'), ('t', 'time'), ('i', 'current'), 
            ('n', 'amount'), ('k', 'temperature'),
                ('j', 'luminous_intensity'))):
            for dim in all_dims:
                self.assertEqual(getattr(dim, abbrev), dim._dims[i])
                self.assertEqual(getattr(dim, name), dim._dims[i])

# FIXME: Currently the 'scale' attribute isn't supported, need to work out
#        whether we want to do this or not.
units_xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<NineML xmlns="http://nineml.net/9ML/2.0">
  <Annotations>
    <Text>
      As NineML uses the format for units/dimensions that was developed for LEMS
      the units/dimension defined on this page have been copied from the example
      LEMS units/dimension that can be found here
      https://github.com/NeuroML/NeuroML2/blob/master/NeuroML2CoreTypes/NeuroMLCoreDimensions.xml
    </Text>
  </Annotations>
  <Dimension name="time" t="1"/>
  <Dimension name="per_time" t="-1"/>
  <Dimension name="voltage" m="1" l="2" t="-3" i="-1"/>
  <Dimension name="per_voltage" m="-1" l="-2" t="3" i="1"/>
  <Dimension name="conductance" m="-1" l="-2" t="3" i="2"/>
  <Dimension name="conductanceDensity" m="-1" l="-4" t="3" i="2"/>
  <Dimension name="capacitance" m="-1" l="-2" t="4" i="2"/>
  <Dimension name="specificCapacitance" m="-1" l="-4" t="4" i="2"/>
  <Dimension name="resistance" m="1" l="2" t="-3" i="-2"/>
  <Dimension name="resistivity" m="2" l="2" t="-3" i="-2"/>
  <Dimension name="charge" i="1" t="1"/>
  <Dimension name="charge_per_mole" i="1" t="1" n="-1"/>
  <Dimension name="current" i="1"/>
  <Dimension name="currentDensity" i="1" l="-2"/>
  <Dimension name="length" l="1"/>
  <Dimension name="area" l="2"/>
  <Dimension name="volume" l="3"/>
  <Dimension name="concentration" l="-3" n="1"/>
  <Dimension name="substance" n="1"/>
  <Dimension name="permeability" l="1" t="-1"/>
  <Dimension name="temperature" k="1"/>
  <Dimension name="idealGasConstantDims" m="1" l="2" t="-2" k="-1" n="-1"/>
  <Dimension name="rho_factor" l="-1" n="1" i="-1" t="-1"/>
  <Unit symbol="s" dimension="time" power="0"/>
  <Unit symbol="per_s" dimension="per_time" power="0"/>
  <Unit symbol="Hz" dimension="per_time" power="0"/>
  <Unit symbol="ms" dimension="time" power="-3"/>
  <Unit symbol="per_ms" dimension="per_time" power="3"/>
  <!--<Unit symbol="min" dimension="time" power="0" scale="60"/>
  <Unit symbol="per_min" dimension="per_time" power="0" scale="0.01666666667"/>
  <Unit symbol="hour" dimension="time" power="0" scale="3600"/>
  <Unit symbol="per_hour" dimension="per_time" power="0"
    scale="0.00027777777778"/>-->
  <Unit symbol="m" dimension="length" power="0"/>
  <Unit symbol="cm" dimension="length" power="-2"/>
  <Unit symbol="um" dimension="length" power="-6"/>
  <Unit symbol="m2" dimension="area" power="0"/>
  <Unit symbol="cm2" dimension="area" power="-4"/>
  <Unit symbol="um2" dimension="area" power="-12"/>
  <Unit symbol="m3" dimension="volume" power="0"/>
  <Unit symbol="cm3" dimension="volume" power="-6"/>
  <Unit symbol="litre" dimension="volume" power="-3"/>
  <Unit symbol="um3" dimension="volume" power="-18"/>
  <Unit symbol="V" dimension="voltage" power="0"/>
  <Unit symbol="mV" dimension="voltage" power="-3"/>
  <Unit symbol="per_V" dimension="per_voltage" power="0"/>
  <Unit symbol="per_mV" dimension="per_voltage" power="3"/>
  <Unit symbol="ohm" dimension="resistance" power="0"/>
  <Unit symbol="kohm" dimension="resistance" power="3"/>
  <Unit symbol="Mohm" dimension="resistance" power="6"/>
  <Unit symbol="S" dimension="conductance" power="0"/>
  <Unit symbol="mS" dimension="conductance" power="-3"/>
  <Unit symbol="uS" dimension="conductance" power="-6"/>
  <Unit symbol="nS" dimension="conductance" power="-9"/>
  <Unit symbol="pS" dimension="conductance" power="-12"/>
  <Unit symbol="S_per_m2" dimension="conductanceDensity" power="0"/>
  <Unit symbol="mS_per_cm2" dimension="conductanceDensity" power="1"/>
  <Unit symbol="S_per_cm2" dimension="conductanceDensity" power="4"/>
  <Unit symbol="F" dimension="capacitance" power="0"/>
  <Unit symbol="uF" dimension="capacitance" power="-6"/>
  <Unit symbol="nF" dimension="capacitance" power="-9"/>
  <Unit symbol="pF" dimension="capacitance" power="-12"/>
  <Unit symbol="F_per_m2" dimension="specificCapacitance" power="0"/>
  <Unit symbol="uF_per_cm2" dimension="specificCapacitance" power="-2"/>
  <Unit symbol="ohm_m" dimension="resistivity" power="0"/>
  <Unit symbol="kohm_cm" dimension="resistivity" power="1"/>
  <Unit symbol="ohm_cm" dimension="resistivity" power="-2"/>
  <Unit symbol="C" dimension="charge" power="0"/>
  <Unit symbol="C_per_mol" dimension="charge_per_mole" power="0"/>
  <Unit symbol="A" dimension="current" power="0"/>
  <Unit symbol="uA" dimension="current" power="-6"/>
  <Unit symbol="nA" dimension="current" power="-9"/>
  <Unit symbol="pA" dimension="current" power="-12"/>
  <Unit symbol="A_per_m2" dimension="currentDensity" power="0"/>
  <Unit symbol="uA_per_cm2" dimension="currentDensity" power="-2"/>
  <Unit symbol="mA_per_cm2" dimension="currentDensity" power="1"/>
  <Unit symbol="mol_per_m3" dimension="concentration" power="0"/>
  <Unit symbol="mol_per_cm3" dimension="concentration" power="6"/>
  <Unit symbol="M" dimension="concentration" power="3"/>
  <Unit symbol="mM" dimension="concentration" power="0"/>
  <Unit symbol="mol" dimension="substance" power="0"/>
  <Unit symbol="m_per_s" dimension="permeability" power="0"/>
  <Unit symbol="cm_per_s" dimension="permeability" power="-2"/>
  <Unit symbol="um_per_ms" dimension="permeability" power="-3"/>
  <Unit symbol="cm_per_ms" dimension="permeability" power="1"/>
  <Unit symbol="degC" dimension="temperature" offset="273.15"/>
  <Unit symbol="K" dimension="temperature" power="0"/>
  <Unit symbol="J_per_K_per_mol" dimension="idealGasConstantDims" power="0"/>
  <Unit symbol="mol_per_m_per_A_per_s" dimension="rho_factor" power="0"/>
</NineML>"""
