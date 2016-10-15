import unittest
from nineml import Document
from nineml.xml import etree, get_element_maker
from nineml.utils import xml_equal


class TestBackwardsCompatibility(unittest.TestCase):

    def setUp(self):
        self.v1_xml = etree.fromstring(version1)
        self.v2_xml = etree.fromstring(version2)
        self.v1_doc = Document.load(version1, url='./dummy.xml')
        self.v2_doc = Document.load(version2, url='./dummy.xml',
                                    register_url=False)
#         list(self.v1.elements)
#         list(self.v2.elements)

    def test_backwards_compatibility(self):
        v1_names = list(self.v1_doc.nineml_types)
        v2_names = list(self.v1_doc.nineml_types)
        self.assertEqual(v1_names, v2_names)
        for name in v1_names:
            v1 = self.v1_doc[name]
            v2 = self.v2_doc[name]
            # Test loaded python objects are equivalent between versions
            self.assertEqual(
                v1, v2, "Loaded version 1 didn't match loaded version 2:\n{}"
                .format(v1.find_mismatch(v2)))
            v1_to_v2_xml = v1.to_xml(self.v2_doc, as_ref=False,
                                     E=get_element_maker(2.0),
                                     no_annotations=True)
            v2_to_v1_xml = v2.to_xml(self.v1_doc, as_ref=False,
                                     E=get_element_maker(1.0),
                                     no_annotations=True)

            v1_xml = self._get_xml_element(self.v1_xml, name)
            v2_xml = self._get_xml_element(self.v2_xml, name)
#             if not xml_equal(v1_to_v2_xml, v2_xml):
#                 v1.to_xml(self.v2_doc, E=get_element_maker(2.0))
            # Test the version 1 converted to version 2
            self.assert_(
                xml_equal(v1_to_v2_xml, v2_xml),
                "v2 produced from v1 doesn't match loaded:\n{}\n\nand\n\n{}"
                .format(xml_to_str(v1_to_v2_xml), xml_to_str(v2_xml)))
            # Test the version 2 converted to version 1
            self.assert_(
                xml_equal(v2_to_v1_xml, v1_xml),
                "v1 produced from v2 doesn't match loaded:\n{}\n\nand\n\n{}"
                .format(xml_to_str(v2_to_v1_xml), xml_to_str(v1_xml)))

    def _get_xml_element(self, xml, name):
        for child in xml.getchildren():
            if child.get('name', child.get('symbol')) == name:
                return child
        raise KeyError("No '{}' in: \n{}"
                       .format(name, xml_to_str(xml)))


def xml_to_str(xml):
    return etree.tostring(xml, encoding="UTF-8", pretty_print=True,
                          xml_declaration=True)


