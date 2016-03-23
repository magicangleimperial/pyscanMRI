from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QListWidgetItem
from PyQt5.QtGui import QIcon
from os import listdir, path
from numpy import zeros, float64, int8, sinc, hanning, linspace, sin, cos
from numpy import concatenate, pi, asarray, ndarray, around, sum, tile, ceil
from numpy import int16, ones, sqrt
from scipy import signal

# Constants to define rate of ADC and DAC cards
DACrate = 250000
ADCrate = 250000


'''                    Select Sequence GUI class
########################################################################
1 - Load all text file from the directory /Sequence
2 - Load a sequence from a text file into Sequence Designer
########################################################################
'''


class GUI_SelectSequence(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = loadUi('scanMRI_SelectSequence.ui', self)
        self.ui.listWidget.itemDoubleClicked.connect(self.select_double)
        self.ui.listWidget.itemClicked.connect(self.select)
        self.main_w = parent
        self.curr_dir = path.dirname(path.abspath(__file__)) + "/Sequence"
        self.icon_dir = path.dirname(path.abspath(__file__)) + "/Icons"
        self.refresh(self.curr_dir)
        default_file = path.dirname(path.realpath(__file__))
        default_file += '/module_seqed/' + 'default.csv'
        # Load a default sequence FID into Sequence Designer
        parent.gui_seqed.readdefault(default_file)
        parent.gui_seqed.load_new_sequence(self.curr_dir + "/FID.csv")

    def refresh(self, dir):
        # Checks the current folder to find sequences (csv files)
        self.ui.listWidget.clear()
        for file in listdir(dir):
            if path.isfile(self.curr_dir + "/" + file):
                if file.endswith(".csv"):
                    sequence = QListWidgetItem(self.ui.listWidget)
                    sequence.setText(file.replace(".csv", ""))
                    sequence.setWhatsThis('Sequence')
                    sequence.setIcon(QIcon(self.icon_dir + "/sequence.png"))
            else:
                sequence = QListWidgetItem(self.ui.listWidget)
                sequence.setText(file)
                sequence.setWhatsThis('Sequence Type')
                sequence.setIcon(QIcon(self.icon_dir + "/folder.png"))
        if dir != path.dirname(path.abspath(__file__)) + "/Sequence":
            sequence = QListWidgetItem(self.ui.listWidget)
            sequence.setText('Back')
            sequence.setWhatsThis('Back')
            sequence.setIcon(QIcon(self.icon_dir + "/back.png"))

    def select(self, item):
        # Behavior of the widget when you click on one element
        if item.whatsThis() == 'Sequence':
            pass
        elif item.whatsThis() == 'Sequence Type':
            self.curr_dir += "/" + item.text()
            self.refresh(self.curr_dir)
        elif item.whatsThis() == 'Back':
            self.curr_dir = path.dirname(path.abspath(__file__)) + "/Sequence"
            self.refresh(self.curr_dir)

    def select_double(self, item):
        # Behavior of the widget when you double click on one element
        filename = self.curr_dir + '/' + item.text().replace("	", "") + ".csv"
        self.main_w.gui_seqed.load_new_sequence(filename)
        if self.main_w.ui.act_preview.isChecked():
            self.main_w.gui_preview.showEvent(None)
        self.close()


'''
            Create the object 'Sequence' from a dictionnary
########################################################################
This class transforms a compact csv file which contains all sequence
intelligence into an explicit package of matrices explicitly describing
each step of the sequence.
########################################################################
'''


class Object_Sequence(object):
    def __init__(self, dic_seq):
        # Defines global parameters
        self.DACrate = DACrate
        self.ADCrate = ADCrate
        # Buffer for one repetition time
        self.buff = self.d(dic_seq['TR'])
        # Real repetition time (because of sampling rounding)
        self.tr = self.buff / self.DACrate
        # Beginning of the signal
        self.chan = self.d(dic_seq['Acquisition Length'][0])
        # Total length of the signal
        self.pts_chan_tot = self.d(dic_seq['Acquisition Length'][-1])
        self.pts_chan_tot += self.d(dic_seq['Acquisition Start'][-1])
        self.pts_chan_tot -= self.d(dic_seq['Acquisition Start'][0])
        # Rise time
        self.rise = int(0.2 / 1000 * self.DACrate)
        # Averaging
        self.nx = dic_seq['Averaging']
        # 90 degree pulse value
        self.pulse_amp_90 = dic_seq['Pulse Value 90']
        # Gradient offset
        self.off = dic_seq['Offset']
        # Number of acquisition
        self.nbr_acq = dic_seq['Acquisition Number']
        # Phase and slice steps
        self.phase_steps = dic_seq['Phase Steps']
        self.slice_steps = dic_seq['Slice Steps']
        # Oblique angle
        self.theta_z = dic_seq['Oblique Angle'][0] / 180 * pi
        self.theta_phase = dic_seq['Oblique Angle'][1] / 180 * pi
        # Sequence index
        self.i_k = self.design_indexes()
        self.pattrn = self.design_pattern()
        self.s_acq = self.d(dic_seq['Acquisition Start'][:])
        self.loop_type = dic_seq['Loop Type']
        # Synthetizer
        self.rf_freq, self.rf_len = self.design_rf(dic_seq)
        if dic_seq['Sequence Mode'] == 'Multi Slice':
            self.design_rf_multislice(dic_seq, dic_seq['Slice Thickness'])
        # Emission board digital channels
        self.digit = self.design_digit(dic_seq)
        # Emission board analogical channels
        self.anlg = self.design_analog(dic_seq)

    def d(self, time):
        # Converts a time into a number of steps
        if type(time) == ndarray:
            res = (time / 1000 * self.DACrate).astype(int)
        elif type(time) == list:
            res = (asarray(time) / 1000 * self.DACrate).astype(int)
        else:
            res = int(time / 1000 * self.DACrate)

        return res

    def design_indexes(self):
        # Define a relation between the k-space index and sequence index
        # The type of interleaving for slices is chosen here for now
        mod = 2
        slice_k = zeros([self.slice_steps])
        for i in range(self.slice_steps):
            if mod == 1:
                if i % 2 == 0:
                    slice_k[i] = i // 2
                else:
                    slice_k[i] = - (i + 1) // 2
            elif mod == 2:
                if i % 2 == 0:
                    slice_k[i] = i // 2
                else:
                    slice_k[i] = (i // 2 + ceil(self.slice_steps / 2))
        dim = [self.nbr_acq, self.phase_steps, self.slice_steps, 2]
        i_kspace = zeros(dim, dtype=int16)
        for i in range(self.nbr_acq):
            for j in range(self.phase_steps):
                for k in range(self.slice_steps):
                    i_kspace[i, j, k, 0] = j
                    i_kspace[i, j, k, 1] = slice_k[k]

        return i_kspace

    def design_pattern(self):
        # Defines gradients changes according to the corresponding index
        phase_pattern = linspace(1, -1, num=self.phase_steps)
        slice_pattern = ones([self.slice_steps], dtype=float64)

        return [phase_pattern, slice_pattern]

    def design_rf(self, seq):
        # Design the list for rf (frequencies and time)
        pulse_start = seq['Pulse Start']
        pulse_len = seq['Pulse Length']
        acq_start = seq['Acquisition Start']
        # 3 rf are needed for each pulse and acq because one is the needed
        # frequency, a second is the rephasing frequency, a third is a zeros
        # frequency to fill empty space
        nbr_rf = 3 * (seq['Pulse Number'] + seq['Acquisition Number'])
        rf_freq = zeros([nbr_rf], dtype=float64)
        rf_len = zeros([nbr_rf], dtype=float64)
        check_array = concatenate((pulse_start, acq_start)).argsort()
        for i in range(nbr_rf // 3):
            if check_array[i] < len(pulse_start):
                rf_freq[3 * i] = seq['Pulse Frequency']
                rf_len[3 * i] = (pulse_len[check_array[i]] + 0.1) / 1000
                t_start = pulse_start[check_array[i]]
                t_start += pulse_len[check_array[i]] + 0.1
            else:
                idx = check_array[i] - len(pulse_start)
                rf_freq[3 * i] = seq['Pulse Frequency'] + self.ADCrate / 4
                rf_len[3 * i] = (seq['Acquisition Length'][idx] + 0.1) / 1000
                t_start = acq_start[idx]
                t_start += (seq['Acquisition Length'][idx] + 0.1) / 1000
            # Apply a 0.01 ms rf with a given freq to rephase the signal
            decimal = rf_freq[3 * i] * rf_len[3 * i]
            rf_freq[3 * i + 1] = 1 - around([decimal - int(decimal)], 2)[0]
            rf_freq[3 * i + 1] *= 100000 % 100000
            rf_len[3 * i + 1] = 0.01 / 1000
            # Add a 0 rf to fill empty space
            if i < nbr_rf // 3 - 1:
                if check_array[i + 1] < len(pulse_start):
                    t_end = pulse_start[check_array[i + 1]]
                else:
                    t_end = acq_start[check_array[i + 1] - len(pulse_start)]
                rf_len[3 * i + 2] = (t_end - t_start - 0.01) / 1000
                rf_freq[3 * i + 2] = 0
            else:
                rf_len[3 * i + 2] = self.tr - sum(rf_len)
                rf_freq[3 * i + 2] = 0

        return rf_freq, rf_len

    def design_rf_multislice(self, seq, slice_thick):
        # Change the rf list for multislice
        mod = 2
        nbr_rf = len(self.rf_freq)
        new_rf_freq = tile(self.rf_freq, self.slice_steps)
        new_rf_len = tile(self.rf_len, self.slice_steps)
        check_ar = concatenate((seq['Pulse Start'], seq['Acquisition Start']))
        check_ar = check_ar.argsort()
        for j in range(self.slice_steps):
            if mod == 1:
                if j % 2 == 0:
                    new_freq = j // 2 * slice_thick
                else:
                    new_freq = - (j + 1) // 2 * slice_thick
            elif mod == 2:
                if j % 2 == 0:
                    new_freq = j // 2 * slice_thick
                else:
                    new_freq = j // 2 + ceil(self.slice_steps / 2)
                    new_freq *= slice_thick
            for i in range(nbr_rf // 3):
                if check_ar[i] < len(seq['Pulse Start']):
                    new_rf_freq[3 * i + j * nbr_rf] = self.rf_freq[3 * i]
                    new_rf_freq[3 * i + j * nbr_rf] += new_freq
                    dec = new_rf_freq[3 * i + j * nbr_rf] * self.rf_len[3 * i]
                    dec = around([dec - int(dec)], 2)[0]
                    new_rf_freq[3 * i + 1 + j * nbr_rf] = 1 - dec
                    new_rf_freq[3 * i + 1 + j * nbr_rf] *= 100000 % 100000
        self.rf_freq = new_rf_freq
        self.rf_len = new_rf_len

        return 0

    def design_digit(self, seq):
        # Design digital matrix
        VT = zeros([self.buff], dtype=int8)
        TR = zeros([self.buff], dtype=int8)
        GXE = ones([self.buff], dtype=int8)
        GYE = ones([self.buff], dtype=int8)
        GZE = ones([self.buff], dtype=int8)
        for j in range(seq['Pulse Number']):
            start = self.d(seq['Pulse Start'][j])
            length = self.d(seq['Pulse Length'][j])
            TR[start: start + length] = 1
        start = self.d(seq['Pulse Start'][0] - 0.05)
        length = self.d(0.008)
        VT[start: start + length] = 1

        return concatenate((VT, TR, GXE, GYE, GZE))

    def design_analog(self, seq):
        # Sinus cardinal shape definition
        data_pulse = zeros([self.buff])
        for j in range(seq['Pulse Number']):
            start = self.d(seq['Pulse Start'][j])
            length = self.d(seq['Pulse Length'][j]) + 1
            shape = sinc(linspace(-3, 3, length))
            for i in range(start, start + length):
                i0 = i - start
                data_pulse[i] = seq['Pulse Value 90'] * seq['Pulse Angle'][j]
                data_pulse[i] *= shape[i0] * hanning(length)[i0] / 90
        # Gradient shape definition
        arg = [seq['Read Start'], seq['Read Length'], seq['Read Amplitude']]
        arg.extend((seq['Read Lobes Amplitude'], seq['Read Lobes Length']))
        data_read = self.design_gradient(*arg)
        arg = [seq['Phase Start'], seq['Phase Length'], seq['Phase Amplitude']]
        arg.extend((seq['Phase Lobes Amplitude'], seq['Phase Lobes Length']))
        data_phase = self.design_gradient(*arg)
        arg = [seq['Slice Start'], seq['Slice Length'], seq['Slice Amplitude']]
        arg.extend((seq['Slice Lobes Amplitude'], seq['Slice Lobes Length']))
        data_slice = self.design_gradient(*arg)
        # Gradient orientation definition
        # (read_phi = 0, read_theta = pi/2 and phase_theta = 0)
        arg = [data_read, data_phase, data_slice]
        data_x, data_y, data_z = self.oblique_gradient(*arg)
        # Preemphasis
        # data_x, data_y, data_z = self.preemphasis(data_x, data_y, data_z)
        # Check maximum amplitude to limit it to 10V maximum
        self.voltage_check(data_x, data_y, data_z, self.off)

        return data_pulse, data_x, data_y, data_z

    def design_gradient(self, start, length, amp, lob_amp, lob_length):
        data = zeros([self.buff])
        rise = int(0.2 / 1000 * self.DACrate)
        for i in range(len(start)):
            # First rise time
            t_start = self.d(start[i]) - rise
            t_end = self.d(start[i])
            for j in range(t_start, t_end):
                data[j] = (amp[i] + lob_amp[i]) * (j - t_start) / rise
            # First lobe plateau
            if self.d(lob_length[i]) != 0 and lob_amp[i] != 0:
                t_start = t_end
                t_end += self.d(lob_length[i])
                for j in range(t_start, t_end):
                    data[j] = amp[i] + lob_amp[i]
            # Decrease time to main plateau
                t_start = t_end
                t_end += rise
                for j in range(t_start, t_end):
                    data[j] = lob_amp[i] * (1.0 - (j - t_start) / rise)
                    data[j] += amp[i]
            # Main plateau
            t_start = t_end
            t_end += self.d(length[i])
            for j in range(t_start, t_end):
                data[j] = amp[i]
            # Second rise time
            t_start = t_end
            t_end += rise
            if self.d(lob_length[i]) != 0 and lob_amp[i] != 0:
                for j in range(t_start, t_end):
                    data[j] = amp[i] + lob_amp[i] * (j - t_start) / rise
                # Second lobe plateau
                t_start = t_end
                t_end += self.d(lob_length[i])
                for j in range(t_start, t_end):
                    data[j] = amp[i] + lob_amp[i]
            # Last decrease time
                t_start = t_end
                t_end += rise
            for j in range(t_start, t_end):
                data[j] = (amp[i] + lob_amp[i]) * (1.0 - (j - t_start) / rise)

        return data

    @staticmethod
    def rotation(point, axis, theta):
        # Rotation around an axis from a theta angle in radian
        x, y, z = point[:]
        u, v, w = axis[:]
        c = (u * x + v * y + w * z) * (1 - cos(theta))
        xp = u * c + x * cos(theta) + (-w * y + v * z) * sin(theta)
        yp = v * c + y * cos(theta) + (w * x - u * z) * sin(theta)
        zp = w * c + z * cos(theta) + (-v * x + u * y) * sin(theta)

        return [xp, yp, zp]

    def oblique_gradient(self, data_read, data_phase, data_slice):
        # Coefficients to equilibrate amplitudes between unbalanced gradients
        # x is used as a reference and is then equal to 1
        coef_y = 1
        coef_z = 1
        # Rotation around z first
        read_orig, phase_orig, slice_orig = [1, 0, 0], [0, 1, 0], [0, 0, 1]
        read_new = self.rotation(read_orig, slice_orig, self.theta_z)
        phase_new = self.rotation(phase_orig, slice_orig, self.theta_z)
        slice_new = self.rotation(slice_orig, slice_orig, self.theta_z)
        # Rotation around y
        read_new = self.rotation(read_new, phase_new, self.theta_phase)
        slice_new = self.rotation(slice_new, phase_new, self.theta_phase)
        # X Component
        x = {'Read': data_read * read_new[0]}
        x.update({'Phase':  data_phase * phase_new[0] / coef_y})
        x.update({'Slice':  data_slice * slice_new[0] / coef_z})
        # Y Component
        y = {'Read': data_read * read_new[1] * coef_y}
        y.update({'Phase': data_phase * phase_new[1]})
        y.update({'Slice': data_slice * slice_new[1] / coef_z * coef_y})
        # Z Component
        z = {'Read': data_read * read_new[2] * coef_z}
        z.update({'Phase': data_phase * phase_new[2] / coef_y * coef_z})
        z.update({'Slice': data_slice * slice_new[2]})

        return x, y, z

    def preemphasis(self, gx, gy, gz):
        gx['Read'] += self.preem(gx['Read'], -0.998, 0.302, -0.989, -0.302)
        gx['Phase'] += self.preem(gx['Phase'], -0.998, 0.302, -0.989, -0.302)
        gx['Slice'] += self.preem(gx['Slice'], -0.998, 0.302, -0.989, -0.302)
        gy['Read'] += self.preem(gy['Read'], -0.998, 0.25, -0.962, -0.25)
        gy['Phase'] += self.preem(gy['Phase'], -0.998, 0.25, -0.962, -0.25)
        gy['Slice'] += self.preem(gy['Slice'], -0.998, 0.25, -0.962, -0.25)
        gz['Read'] += self.preem(gz['Read'], -0.998, 0.4, -0.962, -0.4)
        gz['Phase'] += self.preem(gz['Phase'], -0.998, 0.4, -0.962, -0.4)
        gz['Slice'] += self.preem(gz['Slice'], -0.998, 0.4, -0.962, -0.4)

        return gx, gy, gz

    @staticmethod
    def preem(data, a10, weight0, a11, weight1):
        a, b = [1, a10], [-a10, a10]
        temp = weight0 * signal.lfilter(b, a, data, axis=-1, zi=None)
        a, b = [1, a11], [-a11, a11]
        temp += weight1 * signal.lfilter(b, a, data, axis=-1, zi=None)

        return temp

    @staticmethod
    def voltage_check(data_x, data_y, data_z, offset):
        data_x_final = data_x['Read'] + data_x['Phase'] + data_x['Slice']
        data_x_final += offset[0]
        data_y_final = data_y['Read'] + data_y['Phase'] + data_y['Slice']
        data_y_final += offset[1]
        data_z_final = data_z['Read'] + data_z['Phase'] + data_z['Slice']
        data_z_final += offset[2]
        if any(data_x_final >= 10):
            data_x['Read'] = zeros([len(data_x['Read'])])
            data_x['Phase'] = zeros([len(data_x['Read'])])
            data_x['Slice'] = zeros([len(data_x['Read'])])
            offset[0] = 0
            print('X Voltage above 10V !')
        if any(data_y_final >= 10):
            data_y['Read'] = zeros([len(data_y['Read'])])
            data_y['Phase'] = zeros([len(data_y['Read'])])
            data_y['Slice'] = zeros([len(data_y['Read'])])
            offset[1] = 0
            print('Y Voltage above 10V !')
        if any(data_z_final >= 10):
            data_z['Read'] = zeros([len(data_z['Read'])])
            data_z['Phase'] = zeros([len(data_z['Read'])])
            data_z['Slice'] = zeros([len(data_z['Read'])])
            offset[2] = 0
            print('Z Voltage above 10V !')
        if any(data_x_final <= -10):
            data_x['Read'] = zeros([len(data_x['Read'])])
            data_x['Phase'] = zeros([len(data_x['Read'])])
            data_x['Slice'] = zeros([len(data_x['Read'])])
            offset[0] = 0
            print('X Voltage under -10V !')
        if any(data_y_final <= -10):
            data_y['Read'] = zeros([len(data_y['Read'])])
            data_y['Phase'] = zeros([len(data_y['Read'])])
            data_y['Slice'] = zeros([len(data_y['Read'])])
            offset[1] = 0
            print('Y Voltage under -10V !')
        if any(data_z_final <= -10):
            data_z['Read'] = zeros([len(data_z['Read'])])
            data_z['Phase'] = zeros([len(data_z['Read'])])
            data_z['Slice'] = zeros([len(data_z['Read'])])
            offset[2] = 0
            print('Z Voltage under -10V !')
