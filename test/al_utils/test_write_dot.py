"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from nineml.abstraction_layer.dynamics import writers


class TestWriteDot(object):

    @classmethod
    def test(cls, testable_component, build_dir):
        component = testable_component()
        print '  -- Writing Component to .dot'
        dotfile = build_dir + component.name + '.dot'
        writers.DotWriter.write(component, dotfile)

        print '  -- Building .dot -> pdf, svg, png'
        writers.DotWriter.build(dotfile, output_types=['pdf', 'svg', 'png'])
