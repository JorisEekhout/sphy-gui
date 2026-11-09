# Meteorological forcing map series

Meteorological forcing map-series are series of input maps with the time step indicated in each filename. The filenames have a strict format with 8 characters before a dot (.), and three characters behind the dot. For example the average temperature maps can have the format tavg0000.001, tavg0000.002, etc. The first four characters of the file name is used in the model to infer the names of the whole time series. The user only needs to select a sample file from the folder where the climate data are stored, from which these four characters are automatically obtained.

To generate forcing data you have two options:
1. Interpolate point station data to grids at the model extent and resolution, and convert to PCRaster grid format.
2. Resample existing gridded meteorological data products to model extent and resolution and convert to PCRaster grid format.

Depending on the number of time steps in your model you will probably need to write a script to batch this process and repeat it automatically for multiple time steps. A script like this can be created in any scripting language like for example Python or R. This procedure is automated in the SPHY preprocessor plugin (Terink et al., 2015b).