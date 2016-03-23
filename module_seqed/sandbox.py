from sequence import *

class sandbox(Sequence):
    def __init__(self, gui):
        super(sandbox,self).__init__(gui, 'Sandbox')
        self.name=sandbox.__name__
        print("New sandbox object created")


    def getParameters(self, gui):
        a=0

