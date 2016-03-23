# <center> User Manual </center>

## Run a sequence
- Run the script scanMRI_GUI.py (ctrl + shift + B)
- Click on “open a sequence” and select one
- Click on start to run the sequence
- Click on “View” → “Signal Preview” to have a preview of the
Signal (keep in mind it slows everything down for low TR below
50 ms)
- Click on "save" to save in png or dicom
- If sequence needs to be changed, click on “Sequence” →
“Edit/ Change”

## Edit a sequence
#### "Options" tab
- You can choose the sequence type (only FID and Gradient Echo are working for
  now).
- You can choose the type of 3D image you want with "options". Right now only
multislice is implemented but volumetric and various slicing pattern should be
added soon.
- TR, Nx, phase views and slice views are respectively the repetition time,
the number of averaging, the number of phase views and the
number of slice views
#### "Advanced" tab
- Contains available options to precisely set up your sequence. Lots
of constraints are defined (in module_seqed/FID, FLASH, ...) to minimize the
number of parameters.
#### "Dev" tab
- Those values should not be changed by the user in theory. In practice, as
long as we don't have any robust and automatic calibration, we need to manually
adjust those values before taking images.
- "Index loop" defines how your iteration loop is defined. It has to be noticed
that the slice views is always the first parameter to be incremented. It's
because of a National Instrument limitation [1]. For now we have A -> slice ->
 phase -> averaging and B -> slice -> averaging -> phase

[1]The synthesizer is continuously generating the same frequencies list, over
and over again. If slices were incremented after __np__ phase views for
example, we would have to generate a frequency list containing __np__ identical
frequency multiplied by the number of slices which is not convenient and also
not recommended as the synthesizer has a frequency list limit of 54000
elements.
