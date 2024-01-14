# OpenType `math`

Back to [README](../README.md)\
Back to [User Guide](user-guide.md)

The following table and the implemented use of the TeX/METAFONT `fontdimen`s to set the OpenType parameters are based on Ulrik Vieth's overview [1].

$\sigma_i$ represents TeX's `\fontdimen`$i$ and METAFONT's `fontdimen` $i$ of the symbol font (family 2) of the current style.\
$\xi_i$ represents TeX's `\fontdimen`$i$ and METAFONT's `fontdimen` $i$ of the extension font (family 3) of the current style.

| OpenType paramter                          | Value                                                                                   | Type  | Source                                 |
| ------------------------------------------ | --------------------------------------------------------------------------------------- | ----- | -------------------------------------- |
| `UpperLimitBaselineRiseMin`                | $\xi_{11}$                                                                              | `C`   | [1, Tab. 1]                            |
| `UpperLimitGapMin`                         | $\xi_9$                                                                                 | `C`   | [1, Tab. 1]                            |
| `LowerLimitGapMin`                         | $\xi_{10}$                                                                              | `C`   | [1, Tab. 1]                            |
| `LowerLimitBaselineDropMin`                | $\xi_{12}$                                                                              | `C`   | [1, Tab. 1]                            |
| (no correspondence)                        | $\xi_{13}$                                                                              | `No`  | [1, Tab. 1]                            |
| `StretchStackTopShiftUp`                   | $\xi_{11}$                                                                              | `C`   | [1, Tab. 2]                            |
| `StretchStackGapAboveMin`                  | $\xi_9$                                                                                 | `C`   | [1, Tab. 2]                            |
| `StretchStackGapBelowMin`                  | $\xi_{10}$                                                                              | `C`   | [1, Tab. 2]                            |
| `StretchStackBottomShiftDown`              | $\xi_{12}$                                                                              | `C`   | [1, Tab. 2]                            |
| `OverbarExtraAscender`                     | $\xi_8$                                                                                 | `T`   | [1, Tab. 3]                            |
| `OverbarRuleThickness`                     | $\xi_8$                                                                                 | `T`   | [1, Tab. 3]                            |
| `OverbarVerticalGap`                       | $3\xi_8$                                                                                | `T`   | [1, Tab. 3]                            |
| `UnderbarVerticalGap`                      | $3\xi_8$                                                                                | `T`   | [1, Tab. 3]                            |
| `UnderbarRuleThickness`                    | $\xi_8$                                                                                 | `T`   | [1, Tab. 3]                            |
| `UnderbarExtraDescender`                   | $\xi_8$                                                                                 | `T`   | [1, Tab. 3]                            |
| `FractionNumeratorDisplayStyleShiftUp`     | $\sigma_8$                                                                              | `C`   | [1, Tab. 4]                            |
| `FractionNumeratorShiftUp`                 | $\sigma_9$                                                                              | `C`   | [1, Tab. 4]                            |
| `FractionNumeratorDisplayStyleGapMin`      | $3\xi_8$                                                                                | `T`   | [1, Tab. 4]                            |
| `FractionNumeratorGapMin`                  | $\xi_8$                                                                                 | `T`   | [1, Tab. 4]                            |
| `FractionRuleThickness`                    | $\xi_8$                                                                                 | `T`   | [1, Tab. 4]                            |
| `FractionDenominatorDisplayStyleGapMin`    | $3\xi_8$                                                                                | `T`   | [1, Tab. 4]                            |
| `FractionDenominatorGapMin`                | $\xi_8$                                                                                 | `T`   | [1, Tab. 4]                            |
| `FractionDenominatorDisplayStyleShiftDown` | $\sigma_{11}$                                                                           | `C`   | [1, Tab. 4]                            |
| `FractionDenominatorShiftDown`             | $\sigma_{12}$                                                                           | `C`   | [1, Tab. 4]                            |
| `StackTopDisplayStyleShiftUp`              | $\sigma_8$                                                                              | `C`   | [1, Tab. 4]                            |
| `StackTopShiftUp`                          | $\sigma_{10}$                                                                           | `C`   | [1, Tab. 4]                            |
| `StackDisplayStyleGapMin`                  | $7\xi_8$                                                                                | `T`   | [1, Tab. 4]                            |
| `StackGapMin`                              | $3\xi_8$                                                                                | `T`   | [1, Tab. 4]                            |
| `StackBottomDisplayStyleShiftDown`         | $\sigma_{11}$                                                                           | `C`   | [1, Tab. 4]                            |
| `StackBottomShiftDown`                     | $\sigma_{12}$                                                                           | `C`   | [1, Tab. 4]                            |
| `SuperscriptShiftUp`                       | $\sigma_{13}$, ($\sigma_{14}$)                                                          | `Cst` | [1, Tab. 5]                            |
| `SuperscriptShiftUpCramped`                | $\sigma_{15}$                                                                           | `C`   | [1, Tab. 5]                            |
| `SubscriptShiftDown`                       | $\sigma_{16}$, ($\sigma_{17}$)                                                          | `Csp` | [1, Tab. 5]                            |
| `SuperscriptBaselineDropMax`               | $\sigma_{18}$                                                                           | `C`   | [1, Tab. 5]                            |
| `SubscriptBaselineDropMin`                 | $\sigma_{19}$                                                                           | `C`   | [1, Tab. 5]                            |
| `SuperscriptBottomMin`                     | $\frac14\sigma_5$                                                                       | `T`   | [1, Tab. 5]                            |
| `SubscriptTopMax`                          | $\frac45\sigma_5$                                                                       | `T`   | [1, Tab. 5]                            |
| `SubSuperscriptGapMin`                     | $4\xi_8$                                                                                | `T`   | [1, Tab. 5]                            |
| `SuperscriptBottomMaxWithSubscript`        | $\frac45\sigma_5$                                                                       | `T`   | [1, Tab. 5]                            |
| `SpaceAfterScript`                         | $0.05\thinspace\mathrm{em}$ (`\scriptspace` $=0.5\thinspace\mathrm{pt}$)                | `M`   | [1, Tab. 5]<sup>1</sup>, [2, p. 344]   |
| `RadicalExtraAscender`                     | $\xi_8$                                                                                 | `T`   | [1, Tab. 6]                            |
| `RadicalRuleThickness`                     | $\xi_8$                                                                                 | `T`   | [1, Tab. 6]                            |
| `RadicalDisplayStyleVerticalGap`           | $\xi_8+\frac14\sigma_5$                                                                 | `T`   | [1, Tab. 6]                            |
| `RadicalVerticalGap`                       | $\xi_8+\frac14\xi_8$                                                                    | `T`   | [1, Tab. 6]                            |
| `RadicalKernBeforeDegree`                  | $\frac5{18}\thinspace\mathrm{em}$                                                       | `M`   | [1, Tab. 6]                            |
| `RadicalKernAfterDegree`                   | $\frac{10}{18}\thinspace\mathrm{em}$                                                    | `M`   | [1, Tab. 6]                            |
| `RadicalDegreeBottomRaisePercent`          | $60\thinspace$%                                                                         | `M`   | [1, Tab. 6]                            |
| `ScriptPercentScaleDown`                   | $70\thinspace$% (e.g. $70\thinspace$% – $80\thinspace$%)                                | `M`   | [1, Tab. 7]                            |
| `ScriptScriptPercentScaleDown`             | $50\thinspace$% (e.g. $50\thinspace$% – $60\thinspace$%)                                | `M`   | [1, Tab. 7]                            |
| `DisplayOperatorMinHeight`                 | $1.4\thinspace\mathrm{em}$ (e.g. $12\thinspace\mathrm{pt}$ – $15\thinspace\mathrm{pt}$) | `Nt`  | –<sup>2</sup>, [1, Tab. 7]             |
| (no correspondence)                        | $\sigma_{20}$ (e.g. $20\thinspace\mathrm{pt}$ – $24\thinspace\mathrm{pt}$)              | `No`  | [1, Tab. 7]                            |
| `DelimitedSubFormulaMinHeight`             | $\sigma_{21}$ (e.g. $10\thinspace\mathrm{pt}$ – $12\thinspace\mathrm{pt}$)              | `C?`  | [1, Tab. 7]                            |
| `AxisHeight`                               | $\sigma_{22}$ (axis height)                                                             | `C`   | [1, Tab. 7]                            |
| `AccentBaseHeight`                         | $\sigma_5$ (x-height)                                                                   | `C`   | [1, Tab. 7]                            |
| `FlattenedAccentBaseHeight`                | cap-height (ascent)                                                                     | `Nt?` | –<sup>3</sup>, [1, Tab. 7]             |
| `MathLeading`                              | $\frac3{18}\thinspace\mathrm{em}$                                                       | `Nt?` | –<sup>4</sup>, [1, Tab. 7]<sup>5</sup> |
| `MinConnectorOverlap`                      | $0\thinspace\mathrm{pt}$                                                                | `Nt?` | –<sup>6</sup>, [1, Tab. 7]<sup>5</sup> |

