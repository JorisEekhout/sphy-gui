# Morgan-Morgan-Finney soil erosion model

The MMF soil erosion model requires the following land use specific model parameters:

**Table 1: MMF Table**

| Land Use Class | Plant Height (PH) | Stem density (NV) | Stem Diameter (D) | Canopy Cover (CC) | Ground Cover (GC) | No Erosion | Tillage | Manning | No Vegetation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| -99 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| 1 | 10 | 0.5 | 0.4 | 0.8 | 0.65 | 0 | 0 | 0.2 | 0 |
| 2 | 0.5 | 4 | 0.2 | 0.5 | 0.5 | 0 | 0 | 0.1 | 0 |
| 3 | 0.2 | 20 | 0.15 | 0.3 | 0.35 | 0 | 1 | 0 | 1 |
| … | … | … | … | … | … | … | … | … | … |

Values for the plant height, stem density, stem diameter, canopy cover and ground cover can be found in Table 3 of Morgan and Duzant (2008). However, this table is mostly focused on British crop types and natural vegetation. Still, this table gives some suggestions for different vegetation types, which may help to define the model parameters for other geographical regions. The **No erosion** column is used to indicate with 0 (erosion) or 1 (no erosion) which land use types do not experience erosion, such as water and urban. In case of no erosion, the sediment taken into transport will be set to 0. The **Tillage** column indicates which land use classes apply tillage, i.e. 0 for no tillage and 1 for tillage. In case of tillage, the Manning’s roughness coefficient for soil should be defined with a separate model parameter (see below). The **Manning** column can be used to provide a Manning’s coefficient for irregular-spaced vegetation, commonly used for natural cover types (e.g. forest and shrubland). This column will be ignored in case it is set to 0, in that case the Manning’s roughness coefficient for vegetation will be determined from the stem density and stem diameter. Manning’s coefficient values for different vegetation conditions can be obtained from [Chow (1959)](https://www.fsl.orst.edu/geowater/FX3/help/8_Hydraulic_Reference/Mannings_n_Tables.htm). The **No vegetation** column is used to ignore the Manning’s roughness coefficient for vegetation. This can be useful in the case of land use classes without vegetation cover, like bare soil or continously tilled orchards. In those case the stem density is very low, which may result in unrealistic Manning’s roughness values.

Stem density, stem diameter and ground cover are commonly used for model calibration. Although literature values are available, these values are difficult to obtain for large study areas and may differ from agricultural field to agricultural field or from forest to forest.

The MMF soil erosion model may consider the changes of vegetation conditions in case of a sow-harvest cycle. In that case, the erosion after harvest should be enabled. Another land use specific table (Table 2) should be provided, which gives the values for the period between harvest and sowing (commonly a fallow period):

**Table 2: MMF After Harvest Table**

| Land Use Class | Sowing | Harvest | Plant Height (PH) | Stem Density (NV) | Stem Diameter (D) | Canopy Cover (CC) | Ground Cover (GC) | Tillage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| -99 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| 1 | 102 | 241 | 0.05 | 500 | 0.01 | 0.3 | 0.35 | 1 |
| 2 | 278 | 51 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| … | … | … | … | … | … | … | … | … |

The sowing and harvest dates (day of the year) should be provided in the **Sowing** and **Harvest** columns. The other columns are similar to **Table 1**, with the difference that the values provided in the harvest table (**Table 2**) will be considered in the period between harvest and sowing and **Table 1** during the rest of the year when crops are present. When a land use class does not consider the sowing-harvest cycle (e.g. natural vegetation or orchards/vineyards), the dates should be set to 0.

The detachability of the soil by raindrop impact should be provided for each texture class. Based on laboratory experiments, Quansah (1982) proposed 0.1, 0.5 and 0.3 g J<sup>-1</sup> for clay, silt and sand, respectively. Similarly, the detachability of the soil by runoff should be provided for each texture class, for which Quansah (1982) proposed 1.0, 1.6 and 1.5 g mm<sup>-1</sup> for clay, silt and sand, respectively.

The Manning’s roughness coefficient for bare soil should be provided, for which a default value of 0.015 s m<sup>1/3</sup> should be a reasonable first estimate.

The Manning's roughness for tilled soil should be provided. Morgan & Duzant (2008) proposed the equation below to determine this roughness value for, where RFR can be obtained from Table IV of their paper, with common values for different ploughing equipment.

$$n_{tilled} = exp(-2.1132 + 0.0349 * RFR)$$

Intensity of the erosive rain can be provided with the PrecInt model parameter. Morgan and Duzant (2008) propose 10 mm h<sup>-1</sup> for temperate climates, 25 mm h<sup>-1</sup> for tropical climates and 30 mm h<sup>-1</sup> for strongly seasonal climates (e.g. Mediterranean, tropical monsoon). The intensity of the erosive precipitation will be based on the rainfall intensity obtained from the rainfall input when the infiltration excess surface runoff is enables (see the Infiltration parameters in the Soil parameters tab).

The particle diameter of the three textural classes should be provided, for which Morgan & Duzant (2008) proposes 2 μm for clay, 60 μm for silt and 200 μm for sand. The particle diameter for gravel should only be provided when the Morphodynamics module is enabled.

The sediment and flow density are commonly set to 2650 and 1000 kg m<sup>-3</sup>, where the flow density may be slightly higher (e.g. 1100 kg m<sup>-3</sup>) for runoff on hillslopes (Abrahams et al., 2001).

The flow depth of bare soil and in-field flow depth are used in the immediate deposition calculation. Values of, respectively, 0.005 and 0.1 m are suggested as default values.

The fluid viscosity is nominally set to 0.001 kg m<sup>-1</sup> s<sup>-1</sup>, but often taken as 0.0015 to allow for the effects of the sediment in the flow (Morgan and Duzant, 2008).

See Eekhout et al. (2018) for more details on the implementation and a case study.

# References
Abrahams, A.D., Li, G., Krishnan, C., Atkinson, J.F., 2001. [A sediment transport equation for interrill overland flow on rough surfaces](https://doi.org/10.1002/esp.286). Earth Surface Processes and Landforms 26, 1443–1459. 

Chow, V.T., 1959. [Open-Channel Hydraulics](https://doi.org/ISBN%252007-010776-9). McGraw-Hill Book Company, New York, US. 

Eekhout, J.P.C., Terink, W., de Vente, J., 2018. [Assessing the large-scale impacts of environmental change using a coupled hydrology and soil erosion model](https://doi.org/10.5194/esurf-6-687-2018). Earth Surface Dynamics 6, 687–703. 

Morgan, R.P.C., Duzant, J.H., 2008. [Modified MMF (Morgan–Morgan–Finney) model for evaluating effects of crops and vegetation cover on soil erosion](https://doi.org/10.1002/esp.1530). Earth Surface Processes and Landforms 33, 90–106.

Quansah, C., 1982. Laboratory experimentation for the statistical derivation of equations for soil erosion modelling and soil conservation design (PhD Thesis). Cranfield Institute of Technology.