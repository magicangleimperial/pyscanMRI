from grad import *
from sequence import *

class invrecovery(Sequence):
    def __init__(self, gui):
        super(invrecovery,self).__init__(gui, 'Inversion Recovery')
        self.name=invrecovery.__name__
        print("New InversionRecovery object created")

    def getParameters(self, gui):
        # flash specific parameters:  flipa, rfw, readw

        # convention for last letters of time variables
        # t : start of plateau of pulse (after ramp)
        # w : width ( duration) plateau of pulse
        # c : centre of the plateau of the pulse

        # test data
        te  = float(gui.ui.te.text())
        tr = float(gui.ui.tr.text())
        ti = float(gui.ui.ti.text())

        slt = 5   # slice thickness mm
        fov = 150 # field of view mm

        rfw = float(gui.ui.rfw.text())
        readw = float(gui.ui.acqw.text())
        readw0 = float(gui.ui.phasew.text())

        phasew = float(gui.ui.phasew.text())

        # temporary pulse amplitudes : will be derived from slr rfbw and fov
        sa = float(gui.ui.sliceamp.text())
        pa = float(gui.ui.phaseamp.text())
        ra = float(gui.ui.readamp.text())

        r = riset  # shorthand for risetime
        h = 0.5    # shorthand for half
        # timing
        self.rt = float(gui.ui.riset.text())

        slicet = []
        rf90c  = r + h*rfw
        ta = te/2.0
        slicet.append(ti - (rfw/2))
        rf2start = r + ta - (rfw/2) + ti
        slicet.append(rf2start - 0.525)
        phaset = float(gui.ui.phaset.text())
        sigc   = te + h*rfw + r       # expected centre of signal
        readt2 = (rf90c + te - h *readw + ti)
        pass
        #______________________________________
        # assemble lists of events
        self.clear()
        self.rf.append( RF(r,rfw,180))
        self.rf.append( RF(slicet[0],rfw,90))
        self.rf.append( RF(rf2start - self.rt,rfw,180))

        self.slice.append(Slice(r, rfw, sa))
        self.slice.append( Slice(slicet[0], rfw, sa, postfactor=-1, posttime=phaset, postwidth = phasew ))
        self.slice.append( Slice(slicet[1], rfw, sa, crushwidth = 0.125, crushamp = 3 ))

        self.phase.append( Phase(phaset, phasew, pa))

        self.read.append ( Read(readt2, readw, ra, prefactor = 0.5, pretime = phaset, prewidth = readw0))

        self.acq.append  ( Acq(readt2,readw,acqnum=1))

        self.ti = float(gui.ui.ti.text())
        self.tr = float(gui.ui.tr.text())
        self.te = float(gui.ui.te.text())

        self.AcquisitionPattern(gui)

        self.prepareScan()

def main():
    S = invrecovery()
    S.getParameters()
    print(S)
    S.printEvents()

    S.prepareScan()
    print('Dictionary_Sequence \n',S.Dictionary_Sequence)

if __name__ == '__main__':
    main()