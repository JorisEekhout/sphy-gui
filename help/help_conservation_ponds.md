# Ponds

Ponds and other retention structures, like check dams, are simulated with the Reservoir module. The location of the ponds should be provided in the ponds map. The ponds parameters are provided in the ponds table. All the ponds with the same parameter values should get the same ID in the ponds map. For example, if all the ponds have the same characteristics, then all the ponds should get an ID of 1 in the ponds map. 

In the ponds table the **Pond depth** and **Pond area** should be indicated. The pond area determines the area how much water can reinfiltrate into the soil per day, in case reinfiltration is enabled. The daily outflow is determined by the **Outflow coefficient (Kr)**. A value of Kr = 0 indicates that no water will be released by the pond, unless the capacity is exceeded. With Kr values higher than 0 an amount of water will be released. See xxx for more information on the outflow coefficient and how it is being used in the Reservoir module. The **Trapping efficiency** determines how much sediment is being retained by the pond in case the Erosion and Sediment transport modules are used. 

**Table 1: Pond table**

| ID | Pond depth | Pond area | Outflow coefficient (Kr) | Trapping efficiency |
| :--- | :--- | :--- | :--- | :--- |
| -99 | 1 | 2 | 3 | 4 |
| 1 | value1 | value2 | value3 | value4 |
| etc | etc | etc | etc | etc |

Water stored in the ponds can reinfiltrate into the soil when reinfiltration is enabled. The reinfiltration exponent is an empirical exponent for relative conductivity. A value of 3 is the default value.