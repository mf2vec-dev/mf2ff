# User Guide

Back to [README](../README.md)

You can use mf2ff in two ways:
- on the command line using `python -m mf2ff ...` or
- as an importable Python module using `from mf2ff import Mf2ff`.

This tutorial should provide an introduction to both ways. Afterward, useful options are explained which can be used in both. The last section describes extensions to the METAFONT language that are supported by `mf2ff`.

- [User Guide](#user-guide)
  - [Run `mf2ff` on the command line](#run-mf2ff-on-the-command-line)
  - [Use `mf2ff` from a Python script](#use-mf2ff-from-a-python-script)
  - [Unicode support](#unicode-support)
  - [Specifying code point, Unicode value and glyph name](#specifying-code-point-unicode-value-and-glyph-name)
  - [Options](#options)
    - [`charcode-from-last-ASCII-hex-arg`](#charcode-from-last-ascii-hex-arg)
    - [`cull-at-shipout`](#cull-at-shipout)
    - [`input-encoding`](#input-encoding)
    - [`input-file:`*N* and the `:`*N* syntax](#input-filen-and-the-n-syntax)
    - [`kerning-classes`](#kerning-classes)
    - [`quadratic`](#quadratic)
    - [`remove-artifacts`](#remove-artifacts)
    - [`set-italic-correction`](#set-italic-correction)
    - [`set-math-defaults`](#set-math-defaults)
    - [`set-top-accent` \& `skewchar`](#set-top-accent--skewchar)
    - [`stroke-simplify` \& `stroke-accuracy`](#stroke-simplify--stroke-accuracy)
    - [`upm`](#upm)
    - [`use-ppi-factor`](#use-ppi-factor)
  - [Extensions](#extensions)
    - [Attachment points](#attachment-points)
    - [Glyph extension](#glyph-extension)
    - [Font extension](#font-extension)
    - [Ligtable switch](#ligtable-switch)
    - [General note on extensions](#general-note-on-extensions)


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


## Unicode support

> `mf2ff` supports two different basic alternatives to create fonts that exceed METAFONT's character limit:
> - combination of multiple independent `.mf` inputs into one font,
> - processing of `.mf` input that exceeds METAFONT's character limit.

The difficulty of designing a Unicode with METAFONT is not the definition of non-ASCII characters. The Computer Modern fonts define greek letters, mathematical operators, etc. without any problem, just using a non-ASCII encoding. The main problem is the number of characters will most likely exceed METAFONT's limit of 256 character per font. Computer Modern deals with this by using multiple fonts that are to be used alongside each other (e.g. `cmmi10`, `cmsy10`, `cmex10`).

Because using multiple fonts and having to switch between them is not practical for today's font applications, the characters from multiple `.mf` inputs need to be combined in a single font. `mf2ff` supports this with the [`:`*N* command line option syntax described below](#input-filen-and-the-n-syntax) and with the `inputs` option in the API shown in the `cm_math_10` example. The following aspects need to be considered when working with this approach:
- Code point definition:\
  Either [input encodings](#input-encoding) must be available for each input or the [`glyph_unicode`](#glyph-extension) macro from the [glyph extension](#glyph-extension) needs to be used [deactivating it for the use without `mf2ff`](#general-note-on-extensions).
- Kerning and ligatures:\
  Either combine certain glyphs that should be kerned or used in a ligature definition in one input or deactivating ligature definitions and kerning pairs that work across multiple input for the use without `mf2ff` using an approach [similar to the commands of extensions](#general-note-on-extensions).

`mf2ff` also supports the processing of inputs with more characters than METAFONT's limit. This is possible since from METAFONT's perspective only many contours are compute. They are never drawn to pictures and no picture is shipped out. In accordance with the mf2vec concept, everything is just written to the log file. This approach has one major downside:
- `.mf` input that exceeds METAFONT's character limit produces different output in METAFONT (glyph metrics or glyphs are overwritten). This is no problem for `mf2ff` but for debugging the `.mf` input with METAFONT some glyph definitions / `shipout`s and maybe other commands like `ligtable`, `charlist` and `extensible` need to be commented out or deactivated using an approach [similar to the commands of extensions](#general-note-on-extensions).


## Specifying code point, Unicode value and glyph name

> `mf2ff` supports the following ways to specify the glyph that is created:
> - `beginchar("A", ...);`, `beginchar(65, ...);`, `beginchar(oct"101", ...);`, `beginchar(hex"41", ...);`, ... (the usual way)
> - `beginchar(...);` and `charext` (the usual way with `charext`)
> - `beginchar("0041", ...);` or `beginchar("U+0041", ...);`
> - `beginchar("", ...);` or `beginchar(-1, ...);` and `glyph_unicode` (and optionally `glyph_name`)
> - `beginchar("", ...);` or `beginchar(-1, ...);` and `glyph_name`
> 
> Only the first two are compatible to METAFONT without `mf2ff`.

`mf2ff` provides the following ways to set the code point, Unicode value and glyph name. The relevant definition of variables or use of macros are the last between two shipout (between `beginchar` and `endchar`).
- Only define `charcode`:\
  In plain METAFONT this is equivalent to specifying the first argument of `beginchar` as usual.\
  The value of `charcode` determines the code point in the input encoding.\
  The value of `charcode` should not exceed 4095.99998 and can not exceed 32767.99998.\
  This is compatible to METAFONT as long as $0\le{}$`charext`${}\le255$.
- Only define `charcode` and `charext`:\
  In plain METAFONT this is equivalent to specifying the first argument of `beginchar` as usual and defining `charext`.\
  The value `charcode + charext*256` determines the code point in the input encoding.\
  The values of `charcode` and `charext` should not exceed 4095.99998 and can not exceed 32767.99998.\
  This is compatible to METAFONT as long as $0 \le{}$`charext`${}\le 255$ and the restrictions of METAFONT are kept in mind for glyphs with same `charcode` but different `charext`.
- Passing a hexadecimal string to `ASCII`:\
  In plain METAFONT this is equivalent to specifying the first argument of `beginchar` as a hexadecimal string.\
  The option `charcode-from-last-ASCII-hex-arg` needs to be active.\
  The value of the hexadecimal string passed to `ASCII` determines either the unicode value if the string starts with `U+`, or the code point in the input encoding otherwise.\
  This is *not* compatible to METAFONT, `ASCII` evaluates to the ASCII value of the first character in the argument.
- Define `charcode` as `-1` and `glyph_unicode` (optionally define `glyph_name`):\
  In plain METAFONT this is equivalent to specifying the first argument of `beginchar` as `-1` or an empty string (`""`) and defining `glyph_unicode`.\
  The value of `glyph_unicode` determines the unicode value.\
  This is *not* compatible to METAFONT, METAFONT will use the code point 255 for those glyphs.\
  `glyph_unicode` must be defined as explained [below](#general-note-on-extensions) to work with METAFONT.
  If `glyph_name` is used, the default name of the glyph is overwritten. `glyph_name` must be defined as explained [below](#general-note-on-extensions) to work with METAFONT.
- Define `charcode` as `-1` and `glyph_name`:\
  In plain METAFONT this is equivalent to specifying the first argument of `beginchar` as `-1` or an empty string (`""`) and defining `glyph_name`.\
  The option `extension-glyph` needs to be active.\
  A glyph without a Unicode value is created and given the name defined by `glyph_name`.\
  This is useful for creating characters for the `glyph_replacement_of` or `glyph_replaced_by` macros from the [glyph extension](#glyph-extension).\
  This is *not* compatible to METAFONT, METAFONT will use the code point 255 for those glyphs.\
  `glyph_name` must be defined as explained [below](#general-note-on-extensions) to work with METAFONT.

Other combinations of `charcode`, `charext`, `glyph_unicode` and `glyph_name` are not implemented or not tested and may have unexpected behavior.


## Options

There are different types of options:
- negatable options / boolean options\
  They can be enabled by providing the option `-<option-name>` or setting `mf2ff.options.<option_name> = True` or disabled by providing `-no-<option-name>` or setting `mf2ff.options.<option_name> = False`
- value options\
  These can be given a value of a specific type (e.g. numeric, string, file path or directory) using `-<option-name>=VALUE` or setting `mf2ff.options.<option_name> = VALUE`


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


### `input-encoding`

|||
|-|-|
| CLI | `-input-encoding=`*encoding* |
| API | `mf2ff.options.input_encoding = ` *encoding* |
| default | `UnicodeFull` |

This option specifies the input encoding. Besides FontForge's default encodings, the following encodings are supported:
- `TeX-text`
- `TeX-typewriter-text`
- `TeX-math-italic`
- `TeX-math-symbols`
- `TeX-math-extension`
- `TeX-extended-ASCII`


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


### `set-math-defaults`

|||
|-|-|
| CLI | `-`[`no-`]`set-math-defaults` |
| API | `mf2ff.options.set_math_defaults = True` / `False` |
| default | disabled |

This option enables using the `fontdimen` values to set the OpenType `math` table constants to default TeX equivalent values. An overview of the OpenType `math` constants and the default values that are used when the `set-math-defaults` option is enabled can be found [here](math.md).


### `set-top-accent` & `skewchar`

|||
|-|-|
| CLI | `-`[`no-`]`set-top-accent` |
| API | `mf2ff.options.set_top_accent = True` / `False` |
| default | disabled |

This option enables defining the OpenType math top accent attachment point horizontal position for all glyphs based on the width and the italic correction of the glyph. Kerning with the skewchar is used (if the input contains it) and removed from final kerning tables. The skewchar can be defined with the `skewchar` option.

|||
|-|-|
| CLI | `-`[`no-`]`skewchar=`*number* / `None` |
| API | `mf2ff.options.skewchar = ` *number* / `None` |
| default | `-1` |

If `skewchar` is set to a non-negative number, the kerning pairs with that code point are used to adjust the top accent value. A value of `None` will cause top accent to only use width and italic correction for all glyphs. `skewchar` option with value `-1` (default) use `127` as the skewchar if the input encoding is TeX math italic, `48` if it is TeX math symbols and `None` otherwise.


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
| CLI | `-upm=`*number* / `None` |
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


### Glyph extension
The glyph extension provides several macros to control the code point, glyph references, hinting and OpenType single substitutions.

|||
|-|-|
| CLI |`-`[`no-`]`extension-glyph` |
| API | `mf2ff.options.extension_glyph = True` / `False` |
| default | disabled |

The following macros are available when this extension is active:
- `glyph_name(g_name);` to specify the name of a glyph as a string, e.g. `"a.sc"`.
- `glyph_unicode(g_unicode);` to specify the unicode value of a glyph as an integer or a hexadecimal string.
- `glyph_comment(g_comment);` to define a comment for the glyph as a string.
- `glyph_top_accent(g_top_accent);` to define the glyph's math top accent attachment point horizontal position as a number.
- `glyph_build;` to build the glyph from references to other glyphs, e.g. ligatures, composite glyphs or accented glyphs.
- `glyph_add_reference(g_name, g_transform)` to add a reference to another character, e.g. add a base glyph and a diacritic mark with custom positioning (e.g. `g_transform = identity shifted (w/2, 0);` with plain METAFONT).
- `glyph_add_extrema;` to automatically add extremes to the glyph's contours. This is recommended for automatic hinting (see below).
- `glyph_add_inflections;` to automatically add inflection points to the glyph's contours.
- `glyph_auto_hint;` to automatically add PostScript hints to the glyph.
- `glyph_auto_instruct;` to automatically add TrueType instructions to the glyph.
- `glyph_add_horizontal_hint(y_start, y_end);` to add a custom PostScript horizontal (stem) hint to the glyph.
- `glyph_add_vertical_hint(x_start, x_end);` to add a custom PostScript vertical (stem) hint to the glyph.
- `glyph_add_diagonal_hint(p, q, d);` to add a custom diagonal (stem) hint to the glyph as three pairs representing two points `p`, `q` and a direction `d`, e.g. to improve automatic TrueType instructions.\
  The direction `d` can be omitted. In this case `d` is computed from `p` and `q`.
- `glyph_add_math_kerning_top_right(x, y);`, `glyph_add_math_kerning_top_left(x, y);`, `glyph_add_math_kerning_bottom_right(x, y);` or `glyph_add_math_kerning_bottom_left(x, y);` to add math kerning points to the glyph.
- `glyph_replaced_by(g_name, opentype_feature);` to associate the specified glyph as a replacement glyph with an OpenType single substitution feature to the current glyph.
- `glyph_replacement_of(g_name, opentype_feature);` to associate the current glyph as a replacement glyph with an OpenType single substitution feature to the specified glyph.

Similar to the other extensions, the prefix of the glyph extension macros can be changed:

|||
|-|-|
| CLI |`-extension-glyph-macro-prefix=`*string* |
| API | `mf2ff.options.extension_glyph_macro_prefix = ` *string* |
| default | `glyph` |


### Font extension
The font extension provides several macros to control the font name, metrics, OpenType `math` table constants, PostScript private directory, etc.

|||
|-|-|
| CLI |`-`[`no-`]`extension-font` |
| API | `mf2ff.options.extension_font = True` / `False` |
| default | disabled |

The following macros are available when this extension is active:
- `font_name(f_name);` to specify the font's name as a string.
- `font_family_name(f_family_name);` to specify the font's family name as a string.
- `font_full_name(f_full_name);` to specify the font's full, human readable name as a string.
- `font_weight(f_weight);` to specify the font's weight as a string.
- `font_version(f_version);` to specify the font's version as a string.
- `font_copyright(f_copyright);` to define a copyright notice for the font as a string.
- `font_comment(f_comment);` to define a comment for the font as a string.
- `font_fontlog(f_fontlog);` to define a fontlog for the font as a string.
- `font_ascent(f_ascent);` to define the font's ascent as a number, e.g. `font_ascent(8pt#);`.
- `font_descent(f_descent);` to define the font's descent as a number, e.g. `font_ascent(2pt#);`.
- `font_cap_height(f_cap_height);` to define the OS/2 cap-height of the font as a number.
- `font_underline_position(f_underline_position);` to define the position of the font's underline as a number.
- `font_underline_width(f_underline_width);` to define the width of the font's underline as a number.
- `font_add_extrema;` to automatically add extremes to the contours of all glyph. This is recommended for automatic hinting (see below).
- `font_add_inflections;` to automatically add inflection points to the contours of all glyphs.
- `font_auto_hint;` to automatically add PostScript hints to all glyph.
- `font_auto_instruct;` to automatically add TrueType instructions to all glyph.
- `font_math_constant(name, value)` to define an OpenType `math` table constant, name as a string, value as a number. An overview of the OpenType `math` constants and the default values that are used when the `set-math-defaults` option is enabled can be found [here](math.md).
- `font_postscript_private_dictionary(name, value)` to define an entry in the PostScript private directory, name as string, value depending on entry (arrays as a sting in PostScript format).

Similar to the other extensions, the prefix of the glyph extension macros can be changed:

|||
|-|-|
| CLI |`-extension-font-macro-prefix=`*string* |
| API | `mf2ff.options.extension_font_macro_prefix = ` *string* |
| default | `font` |


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

Similar to the other extensions, the prefix of the ligtable switch macros can be changed:

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
