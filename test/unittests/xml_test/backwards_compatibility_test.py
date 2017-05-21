import unittest
from lxml import etree
from nineml.utils import xml_equal
from nineml.serialization.xml import (
    Unserializer as Uxml, Serializer as Sxml)


class TestBackwardsCompatibility(unittest.TestCase):

    def test_backwards_compatibility(self):
        full_v1_xml = etree.fromstring(version1)
        full_v2_xml = etree.fromstring(version2)
        v1_doc = Uxml(root=etree.fromstring(version1)).unserialize()
        v2_doc = Uxml(root=etree.fromstring(version2)).unserialize()
        v1_doc._url = './dummy.xml'
        v2_doc._url = './dummy.xml'
        # Ensure all elements are loaded
        list(v1_doc.elements)
        list(v2_doc.elements)
        v1_names = list(v1_doc.nineml_types)
        v2_names = list(v1_doc.nineml_types)
        self.assertEqual(v1_names, v2_names)
        for name in v1_names:
            v1 = v1_doc[name]
            v2 = v2_doc[name]
            # Test loaded python objects are equivalent between versions
            self.assertEqual(
                v1, v2,
                "Loaded version 1 didn't match loaded version 2:\n{}"
                .format(v1.find_mismatch(v2)))
            v1_to_v2_xml = Sxml(document=v2_doc, version=2.0).visit(
                v1, ref_style='force_reference')
            v2_to_v1_xml = Sxml(document=v1_doc, version=1.0).visit(
                v2, ref_style='force_reference')
            v1_xml = self._get_xml_element(full_v1_xml, name)
            v2_xml = self._get_xml_element(full_v2_xml, name)
            # Test the version 1 converted to version 2
            self.assert_(
                xml_equal(v1_to_v2_xml, v2_xml),
                "v2 produced from v1 doesn't match loaded:\n{}\n\nand"
                "\n\n{}".format(xml_to_str(v1_to_v2_xml, pp=True),
                                xml_to_str(v2_xml, pp=True)))
            # Test the version 2 converted to version 1
            self.assert_(
                xml_equal(v2_to_v1_xml, v1_xml),
                "v1 produced from v2 doesn't match loaded:\n{}\n\nand\n\n"
                "{}".format(xml_to_str(v2_to_v1_xml, pp=True),
                            xml_to_str(v1_xml, pp=True)))

    def _get_xml_element(self, xml, name):
        for child in xml.getchildren():
            if child.get('name', child.get('symbol')) == name:
                return child
        raise KeyError("No '{}' in: \n{}"
                       .format(name, xml_to_str(xml)))


def xml_to_str(xml, pp=False):
    return etree.tostring(xml, encoding="UTF-8", pretty_print=pp,
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
    <ConnectionRule standard_library="http://nineml.net/9ML/1.0/connectionrules/Probabilistic"/>
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
        <Reference>RDP</Reference>
      </RandomValue>
    </Property>
  </Component>
  <Component name="CRP">
    <Definition>CR</Definition>
    <Property name="probability" units="unitless">
      <SingleValue>0.5</SingleValue>
    </Property>
  </Component>
  <Component name="RDP">
    <Definition>RD</Definition>
    <Property name="maximum" units="unitless">
      <SingleValue>1.0</SingleValue>
    </Property>
    <Property name="minimum" units="unitless">
      <SingleValue>0.0</SingleValue>
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
    <Connectivity>
      <Reference>CRP</Reference>
    </Connectivity>
    <Response>
      <Reference>D_psrP</Reference>
      <FromSource send_port="spike" receive_port="spike"/>
    </Response>
    <Delay units="ms">
      <SingleValue>1.0</SingleValue>
    </Delay>
  </Projection>
  <Selection name="selection">
    <Concatenate>
      <Item index="0">
        <Reference>P1</Reference>
      </Item>
      <Item index="1">
        <Reference>P2</Reference>
      </Item>
    </Concatenate>
  </Selection>
  <Dimension name="dimensionless"/>
  <Dimension name="time" t="1"/>
  <Dimension name="voltage" m="1" l="2" t="-3" i="-1"/>
  <Dimension name="current" i="1"/>
  <Dimension name="capacitance" m="-1" l="-2" t="4" i="2"/>
  <Unit symbol="unitless" dimension="dimensionless" power="0"/>
  <Unit symbol="nA" dimension="current" power="-9"/>
  <Unit symbol="uF" dimension="capacitance" power="-6"/>
  <Unit symbol="mV" dimension="voltage" power="-3"/>
  <Unit symbol="ms" dimension="time" power="-3"/>
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
  <ConnectionRule name="CR" standard_library="http://nineml.net/9ML/1.0/connectionrules/Probabilistic">
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
          <Reference name="RDP"/>
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
    <Connectivity>
      <Reference name="CRP"/>
    </Connectivity>
    <Response>
      <Reference name="D_psrP"/>
    </Response>
    <Delay>
      <Quantity units="ms">
        <SingleValue>1.0</SingleValue>
      </Quantity>
    </Delay>
    <EventPortConnection sender_role="pre" receiver_role="response" send_port="spike" receive_port="spike"/>
    <AnalogPortConnection sender_role="response" receiver_role="post" send_port="a" receive_port="i_ext"/>
  </Projection>
  <Selection name="selection">
    <Concatenate>
      <Item index="0">
        <Reference name="P1"/>
      </Item>
      <Item index="1">
        <Reference name="P2"/>
      </Item>
    </Concatenate>
  </Selection>
  <Dimension name="dimensionless"/>
  <Dimension name="time" t="1"/>
  <Dimension name="voltage" m="1" l="2" t="-3" i="-1"/>
  <Dimension name="current" i="1"/>
  <Dimension name="capacitance" m="-1" l="-2" t="4" i="2"/>
  <Unit symbol="unitless" dimension="dimensionless" power="0"/>
  <Unit symbol="nA" dimension="current" power="-9"/>
  <Unit symbol="uF" dimension="capacitance" power="-6"/>
  <Unit symbol="mV" dimension="voltage" power="-3"/>
  <Unit symbol="ms" dimension="time" power="-3"/>
</NineML>"""
