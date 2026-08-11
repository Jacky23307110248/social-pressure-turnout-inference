# Social-Pressure Turnout RCT: Literature and Claim Audit

Status: verified for report preparation, 2026-08-11

## Audit question

What does the external literature permit this project to claim about replication,
persistence, external validity, mechanisms, interference, and ethics when reanalyzing
the 2006 Michigan social-pressure field experiment?

## Evidence map

| Topic | Source | Evidence used here | Constraint on this project |
|---|---|---|---|
| Original experiment and data | Gerber, Green, and Larimer (2008), *APSR*, DOI: [10.1017/S000305540808009X](https://doi.org/10.1017/S000305540808009X); [Yale project and data page](https://isps.yale.edu/resource/social-pressure-and-voter-turnout-evidence-from-a-large-scale-field-experiment) | Large household-randomized field experiment using verified turnout; treatment arms increased social pressure in ordered bundles. | The present analysis is a transparent reanalysis/replication with additional uncertainty and claim-boundary audits, not a new trial and not a discovery unaffected by prior knowledge. |
| Independent synthesis | [J-PAL evaluation summary](https://www.povertyactionlab.org/evaluation/social-pressure-and-voter-turnout-united-states) | Reports the study population, the large Neighbors effect, complaints/removal requests, estimated cost per additional vote, and evidence from later elections. | Useful for policy context and ethics; numerical inferential claims in the report must come from the archived data and verified code, not from the summary. |
| Persistence | Davenport et al. (2010), *Political Behavior*, [SSRN record and abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1734799), DOI: [10.1007/s11109-010-9122-0](https://doi.org/10.1007/s11109-010-9122-0) | Across more than one million voters from six experiments, some effects persisted for one and sometimes two years. | Persistence is external supporting evidence. It is not identified by the single 2006 outcome analyzed in this project and must not be presented as our estimate. |
| High-salience replication | Rogers et al. (2017), *Electoral Studies*, [Harvard publication page](https://toddrogers.scholars.harvard.edu/publications/social-pressure-and-voting-field-experiment-conducted-high-salience) | A social-pressure field experiment was conducted in a high-salience election, addressing a key scope condition of the original low-salience primary. | Supports broader relevance, but does not license transport of the Michigan 8.13 pp estimate to other elections, states, eras, or delivery channels. |
| Cross-state generalizability | Gerber et al. (2017), *American Politics Research*, DOI: [10.1177/1532673X16686556](https://doi.org/10.1177/1532673X16686556) | Field experimental evidence covers 1.96 million citizens in 17 states; effects vary with context, including election salience. | External evidence favors a general phenomenon, not a universal constant treatment effect. Report the local estimand and discuss effect heterogeneity across contexts. |
| Interference estimands | Hudgens and Halloran (2008), *JASA*, [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC2600548/), DOI: [10.1198/016214508000000292](https://doi.org/10.1198/016214508000000292) | With interference, direct, indirect, total, and overall effects require explicit potential-outcome and allocation definitions; two-stage/group allocation structures support these contrasts. | Because the Neighbors mailer can reveal other household records, no-interference is substantively doubtful. Do not label the simple assignment contrast a pure direct psychological effect. |
| General interference | Aronow and Samii (2017), *Annals of Applied Statistics*, [Yale publication page](https://isps.yale.edu/resource/estimating-average-causal-effects-under-general-interference-with-application-to-a-social), DOI: [10.1214/16-AOAS1005](https://doi.org/10.1214/16-AOAS1005) | Identification under interference requires the randomization design, an exposure mapping, and an estimand tied to the resulting exposure probabilities. | The observed blocks almost always have the same Neighbors saturation. Without exposure variation and a defensible mapping, spillovers are not identified. No simulated exposure design may substitute for missing real support. |
| Backlash and message intensity | Mann (2010), *Political Behavior*, DOI: [10.1007/s11109-010-9124-y](https://doi.org/10.1007/s11109-010-9124-y); Panagopoulos (2010), *Political Behavior*, DOI: [10.1007/s11109-010-9114-0](https://doi.org/10.1007/s11109-010-9114-0) | Related field experiments study less aggressive social pressure and positive/negative social incentives. | A large turnout gain is not sufficient for a policy recommendation. Intrusiveness, reactance, privacy, autonomy, complaints, and less coercive alternatives are part of the welfare comparison. |

## Verified interpretation

### Claims supported by this project

1. In the study population, assignment of a household to the Neighbors-mailer policy
   increased verified 2006 primary turnout relative to control by about 8.13 percentage
   points, with household-clustered uncertainty and block-stratified randomization
   inference supporting a nonzero effect.
2. The ordered treatment-arm effects are monotone in the observed arm means, and the
   Neighbors arm is substantially larger than the Self arm.
3. The treatment effect differs across observed prior-turnout propensity groups; this
   is a prespecified descriptive effect-modification result, not proof of a latent
   psychological mechanism.
4. The result is stable to adjustment, household aggregation, exact-duplicate removal,
   leave-one-block-out analysis, and reported subgroup re-estimation.

### Claims not supported by this project

1. A pure individual-level direct effect under no interference.
2. A separately identified spillover effect on untreated neighbors.
3. A mediation claim assigning each adjacent arm difference to one psychological channel.
4. Persistence beyond the observed election.
5. An invariant 8.13 pp effect in other states, election types, periods, or digital media.
6. A recommendation to deploy the Neighbors treatment without an explicit privacy,
   autonomy, backlash, administrative, and distributional cost analysis.

## Why the spillover result is deliberately absent

The archived design contains 10,000 assignment blocks. In 9,997 blocks the household
allocation is exactly 10 control households and two households in each of the four
active treatment arms. In 9,998 blocks the Neighbors saturation is exactly 1/9, and
within each observed block size there is no Neighbors-saturation variation. Therefore,
the design does not provide the treatment-density support needed to identify a
spillover dose-response. The correct result is `not identified`, not a weak estimate
and not a simulated substitute.

## Report language rule

Use **household-assignment policy ITT** as the principal estimand. Use **bundled
message-arm contrast** for adjacent treatment comparisons. Reserve **direct effect**,
**indirect effect**, **spillover**, and **mediation** for designs and assumptions that
actually identify those quantities.