<sup>1</sup> `SpaceAfterScript` was removed in reprint [3].\
<sup>2</sup> Approximate size of display style operators in Computer Modern.\
<sup>3</sup> cap-height analogous to AccentBaseHeight (x-height).\
<sup>4</sup> Guess.\
<sup>5</sup> `MathLeading` and `MinConnectorOverlap` were removed in reprints [3] and [4].\
<sup>6</sup> No repeater overlap in TeX.

## Types:
`C`: corresponding paramter\
`N`: no correspondence (`No`: no correspondence in OpenType, `Nt`: no correspondence in TeX)\
`T`: TeX rule\
`M`: defined on macro level (`plain.tex` or `latex.ltx`)\
`st`: depends on the style\
`sp`: depends on with or without superscript\
`?`: to be checked

## References
[1] Ulrik Vieth: OpenType Math Illuminated. Proceedings of BachoTeX 2009, pp. 7-16, Bachotek, Poland. https://www.gust.org.pl/bachotex/2009/conference-materials/b2009inside.pdf#page=7 \
[2] Donald E. Knuth: The TeXbook. Addison-Wesley Professional, 1986. ISBN: 978-0201134476 \
[3] Ulrik Vieth: OpenType Math Illuminated. TUGboat, 30:1, pp. 22–31, 2009. http://www.tug.org/TUGboat/tb30-1/tb94vieth.pdf \
[4] Ulrik Vieth: OpenType Math Illuminated. MAPS, 38, pp. 12-21, 2009. https://www.ntg.nl/maps/38/03.pdf
