'''                    Grad Template
########################################################################
A simple definition for a grad pulse, with or without pre/post-pulse.
########################################################################
'''


class Grad(object):
    def __init__(self, time, width, amplitude, crushwidth=0, crushamp=0, prewidth=0, postwidth=0):
        self.type = 'Grad'
        self.time = time
        self.width = width
        self.amplitude = amplitude
        self.crushwidth = crushwidth
        self.crushamp = crushamp
        area = amplitude * (width + 0.2)
        if prewidth > 0:
            self.prewidth = prewidth
            prearea = 0.5 * area
            self.pretime = time - prewidth - 0.4
            self.preamplitude = - prearea/(self.prewidth + 0.2)
        if postwidth > 0:
            self.postwidth = postwidth
            postarea = 0.5 * area
            self.posttime = time + width + 0.4
            self.postamplitude = - postarea/(self.postwidth + 0.2)
