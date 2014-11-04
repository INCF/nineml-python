from .base import ConnectionGenerator
import readers
try:
    import csa
    have_csa = True
except ImportError:
    have_csa = False

if have_csa:
    ConnectionGenerator.selectImplementation(
                         '{http://software.incf.org/software/csa/1.0}CSA', csa)