version1 = """<?xml version="1.0" encoding="UTF-8"?>
<NineML xmlns="http://nineml.net/9ML/1.0">
  <ComponentClass name="D_cell">
    <Parameter name="cm" dimension="capacitance"/>
    <Parameter name="tau" dimension="time"/>
    <Parameter name="v_thresh" dimension="voltage"/>
    <AnalogReducePort name="i_ext" dimension="current" operator="+"/>
    <EventSendPort name="spike"/>
    <Dynamics>
      <StateVariable name="v" dimension="voltage"/>
      <Regime name="sole">
        <TimeDerivative variable="v">
          <MathInline>v/tau + i_ext/cm</MathInline>
        </TimeDerivative>
        <OnCondition target_regime="sole">
          <Trigger>
            <MathInline>v > v_thresh</MathInline>
          </Trigger>
          <OutputEvent port="spike"/>
        </OnCondition>
      </Regime>
    </Dynamics>
  </ComponentClass>
  <ComponentClass name="D_psr">
    <Parameter name="tau" dimension="time"/>
    <Parameter name="weight" dimension="current"/>
    <EventReceivePort name="spike"/>
    <AnalogSendPort name="a" dimension="current"/>
    <Dynamics>
      <StateVariable name="a" dimension="current"/>
      <Regime name="sole">
        <TimeDerivative variable="a">
          <MathInline>a/tau</MathInline>
        </TimeDerivative>
        <OnEvent port="spike" target_regime="sole">
          <StateAssignment variable="a">
            <MathInline>a + weight</MathInline>
          </StateAssignment>
        </OnEvent>
      </Regime>
    </Dynamics>
  </ComponentClass>
  <ComponentClass name="CR">
    <Parameter name="probability" dimension="dimensionless"/>
    <ConnectionRule standard_library="http://nineml.net/9ML/1.0/connectionrules/ProbabilisticConnectivity"/>
  </ComponentClass>
  <ComponentClass name="RD">
    <Parameter name="maximum" dimension="dimensionless"/>
    <Parameter name="minimum" dimension="dimensionless"/>
    <RandomDistribution standard_library="http://www.uncertml.org/distributions/uniform"/>
  </ComponentClass>
  <Component name="D_cellP">
    <Definition>D_cell</Definition>
    <Property name="cm" units="uF">
      <SingleValue>1.0</SingleValue>
    </Property>
    <Property name="tau" units="ms">
      <SingleValue>1.0</SingleValue>
    </Property>
    <Property name="v_thresh" units="mV">
      <SingleValue>-50.0</SingleValue>
    </Property>
  </Component>
  <Component name="D_psrP">
    <Definition>D_psr</Definition>
    <Property name="tau" units="ms">
      <SingleValue>1.0</SingleValue>
    </Property>
    <Property name="weight" units="nA">
      <RandomValue>
        <Component name="RDP">
          <Definition>RD</Definition>
          <Property name="maximum" units="unitless">
            <SingleValue>1.0</SingleValue>
          </Property>
          <Property name="minimum" units="unitless">
            <SingleValue>0.0</SingleValue>
          </Property>
        </Component>
      </RandomValue>
    </Property>
  </Component>
  <Component name="CRP">
    <Definition>CR</Definition>
    <Property name="probability" units="unitless">
      <SingleValue>0.5</SingleValue>
    </Property>
  </Component>
  <Population name="P1">
    <Size>10</Size>
    <Cell>
      <Reference>D_cellP</Reference>
    </Cell>
  </Population>
  <Population name="P2">
    <Size>10</Size>
    <Cell>
      <Reference>D_cellP</Reference>
    </Cell>
  </Population>
  <Projection name="Pr">
    <Source>
      <Reference>P1</Reference>
    </Source>
    <Destination>
      <Reference>P2</Reference>
      <FromResponse send_port="a" receive_port="i_ext"/>
    </Destination>
    <Response>
      <Reference>D_psrP</Reference>
      <FromSource send_port="spike" receive_port="spike"/>
    </Response>
    <Connectivity>
      <Reference>CRP</Reference>
    </Connectivity>
    <Delay units="ms">
      <SingleValue>1.0</SingleValue>
    </Delay>
  </Projection>
  <Dimension name="time" t="1"/>
  <Dimension name="voltage" m="1" l="2" t="-3" i="-1"/>
  <Dimension name="dimensionless"/>
  <Dimension name="current" i="1"/>
  <Dimension name="capacitance" m="-1" l="-2" t="4" i="2"/>
  <Unit symbol="nA" dimension="current" power="-9"/>
  <Unit symbol="uF" dimension="capacitance" power="-6"/>
  <Unit symbol="mV" dimension="voltage" power="-3"/>
  <Unit symbol="ms" dimension="time" power="-3"/>
  <Unit symbol="unitless" dimension="dimensionless" power="0"/>
</NineML>"""

