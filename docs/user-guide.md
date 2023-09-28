# User Guide

Back to [README](../README.md)

You can use mf2ff in two ways:
- on the command line using `python -m mf2ff ...` or
- as an importable Python module using `from mf2ff import Mf2ff`.

This tutorial should provide an introduction to both ways. Afterward, useful options are explained which can be used in both. The last section describes extensions to the METAFONT language that are supported by `mf2ff`.


## Run `mf2ff` on the command line
```sh
python -m mf2ff -remove-artifacts path/to/font.mf
```
You need to use `python3` or `ffpython` depending on your operating system and your system configuration.


## Use `mf2ff` from a Python script

```py
from mf2ff import Mf2ff

mf2ff = Mf2ff()
mf2ff.options.remove_artifacts = True
mf2ff.options.input_file = 'path/to/font.mf'
mf2ff.run()
```

Optionally, you can use the `fontforge` Python module to load the font and make automatic changes to this or a different script. This is especially useful if you want to do a large number of similar changes which is not supported by `mf2ff` (yet).\
(Of course, this also works in a separate script and for fonts generated using the command line.) 

Here is an example:

```py
import fontforge
font = fontforge.open('path/to/font.sfd')
glyph = font['A']
% etc.
```

Please refer to [FontForge's documentation](https://fontforge.org/docs/scripting/python.html#trivial-example) for an introduction and a reference to [all supported features](https://fontforge.org/docs/scripting/python/fontforge.html).


## Options

There are different types of options:
- negatable options / boolean options\
  They can be enabled by providing the option `-<option-name>` or setting `mf2ff.options.<option_name> = True` or disabled by providing `-no-<option-name>` or setting `mf2ff.options.<option_name> = False`
- value options\
  These can be given a value of a specific type (e.g. numeric or string) using `-<option-name>=VALUE` or setting `mf2ff.options.<option_name> = VALUE`


### `charcode-from-last-ASCII-hex-arg`

|||
|-|-|
| CLI | `-`[`no-`]`charcode-from-last-ASCII-hex-arg` |
| API | `mf2ff.options.charcode_from_last_ASCII_hex_arg = True` / `False` |
| default | disabled |

This option uses the last hexadecimal string of even length passed as an argument to `ASCII` since the last shipout command as the encoding value during shipout of the current character, ignoring charcode and charext. This is especially useful when using plain METAFONT's `beginchar` macro. 

This option breaks backwards compatibility with METAFONT.

Example:\
`beginchar("20AC", ...); ... endchar;` will create the glyph at `0x20AC` (Euro sign, `€`) if this option is enabled (assuming Unicode input encoding). If this option is disabled, it will create (or overwrite) the glyph at `U+0032` (digit two, `2`) since it's the first character in the string.


### `cull-at-shipout`

|||
|-|-|
| CLI | `-`[`no-`]`cull-at-shipout` |
| API | `mf2ff.options.cull_at_shipout = True` / `False` |
| default | disabled |

This option runs the cull command according to plain METAFONT's cullit macro before every shipout to remove remaining overlap. A similar operation is done by METAFONT during shipout [The METAFONTbook, pp. 220, 295].

Note that cull commands that are part of the definition of a glyph may result in the `cull-at-shipout` option not making any further changes for some glyphs.


### `input-file:`*N* and the `:`*N* syntax

|||
|-|-|
| CLI | `-input-file:`*N*`=path/to/font.mf` |
| API | `mf2ff.options.inputs = [{'input_file': 'path/to/font.mf'}]` |
| default | not used |

This option provides the ability to specify multiple `.mf` files for `mf2ff`. Input files specified with `-input-file:`*N* (where *N* is an integer) will be processed after the (optional) input file specified after the options. To specify different options for different input files, append the option name with `:`*N* where *N* is the integer of the corresponding input file, e.g. `-input-encoding:0=TeX-math-symbols`. If an option is not specified using the `:`*N* syntax, options without `:`*N* are used as a fallback.

The API equivalent is to specify a list of dicts. Each dict contains an `input_file` key and optionally other options, e.g. `mf2ff.options.inputs = [{'input_file': 'path/to/font.mf', 'input_encoding: 'TeX-math-symbols'}]`.


### `kerning-classes`

|||
|-|-|
| CLI | `-`[`no-`]`kerning-classes` |
| API | `mf2ff.options.kerning_classes = True` / `False` |
| default | disabled (kerning pairs are used) |

Enabling this option switches the `gpos` Lookup table `kern` (kerning table) from Format 0 (kerning pairs) to Format 2 (kerning classes).\
For fonts with many kerning pairs, this may be necessary to prevent FontForge from crashing.

**Tip**: You can use the following macro to specify kerning between two groups of glyphs:
```
def group_kerning(text L)(expr k)(expr Rf)(text R) =
  ligtable for l=L:l:endfor Rf kern k for r=R:,r kern k endfor
enddef;

% example usage:
group_kerning("F", "V", "W", "Y")(-4/5pt#)("c", "e", "o", "q");
```
This should expand to a ligtable command which kerns all combinations of the first list and the second list (e.g. "Fc", "Fo", "We", etc.) with the offset defined in the middle. METAFONT will create 16 kerning pairs from this example. If you run `mf2ff` on input with such this example, it will create the classes based on these kerning pairs and builds up a kerning matrix. If there are other ligtable or group_kerning commands, `mf2ff` will split up or combine the classes according to the kerning specifications. 


### `quadratic`

|||
|-|-|
| CLI | `-`[`no-`]`quadratic` |
| API | `mf2ff.options.quadratic = True` / `False` |
| default | enabled |

This option enables or disables the conversion of the contours on foreground layer to quadratic Bézier curves. It uses FontForge's algorithm. In most cases this is only an approximation.


### `remove-artifacts`

|||
|-|-|
| CLI | `-`[`no-`]`remove-artifacts` |
| API | `mf2ff.options.remove_artifacts = True` / `False` |
| default | disabled |

This option removes contours and parts of contours which are closed and collinear and thus don't have an influence on the shape of the glyph. Those artifacts can result from FontForge's "Overlap" commands.


### `set-italic-correction`

|||
|-|-|
| CLI | `-`[`no-`]`set-italic-correction` |
| API | `mf2ff.options.set_italic_correction = True` / `False` |
| default | enabled |

This option enables or disables setting `glyph.italicCorrection` to the value of `charic` during `shipout`.


### `stroke-simplify` & `stroke-accuracy`

|||
|-|-|
| CLI | `-`[`no-`]`stroke-simplify` |
| API | `mf2ff.options.stroke_simplify = True` / `False` |
| default | enabled |

|||
|-|-|
| CLI | `-stroke-accuracy=`*number* |
| API | `mf2ff.options.stroke_accuracy = ` *number* |
| default | 0.25 (FontForge's default) |

FontForge's `layer.stroke()` function provides `simplify` and `accuracy` options. When enabled, `layer.simplify()` is called on the layer. The `error_bound` argument of `layer.simplify()` can be adjusted using `mf2ff`'s `stroke-accuracy` option.

**See also**: FontForge's [documentation](https://fontforge.org/docs/scripting/python/fontforge.html#fontforge.glyph.stroke) of `glyph.stroke()` which explains the available options for FontForge's stroke functions (`font.stroke()`, `glyph.stroke()` and `layer.stroke()`).


### `upm`

|||
|-|-|
| CLI | `-upm=`*number* / `None`  |
| API | `mf2ff.options.upm = ` *number* / `None` |
| default | `None` |

Specifying UPM (units per em or em size) triggers a preliminary run of METAFONT to estimate the correct ppi. Since METAFONT limits numbers to `4095.99998`, anything above that is handled by using a fraction of the ideal ppi. The left over scaling to the desired UPM is either done by FontForge or using an additional factor in METAFONT (see [`use-ppi-factor`](#use-ppi-factor)).


### `use-ppi-factor`

|||
|-|-|
| CLI | `-`[`no-`]`use-ppi-factor`  |
| API | `mf2ff.options.use_ppi_factor = True` / `False` |
| default | disabled |

If the pixels per inch value to reach the desired UPM exceeds METAFONT's infinity, this option will multiply the pixels per inch value by a factor to reach values above METAFONT's infinity. METAFONT tries to cope with this, but it might be dangerous.\
If this feature is not active, FontForge will scale the font to the desired UPM, which may magnify rounding errors.


## Extensions
Since METAFONT was designed to generate generic font files and TeX font metric files, it doesn't provide access to functionalities available in modern font file formats. `mf2ff` supports the following extension to overcome METAFONT's restrictions:


### Attachment points
Attachment points (called anchors in FontForge) are used to precisely place diacritic marks on base characters. `mf2ff` provides a `-extension-attachment-points` / `mf2ff.options.extension_attachment_points = True` option to activate the attachment point extension.

|||
|-|-|
| CLI |`-`[`no-`]`extension-attachment-points` |
| API | `mf2ff.options.extension_attachment_points = True` / `False` |
| default | disabled |

If enabled, the following macros can be used in `mf2ff`'s input:
- `attachment_point_mark_base(...)` to place the attachment point in a base glyph to attach a mark glyph
- `attachment_point_mark_mark(...)` to place the attachment point in a mark glyph to be attached to a base glyph
- `attachment_point_mkmk_basemark(...)` to place the attachment point in a mark glyph to attach another mark glyph
- `attachment_point_mkmk_mark(...)` to place the attachment point in a mark glyph to be attached to another mark glyph

The arguments (`(...)`) should be comma separated list of:
- `attachment_point_class_name`: The name of the attachment point class, e.g. `"Top"`. Corresponding attachment points need to have the same class name in the base glyph and the mark glyph to be linked.
- `x`: The horizontal position of the attachment point.
- `y`: The vertical position of the attachment point.

Example: `attachment_point_mark_base("Top", w/2, h);`

If the name of one of the macros listed above is already used by the .mf file and you don't want to rename this existing variable or macro, you can use the option `-extension-attachment-points-macro-prefix=`*string* / `mf2ff.options.extension_attachment_points_macro_prefix =`*string* to replace `attachment_point` in the macro names.

|||
|-|-|
| CLI |`-extension-attachment-points-macro-prefix=`*string* |
| API | `mf2ff.options.extension_attachment_points_macro_prefix = ` *string* |
| default | `attachment_point` |

Example: add `-extension-attachment-points-macro-prefix=customPrefix` to your options and use `customPrefix_mark_base("Top", w/2, h);`


### Ligtable switch
While the `ligtable` command can be used to define ligatures, it doesn't allow selection of which OpenType feature to use. The ligtable switch commands provide an interface to switch the used OpenType feature for following ligtable commands. Currently, only ligatures (`=:`) are supported.
|||
|-|-|
| CLI |`-`[`no-`]`extension-ligtable-switch` |
| API | `mf2ff.options.extension_ligtable_switch = True` / `False` |
| default | disabled |

If enabled, the following macros can be used in `mf2ff`'s input:
- `ligtable_switch_lig_to_liga` to switch to the `liga` feature for following ligatures in ligtable commands
- `ligtable_switch_lig_to_dlig` to switch to the `dlig` feature for following ligatures in ligtable commands
- `ligtable_switch_lig_to_hlig` to switch to the `hlig` feature for following ligatures in ligtable commands

Similar to the attachment points extension, you can also change the prefix of the ligtable switch macros:

|||
|-|-|
| CLI |`-extension-ligtable-switch-macro-prefix=`*string* |
| API | `mf2ff.options.extension_ligtable_switch_macro_prefix = ` *string* |
| default | `ligtable_switch` |


### General note on extensions
To be able to run the .mf files also in METAFONT without using `mf2ff`, you need to define the tokens of extensions so METAFONT won't throw an error. Since `mf2ff`'s definition of those macros should not be overwritten by a definitions in the .mf file, you can use the following code to only define them when you don't run `mf2ff` (using the attachment point extension as an example):
```
if unknown __mfIIvec__:
  def attachment_point_mark_base(text t) = enddef;
  def attachment_point_mark_mark(text t) = enddef;
  def attachment_point_mkmk_basemark(text t) = enddef;
  def attachment_point_mkmk_mark(text t) = enddef;
fi
```
The boolean variable `__mfIIvec__` is defined by `mf2ff` to determine if `mf2ff` is used.\
If you use the `extension-attachment-points-macro-prefix` option, change the macro name in the code above accordingly.
