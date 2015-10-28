import unittest
from nineml import load
from nineml.exceptions import NineMLXMLBlockError, NineMLXMLAttributeError


class TestBackwardsCompatibility(unittest.TestCase):

    def setUp(self):
        self.v1 = load(version1)
        self.v2 = load(version2)
#         list(self.v1.elements)
#         list(self.v2.elements)

    def test_dynamics(self):
        v1 = self.v1['D_cellP']
        v2 = self.v2['D_cellP']
        self.assertEqual(
            v1, v2, "Loaded version 1 didn't match loaded version 2:\n{}"
            .format(v1.find_mismatch(v2)))


version1 = """<?xml version="1.0" encoding="UTF-8"?>
<NineML xmlns="http://nineml.net/9ML/1.0">
  <ComponentClass name="D_cell">
    <Parameter name="tau" dimension="time"/>
    <Parameter name="cm" dimension="capacitance"/>
    <Parameter name="v_thresh" dimension="voltage"/>
    <EventSendPort name="spike"/>
    <AnalogReducePort name="i_ext" dimension="current" operator="+"/>
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
    <StateVariable name="a" dimension="current"/>
    <AnalogSendPort name="a" dimension="current"/>
    <Dynamics>
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
    <ConnectionRule standard_library="http://nineml.net/connectionrule/Probabilistic">
      <Parameter name="probability" dimension="dimensionless"/>
    </ConnectionRule>
  </ComponentClass>
  <ComponentClass name="RD">
    <RandomDistribution standard_library="http://uncertml.org/2.0/UniformDistribution.xml">
      <Parameter name="minimum" dimension="dimensionless"/>
      <Parameter name="maximum" dimension="dimensionless"/>
    </RandomDistribution>
  </ComponentClass>
  <Component name="D_cellP">
    <Definition>D_cell</Definition>
    <Property name="tau" units="ms">
      <SingleValue>1.0</SingleValue>
    </Property>
    <Property name="cm" units="uF">
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
      <Component name="RDP">
        <Definition>RD</Definition>
        <Property name="minimum" units="unitless">
          <SingleValue>0.0</SingleValue>
        </Property>
        <Property name="maximum" units="unitless">
          <SingleValue>1.0</SingleValue>
        </Property>
      </Component>
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
      <FromResposne send_port="a" receive_port="i_ext"/>
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
  <Unit symbol="unitless" dimension="dimensionless"/>
</NineML>"""

version2 = """<?xml version="1.0" encoding="UTF-8"?>
<NineML xmlns="http://nineml.net/9ML/2.0">
  <Dynamics name="D_cell">
    <Parameter name="tau" dimension="time"/>
    <Parameter name="cm" dimension="capacitance"/>
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
    <StateVariable name="a" dimension="current"/>
    <AnalogSendPort name="a" dimension="current"/>
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
  <ConnectionRule name="CR" standard_library="http://nineml.net/connectionrule/Probabilistic">
    <Parameter name="probability" dimension="dimensionless"/>
  </ConnectionRule>
  <RandomDistribution name="RD" standard_library="http://uncertml.org/2.0/UniformDistribution.xml">
    <Parameter name="minimum" dimension="dimensionless"/>
    <Parameter name="maximum" dimension="dimensionless"/>
  </RandomDistribution>
  <DynamicsProperties name="D_cellP">
    <Definition name="D_cell"/>
    <Property name="tau">
      <Quantity units="ms">
        <SingleValue>1.0</SingleValue>
      </Quantity>
    </Property>
    <Property name="cm">
      <Quantity units="uF">
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
        <RandomDistributionValue port="out">
          <RandomDistributionProperties name="RDP">
            <Definition name="RD"/>
            <Property name="minimum">
              <Quantity units="unitless">
                <SingleValue>0.0</SingleValue>
              </Quantity>
            </Property>
            <Property name="maximum">
              <Quantity units="unitless">
                <SingleValue>1.0</SingleValue>
              </Quantity>
            </Property>
          </RandomDistributionProperties>
        </RandomDistributionValue>
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
    <EventPortConnection sender_role="pre" receiver_role="response" send_port="spike" receive_port="spike"/>
    <AnalogPortConnection sender_role="response" receiver_role="post" send_port="i_syn" receive_port="i_ext"/>
    <Delay>
      <Quantity units="ms">
        <SingleValue>1.0</SingleValue>
      </Quantity>
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
  <Unit symbol="unitless" dimension="dimensionless"/>
</NineML>"""
