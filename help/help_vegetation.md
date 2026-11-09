# Dynamic vegetation module

Usage of the dynamic vegetation module in SPHY requires a time series of NDVI maps of the study area. These are prepared in the same format and naming conventions as the meteorological forcing map series (`ndvi0000.001`, etc.). The user only needs to select a sample file from the folder where the ndvi data are stored, from which these four characters are automatically obtained. NDVI maps for SPHY applications are typically derived from satellite-based sensors such as Sentinel-2, Landsat 8, or MODIS. As these satellites do not have daily overpass frequencies and clouds sometimes hinder the acquisition of high-quality images, daily NDVI maps are unlikely to be available. When SPHY is run with daily time steps, the model takes the most recent NDVI image until a new one is available from the forcing map series.

The NDVI is used within SPHY as an important indicator of vegetation vigor and amount of vegetation. It allows for dynamic simulation of processes such as evapotranspiration, interception and canopy storage. To couple NDVI with the crop coefficient (*Kc*), it is required to set maximum and minimum NDVI values that are linked to max and min *Kc*. The maximum leaf area index (LAImax) typically depends on vegetation type and should be listed in a lookup table. Table 1 shows the values for a certain number of vegetation types.

**Table 1: LAImax values for different vegetation types (Sellers et al., 1996)**

| Vegetation type | LAImax [-] |
| :--- | :--- |
| **Broadleaf evergreen trees** | 7 |
| **Broadleaf deciduous trees** | 7 |
| **Mixed trees** | 7.5 |
| **Needleleaf evergreen trees** | 8 |
| **High latitude deciduous trees** | 8 |
| **Grass with 10 - 40% woody cover** | 5 |
| **Grass with <10% woody cover** | 5 |
| **Shrubs and bare soil** | 5 |
| **Moss and lichens** | 5 |
| **Bare** | 5 |
| **Cultivated** | 6 |

The interception is determined using a maximum canopy storage model. SPHY provides two models, i.e. Von Hoyningen-Huene (1981): 

$$S_{max} = 0.935 + 0.498 \cdot LAI - 0.00575 \cdot LAI^2$$ 

and Aston (1979): 

$$S_{max} = S_{inf} \cdot (1 - \exp(-\kappa \cdot LAI))$$

The latter model requires additional model parameters, which include the maximum canopy storage (mm) and an exponent. These parameters can also be specified per land use class, for which a look-up table is required. Only use the Maximum Canopy Storage Table input field when a table is used, otherwise leave this input field empty.

Von Hoyningen-Huene, J., 1981. Die Interzeption des Niederschlags in landwirtschaftlichen Pflanzenbeständen. Arbeitsbericht Deutscher Verband für Wasserwirtschaft und Kulturbau, Braunschweig.

Aston, A.R., 1979. Rainfall interception by eight small trees. Journal of Hydrology, 42(3–4), pp.383–396. doi:10.1016/0022-1694(79)90057-X
