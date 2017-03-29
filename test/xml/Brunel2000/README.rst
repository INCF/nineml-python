===================
Brunel (2000) model
===================

1. (Re)-Generate the abstraction layer XML files as follows::

   python alphaPSR.py
   python brunelIaF.py
   python poisson.py
   python staticConnection.py

2. Generate the user-layer XML file, read it in, and run the simulation:

   python run_brunel_network_alpha.py AI

This produces a figure "brunel_network_alpha.png"
