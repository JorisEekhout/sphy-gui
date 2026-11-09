# Erosion module

The SPHY GUI currently accounts for two soil erosion moduls, i.e. MMF and MUSLE. For both models a rock fraction map is required. The rock fraction map can, for instance, be obtained from the formulations suggested by Poesen et al. (1998). 

The soil erosion models are forced by local runoff, without accounting for flow accumulation. Forcing the soil erosion models by accumulated runoff can be enabled, but only in case the Routing Module is used. Forcing the soil erosion model by accumulated runoff can lead to unrealistically high erosion rates in channels. This can be prevented by excluding the channels in this calculation. To make use of this option, the upstream area to define the channel heads should be provided. 

# References
Poesen, J.W., van Wesemael, B., Bunte, K., Benet, A.S., 1998. [Variation of rock fragment cover and size along semiarid hillslopes: a case-study from southeast Spain](https://doi.org/10.1016/S0169-555X(98)00013-0). Geomorphology 23, 323–335. 