# Sediment transport when using simple routing

The sediment transport module can only be used with the MMF soil erosion model. The sediment transport equation includes two model parameters, the beta and gamma parameter. Prosser & Rustomji (2000) suggest to adopt a value of 1.4 for both parameters. However, these two parameters are frequently used for model calibration, for instance, when measured sediment concentration or reservoir sediment yield data are available.

The flow depth parameter is used to determine the flow velocity using the Manning's equation, which is subsequently used to determine the transport capacity. The simple routing does not determine the water depth, so a catchment average value should be provided here. 

Channels have usually a much lower Manning's value than the one obtained from the vegetation characteristics (see MMF model parameters). When enabling the channel Manning's Roughness, the user can provide a specific channel Manning's value. The upstream area should be defined where channels start to form. The channel Manning’s roughness coefficient should be provided, which will override the Manning’s values determined by the vegetation characteristics. Typical channel Manning’s value can be obtained from [Chow (1959)](https://www.fsl.orst.edu/geowater/FX3/help/8_Hydraulic_Reference/Mannings_n_Tables.htm). 

See Eekhout et al. (2018) for more details on the implementation and a case study.

# References
Chow, V.T., 1959. [Open-Channel Hydraulics](https://doi.org/ISBN%252007-010776-9). McGraw-Hill Book Company, New York, US. 

Eekhout, J.P.C., Terink, W., de Vente, J., 2018. [Assessing the large-scale impacts of environmental change using a coupled hydrology and soil erosion model](https://doi.org/10.5194/esurf-6-687-2018). Earth Surface Dynamics 6, 687–703. 

Prosser, I.P., Rustomji, P., 2000. [Sediment transport capacity relations for overland flow](https://doi.org/10.1177/030913330002400202). Progress in Physical Geography 24, 179–193.