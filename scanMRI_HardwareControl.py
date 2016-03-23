'''
                    Take care of all NI cards
########################################################################
NI and pyDAQmx functions are not described here, for more details
check : http://www.ni.com/manuals/
########################################################################
'''
from PyDAQmx import Task, DAQmx_Val_ChanPerLine, DAQmx_Val_Rising as Val_Ris
from PyDAQmx import DAQmx_Val_ContSamps as Val_ContSamps
from PyDAQmx import DAQmx_Val_GroupByChannel as Val_GrpCh
from PyDAQmx import DAQmx_Val_Transferred_From_Buffer as Val_Transf_Buffer
from PyDAQmx import DAQmx_Val_Volts as Volts
from PyDAQmx import DAQmx_Val_Cfg_Default as Cfg_Deft
from threading import Thread
from scipy.optimize import minimize
from ctypes import windll, c_bool, byref, c_int, c_double, c_long
from numpy import zeros, cos, pi, sin, arange, uint8, concatenate, average
from numpy import exp, array, sum, power, float64
from numpy.fft import fft, fftshift, fft2


'''
                    Index definition
########################################################################
This function increments index values (number of averaging, number of
slices, number of phases). It is also triggering the end of the sequence
if self.increment returns 1. It goes in infinite loop for FID sequence.
########################################################################
'''


class Index(object):
    def __init__(self, nps, loop_type, up_index):
        self.nx = nps[0]
        self.phase_steps = nps[1]
        self.slice_steps = nps[2]
        self.up_index = up_index
        # This defines various way to acquire data (average first or ...)
        if loop_type == 'A':
            self.option = self.option_a
        else:
            self.option = self.option_b
        self.i_phase = 0
        self.i_slice = 0
        self.i_fake = 0
        self.curr_nx = 0
        self.blank = 0

    def increment(self):
        # The blank is here because the 1st acquisition is never acquired.
        if self.blank != 0:
            if self.phase_steps != 1 or self.slice_steps != 1:
                res = self.option()
                if res == 1:
                    # Stops the sequence
                    return 1
                if self.up_index is not None:
                    # Update GUI indexes (if GUI exists)
                    ix = [self.curr_nx + 1, self.i_phase + 1, self.i_slice + 1]
                    self.up_index.emit(ix)
            else:
                # Just in case of FID, goes into infinite loop
                if self.curr_nx >= self.nx - 1:
                    self.i_fake += 1
                    self.curr_nx = 0
                else:
                    self.curr_nx += 1
                if self.up_index is not None:
                    ix = [self.curr_nx + 1, self.i_fake + 1, 1]
                    self.up_index.emit(ix)
        else:
            self.blank = 1

        return 0

    def option_a(self):
        if self.i_slice < self.slice_steps - 1:
            self.i_slice += 1
        elif self.i_phase < self.phase_steps - 1:
            self.i_phase += 1
            self.i_slice = 0
        elif self.curr_nx < self.nx - 1:
            self.curr_nx += 1
            self.i_slice = 0
            self.i_phase = 0
        else:
            return 1

    def option_b(self):
        if self.i_slice < self.slice_steps - 1:
            self.i_slice += 1
        elif self.curr_nx < self.nx - 1:
            self.curr_nx += 1
            self.i_slice = 0
        elif self.i_phase < self.phase_steps - 1:
            self.i_phase += 1
            self.i_slice = 0
            self.curr_nx = 0
        else:
            return 1


'''
                    Synthetize frequency
########################################################################
Defines an object to manage the synthetizer.
- rf_freq and rf_dur are wave's frequency and duration
- continuous mode is used
- nifgen exports a signal on RTSI1 (floppy cable inside the computer) which
is used to trigger and synchronize all other cards
########################################################################
'''


