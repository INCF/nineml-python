from lxml import etree

class CgClosure:
    def __init__ (self, formals, pyFunc):
        self.formals = formals
        self.function = pyFunc

    def __call__ (self, parameterSet):
        args = map (lambda name: parameterSet[name].value, self.formals)
        return self.function (*args)

def cgClosureFromURI (uri):
    # Need to obtain XML file here
    filename = uri
    
    doc = etree.parse (filename)
    root = doc.getroot ()
    
