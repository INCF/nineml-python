#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import nineml
from nineml.abstraction_layer.testing_utils import RecordValue, TestableComponent
from nineml.abstraction_layer import ComponentClass
import os, sys, subprocess
from time import localtime, strftime, time
from nineml_component_inspector import nineml_component_inspector

css = """
<style type="text/css">
    body {
        color: #333333;
    }

    html, body {
        height: 100%;
        width: 940px;
        margin: 0 auto;
    
        color: #555;
        background-color: #FFFFFF;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #333333
    }

    h1 {
        #height: 23px;
        margin: 0px;
        border-bottom: 5px solid #636466;
        color: #636466;
        display: block;
    }
  
    table {
        border-collapse:collapse;
        border:thin solid;
    }
    
    tr {
    }

    td {
        border: thin solid;
        padding-left:   10px;
        padding-right:  5px;
        padding-top:    3px;
        padding-bottom: 3px;
    }

    th {
        border: thin solid;
        padding-left:   10px;
        padding-right:  5px;
        padding-top:    7px;
        padding-bottom: 7px;
    }

    thead th, tfoot th, tfoot td {
        background-color: #65944A;
        color: white;
    }

    tfoot td {
        text-align:right
    }
   
</style>
"""

html_template = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
{0}
<body>
<div id="main">
<p> <img src="logo.png"> </p>
<h1>
    NineML Model report: {1}
</h1>

{2}
{3}
</div>

</body>
</head>
"""

def createHTMLReport(inspector, tests, htmlOutputFile, find_files_dir = '.'):
    of = open(htmlOutputFile, 'w')
    components_content, tests_content = inspector.generateHTMLReport(tests)
    
    html = html_template.format(css, inspector.ninemlComponent.name, components_content, tests_content)    
    of.write(html)
    of.close()

def showFile(html):
    if os.name == 'nt':
        os.filestart(html)
    elif os.name == 'posix':
        os.system('/usr/bin/xdg-open ' + html)  