class Nifgen(object):
    def __init__(self, rf_freq, rf_dur):
        # Constants corresponding to various NI options, defined with c_types
        vi = c_int(1)
        o1 = c_int(1)
        o2 = c_int(101)
        o3 = c_int(1000000 + 150000 + 219)
        o4 = c_double(0)
        length = len(rf_freq)
        # Loading the driver to call niFgen functions
        try:
            self.nfg = windll.LoadLibrary("niFgen_32.dll")
        except OSError:
            self.nfg = windll.LoadLibrary("niFgen_64.dll")
        # The way to initialize niFgen can be found in NI examples
        # It is copy/past from that, only translated into c_types
        self.nfg.niFgen_init(b'Dev3', c_bool(1), c_bool(1), byref(vi))
        self.nfg.niFgen_ConfigureChannels(vi, b"0")
        self.nfg.niFgen_ConfigureOutputMode(vi, o2)
        # This is the way to convert numpy array into C array
        rff = rf_freq.ctypes.data
        rfd = rf_dur.ctypes.data
        rf = c_int(0)
        self.nfg.niFgen_CreateFreqList(vi, o1, length, rff, rfd, byref(rf))
        self.nfg.niFgen_ConfigureFreqList(vi, b"0", rf, c_double(4), o4,  o4)
        self.nfg.niFgen_ConfigureDigitalEdgeStartTrigger(vi, b"PFI1", o2)
        self.nfg.niFgen_ConfigureTriggerMode(vi, b"0", c_int(2))
        self.nfg.niFgen_ConfigureOutputEnabled(vi, b"0", c_bool(1))
        # These two lines export the internal clock of the niFgen (100 MHz)
        # divided by 400 (250 kHz) on the RTSI1 channel. It's the only way
        # to be sure that all cards are synchronized on the same clock
        self.nfg.niFgen_SetAttributeViInt32(vi, b"", o3, c_long(400))
        self.nfg.niFgen_ExportSignal(vi, o2, b"", b"RTSI1")
        # self.niFgen.niFgen_ExportSignal(vi, c_int(1000 + 4), b"", b"RTSI2")
        self.nfg.niFgen_Commit(vi)
        self.vi = vi

    def start(self):
        self.nfg.niFgen_InitiateGeneration(self.vi)

    def stop(self):
        self.nfg.niFgen_AbortGeneration(self.vi)

'''
                    Generate digital channel
########################################################################
Defines an object to manage the digital channels (only three here 1 to 3)
-TR is a digital signal used by the TOMCO and the TRbox
-VT triggers the synthetizer start
########################################################################
'''


class DAQ_Dig(Task):
    def __init__(self, digit, read_data, index, stop_all):
        Task.__init__(self)
        # Find the buffer size dividing the array by the number of channels
        self.buff = len(digit) // 5
        # Function to trigger the acquisition analysis
        self.read_data = read_data
        # Initialize an index class
        self.index = index
        # Flag to avoid having double stop function running
        self.index_stop = True
        # Function to stop all cards
        self.stop_all = stop_all
        # Converts digit into uint8 array, just in case
        digit = digit.astype(uint8)
        chan = b"/Dev2/ao/SampleClock"
        self.CreateDOChan(b"Dev2/port0/line1:5", "", DAQmx_Val_ChanPerLine)
        self.CfgSampClkTiming(chan, 250000, Val_Ris, Val_ContSamps, self.buff)
        self.WriteDigitalLines(self.buff, 0, 10, Val_GrpCh, digit, None, None)
        self.AutoRegisterEveryNSamplesEvent(Val_Transf_Buffer, self.buff, 0)

    def EveryNCallback(self):
        # Each TR, the data is read. It is triggered from here because it
        # is not possible to use this function from the ADC card. Also triggers
        # stop of the sequence when it's over.
        argumts = (self.index.i_phase, self.index.i_slice, self.index.curr_nx,)
        Thread(target=self.read_data, args=argumts).start()
        res = self.index.increment()
        if res == 1 and self.index_stop:
            self.index_stop = False
            self.stop_all()

        return 0

    def stop(self):
        # Empty all channels before stopping the task
        self.StopTask()
        dig = zeros([5 * self.buff], dtype=uint8)
        self.WriteDigitalLines(self.buff, 0, 10, Val_GrpCh, dig, None, None)
        self.StartTask()
        self.StopTask()

'''
                    Generate analogical channel
########################################################################
Defines an object to manage the analogical channels (only five here 0 to 4
Sinc, GradX, GradY, GradZ, B0) Notice that the gradients are combined only at
the end, to allow the use of oblique gradients and offsets
########################################################################
'''


