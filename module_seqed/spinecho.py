from grad import *
from sequence import *

class ClassSpinEcho(Sequence):
    def __init__(self, gui):
        super(Spinecho,self).__init__(gui, 'Spin Echo')
        self.name=Spinecho.__name__
        print("New Spinecho object created")

    def getParameters(self, gui):
        # flash specific parameters:  flipa, rfw, readw

        # convention for last letters of time variables
        # t : start of plateau of pulse (after ramp)
        # w : width ( duration) plateau of pulse
        # c : centre of the plateau of the pulse

        # test data
        te  = float(gui.ui.te.text())
        tr = float(gui.ui.tr.text())

        slt = 5   # slice thickness mm
        fov = 150 # field of view mm
        self.rt = gui.ui.riset.value()

        rfw = gui.ui.rfw.value()
        readw = gui.ui.acqw.value()
        readw0 = gui.ui.phasew.value()

        phasew = gui.ui.phasew.value()
        rft = gui.ui.rft.value()
        # temporary pulse amplitudes : will be derived from slr rfbw and fov
        sa = gui.ui.sliceamp.value()
        pa = gui.ui.phaseamp.value()
        ra = gui.ui.readamp.value()

        r = gui.ui.riset.value()  # shorthand for risetime
        h = 0.5    # shorthand for half
        # timing

        slicet = []
        rf90c  = r + h*rfw
        ta = te/2.0
        slicet.append(gui.ui.rft.value())
        rf2start = rft + ta - (rfw/2)
        slicet.append(rf2start - 0.525)
        phaset = float(gui.ui.phaset.text())
        sigc   = te + h*rfw + r       # expected centre of signal
        readt2 = (rf90c + te - h *readw)
        pass
        #______________________________________
        # assemble lists of events
        self.clear()
        self.rf.append( RF(slicet[0],rfw,90))
        self.rf.append( RF(rf2start - self.rt,rfw,180))

        self.slice.append( Slice(slicet[0], rfw, sa, postfactor=-1, posttime=phaset, postwidth = phasew ))
        self.slice.append( Slice(slicet[1], rfw, sa, crushwidth = 0.125, crushamp = 3.5 ))

        self.phase.append( Phase(phaset, phasew, pa))

        self.read.append ( Read(readt2, readw, ra, prefactor = 0.5, pretime = phaset, prewidth = readw0))

        self.acq.append  ( Acq(readt2,readw,acqnum=1))

        self.acqnum = 1
        self.ti = gui.ui.ti.value()
        self.tr = gui.ui.tr.value()
        self.te = gui.ui.te.value()

        self.AcquisitionPattern(gui)

        self.prepareScan()

def main():
    S = Spinecho()
    S.getParameters()
    print(S)
    S.printEvents()

    S.prepareScan()
    print('Dictionary_Sequence \n',S.Dictionary_Sequence)

if __name__ == '__main__':
    main()
