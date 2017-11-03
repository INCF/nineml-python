import unittest
import collections
from nineml.user.multi.namespace import (
    append_namespace, split_namespace, make_delay_trigger_name, 
    split_delay_trigger_name, make_regime_name, split_multi_regime_name)


DummyRegime = collections.namedtuple('DummyNamespaceRegime',
                                     'relative_name')
DummyPC = collections.namedtuple(
    'DummyPC', ('sender_role sender_name send_port_name '
                'receiver_role receiver_name receive_port_name'))


class TestConcatenationFunctions(unittest.TestCase):

    def test_append_namespace(self):
        self.assertEqual(append_namespace('a', 'b'), 'a__b')
        self.assertEqual(append_namespace('a_x', 'b'), 'a_x__b')
        self.assertEqual(append_namespace('a_x', 'b_x'), 'a_x__b_x')
        self.assertEqual(append_namespace('a__x', 'b_x'), 'a__x__b_x')
        self.assertEqual(append_namespace('a__x', 'b__x'), 'a__x__b____x')
        self.assertEqual(append_namespace('a__x__y', 'b__x'),
                         'a__x__y__b____x')
        self.assertEqual(append_namespace('a__x', 'b__x__y'),
                         'a__x__b____x____y')
        self.assertEqual(append_namespace('a__x', 'b___x'), 'a__x__b_____x')
        self.assertEqual(append_namespace('a__x', 'b____x'), 'a__x__b______x')

    def test_split_namespace(self):
        self.assertEqual(split_namespace(append_namespace('a', 'b')),
                          ('a', 'b'))
        self.assertEqual(split_namespace(append_namespace('a_x', 'b')),
                          ('a_x', 'b'))
        self.assertEqual(split_namespace(append_namespace('a_x', 'b_x')),
                          ('a_x', 'b_x'))
        self.assertEqual(split_namespace(append_namespace('a__x', 'b_x')),
                          ('a__x', 'b_x'))
        self.assertEqual(split_namespace(append_namespace('a__x', 'b__x')),
                          ('a__x', 'b__x'))
        self.assertEqual(split_namespace(append_namespace('a__x__y', 'b__x')),
                          ('a__x__y', 'b__x'))
        self.assertEqual(split_namespace(append_namespace('a__x', 'b__x__y')),
                          ('a__x', 'b__x__y')),
        self.assertEqual(split_namespace(append_namespace('a__x', 'b___x')),
                          ('a__x', 'b___x'))
        self.assertEqual(split_namespace(append_namespace('a__x', 'b____x')),
                          ('a__x', 'b____x'))

    def test_make_regime_name(self):
        self.assertEqual(make_regime_name(
            {'a': DummyRegime('R1'), 'b': DummyRegime('R2')}),
            'R1___R2')
        self.assertEqual(make_regime_name(
            {'a': DummyRegime('R1'), 'b': DummyRegime('R2'),
             'c': DummyRegime('R3')}),
            'R1___R2___R3')
        self.assertEqual(make_regime_name(
            {'a': DummyRegime('R1_x'), 'b': DummyRegime('R2'),
             'c': DummyRegime('R3_x')}),
            'R1_x___R2___R3_x')
        self.assertEqual(make_regime_name(
            {'a': DummyRegime('R1__x'), 'b': DummyRegime('R2__x'),
             'c': DummyRegime('R3')}),
            'R1____x___R2____x___R3')
        self.assertEqual(make_regime_name(
            {'a': DummyRegime('R1'), 'b': DummyRegime('R2___x'),
             'c': DummyRegime('R3')}),
            'R1___R2_____x___R3')

    def test_split_multi_regime_name(self):
        self.assertEqual(split_multi_regime_name(make_regime_name(
            {'a': DummyRegime('R1'), 'b': DummyRegime('R2')})),
            ('R1', 'R2'))
        self.assertEqual(split_multi_regime_name(make_regime_name(
            {'a': DummyRegime('R1'), 'b': DummyRegime('R2'),
             'c': DummyRegime('R3')})),
            ('R1', 'R2', 'R3'))
        self.assertEqual(split_multi_regime_name(make_regime_name(
            {'a': DummyRegime('R1_x'), 'b': DummyRegime('R2'),
             'c': DummyRegime('R3_x')})),
            ('R1_x', 'R2', 'R3_x'))
        self.assertEqual(split_multi_regime_name(make_regime_name(
            {'a': DummyRegime('R1__x'), 'b': DummyRegime('R2__x'),
             'c': DummyRegime('R3')})),
            ('R1__x', 'R2__x', 'R3'))
        self.assertEqual(split_multi_regime_name(make_regime_name(
            {'a': DummyRegime('R1'), 'b': DummyRegime('R2___x'),
             'c': DummyRegime('R3')})),
            ('R1', 'R2___x', 'R3'))

    def test_make_delay_trigger_name(self):
        self.assertEqual(make_delay_trigger_name(
            DummyPC('sr', None, 'sp', 'rr', None, 'rp')),
            'sr___sp__rr___rp')
        self.assertEqual(make_delay_trigger_name(
            DummyPC(None, 'sn', 'sp', None, 'rn', 'rp')),
            'sn___sp__rn___rp')
        self.assertEqual(make_delay_trigger_name(
            DummyPC('sr_x', None, 'sp_x', 'rr', None, 'rp_x')),
            'sr_x___sp_x__rr___rp_x')
        self.assertEqual(make_delay_trigger_name(
            DummyPC('sr', None, 'sp__x', 'rr', None, 'rp')),
            'sr___sp____x__rr___rp')
        self.assertEqual(make_delay_trigger_name(
            DummyPC('sr', None, 'sp__x', 'rr___x', None, 'rp')),
            'sr___sp____x__rr_____x___rp')

    def test_split_delay_trigger_name(self):
        self.assertEqual(split_delay_trigger_name(make_delay_trigger_name(
            DummyPC('sr', None, 'sp', 'rr', None, 'rp'))),
            ('sr', 'sp', 'rr', 'rp'))
        self.assertEqual(split_delay_trigger_name(make_delay_trigger_name(
            DummyPC(None, 'sn', 'sp', None, 'rn', 'rp'))),
            ('sn', 'sp', 'rn', 'rp'))
        self.assertEqual(split_delay_trigger_name(make_delay_trigger_name(
            DummyPC('sr_x', None, 'sp_x', 'rr', None, 'rp_x'))),
            ('sr_x', 'sp_x', 'rr', 'rp_x'))
        self.assertEqual(split_delay_trigger_name(make_delay_trigger_name(
            DummyPC('sr', None, 'sp__x', 'rr', None, 'rp'))),
            ('sr', 'sp__x', 'rr', 'rp'))
        self.assertEqual(split_delay_trigger_name(make_delay_trigger_name(
            DummyPC('sr', None, 'sp__x', 'rr___x', None, 'rp'))),
            ('sr', 'sp__x', 'rr___x', 'rp'))