version2 = """<?xml version="1.0" encoding="UTF-8"?>
<NineML xmlns="http://nineml.net/9ML/2.0">
  <Dynamics name="D_cell">
    <Parameter name="cm" dimension="capacitance"/>
    <Parameter name="tau" dimension="time"/>
    <Parameter name="v_thresh" dimension="voltage"/>
    <AnalogReducePort name="i_ext" dimension="current" operator="+"/>
    <EventSendPort name="spike"/>
    <StateVariable name="v" dimension="voltage"/>
    <Regime name="sole">
      <TimeDerivative variable="v">
        <MathInline>v/tau + i_ext/cm</MathInline>
      </TimeDerivative>
      <OnCondition target_regime="sole">
        <Trigger>
          <MathInline>v > v_thresh</MathInline>
        </Trigger>
        <OutputEvent port="spike"/>
      </OnCondition>
    </Regime>
  </Dynamics>
  <Dynamics name="D_psr">
    <Parameter name="tau" dimension="time"/>
    <Parameter name="weight" dimension="current"/>
    <EventReceivePort name="spike"/>
    <AnalogSendPort name="a" dimension="current"/>
    <StateVariable name="a" dimension="current"/>
    <Regime name="sole">
      <TimeDerivative variable="a">
        <MathInline>a/tau</MathInline>
      </TimeDerivative>
      <OnEvent port="spike" target_regime="sole">
        <StateAssignment variable="a">
          <MathInline>a + weight</MathInline>
        </StateAssignment>
      </OnEvent>
    </Regime>
  </Dynamics>
  <ConnectionRule name="CR" standard_library="http://nineml.net/9ML/1.0/connectionrules/ProbabilisticConnectivity">
    <Parameter name="probability" dimension="dimensionless"/>
  </ConnectionRule>
  <RandomDistribution name="RD" standard_library="http://www.uncertml.org/distributions/uniform">
    <Parameter name="maximum" dimension="dimensionless"/>
    <Parameter name="minimum" dimension="dimensionless"/>
  </RandomDistribution>
  <DynamicsProperties name="D_cellP">
    <Definition name="D_cell"/>
    <Property name="cm">
      <Quantity units="uF">
        <SingleValue>1.0</SingleValue>
      </Quantity>
    </Property>
    <Property name="tau">
      <Quantity units="ms">
        <SingleValue>1.0</SingleValue>
      </Quantity>
    </Property>
    <Property name="v_thresh">
      <Quantity units="mV">
        <SingleValue>-50.0</SingleValue>
      </Quantity>
    </Property>
  </DynamicsProperties>
  <DynamicsProperties name="D_psrP">
    <Definition name="D_psr"/>
    <Property name="tau">
      <Quantity units="ms">
        <SingleValue>1.0</SingleValue>
      </Quantity>
    </Property>
    <Property name="weight">
      <Quantity units="nA">
        <RandomValue>
          <RandomDistributionProperties name="RDP">
            <Definition name="RD"/>
            <Property name="maximum">
              <Quantity units="unitless">
                <SingleValue>1.0</SingleValue>
              </Quantity>
            </Property>
            <Property name="minimum">
              <Quantity units="unitless">
                <SingleValue>0.0</SingleValue>
              </Quantity>
            </Property>
          </RandomDistributionProperties>
        </RandomValue>
      </Quantity>
    </Property>
  </DynamicsProperties>
  <ConnectionRuleProperties name="CRP">
    <Definition name="CR"/>
    <Property name="probability">
      <Quantity units="unitless">
        <SingleValue>0.5</SingleValue>
      </Quantity>
    </Property>
  </ConnectionRuleProperties>
  <Population name="P1">
    <Size>10</Size>
    <Cell>
      <Reference name="D_cellP"/>
    </Cell>
  </Population>
  <Population name="P2">
    <Size>10</Size>
    <Cell>
      <Reference name="D_cellP"/>
    </Cell>
  </Population>
  <Projection name="Pr">
    <Pre>
      <Reference name="P1"/>
    </Pre>
    <Post>
      <Reference name="P2"/>
    </Post>
    <Response>
      <Reference name="D_psrP"/>
    </Response>
    <Connectivity>
      <Reference name="CRP"/>
    </Connectivity>
    <Delay>
      <Quantity units="ms">
        <SingleValue>1.0</SingleValue>
      </Quantity>
    </Delay>
    <AnalogPortConnection sender_role="response" receiver_role="post" send_port="a" receive_port="i_ext"/>
    <EventPortConnection sender_role="pre" receiver_role="response" send_port="spike" receive_port="spike"/>
  </Projection>
  <Dimension name="time" t="1"/>
  <Dimension name="voltage" m="1" l="2" t="-3" i="-1"/>
  <Dimension name="dimensionless"/>
  <Dimension name="current" i="1"/>
  <Dimension name="capacitance" m="-1" l="-2" t="4" i="2"/>
  <Unit symbol="nA" dimension="current" power="-9"/>
  <Unit symbol="uF" dimension="capacitance" power="-6"/>
  <Unit symbol="mV" dimension="voltage" power="-3"/>
  <Unit symbol="ms" dimension="time" power="-3"/>
  <Unit symbol="unitless" dimension="dimensionless" power="0"/>
</NineML>"""
