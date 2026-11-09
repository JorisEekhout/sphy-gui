# Sediment transport when using travel time routing

When using the traveltime routing algorithm, the model generates flow velocity and water depth which are used to force the different sediment transport equations. The transport equations are subdivided into two groups. For rills the Govers (1990) and Abrahams et al. (2001) equations can be used, which both have a model parameter which can be used for model calibration. The default value for the ciritical stream power for Govers (1990) is 0.4 kg m<sup>-1</sup> s<sup>-1</sup>. The default value for the critical Shields parameter for Abrahams et al. (2001) is 0.06. For channels the Yalin (1963), Wong and Parker (2006) and Wilcock and Crowe (2003), from which the first two equations include a model parameter for calibration purposes. The default value for the critical shields parameter for Yalin (1963) is 0.06. The default effective critical Shields parameter for Wong and Parker (2006) is 0.0495. The sediment transport algorithm also accounts for a maximum allowable sediment concentration, which is 1060 g l<sup>-1</sup> by default.

# References
Abrahams, A.D., Li, G., Krishnan, C., Atkinson, J.F., 2001. [A sediment transport equation for interrill overland flow on rough surfaces](https://doi.org/10.1002/esp.286). Earth Surface Processes and Landforms 26, 1443–1459. 

Govers, G., 1990. Empirical relationships for the transport capacity of overland flow., in: Erosion, Transport and Deposition Processes. IAHS Publ.

Wilcock, P.R., Crowe, J.C., 2003. [Surface-based Transport Model for Mixed-Size Sediment](https://doi.org/10.1061/(ASCE)0733-9429(2003)129:2(120)). Journal of Hydraulic Engineering 129, 120–128. 

Wong, M., Parker, G., 2006. [Reanalysis and Correction of Bed-Load Relation of Meyer-Peter and Müller Using Their Own Database](https://doi.org/10.1061/(asce)0733-9429(2006)132:11(1159)). Journal of Hydraulic Engineering 132, 1159–1168. 

Yalin, M.S., 1963. An expression for bedload transportation. Journal of the Hydraulics Division. Proceedings of the American Society of Civil Engineers 89, 221–250.