class DAQ_Analog(Task):
    def __init__(self, analog, offset, buff, pattern, gui, index):
        Task.__init__(self)
        # buffer size
        self.buff = buff
        self.gui = gui
        # Patterns defined in the sequence to define gradient variation
        self.p_pat = pattern[0]
        self.s_pat = pattern[1]
        self.analog = analog
        self.offset = offset
        self.index = index
        self.index_stop = 0

        chan = b"/Dev2/RTSI1"
        self.CreateAOVoltageChan(b"Dev2/ao0:4", "", -10, 10, Volts, None)
        self.CfgSampClkTiming(chan, 250000, Val_Ris, Val_ContSamps, buff)
        self.empty()
        self.AutoRegisterEveryNSamplesEvent(Val_Transf_Buffer, buff, 0)

    def start(self):
        # Start task and precalculate in another thread the next needed matrix
        self.StartTask()
        self.index.increment()
        argts = (self.analog, self.offset, self.p_pat[self.index.i_phase])
        argts += (self.s_pat[self.index.i_slice], self.buff, self.gui,)
        Thread(target=self.calc_data, args=argts).start()

    def EveryNCallback(self):
        # Increment index and precalculate in a thread the next needed matrix
        res = self.index.increment()
        if res == 0:
            argts = (self.analog, self.offset, self.p_pat[self.index.i_phase])
            argts += (self.s_pat[self.index.i_slice], self.buff, self.gui,)
            Thread(target=self.calc_data, args=argts).start()
        elif res == 1 and self.index_stop == 0:
            self.index_stop = 1
            Thread(target=self.empty).start()
        return 0

    def stop(self):
        # Stop and empty all channels
        self.StopTask()
        data = zeros([5 * self.buff], dtype=float64)
        self.WriteAnalogF64(self.buff, 0, 10, Val_GrpCh, data, None, None)
        self.StartTask()
        self.StopTask()

    def empty(self):
        data = zeros([5 * self.buff], dtype=float64)
        self.WriteAnalogF64(self.buff, 0, 10, Val_GrpCh, data, None, None)

        return 0

    def calc_data(self, alg, ofst, p_cf, s_cf, buff, gui=None):
        # Combination of gradients according to sequence pattern
        x = alg[1]['Read'] + alg[1]['Phase'] * p_cf + alg[1]['Slice'] * s_cf
        y = alg[2]['Read'] + alg[2]['Phase'] * p_cf + alg[2]['Slice'] * s_cf
        z = alg[3]['Read'] + alg[3]['Phase'] * p_cf + alg[3]['Slice'] * s_cf
        if gui is None:
            data = concatenate((alg[0], x + ofst[0], y + ofst[1]))
            data = concatenate((data, z + ofst[2], zeros([buff]) + ofst[3]))
        else:
            # analog[0][:] *= gui.pulse_amplitude.value() / 1#self.oldPulse
            data = concatenate((alg[0], x + gui.gradx_offset.value()))
            data = concatenate((data, y + gui.grady_offset.value()))
            data = concatenate((data, z + gui.gradz_offset.value()))
            data = concatenate((data, zeros([buff]) + gui.b0_offset.value()))
        try:
            self.WriteAnalogF64(buff, 0, 10.0, Val_GrpCh, data, None, None)
        except:
            print('Writting Error')

        return 0

'''
                    Generate acquisition channel
########################################################################
Deals with the acquisition. Offset supression and quadratic acquisition are
done dynamically, but could be done offline if the speed was too slow.
The 2D fft and the drift cancellation are done here (maybe should be moved
for better structure) at the end of the sequence. 1D dynamic fft is optionnal.
The entire TR is always acquired, and the signal is extracted from it.
########################################################################
'''


