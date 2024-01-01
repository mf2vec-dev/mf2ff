import platform
import re
import sys
from collections import namedtuple
from copy import deepcopy
from pathlib import Path


class Mf2ffOptions:
    def __init__(self, mf2ff_version):
        '''Option and command line argument handling for mf2ff

        Args:
            mf2ff_version (str): version of mf2ff to print in version command
        '''

        self.__dict__['_mf2ff_version'] = mf2ff_version

        # set default values
        self.__dict__['_OPTION_DEFS'] = {
            'ascent': {'type': int | None, 'default': None},
            'base': {'type': str, 'default': ''},
            'charcode_from_last_ASCII_hex_arg': {'type': bool, 'default': False},
            'comment': {'type': str, 'default': ''},
            'copyright': {'type': str, 'default': ''},
            'cull_at_shipout': {'type': bool, 'default': False},
            'cwd': {'type': Path, 'default': Path.cwd()},
            'debug': {'type': bool, 'default': False},
            'descent': {'type': int | None, 'default': None},
            'designsize': {'type': float | None, 'default': None},
            'extension_attachment_points_macro_prefix': {'type': str, 'default': 'attachment_point'},
            'extension_attachment_points': {'type': bool, 'default': False},
            'extension_glyph_macro_prefix': {'type': str, 'default': 'glyph'},
            'extension_glyph': {'type': bool, 'default': False},
            'extension_font_macro_prefix': {'type': str, 'default': 'font'},
            'extension_font': {'type': bool, 'default': False},
            'extension_ligature_macro_prefix': {'type': str, 'default': 'ligature'},
            'extension_ligature': {'type': bool, 'default': False},
            'extension_ligtable_switch_macro_prefix': {'type': str, 'default': 'ligtable_switch'},
            'extension_ligtable_switch': {'type': bool, 'default': False},
            'extrema': {'type': bool, 'default': False},
            'family_name': {'type': str, 'default': ''},
            'first_line': {'type': str, 'default': ''},
            'fix_contours': {'type': bool, 'default': False},
            'font_version': {'type': str, 'default': '001.000'},
            'fontlog': {'type': str, 'default': ''},
            'fontname': {'type': str, 'default': ''},
            'fullname': {'type': str, 'default': ''},
            'glyph_name_suffix': {'type': str | None, 'default': None},
            'hint': {'type': bool, 'default': False},
            'ignore_code_points': {'type': list | None, 'default': None},
            'input_encoding': {'type': str | None, 'default': None},
            'input_encoding_options': {'type': dict | None, 'default': None},
            'input_file': {'type': Path | None, 'default': None},
            'is_type': {'type': bool, 'default': False},
            'italicangle': {'type': float, 'default': 0.0},
            'jobname': {'type': str, 'default': ''},
            'kerning_classes': {'type': bool, 'default': False},
            'ligtable_generalized_code': {'type': bool, 'default': False},
            'mf_options': {'type': list, 'default': ['-interaction=batchmode']},
            'only_code_points': {'type': list | None, 'default': None},
            'ot_sub_feature': {'type': str | None, 'default': None},
            'otf': {'type': bool, 'default': False},
            'output_directory': {'type': Path, 'default': Path.cwd()},
            'output_encoding': {'type': str | None, 'default': None},
            'output_encoding_options': {'type': dict | None, 'default': None},
            'ppi': {'type': float, 'default': 1000.0},
            'quadratic': {'type': bool, 'default': False},
            'quiet': {'type': bool, 'default': False},
            'remove_artifacts': {'type': bool, 'default': False},
            'scripts': {'type': tuple, 'default': (
                ('cyrl', ('dflt',)),
                ('grek', ('dflt',)),
                ('latn', ('dflt',))
            )},
            'set_italic_correction': {'type': bool, 'default': True},
            'set_math_defaults': {'type': bool, 'default': True},
            'set_top_accent': {'type': bool, 'default': False},
            'sfd': {'type': bool, 'default': True},
            'skewchar': {'type': int | None, 'default': -1},
            'space_from_fontdimen': {'type': bool, 'default': True},
            'stroke_accuracy': {'type': float | None, 'default': None}, # None: use fontforge's default (should be 0.25)
            'stroke_simplify': {'type': bool, 'default': True},
            'time': {'type': bool, 'default': False},
            'ttf': {'type': bool, 'default': False},
            'upm': {'type': int | None, 'default': None},
            'upos': {'type': float | None, 'default': None},
            'use_ppi_factor': {'type': bool, 'default': False},
            'uwidth': {'type': float | None, 'default': None},
        }
        self.__dict__['_options'] = {}
        for option_name, option_def in self._OPTION_DEFS.items():
            self._options[option_name] = option_def['default']
        self.__dict__['_OPTIONS_NAMEDTUPLE'] = namedtuple('options', list(self._OPTION_DEFS))
        self.__dict__['_inputs'] = []
        self.__dict__['_index'] = None
        self.__dict__['_params'] = {
            'correct_direction': {
                'scale_factor': 10,
            },
            'remove_artefacts': {
                'collinear': {
                    'distance_threshold': 0.01,
                    'point_threshold': 0.1,
                },
            },
            'remove_overlap': {
                'scale_factor': 1000,
            },
        }

    def __getattr__(self, name):
        '''Get the value of an option

        Args:
            name (str): name of the option

        Raises:
            AttributeError: mf2ff doesn't has this option

        Returns:
            Any: value of option
        '''
        if name == 'index':
            return self._index
        elif name == 'inputs':
            return self._inputs
        elif name == 'params':
            return self._params
        try:
            return self._options[name]
        except KeyError as e:
            raise AttributeError(f'mf2ff has no option `{name}\'', name=name, obj=self._OPTIONS_NAMEDTUPLE) from e

    def __setattr__(self, name, value):
        '''Set the value of an option

        Args:
            name (str): name of the option
            value (Any): new value of the option

        Raises:
            AttributeError: mf2ff doesn't has an option
            TypeError: value has wrong type for option
        '''
        if name == 'inputs':
            self.__dict__['_inputs'] = value
            return
        if name == 'index':
            self.__dict__['_index'] = value
            return
        elif name == 'params':
            self.__dict__['_params'] = value
            return
        elif name not in self._options:
            raise AttributeError(f'mf2ff has no option `{name}\'', name=name, obj=self._OPTIONS_NAMEDTUPLE)

        option_type = self._OPTION_DEFS[name]['type']
        if isinstance(value, int) and issubclass(float, option_type):
            value = float(value)
        elif isinstance(value, str) and issubclass(Path, option_type):
            value = Path(value)
        elif not isinstance(value, option_type):
            raise TypeError(f'invalid type `{type(value)}\' for option `{name}\'')

        # validate option with complex requirements
        if name in ['extension_attachment_points_macro_prefix', 'extension_ligtable_switch_macro_prefix']:
            self._validate_mf_alphabetic_token(value, name)
        elif name == 'scripts':
            self._validate_scripts(value)
        elif name == 'mf_options':
            self._validate_list_of_strings(value, name)

        self._options[name] = value

        if name == 'jobname':
            self._options['mf_options'].append('-jobname=' + value)

    def __deepcopy__(self, memo):
        mf2ff_options_deepcopy = Mf2ffOptions(deepcopy(self._mf2ff_version))
        mf2ff_options_deepcopy.__dict__['_options'] = deepcopy(self._options)
        mf2ff_options_deepcopy.__dict__['_inputs'] = deepcopy(self._inputs)
        mf2ff_options_deepcopy.__dict__['_params'] = deepcopy(self._params)
        memo[id(self)] = mf2ff_options_deepcopy
        return mf2ff_options_deepcopy

    def _validate_mf_alphabetic_token(self, value, name=None):
        if not re.match(r'[A-Za-z_]+', value):
            if name is None:
                raise ValueError(f'invalid value `{value}\'.')
            else:
                raise ValueError(f'invalid value `{value}\' for option `{name}\'.')

    def _validate_scripts(self, script_specs):
        if len(script_specs) == 0:
            raise TypeError(
                f'Tuple must not be empty:\n'
                f'script specifications `{script_specs}\'.'
            )
        for i, script_spec in enumerate(script_specs):
            if not isinstance(script_spec, tuple):
                raise TypeError(
                    f'Tuple elements must be tuples:\n'
                    f'script specification {i} (`{script_spec}\') in script specifications `{script_specs}\'.'
                )
            if len(script_spec) != 2:
                raise ValueError(
                    f'Tuple elements must be tuples of length 2 each:\n'
                    f'script specification {i} (`{script_spec}\') in script specifications `{script_specs}\'.'
                )
            if not isinstance(script_spec[0], str):
                raise TypeError(
                    f'First element must be string:\n'
                    f'script `{script_spec[0]}\' of script specification {i} in script specifications `{script_specs}\'.'
                )
            if len(script_spec[0]) > 4:
                raise ValueError(
                    f'First element must be string of up to 4 characters:\n'
                    f'script `{script_spec[0]}\' of script specification {i} in script specifications `{script_specs}\'.'
                )
            if not isinstance(script_spec[1], tuple):
                raise TypeError(
                    f'Second element must be tuple:\n'
                    f'languages `{script_spec[1]}\' of script specification {i} (`{script_spec[0]}\') in script specifications `{script_specs}\'.'
                )
            for j, lang in enumerate(script_spec[1]):
                if not isinstance(lang, str):
                    raise TypeError(
                        f'Second element must be tuple of strings:\n'
                        f'language {j} (`{lang}\') of script specification {i} (`{script_spec[0]}\') in script specifications `{script_specs}\'.'
                    )
                if len(lang) > 4:
                    raise ValueError(
                        f'Second element must be tuple of strings of up to 4 characters each:\n'
                        f'language {j} (`{lang}\') of script specification {i} (`{script_spec[0]}\') in script specifications `{script_specs}\'.'
                    )

    def _validate_list_of_strings(self, value, name=None):
        for i, s in enumerate(value):
            if not (isinstance(s, str)):
                if name is None:
                    error_first_line = f'List elements must be strings:\n'
                else:
                    error_first_line = f'List elements of option `{name}\' must be strings:\n'
                raise TypeError(
                    error_first_line
                    + f'element {i} (`{s}\') in list `{s}\'.'
                )

    def parse_arguments(self, args):
        '''Parse command line arguments and set appropriate properties.

        Args:
            args (list[str]): command line arguments, e.g. sys.argv
        '''

        # Command line arguments consists of two parts:
        # the options starting with a - and other arguments.
        option_args = True # keep track if still parsing options

        # define groups of options
        mf_options = [
            'file-line-error', 'no-file-line-error', 'halt-on-error', 'ini',
            'parse-first-line', 'no-parse-first-line', 'recorder', '8bit'
        ]
        mf_options_values = [
            'interaction', 'kpathsea-debug', 'mktex', 'no-mktex',
            'translate-file'
        ]
        mf2ff_options_negatable = [
            'charcode-from-last-ASCII-hex-arg', 'cull-at-shipout', 'debug',
            'extrema', 'fix-contours','hint', 'is_type', 'kerning-classes',
            'ligtable-generalized-code', 'otf', 'quadratic', 'quiet',
            'remove-artifacts', 'set-italic-correction', 'set-math-defaults',
            'set-top-accent', 'sfd', 'space-from-fontdimen', 'stroke-simplify',
            'time', 'ttf', 'use-ppi-factor'
        ]
        mf2ff_options_values = [
            'ascent', 'comment', 'copyright', 'descent', 'designsize',
            'familyname', 'fontlog', 'fontname', 'font-version', 'fullname',
            'glyph-name-suffix', 'input-encoding', 'input-file', 'italicangle',
            'ot-sub-feature', 'output-directory', 'output-encoding', 'ppi',
            'skewchar', 'stroke-accuracy', 'upm', 'upos', 'uwidth'
        ]
        code_point_range_list_options = [
            'only-code-points', 'ignore-code-points'
        ]
        extension_names = [
            'attachment-points', 'glyph', 'font', 'ligature', 'ligtable-switch'
        ]
        mf2ff_options_negatable.extend('extension-' + e for e in extension_names)

        i = 1 # i == 0 is mf2ff
        while i < len(args):
            full_arg = args[i] # argument with leading -
            if full_arg[0] == '-' and len(full_arg) > 1: # it is an option
                if option_args: # options only before other arguments
                    if full_arg[1] == '-':
                        # treat --option as -option
                        full_arg = full_arg[1:]
                    arg = full_arg[1:]
                    arg_split = arg.split('=', 1)
                    option_name = arg_split[0]
                    if ':' in option_name:
                        option_name, option_index = option_name.split(':', 1)
                        try:
                            option_index = int(option_index)
                        except ValueError:
                            print(f'! Invalid option index `{option_index}\'. Option ignored.')
                    else:
                        option_index = None
                    try:
                        option_value = arg_split[1]
                    except IndexError:
                        if option_name in (
                            mf_options_values
                            + ['jobname', 'base', 'progname', 'stroke-accuracy']
                            + ['extension-' + e + '-macro-prefix' for e in extension_names]
                            + mf2ff_options_values + ['scripts']
                        ):
                            option_value = args[i+1]
                            i += 1
                        else:
                            option_value = None
                    # options and negatable options directly passed to mf.
                    if option_name in mf_options:
                        # since mf_options is an array, it's get by reference
                        self._get_option('mf_options', option_index, []).append(full_arg)
                    elif option_name == 'jobname':
                        self._set_option('jobname', option_value, option_index)
                        # mf_options is appended by self.__setattr__()
                    # name value options passed to mf
                    elif option_name in mf_options_values:
                        if '=' in arg:
                            # since mf_options is an array, it's get by reference
                            self._get_option('mf_options', option_index, []).append(full_arg)
                        else:
                            # since mf_options is an array, it's get by reference
                            self._get_option('mf_options', option_index, []).extend([full_arg, args[i]]) # i was increased already
                    elif option_name in ['base', 'progname']:
                        # progname also sets base name in mf # TODO
                        # TODO also mf_options?
                        self._set_option('base', option_value, option_index)
                    # negatable mf2ff options
                    elif option_name in mf2ff_options_negatable:
                        name = option_name.replace('-', '_')
                        self.__setattr__(name, True)
                    elif option_name[:3] == 'no-' and option_name[3:] in mf2ff_options_negatable:
                        name = option_name.replace('-', '_')[3:]
                        self.__setattr__(name, False)
                    # name value mf2ff option
                    elif (option_name[:10] == 'extension-'
                            and option_name[10:-13] in extension_names
                            and option_name[-13:] == '-macro-prefix'
                        ):
                        name = ('extension_' + option_name[10:-13].replace('-', '_') + '_macro_prefix')
                        self._set_option(name, option_value, option_index)
                    # name value option which don't need to be passed to mf (stored as properties)
                    elif option_name in mf2ff_options_values:
                        val = option_value
                        name = option_name.replace('-', '_')
                        option_type = self._OPTION_DEFS[name]['type']
                        try:
                            if val == 'None' and isinstance(None, option_type):
                                val = None
                            elif issubclass(int, option_type):
                                val = int(val)
                            elif issubclass(float, option_type):
                                val = float(val)
                        except ValueError:
                            raise ValueError(f'invalid value `{val}\' for option `{option_name}\', cannot be converted to `{option_type}\'')
                        self._set_option(name, val, option_index)
                    elif option_name in code_point_range_list_options:
                        name = option_name.replace('-', '_')
                        code_point_range_list = self._str_to_code_point_range_list(option_value)
                        self._set_option(name, code_point_range_list, option_index)
                    elif option_name == 'scripts':
                        scripts = self._tuple_str_to_scripts(option_value)
                        self._set_option('scripts', scripts, option_index)
                    elif option_name == 'version':
                        self._print_version_and_exit()
                    elif option_name == 'help':
                        self._print_help_and_exit()
                    else:
                        # current option doesn't match any of the previous cases
                        print('! Unrecognized option `' + full_arg + '\'. Option ignored.')
                else:
                    # If the argument starts with a - and options prcessing already
                    # finished, don't process any further arguments.
                    break
            else:
                # without - this argument is no option
                option_args = False
                if full_arg[0] == '&': # & introduces the name of the base
                    base = arg # TODO
                elif full_arg[0] == '\\': # line starting with \ should be processed first.
                    self.first_line += arg + ' ' + ' '.join(self.args[i+1:])
                    break
                else: # everything else is a filename
                    self.input_file = full_arg
                    # Open the file and if the first line starts with %&, take this
                    # as the name of the base file and tell mf to skip the first
                    # line.
                    try:
                        with open(self.input_file, 'r+') as f:
                            first_line = f.readline().strip()
                            if first_line[:2] == '%&':
                                base = full_arg[2:] # TODO
                                self.mf_options.append('-no-parse-first-line')
                    except IOError:
                        print('! I can\'t find file: ' + str(self.input_file))
                        sys.exit(1)
                    break
            i += 1 # next argument

    def _set_option(self, option_name, option_value, option_index=None):
        if option_index is None:
            self.__setattr__(option_name, option_value)
        else:
            # ensure _inputs has enough elements. If already enough, following
            # loop is skipped automatically
            for _ in range(len(self._inputs), option_index+1):
                self._inputs.append({})
            self._inputs[option_index][option_name] = option_value

    def _get_option(self, option_name, option_index=None, default=None):
        if option_index is None:
            return self.__getattr__(option_name)
        else:
            # ensure _inputs has enough elements. If already enough, following
            # loop is skipped automatically
            for _ in range(len(self._inputs), option_index+1):
                self._inputs.append({})
            return self._inputs[option_index].get(option_name, default)

    def update(self, new_options):
        '''Update mf2ff options

        Args:
            new_options (dict): dict of option names and new values
        '''
        for option_name, option_value in new_options.items():
            self.__setattr__(option_name.replace('-', '_'), option_value)

    def iterinputs(self):
        '''generator yielding instances of Mf2ffOptions updates with the options of self.inputs

        Yields:
            Mf2ffOptions: instances of Mf2ffOptions corresponding to self and self.inputs
        '''
        if len(self._inputs) == 0:
            yield self
            return
        i = 0
        if self._options['input_file'] is not None:
            options = deepcopy(self)
            options.inputs = []
            options.index = i
            yield options
            i += 1
        for input_options in self._inputs:
            options = deepcopy(self)
            options.inputs = []
            options.index = i
            options.update(input_options)
            yield options
            i += 1

    def _str_to_code_point_range_list(self, s):
        if s == 'None':
            return None
        code_point_list = []
        for code_point_range_str in s.split(','):
            code_point_range = code_point_range_str.split('-')
            for i in range(len(code_point_range)):
                if code_point_range[i][:2].lower() == '0x':
                    code_point_range[i] = int(code_point_range[i], 16)
                else:
                    code_point_range[i] = int(code_point_range[i])
            code_point_list.append(code_point_range)
        return code_point_list

    def _tuple_str_to_scripts(self, s):
        str_pattern = r'((?:\'\w*\'|\"\w*\"))'
        script_tuple_pattern = (
            r'\(\s*' + str_pattern + r'\s*,\s*\(\s*' # ('latn',(
            r'((?:|' # can be empty
            r'' + str_pattern + r'\s*,\s*' # 'dflt',
            + r'|' + str_pattern + r'(?:\s*,\s*' + str_pattern + r')+\s*,?' # 'dflt', 'ENG' # 'dflt', 'ENG', 'FRA'
            r'))'
            r'\s*\)\s*,?\s*\)' # ))
        )
        scripts_tuple_pattern = (
            r'\(\s*'
            r'((?:' # no | here, cannot be empty: Segmentation fault (core dumped)
            + script_tuple_pattern + r'\s*,'
            + r'|' + script_tuple_pattern + r'(?:\s*,\s*' + script_tuple_pattern + r')+\s*,?'
            r'))'
            r'\s*\)'
        )
        scripts_tuple_match = re.match(scripts_tuple_pattern, s)
        if scripts_tuple_match:
            script_tuple_matches = re.finditer(script_tuple_pattern, scripts_tuple_match.group(1))
            scripts = [] # use list to be able to append
            for script_tuple_match in script_tuple_matches:
                script_tuple = (script_tuple_match.group(1)[1:-1], tuple(s.group()[1:-1] for s in re.finditer(str_pattern, script_tuple_match.group(2))))
                scripts.append(script_tuple)
            return tuple(scripts)
        else:
            raise ValueError(f'invalid value `{s}\' for option `scripts\'')

    def _print_version_and_exit(self):
        print('mf2ff ' + self._mf2ff_version)
        print('Copyright (C) 2018--2023')
        sys.exit()

    def _print_help_and_exit(self):
        if platform.system():
            python_name = 'ffpython'
        else:
            python_name = 'python3'
        help_text = (
            'Help on mf2ff\n'
            '=============\n'
            '\n'
            f'Usage: {python_name} mf2ff.py [options] myfont.mf\n'
            'Interactive usage with a prompt for input is not supported.\n'
            '\n'
            'Options:\n'
            '  -ascent=NUM       set font\'s ascent\n'
            '  -[no-]charcode-from-last-ASCII-hex-arg\n'
            '                    disable/enable use of last hex string argument of ASCII primitive for encoding slot\n'
            '                      In plain MF, this enables interpretation of first argument of beginchar as hex encoding value.\n'
            '                      This breaks backwards compatibility with MF.\n'
            '                      If disabled, the ASCII code of the first string character (i.e. first hex digit) is used.\n'
            '  -comment=STR      set font\'s comment\n'
            '  -copyright=STR    set font\'s copyright notice\n'
            '  -[no-]cull-at-shipout\n'
            '                    disable/enable extra culling at shipout.\n'
            '                      MF ships out only positive pixels which is\n'
            '                      equivalent to cullit before shipout. (default: disabled)\n'
            '  -[no-]debug       disable/enable debugging mode of mf2ff\n'
            '  -descent=NUM      set font\'s descent\n'
            '  -designsize=NUM   set font\'s design size\n'
            '  -[no-]extension-attachment-points\n'
            '                    enable/disable attachment point extension (default: disabled)\n'
            '  -extension-attachment-points-macro-prefix=STR\n'
            '                    set macro name prefix (default: \'attachment_point\')\n'
            '                      choose so that in mf files there are none of:\n'
            '                      <macro-prefix>_mark_base, <macro-prefix>_mark_mark, <macro-prefix>_mkmk_basemark, <macro-prefix>_mkmk_mark\n'
            '  -[no-]extension-glyph\n'
            '                    enable/disable glyph extension (default: disabled)\n'
            '  -extension-glyph-macro-prefix=STR\n'
            '                    set macro name prefix (default: \'glyph\')\n'
            '                      choose so that in mf files there are no glyph macros.\n'
            '  -[no-]extension-font\n'
            '                    enable/disable font extension (default: disabled)\n'
            '  -extension-font-macro-prefix=STR\n'
            '                    set macro name prefix (default: \'font\')\n'
            '                      choose so that in mf files there are no font macros.\n'
            '  -[no-]extension-ligature\n'
            '                    enable/disable ligature extension (default: disabled)\n'
            '  -extension-ligature-macro-prefix=STR\n'
            '                    set macro name prefix (default: \'ligature\')\n'
            '                      choose so that in mf files there are no ligature macros.\n'
            '  -[no-]extension-ligtable-switch\n'
            '                    enable/disable ligtable switch extension (default: disabled)\n'
            '  -extension-ligtable-switch-macro-prefix=STR\n'
            '                    set macro name prefix (default: \'ligtable_switch\')\n'
            '                      choose so that in mf files there are no ligtable switch macros.\n'
            '  -[no-]extrema     disable/enable extrema adding (default: disabled)\n'
            '  -familyname=STR   set font\'s family name\n'
            '  -[no-]fix-contours\n'
            '                    disable/enable contour fixing in FontForge (default: disabled)\n'
            '  -fontlog=STR      set font\'s log\n'
            '  -fontname=STR     set font\'s name\n'
            '  -font-version=STR set font\'s version\n'
            '  -fullname=STR     set font\'s full name\n'
            '  -glyph-name-suffix=STR\n'
            '                    set glyph name suffix for all glyphs\n'
            '                      It should start with some kind of a separator, e.g. a period.\n'
            '                      Currently, this only applies if -ot-sub-feature option is enabled.\n'
            '  -help             display this help\n'
            '  -[no-]hint        disable/enable auto hinting and auto instructing (default: disabled)\n'
            '  -ignore-code-points=RANGES\n'
            '                    specify ranges (inclusive) of code points to ignore, other code points are processed\n'
            '                      e.g. 0x00-0x1F,0x7F to ignore ASCII control characters\n'
            '  -input-encoding=STR\n'
            '                    specify encoding of the input file.\n'
            '                      Set None to use Unicode. (default: None)\n'
            '  -[no-]is_type     disable/enable definition of is_pen and is_picture\n'
            '                      as pen and picture, respectively (default: disabled)\n'
            '  -italicangle=NUM  set font\'s italic angle\n'
            '  -[no-]kerning-classes\n'
            '                    disable/enable kerning classes instead of kerning pairs\n'
            '                      (default: disabled = kerning pairs)\n'
            '  -[no-]ligtable-generalized-code\n'
            '                    disable/enable support for hexadecimal, unicode and glyph name values for <code> in ligtable commands\n'
            '                      (default: disabled)\n'
            '  -only-code-points=RANGES\n'
            '                    specify ranges (inclusive) of code points to process, other code points are ignored\n'
            '                      e.g. 0x41-0x5A,0x61-0x7A for latin letters only\n'
            '  -ot-sub-feature=STR\n'
            '                    specify all glyphs as a replacement of a OpenType substitution feature tag (four characters)\n'
            '                      The glyphs will have no Unicode value but a name suffixed with the feature tag (or the glyph-name-suffix).\n'
            '  -[no-]otf         disable/enable OpenType output generation (default: disabled)\n'
            '  -output-directory=DIR\n'
            '                    set existing directory DIR as output directory\n'
            '  -output-encoding=STR\n'
            '                    set encoding of the generated output.\n'
            '                      Set None to use same as input. (default: None)\n'
            '  -ppi=NUM          set pixels per inch (default: 1000.0)\n'
            '  -[no-]quadratic   approximate cubic with quadratic Bézier curves\n'
            '  -[no-]remove-artifacts\n'
            '                    disable/enable removing of artifacts (default: disabled)\n'
            '  -scripts=TUPLE    set scripts for tables,\n'
            '                      e.g. ((\'latn\',(\'dflt\',)),)\n'
            '  -[no-]set-italic-correction\n'
            '                    disable/enable setting italic correction based on charic (default: enabled)\n'
            '  -[no-]set-math-defaults\n'
            '                    disable/enable setting OpenType math table constants based on fontdimens and TeX rules (default: enabled)\n'
            '  -[no-]set-top-accent\n'
            '                    set the top accent position based on skewchar kerning\n'
            '  -[no-]sfd         disable/enable Spline Font Database (FontForge\n'
            '                      Project) output generation (default: enabled)\n'
            '  -skewchar=NUM     set the skewchar as an integer (decimal) to use if set-top-accent is enabled\n'
            '                      A value of None treats all glyphs the same and keeps the kerning as defined.\n'
            '                      A value of -1 will use 127 for TeX-math-italic, 48 for TeX-math-symbols and None otherwise.\n'
            '                      (default: -1)\n'
            '  -[no-]space-from-fontdimen\n'
            '                    disable/enable creating an empty space glyph at U+0020 from fontdimen 2.\n'
            '                      If input encoding has no code point for space, a new one is created.\n'
            '  -stroke-accuracy=NUM\n'
            '                    set stroke accuracy, i.e. target for the allowed error in em-units\n'
            '                      for layer.simplify() during layer.stoke(). Has no effect if\n'
            '                      stroke-simplify is disabled. (default: 0.25)\n'
            '  -[no-]stroke-simplify\n'
            '                    disable/enable stroke simplification (default: enabled)\n'
            '  -[no-]time        disable/enable timing (default: disabled)\n'
            '  -[no-]ttf         disable/enable TrueType output generation (default: disabled)\n'
            '  -upm=NUM          desired UPM (units per em) or em size. If \'None`, UPM depends on ppi. (default: \'None`)\n'
            '  -upos=NUM         set the font\'s underline position in font units\n'
            '  -[no-]use-ppi-factor\n'
            '                      use a factor for the pixels per inch to reach target upm (default: disabled)\n'
            '                      Note: This can result in values greater than MF\'s infinity.\n'
            '                            MF tries to cope with it, but it might be dangerous.\n'
            '  -uwidth=NUM       set the font\'s underline width in font units\n'
            '  -version          output version information of mf2ff and exit\n'
            '\n'
            'All options that affect the processing of .mf files can be suffixed with `:N\',\n'
            'where N is an integer, to process multiple .mf files and combine the results\n'
            'into a single font, e.g -input_file:0=font0.mf\n'
            '-input_encoding:0=TeX-math-italic -input_file:1=font1.mf\n'
            '-input_encoding:1=TeX-math-symbols [...]\n'
            '\n'
            'The following options are also available and are passed to METAFONT:\n'
            '  -[no-]file-line-error\n'
            '  -halt-on-error\n'
            '  -ini\n'
            '  -[no-]parse-first-line\n'
            '  -recorder\n'
            '  -8bit\n'
            'METAFONT\'s -version option is not available here because it only outputs text\n'
            'to the terminal.\n'
            '\n'
            'Please see METAFONT\'s help (run `mf -help\') to get more information about\n'
            'its options and for alternative usage patterns. Some of the METAFONT options\n'
            'may have no effect in mf2ff.\n'
            '\n'
            '\n'
            'It won\'t work!\n'
            '===============\n'
            '\n'
            'The problem may be a unloadable fontforge module.\n'
            'Try the following:\n'
            '- Please make sure fontforge and mf are installed.\n'
            '- On Windows, please run fontforge-console.bat once and make sure to use\n'
            '  ffpython.\n'
            '\n'
            '\n'
            'Copyright and license information\n'
            '=================================\n'
            '\n'
            '  MIT License\n'
            '  Copyright (C) 2018--2023\n'
            '\n'
            'For more information, please see LICENSE.txt.\n'
        )
        print(help_text)
        sys.exit()
