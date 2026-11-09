# Reporting

SPHY includes a large number of processes from which output can be generated through maps and timeseries. In a separate csv-file, the user can decide how map output should be generated for 50+ model variables. The csv-file has 6 columns: `name`, `map`, `avg`, `timeseries`, `filename` and `comment`. By default the csv-file is named `reporting.csv` and is located in the SPHY directory. To output variables other than the defaults, users must place the `reporting.csv` file in the input directory, where SPHY map inputs are located.

The first column refers to the variable name in the model, which should not be changed.

In the second column the user can decide with which frequency the map (sum) output should be generated. This is usually used for water balance fluxes, such as precipitation, evapotranspiration, runoff and sediment transport output:

**Table 1: Variables from which the sum should be reported**

| Code | Meaning | Number of maps generated | Common application |
| :--- | :--- | :--- | :--- |
| **Y** | Yearly sum | Number of years in simulation | Water balance fluxes, e.g. precipitation, evapotranspiration, runoff |
| **M** | Monthly sum | Number of months in simulation (12 * number of years) | Water balance fluxes, e.g. precipitation, evapotranspiration, runoff |
| **D** | Daily output | Each time step | Not commonly used |
| **MS** | Long-term average monthly sum | 12 maps | Water balance fluxes, e.g. precipitation, evapotranspiration, runoff |

The third column is used to indicate the output variables that should be generated as an average. This is most commonly used for water balance storage components, such as canopy, snow, rootzone and groundwater storage, but also for plant water stress.

**Table 2: Variables from which the average should be reported**

| Code | Meaning | Number of generated maps | Common applications |
| :--- | :--- | :--- | :--- |
| **Y** | Yearly average | Number of years in simulation | Water balance storage components, e.g. snow, rootzone and groundwater storage |
| **M** | Monthly average | Number of months in simulation (12 * number of years) | Water balance storage components, e.g. snow, rootzone and groundwater storage |
| **MA** | Long-term monthly average | 12 maps | Water balance storage components, e.g. snow, rootzone and groundwater storage |

In the second and third column more than one output frequency can be selected, separated with a “+” symbol. For example, when the user wants to get yearly and long-term average monthly output, the following combination should be provided: “Y+MA”.

The fourth column is used to indicate which variables should generate daily timeseries. In this case only one frequency can be used, which is daily (D). The time series will be generated at the stations, hence, the output file will contain 1 column with the time steps of the simulation, which is followed by one column per station. Time series output is generally used for routed runoff and sediment flux:

**Table 3: Variable from which a time series should be reported**

| Code | Meaning | Number of time steps | Common application |
| :--- | :--- | :--- | :--- |
| **D** | Daily time series | All time steps | Routed runoff and sediment flux |

In the fifth column the user can define the filename (prefix). The maximum number of characters used here depends on the number of simulated time steps. The file names of map output (sum or average maps) is constructed as follows, in case of daily (D) output: `SedFlxD0.001`, `SedFlxD0.002`, `SedFlxD0.003`, etc. In this case, a prefix of 6 characters is used (i.e. SedFlx). The model will crash in case the simulation has more than 9999 time steps. In case of more than 9999 time steps, a prefix of maximum 5 characters should be used (e.g. SdFlx): `SdFlxD10.000`, `SdFlxD10.001`, `SdFlxD10.002`, etc.

The sixth column provides comments for each of the model variables, such as the full name and the unit.

In column 2-4, `NONE` indicates that no output will be generated. Only model output will be generated for model variables that are considered during the simulation. So, if the reporting csv-table indicates that sediment flux should be reported, but the sediment transport module is not used (as indicated in Sediment Transport tab), then no sediment flux will be generated. 

**Table 4: Example of the reporting file**

| Model name | Map | Avg | Timeseries | Filename | Comment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TotPrec** | Y | NONE | NONE | Prec | PRECIPITATION in mm |
| **PlantStress** | NONE | MA | NONE | Pws | PLANT WATER STRESS dimensionless |
| **StorRootW** | NONE | Y | NONE | Rootw | ROOTZONE STORAGE in mm |
| **QallRAtot** | NONE | NONE | D | QAll | ROUTED TOTAL RUNOFF in m3/s |
| **...** | ... | ... | ... | ... | ... |