class DAQ_Acq(Task):
    def __init__(self, buff, chan, nps, start_acq, i_kspace, up_sigs):
        Task.__init__(self)
        self.nx = nps[0]
        self.p_steps = nps[1]
        self.s_steps = nps[2]
        # total number of acquisition needed
        self.tot = (nps[2] - 1) * (nps[1] - 1) * (nps[0] - 1)
        # index defining the beginning of the signal in the acquisition matrix
        self.s_acq = start_acq
        # Matrix to define correspondancy between index and k_space lines
        self.i_k = i_kspace
        # Total length of the matrix containing the signal
        self.chan = chan
        self.up_graph = up_sigs[0]
        self.up_graph2d = up_sigs[1]
        self.buff = buff
        # Precalculation of the matrices needed for quadratic acq
        self.q_cos = cos(2 * pi * arange(chan) / 4)
        self.q_sin = sin(2 * pi * arange(chan) / 4)
        # This is for 2 channels
        self.read = zeros([2 * self.buff], dtype=float64)
        # Chan is twice smaller in fft because of quadratic acquisition
        self.data_k = zeros([chan, nps[1], nps[2], nps[0]], dtype=complex)
        self.data_fft = zeros((chan / 2, nps[1], nps[2]), dtype=complex)
        # self.data_fft = zeros((chan / 2, p_steps, nx + 1), dtype=complex)
        self.CreateAIVoltageChan("Dev1/ai0:1", "", Cfg_Deft, -1, 1, Volts, None)
        ln = b"/Dev2/ao/SampleClock"
        self.CfgSampClkTiming(ln, 250000, Val_Ris, Val_ContSamps, buff)
        # self.CfgSampClkTiming(b"/Dev1/RTSI1", 250000, ...)

    def read_data(self, p_idx, s_idx, curr_nx):
        try:
            ag = (self.buff, 10, Val_GrpCh, self.read, 2 * self.buff, None, None)
            self.ReadAnalogF64(*ag)
        except:
            print('Error in Acq')
        data_k = self.read[self.s_acq[0]: self.s_acq[0] + self.chan]
        # Just a test for second channel
        data_k2 = self.read[self.s_acq[0] + self.buff: self.s_acq[0] + self.chan + self.buff]
        # Offset is removed
        data_k = data_k - average(data_k)
        i_k = [self.i_k[0, p_idx, s_idx, 0], self.i_k[0, p_idx, s_idx, 1]]
        self.data_k[:, i_k[0], i_k[1], curr_nx].real = 2 * data_k * self.q_cos
        self.data_k[:, i_k[0], i_k[1], curr_nx].imag = 2 * data_k * self.q_sin
        if self.up_graph:
            # optional 1D fft to check dynamically the signal
            allchan_k = [data_k, data_k2]
            allchan_kb = [self.data_k[:, i_k[0], i_k[1], curr_nx], data_k2]
            self.up_graph.emit(allchan_k, allchan_kb)
        if curr_nx == self.nx - 1:
            if p_idx == self.p_steps - 1:
                if s_idx == self.s_steps - 1 and self.p_steps > 1:
                    # Cancel drift and apply 2D fft
                    self.cancel_drift()
                    self.fft_2d()
                    if self.up_graph2d is not None:
                        self.up_graph2d.emit(self.data_fft, self.data_k)
        return 0

    def fft_2d(self):
        datak_n = zeros([self.chan, self.p_steps, self.s_steps], dtype=complex)
        for i in range(self.nx):
            datak_n[:, :, :] += self.data_k[:, :, :, i]
        for i in range(self.s_steps):
            data_tmp = fft2(datak_n[:, :, i])
            data_tmp = fftshift(data_tmp)[self.chan / 4: 3 * self.chan / 4, :]
            self.data_fft[:, :, i] = data_tmp

    def cancel_drift(self):
        # Analyze the phase drift, and interpolate it across images to cancel
        # it. Important for averaging
        for k in range(self.s_steps):
            sgnl_ref = fft(self.data_k[:, self.p_steps / 2, k, 0])
            sgnl_ref = fftshift(sgnl_ref)[3 * self.chan / 8: 5 * self.chan / 8]
            for i in range(1, self.nx):
                signal = fft(self.data_k[:, self.p_steps / 2, k, i])
                signal = fftshift(signal)[3 * self.chan / 8: 5 * self.chan / 8]

                def obj_func(x):
                    new = signal * exp(1j * x[0])
                    res = power(sgnl_ref.real - new.real, 2)
                    res += power(sgnl_ref.imag - new.imag, 2)
                    return sum(res)
                x0 = array([pi])
                bnds = (0, 2 * pi)
                res = minimize(obj_func, x0, method="L-BFGS-B", bounds=[bnds])
                print(res.x)
                for j in range(self.p_steps):
                    self.data_k[:, j, k, i] *= exp(1j * res.x[0])

'''
                    Runtime
########################################################################
Defines an object to manage the digital channels : TR, AD and VT
########################################################################
'''


class RunTime(object):
    def __init__(self, P, up_sigs=None, gui=None, stop=None):
        super().__init__()
        # Initialize all class needed for the sequence management
        up_index = up_sigs[2]
        nps = [P.nx, P.phase_steps, P.slice_steps]
        idx_dig = Index(nps, P.loop_type, up_index)
        idx_anlg = Index(nps, P.loop_type, None)
        self.niFgen = Nifgen(P.rf_freq, P.rf_len)
        self.DAQ_Acq = DAQ_Acq(P.buff, P.chan, nps, P.s_acq, P.i_k, up_sigs)
        self.DAQ_D = DAQ_Dig(P.digit, self.DAQ_Acq.read_data, idx_dig, stop)
        self.DAQ_A = DAQ_Analog(P.anlg, P.off, P.buff, P.pattrn, gui, idx_anlg)

    def start(self):
        # Start the sequence in the right order
        self.DAQ_D.StartTask()
        self.DAQ_Acq.StartTask()
        self.DAQ_A.start()
        self.niFgen.start()

        return 0

    def stop(self):
        # Stops everything
        if self.niFgen is not None:
            self.niFgen.stop()
        if self.DAQ_D is not None:
            self.DAQ_D.stop()
        if self.DAQ_Acq is not None:
            self.DAQ_Acq.StopTask()
        if self.DAQ_A is not None:
            self.DAQ_A.stop()
        if self.niFgen is not None:
            self.niFgen.nfg.niFgen_close(self.niFgen.vi)
        if self.DAQ_D is not None:
            self.DAQ_D = None
        if self.niFgen is not None:
            self.niFgen = None
        if self.DAQ_A is not None:
            self.DAQ_A = None
        if self.DAQ_Acq is not None:
            self.DAQ_Acq = None
