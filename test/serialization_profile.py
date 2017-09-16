from __future__ import print_function
import shutil
import os.path
import tempfile
import cProfile
import pstats
import nineml
from nineml.utils.comprehensive_example import (
    instances_of_all_types, v1_safe_docs)
from nineml.serialization import ext_to_format, format_to_serializer


format_to_ext = dict((v, k) for k, v in ext_to_format.items())  # @UndefinedVariable @IgnorePep8


print_serialized = False
printable = ('xml', 'json', 'yaml')

_tmp_dir = tempfile.mkdtemp()


def function():
    for version in (1.0, 2.0):
        if version == 1.0:
            docs = v1_safe_docs
        else:
            docs = list(instances_of_all_types['NineML'].values())
        for format in format_to_serializer:  # @ReservedAssignment
            try:
                ext = format_to_ext[format]
            except KeyError:
                continue  # ones that can't be written to file (e.g. dict)
            for i, document in enumerate(docs):
                doc = document.clone()
                url = os.path.join(
                    _tmp_dir, 'test{}v{}{}'.format(i, version, ext))
                nineml.write(url, doc, format=format, version=version,
                             indent=2)
                if print_serialized and format in printable:
                    with open(url) as f:
                        print(f.read())
                reread_doc = nineml.read(url, reload=True)  # @UnusedVariable

    shutil.rmtree(_tmp_dir)

out_file = os.path.join(os.getcwd(), 'serial_profile.out')

cProfile.run('function()', out_file)

p = pstats.Stats(out_file)

p.sort_stats('cumtime').print_stats()
