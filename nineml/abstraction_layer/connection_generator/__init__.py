

from .base import ConnectionGenerator
import readers
import csa
ConnectionGenerator.selectImplementation('{http://software.incf.org/software/csa/1.0}CSA', csa)