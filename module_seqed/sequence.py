from csv import writer
'''                    Sequence Object
########################################################################
This object link a gui with an update function, to have an up-to-date
dictionnary/graph. Defines also a way to read a dictionnary to update the
GUI and a save function.
########################################################################
'''


class Sequence(object):
    def __init__(self, gui, seqtype):
        self.dict_seq = {}
        self.gui = gui
        # Link all signals/slots, critical part
        arg_tot = [self.up_core_pulse, self.up_core_read, self.up_core_phase]
        arg_tot.append(self.up_core_slice)
        [gui.acqw.valueChanged.connect(x) for x in arg_tot]
        [gui.phaset.valueChanged.connect(x) for x in arg_tot[1:3]]
        [gui.phasew.valueChanged.connect(x) for x in arg_tot[1:]]
        [gui.rft.valueChanged.connect(x) for x in arg_tot[1:]]
        [gui.rfw.valueChanged.connect(x) for x in arg_tot]
        [gui.riset.valueChanged.connect(x) for x in arg_tot[1:]]
        gui.readamp.valueChanged.connect(self.up_core_read)
        gui.phaseamp.valueChanged.connect(self.up_core_phase)
        gui.sliceamp.valueChanged.connect(self.up_core_slice)
        gui.acqnum.valueChanged.connect(self.up_core_read)
        gui.flipa.valueChanged.connect(self.up_core_pulse)
        gui.comboBox_loop.currentIndexChanged.connect(self.up_loop)
        gui.slicethickness.valueChanged.connect(self.up_thick)
        gui.gradx_offset.valueChanged.connect(self.up_offset)
        gui.grady_offset.valueChanged.connect(self.up_offset)
        gui.gradz_offset.valueChanged.connect(self.up_offset)
        gui.b0_offset.valueChanged.connect(self.up_offset)
        gui.nx.valueChanged.connect(self.up_averaging)
        gui.pulse_amplitude.valueChanged.connect(self.up_pulse_amplitude)
        gui.pulse_frequency.valueChanged.connect(self.up_pulse_frequency)
        gui.tr.valueChanged.connect(self.up_tr)
        gui.phase_steps.valueChanged.connect(self.up_phase_steps)
        gui.slice_steps.valueChanged.connect(self.up_slice_steps)
        gui.te.valueChanged.connect(self.up_te)
        gui.ti.valueChanged.connect(self.up_ti)
        gui.thetaz.valueChanged.connect(self.up_oblique)
        gui.thetap.valueChanged.connect(self.up_oblique)

    def readfromdict(self, dictio):
        # Read all values in csv and put them in spinboxes. Signals and slots
        # need to be blocked before doing that
        curr_index = self.gui.option.findText(dictio['Sequence Mode'])
        self.gui.option.setCurrentIndex(curr_index)
        curr_index = self.gui.comboBox_loop.findText(dictio['Loop Type'])
        self.gui.comboBox_loop.setCurrentIndex(curr_index)
        self.gui.tr.setValue(dictio['TR'])
        self.gui.te.setValue(dictio['TE'])
        self.gui.riset.setValue(dictio['Rise Time'])
        self.gui.rfw.setValue(dictio['Pulse Length'][0])
        self.gui.rft.setValue(dictio['Pulse Start'][0])
        self.gui.sliceamp.setValue(dictio['Slice Amplitude'][0])
        if len(dictio['Read Amplitude']) > 1:
            self.gui.readamp.setValue(dictio['Read Amplitude'][1])
        else:
            self.gui.readamp.setValue(dictio['Read Amplitude'][0])
        self.gui.acqw.setValue(dictio['Acquisition Length'][0])
        self.gui.phaset.setValue(dictio['Phase Start'][0])
        self.gui.phasew.setValue(dictio['Phase Length'][0])
        self.gui.phaseamp.setValue(dictio['Phase Amplitude'][0])
        self.gui.ti.setValue(dictio['TI'])
        self.gui.flipa.setValue(dictio['Pulse Angle'][0])
        self.gui.phase_steps.setValue(dictio['Phase Steps'])
        self.gui.slice_steps.setValue(dictio['Slice Steps'])
        self.gui.slicethickness.setValue(dictio['Slice Thickness'])
        self.gui.thetaz.setValue(dictio['Oblique Angle'][0])
        self.gui.thetap.setValue(dictio['Oblique Angle'][1])

    def up_all(self):
        # Update the entire dictionnary according to GUI values
        self.dict_seq.update({'Rise Time': self.gui.riset.value()})
        self.dict_seq.update({'Sequence Mode': self.gui.option.currentText()})
        self.dict_seq.update({'Sequence Type': self.gui.seqtype.currentText()})
        self.up_core_read()
        self.up_core_phase()
        self.up_core_slice()
        self.up_core_pulse()
        self.up_ti()
        self.up_te()
        self.up_tr()
        self.up_phase_steps()
        self.up_slice_steps()
        self.up_pulse_frequency()
        self.up_pulse_amplitude()
        self.up_averaging()
        self.up_thick()
        self.up_loop()
        self.up_offset()
        self.up_oblique()

    def up_core_slice(self):
        # Update the slice part dictionnary according to GUI values
        self.get_parameters()
        self.dict_seq.update({'Slice Start': []})
        self.dict_seq.update({'Slice Length': []})
        self.dict_seq.update({'Slice Amplitude': []})
        self.dict_seq.update({'Slice Lobes Amplitude': []})
        self.dict_seq.update({'Slice Lobes Length': []})
        for i in range(len(self.slice)):
            if hasattr(self.slice[i], 'pretime'):
                self.dict_seq['Slice Start'].append(self.slice[i].pretime)
                self.dict_seq['Slice Length'].append(self.slice[i].prewidth)
                self.dict_seq['Slice Amplitude'].append(self.slice[i].preamplitude)
                self.dict_seq['Slice Lobes Amplitude'].append(0.)
                self.dict_seq['Slice Lobes Length'].append(0.)
            self.dict_seq['Slice Start'].append(self.slice[i].time)
            self.dict_seq['Slice Length'].append(self.slice[i].width)
            self.dict_seq['Slice Amplitude'].append(self.slice[i].amplitude)
            self.dict_seq['Slice Lobes Length'].append(self.slice[i].crushwidth)
            self.dict_seq['Slice Lobes Amplitude'].append(self.slice[i].crushamp)
            if hasattr(self.slice[i], 'posttime'):
                self.dict_seq['Slice Start'].append(self.slice[i].posttime)
                self.dict_seq['Slice Length'].append(self.slice[i].postwidth)
                self.dict_seq['Slice Amplitude'].append(self.slice[i].postamplitude)
                self.dict_seq['Slice Lobes Amplitude'].append(0.)
                self.dict_seq['Slice Lobes Length'].append(0.)
        self.dict_seq.update({'Slice Number': len(self.dict_seq['Slice Start'])})
        self.gui.widget_Slice.update_figure(self.dict_seq, 'Slice')

    def up_core_phase(self):
        # Update the phase part dictionnary according to GUI values
        self.get_parameters()
        self.dict_seq.update({'Phase Start': [x.time for x in self.phase]})
        self.dict_seq.update({'Phase Length': [x.width for x in self.phase]})
        self.dict_seq.update({'Phase Amplitude': [x.amplitude for x in self.phase]})
        self.dict_seq.update({'Phase Lobes Amplitude': [0. for x in self.phase]})
        self.dict_seq.update({'Phase Lobes Length': [0. for x in self.phase]})
        self.dict_seq.update({'Phase Number': len(self.phase)})
        self.gui.widget_Phase.update_figure(self.dict_seq, 'Phase')

    def up_core_read(self):
        self.get_parameters()
        self.dict_seq.update({'Read Start': []})
        self.dict_seq.update({'Read Length': []})
        self.dict_seq.update({'Read Amplitude': []})
        self.dict_seq.update({'Read Lobes Amplitude': []})
        self.dict_seq.update({'Read Lobes Length': []})
        for i in range(len(self.read)):
            if hasattr(self.read[i], 'pretime'):
                self.dict_seq['Read Start'].append(self.read[i].pretime)
                self.dict_seq['Read Length'].append(self.read[i].prewidth)
                self.dict_seq['Read Amplitude'].append(self.read[i].preamplitude)
                self.dict_seq['Read Lobes Amplitude'].append(0.)
                self.dict_seq['Read Lobes Length'].append(0.)
            self.dict_seq['Read Start'].append(self.read[i].time)
            self.dict_seq['Read Length'].append(self.read[i].width)
            self.dict_seq['Read Amplitude'].append(self.read[i].amplitude)
            self.dict_seq['Read Lobes Amplitude'].append(0.)
            self.dict_seq['Read Lobes Length'].append(0.)
            if hasattr(self.read[i], 'posttime'):
                self.dict_seq['Read Start'].append(self.read[i].posttime)
                self.dict_seq['Read Length'].append(self.read[i].postwidth)
                self.dict_seq['Read Amplitude'].append(self.read[i].postamplitude)
                self.dict_seq['Read Lobes Amplitude'].append(0.)
                self.dict_seq['Read Lobes Length'].append(0.)
        self.dict_seq.update({'Read Number': len(self.dict_seq['Read Start'])})
        self.dict_seq.update({'Acquisition Start': [x.time for x in self.acq]})
        self.dict_seq.update({'Acquisition Length': [x.width for x in self.acq]})
        self.dict_seq.update({'Acquisition Number': len(self.acq)})
        self.gui.widget_Read.update_figure(self.dict_seq, 'Read')

    def up_core_pulse(self):
        self.get_parameters()
        value = [x.time for x in self.rf]
        self.dict_seq.update({'Pulse Start': value})
        value = [x.width for x in self.rf]
        self.dict_seq.update({'Pulse Length': value})
        value = [x.amplitude for x in self.rf]
        self.dict_seq.update({'Pulse Angle': value})
        value = len(self.rf)
        self.dict_seq.update({'Pulse Number': value})
        self.gui.widget_RF.update_figure(self.dict_seq, 'RF')

    def up_ti(self):
        value = self.gui.ti.value()
        self.dict_seq.update({'TI': value})

    def up_te(self):
        value = self.gui.te.value()
        self.dict_seq.update({'TE': value})
        self.up_core_read()
        self.up_core_phase()
        self.up_core_slice()

    def up_tr(self):
        value = self.gui.tr.value()
        self.dict_seq.update({'TR': value})

    def up_phase_steps(self):
        value = self.gui.phase_steps.value()
        self.dict_seq.update({'Phase Steps': value})

    def up_slice_steps(self):
        value = self.gui.slice_steps.value()
        self.dict_seq.update({'Slice Steps': value})

    def up_pulse_frequency(self):
        value = self.gui.pulse_frequency.value()
        self.dict_seq.update({'Pulse Frequency': value})

    def up_pulse_amplitude(self):
        value = self.gui.pulse_amplitude.value()
        self.dict_seq.update({'Pulse Value 90': value})

    def up_averaging(self):
        value = self.gui.nx.value()
        self.dict_seq.update({'Averaging': value})

    def up_thick(self):
        value = self.gui.slicethickness.value()
        self.dict_seq.update({'Slice Thickness': value})

    def up_loop(self):
        value = str(self.gui.comboBox_loop.currentText())
        self.dict_seq.update({'Loop Type': value})

    def up_offset(self):
        value = [self.gui.gradx_offset.value(), self.gui.grady_offset.value()]
        value.append(self.gui.gradz_offset.value())
        value.append(self.gui.b0_offset.value())
        self.dict_seq.update({'Offset': value})

    def up_oblique(self):
        value = [self.gui.thetaz.value(), self.gui.thetap.value()]
        self.dict_seq.update({'Oblique Angle': value})

    def writetocsv(self, fn):
        # Save the sequence in a csv file
        keys = list(self.dict_seq.keys())
        file_seq = writer(open(fn, 'w', newline=''))
        for key in sorted(keys):
            val = self.dict_seq[key]
            file_seq.writerow([key, val])
