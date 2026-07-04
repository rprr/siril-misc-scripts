# siril-misc-scripts
For Astrophotography

## Requirements
- This is for Mac OS X but should work on linux with some mods.
- Install Siril
- Create your python environment. I just used the built in venv. See requirements.txt for specific python packages needed. 

## siril_psf_analyzer.py
- Needs a fits file specified. 
- Only tested on the Seestar S30 Pro (OSC sensor)
- Finds stars and returns statistics of the PSF
- ** CAVEAT **: used some AI (google) prompts to create this code

## Usage
- Activate your python environment\
  `source /link/to/python_env/bin/activate`
- Run the script\
  `./siril_psf_analyzer.py my_fits_file.fit`
- Other than some log messages, your output should look like this
```
------------------------------------------------------------
===========================================================================
      TRUE GLOBAL AXIS-SPECIFIC AVERAGES (ALL STARS)
===========================================================================
Total Stars Processed : 2361
Average FWHM X-Axis   : 7.0971 px  (26.5326 arcsec)
Average FWHM Y-Axis   : 6.3255 px  (23.6478 arcsec)
Aspect Ratio (Y/X)    : 0.8913 (1.0 = Perfect Circle)

===========================================================================
      DETAILED MATRIX: 10 STARS CLOSEST TO MEDIAN BRIGHTNESS (-15.22 mag)
===========================================================================
  ID   X_Pos   Y_Pos  Magnitude  FWHMx[px]  FWHMy[px]  FWHMx["]  FWHMy["]
1169  437.91 3156.98     -15.23       7.33       6.53     27.40     24.43
1170  145.04  490.78     -15.23       7.06       6.55     26.41     24.48
1171  785.26  507.45     -15.23       7.16       5.90     26.77     22.04
1177 1197.60 3554.72     -15.22       7.91       7.74     29.57     28.94
1178  277.39  768.36     -15.22       6.80       6.20     25.43     23.19
1179 2035.24 1706.38     -15.22       6.86       6.50     25.66     24.31
1180 1494.57 3117.05     -15.22       7.14       6.53     26.70     24.41
1181  200.25  969.35     -15.22       6.81       6.11     25.47     22.85
1182  268.16 3364.76     -15.22       7.94       6.89     29.69     25.76
1193 1505.84 2447.96     -15.21       6.43       6.26     24.05     23.40
===========================================================================
```
- It also makes an output file with all of the stars in the current directory
