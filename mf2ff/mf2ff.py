import os
import platform
import re
import subprocess
import sys
import unicodedata
from copy import deepcopy
from functools import reduce
from itertools import combinations, permutations
from math import atan, atan2, cos, pi, sin, sqrt
from pathlib import Path
from time import time

import tex_encodings
from mf2ff_options import Mf2ffOptions

try:
    import fontforge
    import psMat
except ImportError:
    if platform.system() == 'Windows':
        print('! No module named \'fontforge\'. Check that fontforge is installed and that you are using ffpython (you may need to add it to your PATH).')
        sys.exit(1)
    else:
        print('! No module named \'fontforge\'. Check that fontforge is installed and that the module can be found in PYTHONPATH.')
        sys.exit(1)

__version__ = '0.3.0'

class Mf2ff:
    '''The main class of mf2ff

    Usage example:
        from mf2ff import Mf2ff
        mf2ff = Mf2ff()
        mf2ff.options.input_file = 'path/to/myfont.mf'
        mf2ff.run() # generates path/to/myfont.sfd
    '''

    # "[...] a complex pen is one whose boundary contains at least two points." (The METAFONTbook, p. 119)
    SIMPLE_PENS = ('(0,0) .. cycle', '(0,0)..controls (0,0) and (0,0) ..cycle')

    MF_INFINITY = 4095.99998
    MF_OVERFLOW = 32767.99998

    def __init__(self):
        self.MARKER = '@mf2vec@'

        self.last_known_line = 0

        self.options = Mf2ffOptions(__version__)

        # first of every dict element is default
        self.supported_ligtable_ot_features = {
            'lig': ['liga', 'dlig', 'hlig']
        }

        # On Windows, ANSI Control Sequence are not available by default. They
        # can be activated by running the color command.
        if platform.system() == 'Windows':
            os.system('color')


    def run(self, return_font=False):
        '''run mf2ff

        Call this method after all options are set.

        Args:
            return_font (bool, optional): Return the generated font. Defaults
              to False (don't return the font). If the font is not returned, it
              is closed to free memory.

        Returns:
            fontforge.font or None: the generated font (if return_font is True)
        '''

        M = self.MARKER

        if not self.options.input_file and not self.options.inputs and not self.options.first_line:
            print('! No input')
            sys.exit(1)

        self.font_add_extrema = False
        self.font_add_inflections = False
        self.font_round = False
        self.font_auto_hint = False
        self.font_auto_instruct = False

        if self.options.set_math_defaults:
            self.fontdimens = {
                'family2': [None]*(1+22), # sigma_5, ..., sigma_22
                'family3': [None]*(1+13) # xia_8, ..., xi_13
            }
            self.specified_math_constants = []

        if not self.options.fontname:
            self.options.fontname = self.options.jobname
        if not self.options.family_name:
            self.options.family_name = self.options.fontname
        if not self.options.fullname:
            self.options.fullname = self.options.fontname

        # set up font object to be filled with
        self.font = fontforge.font()
        if self.options.ascent is None:
            self.font.ascent = 0
        else:
            self.font.ascent = self.options.ascent
        self.font.comment = self.options.comment
        self.font.copyright = self.options.copyright
        if self.options.descent is None:
            self.font.descent = 0
        else:
            self.font.descent = self.options.descent
        if self.options.designsize is not None:
            self.font.design_size = self.options.designsize
        self.font.familyname = self.options.family_name
        self.font.fontlog = self.options.fontlog
        self.font.fontname = self.options.fontname
        self.font.version = self.options.font_version
        self.font.fullname = self.options.fullname
        self.font.italicangle = self.options.italicangle
        if self.options.upos is not None:
            self.font.upos = self.options.upos
        if self.options.uwidth is not None:
            self.font.uwidth = self.options.uwidth

        for self.input_options in self.options.iterinputs():
            if not self.input_options.jobname:
                if self.input_options.input_file:
                    self.input_options.jobname = self.input_options.input_file.with_suffix('').name
                else:
                    # use mfput since it's used as the jobname by mf in this case
                    self.jobname = 'mfput'
            if not self.options.jobname:
                self.options.jobname = self.input_options.jobname
            self.input_options.mf_options.append('-jobname=' + self.input_options.jobname)
            self.input_options.mf_options.append('-output-directory=' + str(self.input_options.output_directory))

            self.define_patterns()
            self.log_path = Path(self.input_options.output_directory) / (self.input_options.jobname + '.log')

            self.ppi = self.input_options.ppi
            self.ppi_factor = 1
            self.define_mf_first_line()

            pre_run_required = self.input_options.upm is not None and (self.options.ascent is None or self.options.descent is None)
            if pre_run_required:
                self.run_mf(is_pre_run=True)
                self.extract_cmds_from_log()
                pre_run_results = self.process_pre_run_commands()
                # upm
                orig_upm = pre_run_results['ascent'] + pre_run_results['descent']
                if orig_upm > 0:
                    target_upm = self.input_options.upm
                    target_ppi = self.input_options.ppi * target_upm / orig_upm
                    mf_target_ppi = target_ppi
                    ppi_overflow_factor = 1
                    while mf_target_ppi > self.MF_OVERFLOW:
                        # reduce mf_target_ppi to prevent arithmetic overflow
                        # in METAFONT
                        ppi_overflow_factor += 1
                        mf_target_ppi = target_ppi/ppi_overflow_factor
                    self.ppi = mf_target_ppi
                    while self.ppi > self.MF_INFINITY:
                        # create font with lower UPM to not exceed METAFONT's
                        # infinity with pixels_per_inch value
                        self.ppi_factor += 1
                        self.ppi = mf_target_ppi/self.ppi_factor
                # else there FontForge will print an 'Internal Error: NaN value
                # in spline creation' when setting self.font.em to upm later,
                # but it won't crash.

                # redefine self.mf_first_line with new self.ppi value
                self.define_mf_first_line()

            self.run_mf()

            # open and process log file
            start_time_ff = time()
            self.extract_cmds_from_log()

            if not self.input_options.quiet:
                print('processing its output...')
                print('Some error messages below come directly from fontforge and cannot be muted.')
                print('Line is last known line from current file.')

            if self.input_options.input_encoding is None:
                self.reencode('UnicodeFull')
            else:
                self.reencode(self.input_options.input_encoding, self.input_options.input_encoding_options)

            # picture variables are processed inside fontforge using layers.
            # A dict is used to keep track of the pictures
            self.pictures = {}
            self.pictures['nullpicture'] = fontforge.layer() # predefined empty picture
            self.named_points = {
                'nullpicture': {}
            }

            # a separate font object with a dedicated glyph is used for
            # processing
            internal_font = fontforge.font()
            self.proc_glyph = internal_font.createChar(-1, 'proc_glyph')

            # keep a record of ligtable's skipto labels
            self.skiptos = {}

            self.process_commands(start_time_ff)

            if not self.input_options.quiet:
                print('')

            end_time_ff = time()
            if self.input_options.time:
                print('  (took ' + '%.2f' % (end_time_ff-start_time_ff) + 's)')

            if self.input_options.clean_log:
                pattern = re.sub(r'(\.|\^|\$|\*|\+|(?<!\n)\?|\||\\|\(|\)|\[|\]|\{|\})', r'\\\1', '\n?'.join(self.mf_first_line), flags=re.DOTALL) \
                    + '\n|\n' + '\n?'.join(M) + '.*?\n' + '\n?'.join(M)
                start_time_log = time()
                clean_log = re.sub(pattern, '', self.orig_log_data, flags=re.DOTALL)

                if self.input_options.debug:
                    extension = '.clean.log'
                else:
                    extension = '.log'
                log_path_str = str(self.log_path.with_suffix('')) + extension
                try:
                    with open(log_path_str, 'w') as outfile:
                        outfile.write(clean_log)
                except IOError:
                    print('! I can\'t find file: `' + log_path_str + '\'.')
                    sys.exit(1)
                end_time_log = time()
                if not self.input_options.quiet:
                    print('Log file cleaned up:', log_path_str)
                if self.input_options.time:
                    print('  (took ' + '%.2f' % (end_time_log-start_time_log) + 's)')

        self.apply_font_options_and_save()

        if not self.options.quiet:
            print('Done.')

        # cleanup
        internal_font.close()

        if return_font:
            return self.font
        else:
            self.font.close()

    def define_mf_first_line(self):
        '''define self.mf_first_line based on options
        '''
        # load base file if defined
        if self.input_options.base:
            input_base = 'input ' + self.base + ';'
        else:
            input_base = ''

        # If option is_type is given, add the extra definitions is_pen and
        # is_picture.
        extra_defs = ''
        if self.input_options.is_type:
            extra_defs += 'let is_pen = __mfIIvec__orig_pen__;'
            extra_defs += 'let is_picture = __mfIIvec__orig_picture__;'

        # The first line of the mf argument start with a backslash (\\) so mf
        # knows the first argument is not a file to be loaded. After that
        # initial backslash a list of mf commands is passed to mf.
        self.mf_first_line = ('\\ '
            # redefinition of mf tokens, extra definitions which depend on
            # options, the input of the base file, the first line given by the
            # user and the input of the given input file.
            + self.get_redefinitions()
            + extra_defs
            + input_base
            + self.input_options.first_line
        )
        if self.input_options.input_file is not None:
            self.mf_first_line += 'input ' + str(self.input_options.input_file)

    def run_mf(self, is_pre_run=False):
        '''runs METAFONT with self.mf_options and self.mf_first_line.
        stdout is devnull
        '''
        if is_pre_run:
            if not self.input_options.quiet:
                print('running METAFONT (preliminary run) ...')
        else:
            if not self.input_options.quiet:
                print('running METAFONT...')
            start_time_mf = time()
        subprocess.call(
            ['mf'] + self.input_options.mf_options + [self.mf_first_line],
            stdout=subprocess.DEVNULL,
            cwd=self.input_options.cwd
        )
        end_time_mf = time()
        if self.input_options.time and not is_pre_run:
            print('  (took ' + '%.2f' % (end_time_mf-start_time_mf) + 's)')

    def extract_cmds_from_log(self):
        '''open log file and extract all commands

        sets self.orig_log_data and self.cmds
        '''
        try:
            with open(self.log_path, 'r+') as f:
                self.orig_log_data = f.read()
        except IOError as e:
            print('! I can\'t find file: `' + str(self.log_path) + '\'.')
            print(e)
            sys.exit(1)

        log_data = self.error_pattern.sub('', self.orig_log_data)
        log_data = re.sub('\n', '', log_data)
        log_data = log_data.split(self.mf_first_line, 1)[1] # interesting info only after the input
        self.cmds = self.command_pattern.findall(log_data) # find all commands

    def process_pre_run_commands(self):
        '''process commands for preliminary run

        Returns:
            dict: results of preliminary run
        '''
        pre_run_results = {
            'ascent': 0,
            'descent': 0,
        }

        ascent_specified = False
        descent_specified = False

        i = 0
        while i < len(self.cmds):
            cmd = self.cmds[i]
            cmd_name = cmd[0]
            self.cmd_body = cmd[2]

            if (cmd_name == 'shipout'
                and (self.options.ascent is None or self.options.descent is None)
                and (not ascent_specified or not descent_specified)
            ):
                shipout = self.shipout_pattern.search(self.cmd_body)
                hppp = float(shipout.group(1))
                charht = round(float(shipout.group(5))*hppp)
                chardp = round(float(shipout.group(6))*hppp)
                if (
                    self.options.ascent is None
                    and not ascent_specified
                    and charht > pre_run_results['ascent']
                ):
                    pre_run_results['ascent'] = charht
                if (
                    self.options.descent is None
                    and not descent_specified
                    and chardp > pre_run_results['descent']
                ):
                    pre_run_results['descent'] = chardp
            elif cmd_name[:5] == 'font_':
                font_cmd = cmd_name[5:]
                if font_cmd in ['ascent', 'descent']:
                    hppp, val = self.cmd_body.split('>> ')
                    val = round(float(val)*float(hppp))
                    if font_cmd == 'ascent':
                        pre_run_results['ascent'] = val
                        ascent_specified = True
                    elif font_cmd == 'descent':
                        pre_run_results['descent'] = val
                        descent_specified = True
            # else command not important in pre run
            i += 1
        return pre_run_results

    def process_commands(self, start_time_ff):
        '''processes the commands cmds

        shows progress and eta based on start_time_ff

        Args:
            start_time_ff (float): start time of fontforge from time.time()
        '''

        pos_list = []
        sub_list = []
        charlist_list = []
        extensible_list = []

        base_glyphs_of_variants = {}

        if self.input_options.charcode_from_last_ASCII_hex_arg:
            last_ASCII_hex_arg_value = None
            last_ASCII_hex_arg_is_unicode = False

        if self.input_options.kerning_classes:
            kerning_list = {
                'left-glyphs': [],
                'right-glyphs': [],
                'offsets': []
            }
        attachment_points = []
        current_ligtable_to_feature = { # set defaults (first item in lists)
            ligtable_op_type: ligtable_ot_features[0]
            for ligtable_op_type, ligtable_ot_features in self.supported_ligtable_ot_features.items()
        }

        ascent_specified = False
        descent_specified = False

        glyph_unicode = None
        self.glyph_replacements = [] # for all glyphs
        if self.input_options.extension_glyph:
            glyph_name = None
            glyph_comment = None
            glyph_top_accent = None
            glyph_build = False
            glyph_references = []
            glyph_add_extrema = False
            glyph_add_inflections = False
            glyph_round = False
            glyph_auto_hint = False
            glyph_auto_instruct = False
            glyph_replacements = [] # for current glyph
            glyph_hints = []
            glyph_math_kernings = {
                'top_right': [],
                'top_left': [],
                'bottom_right': [],
                'bottom_left': []
            }

            self.glyph_references = []

            specified_top_accents = []

        if self.input_options.extension_ligature:
            carets = []

        i = 0
        while i < len(self.cmds):
            cmd = self.cmds[i]
            cmd_name = cmd[0]
            if cmd[1]:
                self.last_known_line = int(cmd[1])
            self.cmd_body = cmd[2]

            self.show_progress(start_time_ff, i)

            if cmd_name == 'ASCII' and self.input_options.charcode_from_last_ASCII_hex_arg:
                ascii_str_arg = self.cmd_body[1:-1]
                if len(ascii_str_arg) > 0 and (len(ascii_str_arg) % 2) == 0: # only even number of characters
                    try:
                        ascii_arg_first_char = ascii_str_arg[0]
                        if ascii_str_arg[:2].lower() == 'u+':
                            # remove U+ or u+ which is not supported by int()
                            ascii_str_arg = ascii_str_arg[2:]
                            last_ASCII_hex_arg_is_unicode = True
                        else:
                            last_ASCII_hex_arg_is_unicode = False
                        # int(x, 16) allows upper, lower case and 0x/0X prefix
                        # second tuple element is the int that MF sees and uses for offsets
                        last_ASCII_hex_arg_value = (int(ascii_str_arg, 16), ord(ascii_arg_first_char))
                    except ValueError:
                        # ignore if it's not a valid hex string
                        pass

            # addto\
            # TODO This section needs to be tested and maybe reworked! mf only
            # makes one line with each pen stroke so doublepath is needed for a
            # full stroke. Using contour with a pen results in an offset line,
            # left or right depending on the direction of the path. One of the
            # flags removeinternal or removeexternal might be useful to do this.
            elif cmd_name == 'addto':
                addto = self.cmd_body[1:-1] # clip quotes
                if self.cmds[i+1][0] == 'turningcheck':
                    # turningcheck is always followed by turningnumber
                    turningcheck = int(self.cmds[i+1][2])
                    turningnumber = int(self.cmds[i+2][2])
                    j = i + 3
                else:
                    j = i + 1

                # next command is also, contour or doublepath
                addto_next_cmd_name = self.cmds[j][0]
                if self.cmds[j][1]:
                    self.last_known_line = int(self.cmds[j][1])
                addto_next_cmd_body = self.cmds[j][2]
                j += 1

                # pen and weight
                # set default values
                # "If no pen is given, the pen is assumed to be 'nullpen'; if no
                # weight is given, the weight is assumed to be +1."
                # (The METAFONTbook, p. 118)
                pen = '(0,0) .. cycle' # this is nullpen; in mf, type: show nullpen;
                weight = 1
                # Loop over all commands and overwrite pen and weight if there
                # are multiple withpen and withweight commands: "If more than one
                # pen or weight is given, the last specification overrides all
                # previous ones." (The METAFONTbook, p. 118)
                while j < len(self.cmds):
                    cmd = self.cmds[j]
                    cmd_name = cmd[0]
                    if cmd[1]:
                        self.last_known_line = int(cmd[1])
                    self.cmd_body = cmd[2]

                    if cmd_name == 'withpen':
                        pen = self.cmd_body
                    elif cmd_name == 'withweight':
                        # The weight is "rounded to the nearest integer"
                        # (The METAFONTbook, p. 118).
                        weight = int(round(float(self.cmd_body)))
                    else:
                        break
                    j += 1
                i = j - 1 # i will be increased at the end of the outer while loop

                # processing of instructions on what to add to the picture
                if addto_next_cmd_name == 'mi': # - (minus)
                    # TODO can - even occur here?
                    # TODO i instead of j?
                    self.pictures[addto] += self.pictures[self.cmds[j][1:-1]].reverseDirection()
                    j += 1
                elif addto_next_cmd_name == 'also':
                    # use a copy (duplicate) of the also picture so transform is not applied to original
                    self.pictures['temp_layer'] = self.pictures[addto_next_cmd_body[1:-1]].dup()
                    transform_ps_matrix = psMat.identity()
                    jj = i + 1
                    while jj < len(self.cmds):
                        addto_also_next_cmd_name = self.cmds[jj][0]
                        addto_also_next_cmd_body = self.cmds[jj][2]
                        if addto_also_next_cmd_name == 'rotated':
                            transform_ps_matrix = psMat.compose(transform_ps_matrix, psMat.rotate(float(addto_also_next_cmd_body)/180*pi))
                        elif addto_also_next_cmd_name == 'scaled':
                            transform_ps_matrix = psMat.compose(transform_ps_matrix, psMat.scale(float(addto_also_next_cmd_body)))
                        elif addto_also_next_cmd_name == 'shifted':
                            translate_x = float(self.pair_pattern.search(addto_also_next_cmd_body).group(1))
                            translate_y = float(self.pair_pattern.search(addto_also_next_cmd_body).group(2))
                            transform_ps_matrix = psMat.compose(transform_ps_matrix, psMat.translate(translate_x, translate_y))
                        elif addto_also_next_cmd_name == 'slanted':
                            transform_ps_matrix = psMat.compose(transform_ps_matrix, psMat.skew(atan(float(addto_also_next_cmd_body))))
                        elif addto_also_next_cmd_name == 'xscaled':
                            transform_ps_matrix = psMat.compose(transform_ps_matrix, psMat.scale(float(addto_also_next_cmd_body), 0))
                        elif addto_also_next_cmd_name == 'yscaled':
                            transform_ps_matrix = psMat.compose(transform_ps_matrix, psMat.scale(0, float(addto_also_next_cmd_body)))
                        else:
                            break
                        jj += 1
                    i = jj - 1 # i will be increased at the end of the outer while loop
                    self.pictures['temp_layer'].transform(transform_ps_matrix)
                    self.pictures[addto] += self.pictures['temp_layer']
                else: # add a path
                    # There are four basic cases of adding a path to a glyph:
                    # 1. A contour without a pen: The contour is simply added
                    #    to the glyph. (fill c;)
                    # 2. A doublepath without a pen: This will have no effect
                    #    in mf so it is ignored in FontForge too.
                    # 3. A contour with a pen: The contour is added to the
                    #    glyph with an offset. A closed path will fill an area,
                    #    without a hole, an open path will cause an error in mf
                    #    and in FontForge.
                    # 4. A doublepath with a pen: A simple pen stroke added to
                    #    the glyph. (draw p;)
                    #
                    # Since in some cases multiple paths are added, create a
                    # list of paths. The command body of the contour or
                    # doublepath command is a path.
                    paths = [addto_next_cmd_body]
                    # Add the path multiple times, according to the weight.
                    paths = paths*abs(weight)

                    # 1st case: contour without pen
                    if addto_next_cmd_name == 'contour' and pen in self.SIMPLE_PENS:
                        # If turningcheck is negative the paths are just added
                        # according to the sign of the weight. Otherwise, the
                        # turningnumber is used (== is equivalent to the XOR
                        # operator). NOTE: "within FontForge all outer
                        # boundaries must be drawn clockwise" (FonForge
                        # Tutorial, 4.2.), while its counter clockwise in mf, so
                        # all paths need to be added reversed for positive
                        # weights.
                        if turningcheck <= 0: # use the path direction directly
                            if weight > 0:
                                self.add_contours(addto, [self.reversed_path(p) for p in paths])
                            elif weight < 0:
                                self.add_contours(addto, paths)
                            # TODO is the behavior correct for weight == 0 ?
                        else:
                            if (weight > 0) == (turningnumber > 0): # adjust the path direction according to the weight
                                self.add_contours(addto, [self.reversed_path(p) for p in paths])
                            elif (weight < 0) == (turningnumber > 0):
                                self.add_contours(addto, paths)
                            # TODO is the behavior correct for weight == 0 ?

                    # 3rd and 4th case: contour/doublepath with pen
                    elif pen not in self.SIMPLE_PENS:
                        self.pictures['temp_layer'] = fontforge.layer()

                        # Removing the overlap on the layer (default) produces
                        # no hole in non cyclic overlapping strokes. Removing
                        # overlap on the contour produces a hole with wrong
                        # direction, so it's no real hole. The direction needs
                        # to be corrected later. This may be a bug in FontForge.
                        stroke_kwargs = {'removeoverlap': 'contour'}

                        # If it's a doublepath just add a normal stroke, without
                        # anything special. This is the 4th case.
                        if addto_next_cmd_name == 'doublepath':
                            # 4th case
                            self.add_contours('temp_layer', paths)
                        else: # 3rd case: contour with pen
                            self.add_contours('temp_layer', [self.reversed_path(p) for p in paths])
                            # Internal removal is described as "When a contour
                            # is closed and clockwise, only the smaller “inside”
                            # contour is retained." (FontForge's documentation:
                            # glyph.stroke())
                            stroke_kwargs.update({'removeinternal': True})

                        stroke_kwargs.update({'simplify': self.input_options.stroke_simplify})
                        if self.input_options.stroke_accuracy is not None: # None -> Fontforge's default value
                            stroke_kwargs.update({'accuracy': self.input_options.stroke_accuracy})

                        pen_first_point = self.pair_pattern.search(pen) # TODO better with .groups ?
                        pen_joins = self.join_pattern.findall(pen[pen_first_point.end():])

                        # If the pen's path has 8 points, it is assumed to be a
                        # circle / ellipse.
                        pen_is_circle = False
                        if len(pen_joins) == 8:
                            # TODO more conditions
                            pen_is_circle = True

                        if pen_is_circle:
                            # TODO better to get both widths and compare to
                            # determine which one is minor_width ?
                            width = sqrt((float(pen_joins[3][4])-float(pen_first_point.group(1)))**2 + (float(pen_joins[3][5])-float(pen_first_point.group(2)))**2)
                            minor_width = sqrt((float(pen_joins[5][4])-float(pen_joins[1][4]))**2 + (float(pen_joins[5][5])-float(pen_joins[1][5]))**2)
                            angle = atan2(float(pen_joins[3][5])-float(pen_first_point.group(2)),float(pen_joins[3][4])-float(pen_first_point.group(1)))
                            self.pictures['temp_layer'] = self.pictures['temp_layer'].stroke('elliptical', width, minor_width, angle, **stroke_kwargs)

                        elif len(pen_joins) == 2 and pen_joins[1][6] == 'cycle':
                            # penrazor case

                            # FontForge doesn't support pens with height 0. A
                            # workaround is not possible since isClockwise
                            # doesn't work for self intersecting contours.
                            # Therefore, an dedicated pen implementation is
                            # done for the penrazor case.

                            # TODO check if straight
                            z1 = [float(pen_first_point.group(1)), float(pen_first_point.group(2))]
                            z2 = [float(pen_joins[0][4]), float(pen_joins[0][5])]
                            width = sqrt((z2[0] - z1[0])**2 + (z2[1] - z1[1])**2)
                            angle = atan((z2[1] - z1[1]) / (z2[0] - z1[0]))

                            path_layer = self.pictures['temp_layer'].dup()
                            self.pictures['temp_layer'] = fontforge.layer()

                            for c in path_layer:
                                contour_layer = fontforge.layer()
                                # The contour is rotated so that penrazor is
                                # always horizontal. This is important when
                                # adding extreme points.
                                c.transform(psMat.rotate(-angle))
                                c.addExtrema('all')

                                # Looping over segments so skip last point.
                                for p_i in [i for i, p in enumerate(c[:-1]) if p.on_curve]:
                                    # Find next on-curve point. i+1 ... i+3 can
                                    # be the next on-curve point.
                                    for p_j in range(p_i+1, p_i+4):
                                        if p_j >= len(c):
                                            p_j -= len(c)
                                        if c[p_j].on_curve:
                                            break
                                    if p_j < p_i:
                                        c1 = c[p_i:]+c[:p_j+1].dup()
                                    else:
                                        c1 = c[p_i:p_j+1].dup()
                                    c2 = c1.dup().reverseDirection()
                                    c1.transform(psMat.translate(width/2, 0))
                                    c2.transform(psMat.translate(-width/2, 0))
                                    c_penrazor = c1 + c2
                                    c_penrazor.closed = True
                                    # penrazor always draws positive.
                                    if not c_penrazor.isClockwise():
                                        c_penrazor.reverseDirection()
                                    contour_layer += c_penrazor
                                self.remove_overlap(contour_layer)
                                self.pictures['temp_layer'] += contour_layer
                            self.pictures['temp_layer'].transform(psMat.rotate(angle))

                        else:
                            # FontForge only supports elliptical or polygonal
                            # pens, so all other pens are treated as polygons.
                            pen_contour = fontforge.contour()
                            pen_contour.moveTo(float(pen_first_point.group(1)), float(pen_first_point.group(2)))
                            for j in pen_joins[:-1]:
                                pen_contour.lineTo(float(j[4]), float(j[5]))
                            pen_contour.closed = True # TODO is pen_contour from mf always closed or is it necessary to check it?
                            pen_contour = pen_contour.reverseDirection() # TODO is this always required? Why?
                            try:
                                self.pictures['temp_layer'] = self.pictures['temp_layer'].stroke('convex', pen_contour, **stroke_kwargs)
                            except ValueError as e1:
                                pen_contour = pen_contour.reverseDirection()
                                try:
                                    self.pictures['temp_layer'] = self.pictures['temp_layer'].stroke('convex', pen_contour, **stroke_kwargs)
                                except ValueError as e2:
                                    print('! Pen can\'t be used here. METAFONT gives:')
                                    print('    ' + pen)
                                    print('  fontforge raises:')
                                    print('    ' + str(e1))
                                    print('  Even after reversing the pen\'s outline path\'s direction, fontforge raises:')
                                    print('    ' + str(e2))
                                    print('  The contour is simply added without using a pen. It may not be closed. This might produce correct results if penspeck is used (which is used by drawdot)')
                                    # TODO identify when penspeck is used and skip the errors

                        # Fix possible wrong direction of a hole created by
                        # stroke(). Note: This also seems to change the contour
                        # order in the glyph's layer. The outer contour always
                        # seems to be the last contour
                        self.correct_direction('temp_layer')
                        # add stroked layer to glyph
                        self.pictures[addto] += self.pictures['temp_layer']

                    # 2nd case: doublepath without pen
                    else:
                        # doublepath without pen has no effect
                        pass

            # cull\
            # TODO This section needs extensive testing and rework!
            elif cmd_name == 'cull':
                cull_pic_name = self.cmd_body[1:-1] # clip quotes
                keep_or_drop = self.cmds[i+1][0]
                a, b = [int(float(s)) for s in self.pair_pattern.search(self.cmds[i+1][2]).groups()]
                weight = 1 # default (The METAFONTbook, p. 120, 118)
                num_paths = len(self.pictures[cull_pic_name])

                i += 1
                j = i+1
                while j < len(self.cmds):
                    cmd = self.cmds[j]
                    cmd_name = cmd[0]
                    self.cmd_body = cmd[2]

                    if cmd_name == 'withweight':
                        # The weight is "rounded to the nearest integer"
                        # (The METAFONTbook, p. 120, 118).
                        weight = int(round(float(self.cmd_body)))
                    else:
                        break
                    j += 1
                i = j-1

                # num_paths is the max number of overlaps
                # if a or b exceed this number, all paths need to be combined
                drop_pos = (
                    keep_or_drop == 'dropping' and a == 1 and b >= num_paths
                    or keep_or_drop == 'keeping' and a <= -num_paths and b == 0
                )
                drop_neg = ( # cullit
                    keep_or_drop == 'dropping' and -a >= num_paths and b == 0
                    or keep_or_drop == 'keeping' and a == 1 and b >= num_paths
                )
                if drop_pos or drop_neg:
                    # TODO reverse before and after remove_overlap needed for drop_pos?
                    self.remove_overlap(cull_pic_name)

                    # TODO explain this section
                    drop_contours = []
                    temp_layer = self.pictures[cull_pic_name]
                    corrected_picture = self.pictures[cull_pic_name].dup()
                    self.correct_direction(corrected_picture)
                    for j, (cl, l) in enumerate(zip(corrected_picture, self.pictures[cull_pic_name])):
                        if (
                            drop_pos and cl.isClockwise() == l.isClockwise()
                            or drop_neg and cl.isClockwise() != l.isClockwise()
                        ):
                            drop_contours.append(j)
                    self.pictures[cull_pic_name] = fontforge.layer()
                    for k, c in enumerate(temp_layer):
                        if k not in drop_contours:
                            self.pictures[cull_pic_name] += temp_layer[k]
                elif keep_or_drop == 'dropping' and a == 0 and b == 0:
                    # everything non-zero will stay
                    self.remove_overlap(cull_pic_name)
                    self.correct_direction(cull_pic_name)
                elif keep_or_drop == 'keeping' and a == 0 and b == 0:
                    print('! cull V keeping (0, 0) isn\'t allowed (see The METAFONTbook, p. 120)')
                    print('  ignoring this cull command')
                elif keep_or_drop == 'keeping':
                    # TODO check usage of a and b here, b not used
                    contour_combinations = list(combinations(self.pictures[cull_pic_name], a))
                    and_layers = []
                    for j in range(len(contour_combinations)):
                        j_layer = fontforge.layer()
                        for k, c in enumerate(contour_combinations[j]):
                            j_layer += c
                            if k != 0:
                                # intersect only works in a glyph
                                self.proc_glyph.layers[1] = j_layer
                                self.proc_glyph.intersect()
                                j_layer = self.proc_glyph.layers[1]
                        and_layers.append(j_layer)
                    keeping_layer = fontforge.layer()
                    # combine all layers
                    for l in and_layers:
                        keeping_layer += l

                    self.proc_glyph.layers[1] = keeping_layer
                    # TODO: suppress warning during overlap removal:
                    # 'Internal Error (overlap) in proc_glyph: Neither needed nor unneeded'

                    # The removeOverlap() method sometimes creates warnings
                    # while result is OK. They can't be suppressed with
                    # temporarily redirecting stdout or with echo OFF. Therefor
                    # ANSI Control Sequences are used to remove them. They start
                    # with the hexadecimal code of the escape character
                    # (\x1b), followed by the Control Sequence Introducer,
                    # an opening bracket ([). The letter after the bracket
                    # specifies the control sequence. The letter may be preceded
                    # by a number whose meaning depends on the control sequence.

                    # Before the removeOverlap() method is called, the current
                    # cursor position is saved with \x1b[s. After the call of
                    # the command there may be a warning which should be
                    # suppressed. To hide it, The cursor is restored to the
                    # saved position with \x1b[u. Since the waring contains a
                    # line break, the cursor needs to move one line up (\x1b[A).
                    # TODO multiple lines up?
                    # \x1b[J erases the warning.
                    # TODO what does \x1b[J do or erase exactly
                    print('\x1b[s', end = '')
                    self.proc_glyph.removeOverlap()
                    print('\x1b[u\x1b[A\x1b[J', end = '')

                    keeping_layer = self.proc_glyph.layers[1]
                    if weight < 0:
                        # reverse cull result for negative weight
                        keeping_layer.reverseDirection()
                    # Add the contours multiple times by the absolute value of
                    # the weight and reduce the multiple layers to a single one.
                    # The result is the new picture after culling it.
                    self.pictures[cull_pic_name] = reduce(lambda x, y: x + y, [keeping_layer]*abs(weight))
                else:
                    print('! cull not fully supported yet.')

            elif cmd_name == 'picture':
                for pic_name in self.split_pattern.split(self.cmd_body):
                    # create layer for each picture
                    pic_name = pic_name[1:-1] # clip quotes
                    self.pictures[pic_name] = fontforge.layer()
                    self.named_points[pic_name] = {}

            elif cmd_name == 'pic_eqn':
                j = i+1
                j_eq = [i-1]
                complex_expressions = []
                while j < len(self.cmds):
                    if self.cmds[j][0] not in ('pic', 'eq', 'as', 'pl', 'mi'):
                        break
                    elif self.cmds[j][0] in ('eq', 'as'):
                        if j-j_eq[-1] < 2:
                            complex_expressions.append(j)
                            if len(complex_expressions) > 1:
                                print('! ignoring complex picture expression')
                        j_eq += [j]
                    j += 1

                j_eq += [j]

                for k in j_eq[:-2]:
                    if len(complex_expressions) == 0:
                        pic_name_lhs = self.cmds[k+1][2][1:-1]
                        pic_name_rhs = self.cmds[j_eq[-2]+1][2][1:-1]
                        if self.cmds[k-1][0] == 'mi':
                            self.pictures[pic_name_lhs] = fontforge.layer()
                            for c in self.pictures[pic_name_rhs]:
                                self.pictures[pic_name_lhs] += c
                            self.pictures[pic_name_lhs] = self.pictures[pic_name_lhs].reverseDirection()
                            self.named_points[pic_name_lhs] = deepcopy(self.named_points[pic_name_rhs])
                        else:
                            self.pictures[pic_name_lhs] = fontforge.layer()
                            for c in self.pictures[pic_name_rhs]:
                                self.pictures[pic_name_lhs] += c
                            self.named_points[pic_name_lhs] = deepcopy(self.named_points[pic_name_rhs])
                    else:
                        for k in range(i,j):
                            if k not in complex_expressions[1:]:
                                continue
                            for l in range(j_eq[k-1], j_eq[k], 2):
                                if self.cmds[l][2] != 'pic':
                                    continue
                                if self.cmds[l-1][2] in ('eq', 'as', 'pl'):
                                    self.pictures[self.cmds[j_eq[-1]][2][1:-1]] += self.pictures[self.cmds[l][2][1:-1]]
                                elif self.cmds[l-1][2] == 'mi':
                                    self.pictures[self.cmds[j_eq[-1]][2][1:-1]] += self.pictures[self.cmds[l][2][1:-1]].reverseDirection()
                i = j_eq[-1]-1

            elif cmd_name == 'shipout':
                skip_glyph = False

                shipout = self.shipout_pattern.search(self.cmd_body)
                hppp = float(shipout.group(1))

                # "The values of xoffset, yoffset, charcode, and charext are
                # first rounded to integers, if necessary." (The METAFONTbook,
                # p. 220)
                charcode = round(float(shipout.group(2)))
                charext = round(float(shipout.group(3)))
                charwd = round(float(shipout.group(4))*hppp)
                charht = round(float(shipout.group(5))*hppp)
                chardp = round(float(shipout.group(6))*hppp)
                charic = round(float(shipout.group(7))*hppp)
                # 8 and 9 are chardx, chardy
                xoffset = round(float(shipout.group(10)))
                yoffset = round(float(shipout.group(11)))

                if self.input_options.charcode_from_last_ASCII_hex_arg and last_ASCII_hex_arg_value is not None:
                    # This assumes that the last use of ASCII with a valid hex
                    # string was to set charcode, e.g. no use of ASCII with a
                    # valid hex string between beginchar ... endchar (if used).
                    glyph_code = last_ASCII_hex_arg_value[0]
                    # Support offsets offsets based on hex codes.
                    glyph_code += charcode - last_ASCII_hex_arg_value[1]
                    last_ASCII_hex_arg_value = None
                    if last_ASCII_hex_arg_is_unicode:
                        # If it's a unicode value, reset glyph_code (glyph_code
                        # is ASCII value of U or u). If no glyph_unicode was
                        # defined using the glyph extension, use the unicode
                        # value from ASCII. This means a unicode value from
                        # ASCII stored in glyph_code is discarded if
                        # glyph_unicode is used.
                        if glyph_unicode is None:
                            glyph_unicode = glyph_code
                        glyph_code = -1
                    last_ASCII_hex_arg_is_unicode = False
                else:
                    glyph_code = charcode + charext*256
                pic_name = self.cmds[i+1][2][1:-1] # clip quotes
                pic = self.pictures[pic_name]

                if self.input_options.fix_contours:
                    self.fix_contours(pic)

                if self.input_options.remove_artifacts:
                    self.remove_artifacts(pic)

                if self.input_options.remove_collinear:
                    self.remove_collinear(pic)

                if self.input_options.cull_at_shipout:
                    # Above fixes are after actual cull-at-shipout so remove
                    # overlaps again.
                    self.remove_overlap(pic)

                if glyph_code >= 0:
                    # do this before any glyph_code changes
                    skip_glyph = self.should_skip_glyph(glyph_code)

                # Open Type Substitution glyphs need different glyph name
                if self.input_options.ot_sub_feature is not None:
                    if glyph_code < 0:
                        if glyph_unicode is not None:
                            base_glyph_name = fontforge.nameFromUnicode(glyph_unicode)
                        elif glyph_name is not None:
                            base_glyph_name = glyph_name
                        else:
                            raise ValueError('! glyph without glyph code, unicode value and glyph name')
                    else:
                        # TODO This solution is not ideal.
                        try:
                            # TODO If the input encoding changes, some names
                            # might be wrong.
                            base_glyph_name = self.font[glyph_code].glyphname
                        except TypeError:
                            # if the encoding changed and the character ahs no unicode
                            base_glyph_name = 'NameMe.' + str(glyph_code)
                    # set glyph code and unicode value to unset values to
                    # create glyph with name below
                    glyph_code = -1
                    glyph_unicode = None
                    if self.input_options.glyph_name_suffix is not None:
                        glyph_name_suffix = self.input_options.glyph_name_suffix
                    else:
                        glyph_name_suffix = '.' + self.input_options.ot_sub_feature
                    glyph_name = base_glyph_name + glyph_name_suffix

                if glyph_unicode is not None and glyph_code == -1:
                    # If no glyph_name is defined, use the unicode default name
                    # instead.
                    if not self.input_options.extension_glyph or glyph_name is None:
                        # TODO Better check with actual code point of current
                        # encoding. How to get it?
                        glyph_name = fontforge.nameFromUnicode(glyph_unicode)
                    elif self.input_options.extension_glyph and glyph_name[0] == '"':
                        glyph_name = glyph_name[1:-1]
                    glyph = self.font.createChar(glyph_unicode, glyph_name)
                elif glyph_unicode is None and glyph_code == -1 and glyph_name is not None:
                    if not skip_glyph:
                        glyph = self.font.createChar(-1, glyph_name)
                else:
                    if not skip_glyph:
                        glyph = self.font.createMappedChar(glyph_code)

                if not skip_glyph:
                    glyph.layers[1] = pic

                    # transform before setting glyph.width\
                    # glyph.transform has no 'noWidth' flag. This is strange
                    # because font.transform supports this flag and the GUI glyph
                    # transform dialog has a 'Transform Width Too' checkbox that
                    # can be unchecked.
                    if xoffset != 0 or yoffset != 0:
                        # "The pixels of v are shifted by (xoffset, yoffset) as
                        # they are shipped out." (The METAFONTbook, p. 220)
                        glyph.transform((1.0, 0.0, 0.0, 1.0, xoffset, yoffset))

                    glyph.width = charwd
                    glyph.texheight = charht
                    glyph.texdepth = chardp
                    if self.input_options.set_italic_correction:
                        glyph.italicCorrection = charic
                    else:
                        # also ignore ic value in other calculations below
                        charic = 0

                    if self.input_options.extension_glyph and glyph_top_accent is not None:
                        glyph.topaccent = glyph_top_accent
                        # TODO how to get the code point if encoding is not unicode?
                        specified_top_accents.append(glyph.glyphname)
                    elif self.input_options.set_top_accent:
                        glyph.topaccent = round((charwd + charic)/2)
                        # skewchar kerning is handled at the end

                    for attachment_point_class_name, lookup_type, x, y in attachment_points:
                        glyph.addAnchorPoint(attachment_point_class_name, lookup_type, x, y)
                attachment_points = []

                if not skip_glyph and self.input_options.ot_sub_feature is not None:
                    self.glyph_replacements.append((base_glyph_name, self.input_options.ot_sub_feature, glyph_name))

                if self.input_options.extension_glyph:
                    # Setting glyph.glyphname or glyph.unicode after creation
                    # somehow messes up the encoding.
                    if not skip_glyph:
                        if glyph_comment is not None:
                            if glyph_comment[0] == '"':
                                glyph_comment = glyph_comment[1:-1]
                            glyph.comment = glyph_comment
                        if glyph_build:
                            glyph.build()
                        if len(glyph_references) > 0:
                            for referenced_name, transform_str in glyph_references:
                                transform_str = transform_str[1:-1] # remove '(' and ')'
                                mf_transform = [float(t) for t in transform_str.split(',')]
                                ps_matrix = tuple(mf_transform[2:] + mf_transform[:2]) # move translate parts to end
                                if referenced_name[0] == '"':
                                    referenced_name = referenced_name[1:-1]
                                self.glyph_references.append((glyph.glyphname, self.to_glyph_name(referenced_name), ps_matrix))
                        if glyph_add_extrema:
                            glyph.addExtrema()
                        if glyph_add_inflections:
                            glyph.addInflections()
                        if glyph_round:
                            glyph.round()
                        if glyph_auto_hint:
                            glyph.autoHint()
                        # do manual hints after autoHint since autoHint clears hints
                        # do manual hints before autoInstr since autoInstr is based on hints
                        if len(glyph_hints) > 0:
                            for hint_type, *args in glyph_hints:
                                if hint_type == 'diagonal':
                                    # args are 2 to 3 strings of a pair each
                                    args = [a[1:-1].split(',') for a in args] # remove '(', ')' and split x and y parts
                                    args = [(round(float(a[0]), 6), round(float(a[1]), 6)) for a in args]
                                    dhints = list(glyph.dhints)
                                    p0 = args[0]
                                    p1 = args[1]
                                    if len(args) == 3:
                                        unit_vec = args[2]
                                    else:
                                        unit_vec = (p1[1]-p0[1], p1[0]-p0[0]) # perpendicular to vector p0 -> p1
                                        # The unit vector passed to FontForge
                                        # doesn't need to have length 1. FontForge
                                        # will do it's own normalization. No need
                                        # to do it here.
                                    dhints.append((p0, p1, unit_vec))
                                    # TODO Why aren't they displayed in the GUI?
                                    # dhints created in the gui are. The only
                                    # difference is that the numbers of dhints
                                    # created in the GUI are rounded to 6 digits,
                                    # but FontForge's normalization of unit_vec
                                    # makes this impossible from the Python API.
                                    glyph.dhints = tuple(dhints)
                                else:
                                    # glyph.addHint() hangs, using hhints/vhints
                                    args = [float(a) for a in args]
                                    if hint_type == 'horizontal':
                                        hints = glyph.hhints
                                    else:
                                        hints = glyph.vhints
                                    start = min(args)
                                    width = max(args) - min(args)
                                    hints = tuple(list(hints) + [(start, width)])
                                    if hint_type == 'horizontal':
                                        glyph.hhints = hints
                                    else:
                                        glyph.vhints = hints
                        if glyph_auto_instruct:
                            glyph.autoInstr()
                        for corner, kernings in glyph_math_kernings.items():
                            if len(kernings) > 0:
                                if corner.split('_')[1] == 'right':
                                    kernings = [(
                                        round(float(x) - (charwd + charic)),
                                        round(float(y))
                                    ) for x, y in kernings]
                                else:
                                    kernings = [(
                                        round(float(x)),
                                        round(float(y))
                                    ) for x, y in kernings]
                                if corner == 'top_right':
                                    glyph.mathKern.topRight = tuple(kernings)
                                elif corner == 'top_left':
                                    glyph.mathKern.topLeft = tuple(kernings)
                                elif corner == 'bottom_right':
                                    glyph.mathKern.bottomRight = tuple(kernings)
                                elif corner == 'bottom_left':
                                    glyph.mathKern.bottomLeft = tuple(kernings)

                        if len(glyph_replacements) > 0:
                            # replace None by glyph name
                            glyph_replacements = [tuple(glyph.glyphname if r is None else r for r in gr) for gr in glyph_replacements]
                            self.glyph_replacements.extend(glyph_replacements)

                    # reset everything for next glyph
                    glyph_name = None
                    glyph_comment = None
                    glyph_top_accent = None
                    glyph_build = False
                    glyph_references = []
                    glyph_add_extrema = False
                    glyph_add_inflections = False
                    glyph_round = False
                    glyph_auto_hint = False
                    glyph_auto_instruct = False
                    glyph_hints = []
                    glyph_math_kernings = {
                        'top_right': [],
                        'top_left': [],
                        'bottom_right': [],
                        'bottom_left': []
                    }
                    glyph_replacements = []

                if self.input_options.extension_ligature:
                    sub_list = [[(glyph.glyphname, True) if s[0] is None else s[0]] + s[1:] for s in sub_list]
                    glyph.lcarets = tuple(carets)

                glyph_unicode = None

                if not skip_glyph:
                    if self.options.ascent is None and not ascent_specified and charht > self.font.ascent:
                        self.font.ascent = charht
                    if self.options.descent is None and not descent_specified and chardp > self.font.descent:
                        self.font.descent = chardp

                i += 1

            elif cmd_name == 'ligtable':
                cmd_body_parts = self.cmd_body.split('>> ')
                hppp = float(cmd_body_parts[0])
                self.cmd_body = cmd_body_parts[1]

                tmp_list = []
                tmp_sub_list = []
                tmp_pos_list = []

                j = i+1
                while j < len(self.cmds):
                    cmd = self.cmds[j]
                    cmd_name = cmd[0]
                    self.cmd_body = cmd[2].split('>> ')[0]
                    self.last_cmd_body = self.cmds[j-1][2].split('>> ')[-1]

                    if cmd_name == ':':
                        # "[...] after having been rounded to the nearest
                        # integer; or it should be a string [...]" (The
                        # METAFONTbook, p. 317)
                        tmp_list.append([[self.last_cmd_body[1:-1] if self.last_cmd_body[0] == '"' else round(float(self.last_cmd_body))]])
                    elif cmd_name == '::':
                        if self.last_cmd_body in self.skiptos:
                            tmp_list += self.skiptos[self.last_cmd_body]
                    elif cmd_name == ':||':
                        print('! ligtable :|| not supported yet, ignored')
                    elif cmd_name == 'kern':
                        char = self.last_cmd_body
                        kern = self.cmd_body
                        char = char[1:-1] if char[0] == '"' else round(float(char))
                        kern = int(float(kern)*hppp)
                        tmp_pos_list += deepcopy(tmp_list)
                        for k in range(len(tmp_pos_list)-len(tmp_list),len(tmp_pos_list)):
                            tmp_pos_list[k] = [tmp_pos_list[k][0] + [char]] + [kern]
                    elif '=:' in cmd_name:
                        cmd_name_parts = cmd_name.split('=:',1)
                        lig_type = '=:' # start with the characters in the center
                        if 'p' in cmd_name_parts[0]:
                            lig_type = '|' + lig_type
                        else:
                            lig_type = ' ' + lig_type
                        if 'p' in cmd_name_parts[1]:
                            lig_type = lig_type + '|'
                        else:
                            lig_type = lig_type + ' '
                        if 'g' in cmd_name_parts[1]:
                            lig_type = lig_type + '>'
                            print('! ligtable > and >> not supported yet, they will be ignored')
                        else:
                            lig_type = lig_type + ' '
                        if 'gg' in cmd_name_parts[1]:
                            # add a second > (or second space)
                            lig_type = lig_type + '>'
                        else:
                            lig_type = lig_type + ' '

                        char = self.last_cmd_body
                        lig = self.cmd_body
                        char = char[1:-1] if char[0] == '"' else round(float(char))
                        lig = lig [1:-1] if lig [0] == '"' else round(float(lig ))
                        tmp_sub_list += deepcopy(tmp_list)
                        for i in range(len(tmp_sub_list)-len(tmp_list), len(tmp_sub_list)):
                            tmp_sub_list[i] = [(lig, False), lig_type, tmp_sub_list[i][0] + [char], current_ligtable_to_feature['lig']] # False: lig is not a glyph name
                    elif cmd_name == 'skipto':
                        self.skiptos[self.last_cmd_body] = tmp_list
                    else:
                        break
                    j += 1
                i = j-1

                pos_list.extend(tmp_pos_list)
                sub_list.extend(tmp_sub_list)

            elif cmd_name == 'fontdimen':
                cmd_body_parts = self.cmd_body.split('>> ')
                hppp = float(cmd_body_parts[0])
                first_fontdimen = int(cmd_body_parts[1])
                params = [float(p) for p in self.cmds[i+1][2].split('>> ')]
                i += 1
                for j, k in enumerate(range(first_fontdimen, first_fontdimen + len(params))):
                    if k == 1:
                        slant = params[j]
                        if slant == 0:
                            # prevent -0
                            self.font.italicangle = 0.0
                        else:
                            self.font.italicangle = -atan(slant)*180/pi
                    elif k == 2:
                        if self.input_options.space_from_fontdimen:
                            self.font.createChar(32, 'space').width = round(params[j]*hppp)
                    elif k == 5:
                        # font.os2_xheight not in FontForge docs
                        self.font.os2_xheight = round(params[j]*hppp)
                    if self.input_options.input_encoding is not None:
                        if self.input_options.input_encoding.lower().replace(' ', '-') == 'tex-math-symbols' and 5 <= k <= 22:
                            self.fontdimens['family2'][k] = round(params[j]*hppp)
                        elif self.input_options.input_encoding.lower().replace(' ', '-') == 'tex-math-extension' and 8 <= k <= 13:
                            self.fontdimens['family3'][k] = round(params[j]*hppp)

            elif cmd_name == 'charlist':
                base_glyph = self.cmd_body[1:-1] if self.cmd_body[0] == '"' else int(self.cmd_body)
                # TODO big accents: horizontal variants
                charlist = []
                j = i+1
                while j < len(self.cmds):
                    cmd = self.cmds[j]
                    cmd_name = cmd[0]
                    if cmd_name == ":":
                        charlist.append(cmd[2][1:-1] if cmd[2][0] == '"' else int(cmd[2]))
                    else:
                        break
                    j += 1
                i = j-1
                charlist_list.append((base_glyph, charlist))
                # save last variant in case it is extensible
                base_glyphs_of_variants[charlist[-1]] = base_glyph

            elif cmd_name == 'extensible':
                label_glyph = self.cmd_body[1:-1] if self.cmd_body[0] == '"' else int(self.cmd_body)
                cmd_body_part = [p[1:-1] if p[0] == '"' else int(p) for p in self.cmds[i+1][2].split('>> ')]
                i += 1
                vertical_components = []
                if cmd_body_part[2] != 0: # bottom (only non-zero)
                    vertical_components.append([cmd_body_part[2], 0, 0, 0, 'texdepth'])
                vertical_components.append([cmd_body_part[3], 1, 'texdepth', 'texdepth', 'texdepth']) # extender / repeater
                if cmd_body_part[1] != 0: # middle (only non-zero)
                    vertical_components.append([cmd_body_part[1], 0, 0, 0, 'texdepth'])
                    vertical_components.append([cmd_body_part[3], 1, 'texdepth', 'texdepth', 'texdepth']) # extender / repeater (only if middle)
                if cmd_body_part[0] != 0: # top (only non-zero)
                    vertical_components.append([cmd_body_part[0], 0, 0, 0, 'texdepth'])
                extensible_list.append((label_glyph, tuple(vertical_components)))

            elif cmd_name == 'end':
                design_size = float(self.cmd_body)
                if design_size != 0: # 0 is default/unset
                    self.font.design_size = design_size

            # extension
            elif cmd_name[:17] == 'attachment_point_':
                lookup_feature, attachment_point_type = cmd_name[17:].split('_')
                attachment_point = self.attachment_point_pattern.search(self.cmd_body)
                attachment_point_class_name = attachment_point.group(1)[1:-1] # clip quotes
                x = float(attachment_point.group(2))
                y = float(attachment_point.group(3))
                if lookup_feature == 'mark':
                    lookup_type = 'gpos_mark2base'
                if lookup_feature == 'mkmk':
                    lookup_type = 'gpos_mark2mark'
                subtable_name = lookup_type+'_subtable'
                if self.input_options.index is not None:
                    subtable_name += f'_{self.input_options.index}'
                if lookup_type not in self.font.gpos_lookups:
                    if lookup_type == 'gpos_mark2mark' and 'gpos_mark2base' in self.font.gpos_lookups:
                        # make sure mark2mark lookup is after mark2base lookup, not first lookup (default)
                        addLookup_args = ["gpos_mark2base"] # after_lookup_name
                    else:
                        addLookup_args = []
                    self.font.addLookup(lookup_type, lookup_type, None, ((lookup_feature, self.input_options.scripts),), *addLookup_args)
                if subtable_name not in self.font.getLookupSubtables(lookup_type):
                    self.font.addLookupSubtable(lookup_type, subtable_name)
                if attachment_point_class_name not in self.font.getLookupSubtableAnchorClasses(subtable_name):
                    self.font.addAnchorClass(subtable_name, attachment_point_class_name)
                attachment_points.append((attachment_point_class_name, attachment_point_type, x, y))

            elif cmd_name[:5] == 'font_':
                font_cmd = cmd_name[5:]
                cmd_body_parts = self.cmd_body.split('>> ')
                if font_cmd in ['name', 'family_name', 'full_name', 'weight', 'version', 'copyright', 'comment', 'fontlog']:
                    val = self.cmd_body
                    if val[0] == '"':
                        val = val[1:-1]
                    if font_cmd == 'name':
                        self.font.fontname = val
                    elif font_cmd == 'family_name':
                        self.font.familyname = val
                    elif font_cmd == 'full_name':
                        self.font.fullname = val
                    elif font_cmd == 'weight':
                        self.font.weight = val
                    elif font_cmd == 'version':
                        self.font.version = val
                    elif font_cmd == 'copyright':
                        self.font.copyright = val
                    elif font_cmd == 'comment':
                        self.font.comment = val
                    elif font_cmd == 'fontlog':
                        self.font.fontlog = val
                elif font_cmd in ['ascent', 'descent', 'cap_height', 'underline_position', 'underline_width']:
                    hppp, val = self.cmd_body.split('>> ')
                    val = round(float(val)*float(hppp))
                    if font_cmd == 'ascent':
                        self.font.ascent = val
                        ascent_specified = True
                    elif font_cmd == 'descent':
                        self.font.descent = val
                        descent_specified = True
                    elif font_cmd == 'cap_height':
                        self.font.os2_capheight = val
                    elif font_cmd == 'underline_position':
                        self.font.upos = val
                    elif font_cmd == 'underline_width':
                        self.font.uwidth = val
                elif font_cmd == 'add_extrema':
                    self.font_add_extrema = True
                elif font_cmd == 'add_inflections':
                    self.font_add_inflections = True
                elif font_cmd == 'round':
                    self.font_round = True
                elif font_cmd == 'auto_hint':
                    self.font_auto_hint = True
                elif font_cmd == 'auto_instruct':
                    self.font_auto_instruct = True
                elif font_cmd == 'math_constant':
                    # FontForge doesn't provide Python access to the device
                    # tables.
                    if len(cmd_body_parts) != 2:
                        raise TypeError(f'{self.input_options.extension_font_macro_prefix}_{font_cmd} takes exactly two argument ({len(cmd_body_parts)} given)')
                    const_name, const_value = cmd_body_parts
                    if const_name[0] == '"':
                        const_name = const_name[1:-1]
                    const_value = round(float(const_value))
                    self.font.math.__setattr__(const_name, const_value)
                    self.specified_math_constants.append(const_name)
                elif font_cmd == 'postscript_private_dictionary':
                    if len(cmd_body_parts) != 2:
                        raise TypeError(f'{self.input_options.extension_font_macro_prefix}_{font_cmd} takes exactly two argument ({len(cmd_body_parts)} given)')
                    private_name, private_value = cmd_body_parts
                    if private_name[0] == '"':
                        private_name = private_name[1:-1]
                    if private_value[0] == '"':
                        private_value = private_value[1:-1]
                    private_value = private_value.strip()
                    # fontforge doesn't check values, do basic checks here
                    try:
                        if private_name in ['BlueValues', 'OtherBlues', 'FamilyBlues', 'FamilyOtherBlues']:
                            # array of integers with even length
                            assert private_value[0] == '[' and private_value[-1] == ']'
                            vals = private_value[1:-1].split()
                            [int(v) for v in vals] # raises ValueErrors if no ints
                            if private_name in ['BlueValues', 'FamilyBlues']:
                                max_num_pairs = 7
                            if private_name in ['OtherBlues', 'FamilyOtherBlues']:
                                max_num_pairs = 5
                            assert len(vals) % 2 == 0 and len(vals)/2 <= max_num_pairs
                        elif private_name == ['BlueScale', 'ExpansionFactor']:
                            # float
                            float(private_value) # raises ValueError if no float
                        elif private_name in ['BlueShift', 'BlueFuzz', 'lenIV', 'LanguageGroup']:
                            # int
                            int(private_value) # raises ValueError if no int
                        elif private_name in ['StdHW', 'StdVW']:
                            # array of one integer (length 1)
                            assert private_value[0] == '[' and private_value[-1] == ']'
                            int(private_value[1:-1])
                        elif private_name in ['StemSnapH', 'StemSnapV']:
                            # array with length <= 12 of increasing integers
                            assert private_value[0] == '[' and private_value[-1] == ']'
                            vals = private_value[1:-1].split()
                            vals = [int(v) for v in vals] # raises ValueErrors if no ints
                            assert vals == sorted(vals)
                            assert len(vals) <= 12
                        elif private_name == ['forceBold', 'RndStemUp']:
                            # boolean
                            assert private_value in ['true', 'false']
                        else:
                            print(f'! Unknown PostScript private directory entry {private_name}')
                    except (AssertionError, ValueError):
                        raise ValueError(f'value `{private_value}\' of PostScript private directory entry {private_name} is invalid.')
                    self.font.private[private_name] = private_value

            elif cmd_name[:6] == 'glyph_':
                glyph_cmd = cmd_name[6:]
                cmd_body_parts = self.cmd_body.split('>> ')
                if glyph_cmd in ['name', 'unicode', 'comment', 'top_accent']:
                    if len(cmd_body_parts) != 1:
                        raise TypeError(f'{self.input_options.extension_glyph_macro_prefix}_{glyph_cmd} takes exactly one argument ({len(cmd_body_parts)} given)')
                    arg = cmd_body_parts[0]
                    if glyph_cmd in ['name', 'comment']:
                        if arg[0] == '"':
                            arg = arg[1:-1]
                        else:
                            raise TypeError(f'argument of {self.input_options.extension_glyph_macro_prefix}_{glyph_cmd} needs to be a string')
                        if glyph_cmd == 'name':
                            glyph_name = arg
                        elif glyph_cmd == 'comment':
                            glyph_comment = arg
                    elif glyph_cmd == 'unicode':
                        if arg[0] == '"':
                            arg = arg[1:-1]
                            if arg.lower()[:2] == 'u+':
                                # remove U+ or u+ which is not supported by int()
                                arg = arg[2:]
                            arg = int(arg, 16)
                        else:
                            arg = round(float(arg))
                        glyph_unicode = arg
                    else: # 'top_accent'
                        glyph_top_accent = round(float(arg))
                elif glyph_cmd == 'build':
                    glyph_build = True
                elif glyph_cmd == 'add_reference':
                    if len(cmd_body_parts) != 2:
                        raise TypeError(f'{self.input_options.extension_glyph_macro_prefix}_{glyph_cmd} takes exactly two arguments ({len(cmd_body_parts)} given)')
                    glyph_references.append(cmd_body_parts)
                elif glyph_cmd == 'add_extrema':
                    glyph_add_extrema = True
                elif glyph_cmd == 'add_inflections':
                    glyph_add_inflections = True
                elif glyph_cmd == 'round':
                    glyph_round = True
                elif glyph_cmd == 'auto_hint':
                    glyph_auto_hint = True
                elif glyph_cmd == 'auto_instruct':
                    glyph_auto_instruct = True
                elif glyph_cmd in ['add_horizontal_hint', 'add_vertical_hint', 'add_diagonal_hint']:
                    glyph_hints.append([glyph_cmd[4:-5]] + cmd_body_parts)
                elif glyph_cmd[:17] in 'add_math_kerning_':
                    glyph_math_kernings[glyph_cmd[17:]].append(cmd_body_parts)
                elif glyph_cmd in ['replaced_by', 'replacement_of']:
                    if len(cmd_body_parts) != 2:
                        raise TypeError(f'{self.input_options.extension_glyph_macro_prefix}_{glyph_cmd} takes exactly two arguments ({len(cmd_body_parts)} given)')
                    # cmd_body_parts is [other_glyph_name, ot_feature]
                    cmd_body_parts = [p[1:-1] if p[0] == '"' else p for p in cmd_body_parts] # remove "
                    replacement = cmd_body_parts + [None] # None will be replaced by current glyph's name
                    if glyph_cmd == 'replaced_by':
                        replacement.reverse() # current glyph always first
                    glyph_replacements.append(replacement)

            elif cmd_name[:9] == 'ligature_':
                ligature_command = cmd_name[9:]
                cmd_body_parts = self.cmd_body.split('>> ')
                if ligature_command == 'components':
                    components = [c[1:-1] if c[0] == '"' else round(float(c)) for c in cmd_body_parts]
                    sub_list.append([None, ' :=   ', components, current_ligtable_to_feature['lig']])
                elif ligature_command == 'carets':
                    carets = [int(c) for c in cmd_body_parts]

            elif cmd_name[:16] == 'ligtable_switch_':
                ligtable_op_type, ot_feature = cmd_name[16:].split('_to_')
                current_ligtable_to_feature[ligtable_op_type] = ot_feature

            elif cmd_name[:8] == 'outline_':
                outline_command = cmd_name[8:]
                cmd_body_parts = self.cmd_body.split('>> ')
                pic_name = cmd_body_parts[0][1:-1] # clip quotes
                cmd_body_parts = cmd_body_parts[1:]
                if outline_command == 'sort_canonical':
                    # Canonical methods are only available for glyph.
                    # Use self.proc_glyph font to apply sorting.
                    self.proc_glyph.layers[1] = self.pictures[pic_name]
                    self.proc_glyph.canonicalStart()
                    self.proc_glyph.canonicalContours()
                    self.pictures[pic_name] = self.proc_glyph.layers[1]
                elif outline_command == 'sort_dir':
                    dir_deg = float(cmd_body_parts[0])
                    ang_deg = dir_deg
                    # set first of each contour
                    best_dists = []
                    contours = list(self.pictures[pic_name])
                    for c in contours:
                        best_dist = None
                        best_i_p = None
                        for i_p, p in enumerate(c):
                            if not p.on_curve:
                                continue
                            # signed distance to origin measured in dir
                            dist = sin(ang_deg*pi/180)*p.x+cos(ang_deg*pi/180)*p.y
                            if best_dist is None:
                                best_dist = dist
                                best_i_p = i_p
                            elif (
                                dist < best_dist
                                or (dist == best_dist and abs(p.y) < abs(c[best_i_p].y))
                                or (dist == best_dist and abs(p.y) == abs(c[best_i_p].y) and p.x < c[best_i_p].x)
                            ):
                                best_dist = dist
                                best_i_p = i_p
                        if best_i_p is not None:
                            c.makeFirst(best_i_p)
                            best_dists.append(best_dist)
                    # sort contours
                    self.pictures[pic_name] = fontforge.layer()
                    for dist, c in sorted(zip(best_dists, contours), key=lambda x: x[0]):
                        self.pictures[pic_name] += c
                elif outline_command == 'point_name_by_coords':
                    coords, r, name = cmd_body_parts
                    coords = tuple(float(c) for c in coords[1:-1].split(',')) # clip ()
                    r = float(r)
                    name = name[1:-1] # clip ""
                    best_dist = None
                    best_i_c = None
                    best_i_p_oc = None
                    for i_c, c in enumerate(self.pictures[pic_name]):
                        i_p_oc = -1
                        for p in c:
                            if p.on_curve:
                                i_p_oc += 1
                            else:
                                continue
                            dist = sqrt((p.x-coords[0])**2+(p.y-coords[1])**2)
                            if dist > r:
                                continue # ignore
                            if best_dist is None or dist < best_dist:
                                best_dist = dist
                                best_i_c = i_c
                                best_i_p_oc = i_p_oc
                    if best_dist is None:
                        if not self.input_options.quiet:
                            print(f'! No point found at ({coords[0]},{coords[1]}) to name "{name}".')
                    else:
                        self.named_points[pic_name][name] = (best_i_c, best_i_p_oc)
                elif outline_command == 'point_name_by_index':
                    i_c, i_p_oc, name = cmd_body_parts
                    i_c = int(i_c, 10)
                    i_p_oc = int(i_p_oc, 10)
                    name = name[1:-1] # clip ""
                    if i_c < len(self.pictures[pic_name]) and i_p_oc < len(self.pictures[pic_name][i_c]):
                        self.named_points[pic_name][name] = (i_c, i_p_oc)
                    elif not self.input_options.quiet:
                        print(f'! No point found on contour {i_c} at index {i_p_oc} to name "{name}".')
                elif outline_command == 'point_make_first':
                    name = cmd_body_parts[0]
                    name = name[1:-1] # clip ""
                    if name in self.named_points[pic_name]:
                        i_c, i_p_oc = self.named_points[pic_name][name]
                        try:
                            # find i_p for i_p_oc
                            for i_p, p in enumerate(self.pictures[pic_name][i_c]):
                                if not p.on_curve:
                                    continue
                                i_p_oc -= 1
                                if i_p_oc == -1:
                                    break
                            self.pictures[pic_name][i_c].makeFirst(i_p)
                        except IndexError:
                            if not self.input_options.quiet:
                                print(f'! Point "{name}" cannot be found.')
                    elif not self.input_options.quiet:
                        print(f'! No point named "{name}".')
                elif outline_command == 'point_make_first_contour':
                    name = cmd_body_parts[0]
                    name = name[1:-1] # clip ""
                    if name in self.named_points[pic_name]:
                        i_c = self.named_points[pic_name][name][0]
                        try:
                            l = self.pictures[pic_name]
                            self.pictures[pic_name] = fontforge.layer()
                            self.pictures[pic_name] += l[i_c]
                            for c in l:
                                if c != l[i_c]:
                                    self.pictures[pic_name] += l[i_c]
                        except IndexError:
                            if not self.input_options.quiet:
                                print(f'! Contour of point "{name}" cannot be found.')
                    elif not self.input_options.quiet:
                        print(f'! No point named {name}.')
                elif outline_command == 'point_delete':
                    name = cmd_body_parts[0]
                    name = name[1:-1] # clip ""
                    if name in self.named_points[pic_name]:
                        i_c, i_p_oc = self.named_points[pic_name][name]
                        try:
                            # find i_p for i_p_oc
                            for i_p, p in enumerate(self.pictures[pic_name][i_c]):
                                if not p.on_curve:
                                    continue
                                i_p_oc -= 1
                                if i_p_oc == -1:
                                    break
                            self.pictures[pic_name][i_c].merge(i_p)
                        except IndexError:
                            if not self.input_options.quiet:
                                print(f'! Point "{name}" cannot be found.')
                    elif not self.input_options.quiet:
                        print(f'! No point named "{name}".')
                elif outline_command == 'point_delete_contour':
                    name = cmd_body_parts[0]
                    name = name[1:-1] # clip ""
                    if name in self.named_points[pic_name]:
                        i_c = self.named_points[pic_name][name][0]
                        try:
                            del self.pictures[pic_name][i_c]
                        except IndexError:
                            if not self.input_options.quiet:
                                print(f'! Point "{name}" cannot be found.')
                    elif not self.input_options.quiet:
                        print(f'! No point named "{name}".')

            else:
                print('! "' + cmd_name + '": ' + self.cmd_body + '?')
                print('  This may be a syntax error. Run file with METAFONT to find it.')
                print('  If the input is correct, consider reporting a bug.')
            i += 1

        # all commands processed, but for some commands post processing is needed
        for sub in sub_list:
            lig = sub[0][0] if sub[0][1] else self.to_glyph_name(sub[0][0]) # sub[0][1]: is_glyph_name
            lig_type = sub[1]
            char1 = self.to_glyph_name(sub[2][0])
            char2 = self.to_glyph_name(sub[2][1])
            if lig_type[0] == ' ' and lig_type[3] == ' ':
                ot_feature = sub[3]
                lookup_type = 'gsub_ligature'
                lookup_name = lookup_type + '_' + ot_feature
                subtable_name = lookup_name + '_subtable'
                if self.input_options.index is not None:
                    subtable_name += f'_{self.input_options.index}'
                if lookup_name not in self.font.gsub_lookups:
                    self.font.addLookup(lookup_name, lookup_type, (), ((ot_feature, self.input_options.scripts),))
                if subtable_name not in self.font.getLookupSubtables(lookup_name):
                    self.font.addLookupSubtable(lookup_name, subtable_name)
                if len(sub[2]) > 2:
                    # ligature extension enables more than 2 components
                    components = tuple(self.to_glyph_name(c) for c in sub[2])
                else:
                    components = (char1, char2)
                # Try to create the ligature. FontForge will raise a TypeError,
                # if one of the characters is unknown. In that case, print a
                # warning and continue
                try:
                    self.font[lig].addPosSub(subtable_name, components)
                except TypeError as e:
                    print('! Error while adding ligature:', e, '(either '+repr(char1)+' or '+repr(char2)+' is unknown) Ignored.')
            elif lig_type[0] == '|' and lig_type[3] == ' ':
                lookup_type = 'gsub_single'
                lookup_name = lookup_type + '_after_' + char1
                subtable_name = lookup_name + '_subtable'
                if self.input_options.index is not None:
                    subtable_name += f'_{self.input_options.index}'
                if lookup_name not in self.font.gsub_lookups:
                    self.font.addLookup(lookup_name, lookup_type, (), ())
                if subtable_name not in self.font.getLookupSubtables(lookup_name):
                    self.font.addLookupSubtable(lookup_name, subtable_name)
                self.font[char2].addPosSub(subtable_name, lig)
                if 'gsub_contextchain' not in self.font.gsub_lookups:
                    self.font.addLookup('gsub_contextchain', 'gsub_contextchain', (), (('calt', self.input_options.scripts),))
                contextchain_subtable_name = 'gsub_contextchain_subtable_' + char1 + '_' + char2
                self.font.addContextualSubtable(
                    'gsub_contextchain', contextchain_subtable_name, 'glyph',
                    char1 + ' | ' + char2 + ' @<' + lookup_name + '> |'
                )
            elif lig_type[0] == ' ' and lig_type[3] == '|':
                lookup_type = 'gsub_single'
                lookup_name = lookup_type + '_before_' + char2
                subtable_name = lookup_name + '_subtable'
                if self.input_options.index is not None:
                    subtable_name += f'_{self.input_options.index}'
                if lookup_name not in self.font.gsub_lookups:
                    self.font.addLookup(lookup_name, lookup_type, (), ())
                if subtable_name not in self.font.getLookupSubtables(lookup_name):
                    self.font.addLookupSubtable(lookup_name, subtable_name)
                self.font[char1].addPosSub(subtable_name, lig)
                if 'gsub_contextchain' not in self.font.gsub_lookups:
                    self.font.addLookup('gsub_contextchain', 'gsub_contextchain', (), (('calt', self.input_options.scripts),))
                contextchain_subtable_name = 'gsub_contextchain_subtable_' + char1 + '_' + char2
                self.font.addContextualSubtable(
                    'gsub_contextchain', contextchain_subtable_name, 'glyph',
                    '| ' + char1 + ' @<' + lookup_name + '> | ' + char2
                )
            elif lig_type[0] == '|' and lig_type[3] == '|':
                lookup_type = 'gsub_multiple'
                lookup_name = lookup_type + '_between_' + char1
                subtable_name = lookup_name + '_' + char2 + '_subtable'
                if self.input_options.index is not None:
                    subtable_name += f'_{self.input_options.index}'
                if lookup_name + '_' + char2 not in self.font.gsub_lookups:
                    self.font.addLookup(lookup_name + '_' + char2, lookup_type, (), ())
                if subtable_name not in self.font.getLookupSubtables(lookup_name + '_' + char2):
                    self.font.addLookupSubtable(lookup_name + '_' + char2, subtable_name)
                self.font[char2].addPosSub(subtable_name, (lig, char2))
                if 'gsub_contextchain' not in self.font.gsub_lookups:
                    self.font.addLookup('gsub_contextchain', 'gsub_contextchain', (), (('calt', self.input_options.scripts),))
                contextchain_subtable_name = 'gsub_contextchain_subtable_' + char1 + '_' + char2
                self.font.addContextualSubtable(
                    'gsub_contextchain', contextchain_subtable_name, 'glyph',
                    char1 + ' | ' + char2 + ' @<' + lookup_name + '_' + char2 + '> |'
                )

        if self.input_options.set_top_accent:
            skewchar = self.input_options.skewchar
            if skewchar < 0:
                skewchar = None
                if self.input_options.input_encoding is not None:
                    if self.input_options.input_encoding.lower().replace(' ', '-') == 'tex-math-italic':
                        skewchar = 127
                    elif self.input_options.input_encoding.lower().replace(' ', '-') == 'tex-math-symbols':
                        skewchar = 48
            if skewchar is not None:
                # extract all skewchar kerning pairs
                skewchar_kerns = [
                    [ # TODO always int / code point in pos_list
                        pos[0][0] if isinstance(pos[0][0], int) else ord(pos[0][0]),
                        pos[1]
                    ] for pos in pos_list if pos[0][1] == skewchar
                ]
                # remove skewchar kerning pairs in pos_list
                pos_list = [pos for pos in pos_list if pos[0][1] != skewchar]

                # set topaccent with the kerning of skewchar
                for skewchar_kern in skewchar_kerns:
                    if (
                        not self.input_options.extension_glyph
                        or (self.input_options.extension_glyph and self.font[skewchar_kern[0]].glyphname not in specified_top_accents)
                    ):
                        wx = self.font[skewchar_kern[0]].width + self.font[skewchar_kern[0]].italicCorrection
                        s = skewchar_kern[1] # kern value of glyph skewchar_kern[0] and glyph skewchar
                        self.font[skewchar_kern[0]].topaccent = round(wx/2 + s)

        if len(pos_list) > 0:
            if self.input_options.kerning_classes:
                leftGlyphs = kerning_list['left-glyphs']
                rightGlyphs = kerning_list['right-glyphs']
                offsets = kerning_list['offsets']
                for pos in pos_list:
                    lChar = self.to_glyph_name(pos[0][0])
                    rChar = self.to_glyph_name(pos[0][1])
                    offset = pos[1]
                    if lChar in leftGlyphs:
                        idxL = leftGlyphs.index(lChar)
                    else:
                        leftGlyphs.append(lChar)
                        if len(offsets) > 0:
                            offsets.append([0]*len(offsets[-1]))
                        else:
                            offsets.append([])
                        idxL = len(leftGlyphs)-1
                    if rChar in rightGlyphs:
                        idxR = rightGlyphs.index(rChar)
                    else:
                        rightGlyphs.append(rChar)
                        idxR = len(rightGlyphs)-1
                        for i_offset in range(len(offsets)):
                            offsets[i_offset].append(0)
                    offsets[idxL][idxR] = offset
                    # combination of glyphs to classes will be done at the end
            else:
                # kerning pairs
                lookup_type = 'gpos_pair'
                subtable_name = lookup_type + '_subtable'
                if self.input_options.index is not None:
                    subtable_name += f'_{self.input_options.index}'
                if lookup_type not in self.font.gpos_lookups:
                    self.font.addLookup(lookup_type, lookup_type, (), (('kern', self.input_options.scripts),))
                if subtable_name not in self.font.getLookupSubtables(lookup_type):
                    self.font.addLookupSubtable(lookup_type, subtable_name)
                for pos in pos_list:
                    char1 = self.to_glyph_name(pos[0][0])
                    char2 = self.to_glyph_name(pos[0][1])
                    kern = pos[1]
                    try:
                        self.font[char1].addPosSub(subtable_name, char2, 0, 0, kern, 0, 0, 0, 0, 0)
                    except TypeError as e:
                        print('! Error while adding kerning pair:', e, '(either '+repr(char1)+' or '+repr(char2)+' is unknown) Ignored.')

        if self.input_options.kerning_classes and len(kerning_list['offsets']) > 0:
            # make every glyph a class
            leftClasses = [[glyph_name] for glyph_name in kerning_list['left-glyphs']]
            rightClasses = [[glyph_name] for glyph_name in kerning_list['right-glyphs']]
            offsets = kerning_list['offsets']

            # remove duplicate rows
            i = 0
            while i < len(offsets)-1: # -1: last row has no following rows to check
                ii = i+1
                while ii < len(offsets):
                    if offsets[i] == offsets[ii]:
                        leftClasses[i].extend(leftClasses[ii])
                        del leftClasses[ii]
                        del offsets[ii]
                    else:
                        ii += 1
                i += 1

            # remove duplicate columns
            j = 0
            while j < len(offsets[0])-1: # -1: last column has no following columns to check
                jj = j+1
                while jj < len(offsets[0]):
                    if all([offsets[i1][j] == offsets[i1][jj] for i1 in range(len(offsets))]):
                        rightClasses[j].extend(rightClasses[jj])
                        del rightClasses[jj]
                        for i in range(len(offsets)):
                            del offsets[i][jj]
                    else:
                        jj += 1
                j += 1

            # finally pass to FontForge\
            # The fist right class is replaced by None (GUI: {Everything Else} /
            # {All}) by FontForge. Add None class to prevent overwriting first
            # right class.
            rightClasses = [None]+rightClasses
            offsets = [[0]+row for row in offsets]
            offset_flattened = [offset for row in offsets for offset in row]
            lookup_type = 'gpos_pair'
            subtable_name = 'gpos_pair_subtable'
            if lookup_type not in self.font.gpos_lookups:
                self.font.addLookup(lookup_type, lookup_type, (), (('kern', self.input_options.scripts),))
            if self.input_options.index is not None:
                subtable_name += f'_{self.input_options.index}'
            self.font.addKerningClass(lookup_type, subtable_name, leftClasses, rightClasses, offset_flattened)

        for base_glyph, charlist in charlist_list:
            charlist = [self.to_glyph_name(c) for c in charlist]
            vertical_variants_str = ' '.join(charlist)
            base_glyph_name = self.to_glyph_name(base_glyph)
            base_glyph = self.font[base_glyph_name]
            base_glyph.verticalVariants = vertical_variants_str

        base_glyph_names_of_variants = {self.to_glyph_name(v): self.to_glyph_name(bg) for v, bg in base_glyphs_of_variants.items()}
        for label_glyph, vertical_components in extensible_list:
            # The label glyph can be the last glyph in a character list. In
            # this case, it defines the expandable of the base glyph of the
            # character list.
            
            label_glyph_name = self.to_glyph_name(label_glyph)
            
            if label_glyph_name in base_glyph_names_of_variants: # base is only known in MF when label of extensible is part of a charlist
                base_glyph_name = base_glyph_names_of_variants[label_glyph_name]
                # remove label glyph from charlist
                label_glyph_charlist_index = [i for i, cl in enumerate(charlist_list) if self.to_glyph_name(cl[0])==base_glyph_name][0]
                charlist = charlist_list[label_glyph_charlist_index][1]
                assert label_glyph_name == self.to_glyph_name(charlist[-1])
                charlist_list[label_glyph_charlist_index] = (charlist_list[label_glyph_charlist_index][0], charlist[:-1])
            else:
                base_glyph_name = label_glyph_name
            base_glyph = self.font[base_glyph_name]
            vertical_components = [[self.to_glyph_name(vc[0])] + vc[1:] for vc in vertical_components]
            base_glyph.verticalComponents = (
                tuple([vc[0], vc[1]] + [self.font[vc[0]].texdepth if p == 'texdepth' else p for p in vc[2:]])
                for vc in vertical_components
            )

        if self.input_options.extension_font:
            if self.font_add_extrema:
                self.font.selection.all()
                self.font.addExtrema()
            if self.font_add_inflections:
                self.font.selection.all()
                self.font.addInflections()
            if self.font_round:
                self.font.selection.all()
                self.font.round()
            if self.font_auto_hint:
                self.font.selection.all()
                self.font.autoHint()
            if self.font_auto_instruct:
                self.font.selection.all()
                self.font.autoInstr()

        if self.input_options.extension_glyph:
            for glyph_name, reference_name, reference_ps_matrix in self.glyph_references:
                self.font[glyph_name].addReference(reference_name, reference_ps_matrix)

        for glyph_name, ot_feature, replacement_glyph_name in self.glyph_replacements:
            lookup_type = 'gsub_single'
            lookup_name = lookup_type + '_' + ot_feature
            subtable_name = lookup_name + '_subtable'
            if lookup_name not in self.font.gsub_lookups:
                self.font.addLookup(lookup_name, lookup_type, (), ((ot_feature, self.input_options.scripts),))
                self.font.addLookupSubtable(lookup_name, subtable_name)
            try:
                self.font[glyph_name].addPosSub(subtable_name, replacement_glyph_name)
            except TypeError:
                # something went wrong, most likely ot-sub-feature option
                # enabled and different encoding.
                print(f'! Glyph {glyph_name} doesn\'t exist while adding {lookup_type} replacement. Ignored.')

    def apply_font_options_and_save(self):
        '''apply self.options to self.font and generate font file
        '''
        # rescale to match UPM
        if self.options.upm is not None:
            self.font.em = self.options.upm

        if self.options.set_math_defaults:
            self.set_default_math_constants()

        if self.options.quadratic:
            for layer_name in self.font.layers:
                self.font.layers[layer_name].is_quadratic = True

        if self.options.extrema:
            self.font.selection.all()
            self.font.addExtrema()

        if self.options.round:
            self.font.selection.all()
            self.font.round()

        if self.options.hint:
            self.font.selection.all()
            self.font.autoHint()
            self.font.autoInstr()

        if self.options.output_encoding is not None:
            self.reencode(self.options.output_encoding, self.options.output_encoding_options)

        output_path = self.options.output_directory / self.options.jobname
        if self.options.sfd:
            file_path = str(output_path) + '.sfd'
            self.font.save(file_path)
            if not self.input_options.quiet:
                print('Saved:', file_path)
        if self.options.otf:
            file_path = str(output_path) + '.otf'
            self.font.generate(file_path)
            if not self.input_options.quiet:
                print('Generated:', file_path)
        if self.options.ttf:
            file_path = str(output_path) + '.ttf'
            self.font.generate(file_path, flags='opentype')
            if not self.input_options.quiet:
                print('Generated:', file_path)


    def check_scripts(self, scripts):
        '''checks if scripts has the correct structure

        Args:
            scripts (any): variable to check for correct structure

        Returns:
            bool: whether scripts has the correct structure
        '''
        if not isinstance(scripts, tuple):
            return False

        for item in scripts:
            if (not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not isinstance(item[0], tuple)
            ):
                return False
            for element in item[1]:
                if not isinstance(element, str):
                    return False

    def define_patterns(self):
        M = self.MARKER
        # all command names which are written into the log file, g means >
        # (greater), p means | (pipe) # TODO explain why replacement is needed
        self.command_pattern = re.compile(M+
            r'('
                r'addto|also|contour|doublepath|turningcheck|turningnumber|withpen|withweight'
                r'|rotated|scaled|shifted|slanted|xscaled|yscaled'
                r'|cull|keeping|dropping'
                r'|picture|pic_eqn|pic|as|eq|mi|pl'
                r'|shipout'
                r'|ligtable|:|::|pp:|kern|=:|p=:|p=:g|=:p|=:pg|p=:p|p=:pg|p=:pgg|skipto'
                r'|fontdimen|charlist|extensible|end'
                +(
                    r'|ASCII'
                    if self.input_options.charcode_from_last_ASCII_hex_arg else r''
                )
                +(
                    r'|'+self.input_options.extension_attachment_points_macro_prefix+r'_(?:mark_(?:base|mark)|mkmk_(?:basemark|mark))'
                    if self.input_options.extension_attachment_points else r''
                )
                +(
                    r'|font_(?:'
                        r'name|family_name|full_name'
                        r'|weight|version|copyright|comment|fontlog'
                        r'|ascent|descent|cap_height'
                        r'|underline_(?:position|width)'
                        r'|add_(?:extrema|inflections)|auto_(?:hint|instruct)'
                        r'|math_constant|postscript_private_dictionary'
                    r')'
                    if self.input_options.extension_font else r''
                )
                +(
                    r'|glyph_(?:'
                        r'name|unicode|comment|top_accent|build|add_reference'
                        r'|add_(?:extrema|inflections)|auto_(?:hint|instruct)'
                        r'|add_(?:(?:horizontal|vertical|diagonal)_hint|math_kerning_(?:top|bottom)_(?:right|left))'
                        r'|replaced_by|replacement_of'
                    r')'
                    if self.input_options.extension_glyph else r''
                )
                +(
                    r'|ligature_(?:components|carets)'
                    if self.input_options.extension_ligature else r''
                )
                +(
                    r'|'+r'|'.join(
                        r'ligtable_switch_' + ligtable_op_type + r'_to_' + ligtable_ot_feature
                        for ligtable_op_type in self.supported_ligtable_ot_features
                        for ligtable_ot_feature in self.supported_ligtable_ot_features[ligtable_op_type]
                    ) if self.input_options.extension_ligtable_switch else r''
                )
                +(
                    r'|outline_(?:'
                        r'sort_(?:canonical|dir)'
                        r'|point_(?:'
                            r'name_by_(?:coords|index)'
                            r'|make_first(?:_contour)?'
                            r'|delete(?:_contour)?'
                        r')'
                    r')'
                    if self.input_options.extension_outline else r''
                )
                +
            r')'
            r'(?:>> (?:(?:Path|Pen polygon) at line (\d+):)?(.*?))?'+M, re.DOTALL)
        # The begin of every message to the log file (also part of the above
        # pattern), used to split up multiple pieces of information written to
        # the log file by a single command.
        self.split_pattern = re.compile(r'>> (?:(?:Path|Pen polygon) at line \d+:)?')
        # patterns for pair and join, join always follows a pair of a join
        self.pair_pattern = re.compile(r'\((.*?),(.*?)\)')
        self.join_pattern = re.compile(r'\.\.controls \((.*?),(.*?)\) and \((.*?),(.*?)\) \.\.(?:\((.*?),(.*?)\)|(cycle))')
        # all information given at the shipout of a character.
        self.shipout_pattern = re.compile(r'(.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)$')
        # all information in a metafont error
        self.error_pattern = re.compile(r'^! (?:.|\n)*?^l.(?:.|\n)*?\n\n', re.MULTILINE)
        # extension: attachment_point
        self.attachment_point_pattern = re.compile(r'(.*?)>> (.*?)>> (.*?)$')

    def get_redefinitions(self):
        '''return mf code containing redefinitions needed for mf2ff

        Returns:
            str: mf code
        '''
        # abbreviations for inserting log file markers for redefined tokens
        M = self.MARKER
        m_ = 'message"'+M # begin redefined token, followed by token name or identifier
        m__ = m_+'";'     # end of redefined token, possibly preceded by an expression
        mm_ = m__+m_      # end of redefined token and begin of new redefined token
        return (
            'if unknown __mfIIvec__:boolean __mfIIvec__;__mfIIvec__:=true;fi '
            # First, some mf primitives are saved, so they are accessible even
            # after redefining them or loading a different base file.
            'let __mfIIvec__orig_colon__= :;'
            'let __mfIIvec__orig_else__=else;'
            'let __mfIIvec__orig_elseif__=elseif;'
            'let __mfIIvec__orig_end__=end;'
            'let __mfIIvec__orig_eq__= =;'
            'let __mfIIvec__orig_for__=for;'
            'let __mfIIvec__orig_forever__=forever;'
            'let __mfIIvec__orig_forsuffixes__=forsuffixes;'
            'let __mfIIvec__orig_if__=if;'
            'let __mfIIvec__orig_pen__=pen;'
            'let __mfIIvec__orig_picture__=picture;'
            'let __mfIIvec__orig_hide__=hide;'

            # Numerical equations should still be processed in mf to get the
            # correct results. This is different for picture equations. They
            # need to be evaluated in fontforge using boolean operations. To
            # keep track of the type of equation, a boolean is used.
            'boolean __mfIIvec__pic_eqn__;__mfIIvec__pic_eqn__:=false;'

            ## redefinitions
            # All redefinitions use the undelimited parameter text t, therefor
            # all tokens of this command until the next semicolon (;) are
            # processed according to the redefinition. This makes sure that the
            # whole variable names are written to the log file and e.g. numeric
            # expressions in the subscript are evaluated before writing it to
            # the log file.

            ## colon (:)
            # Since the if and for statements can be everywhere and they are
            # using the colon too, it has to be redefined inside every if,
            # elseif, else, for, forever and forsuffixes. The following
            # subroutine should be called in a group when redefining statements
            # that can contain colons which should be redefined, e.g. the colons
            # in a ligtable or fontdimen statement. The subroutine should be
            # called before evaluating the content of the statement so the colon
            # definition changes to it original meaning if there is a if, for,
            # etc. in the statement and back after the colon
            'def __mfIIvec__redef_colon__='
                # The following colon definition is made for being used when
                # waiting for a colon a) separating boolean expression and
                # conditional text (in if or elseif), b) after else or c)
                # separating a loop header and loop text (in for, forsuffixes,
                # forever) where the condition or the loop is inside a statement
                # that needs to be redefined to write the statement to the log
                # file but the colon is also used by that statement so it needs
                # to be redefined as well, e.g. ligtable and fontdimen
                # statements. Inside of __mfIIvec__special_colon__, the
                # definition of the colon is switched back to
                # __mfIIvec__other_colon__ which should be defined to add a
                # message to the the log file that there was a colon.
                'def __mfIIvec__special_colon__='
                    '__mfIIvec__orig_hide__(let: =__mfIIvec__other_colon__;)'
                    '__mfIIvec__orig_colon__ '
                'enddef;'
                # The following sparks are redefined by this subroutine to
                # activate the __mfIIvec__special_colon__ (which deactivates
                # itself).
                'save if,elseif,else,for,forsuffixes,forever;'
                'def if='
                    '__mfIIvec__orig_if__ '
                    '__mfIIvec__orig_hide__(let: =__mfIIvec__special_colon__;)'
                'enddef;'
                'def elseif='
                    '__mfIIvec__orig_elseif__ '
                    '__mfIIvec__orig_hide__(let: =__mfIIvec__special_colon__;)'
                'enddef;'
                'def else='
                    '__mfIIvec__orig_else__ '
                    '__mfIIvec__orig_hide__(let: =__mfIIvec__special_colon__;)'
                'enddef;'
                'def for='
                    '__mfIIvec__orig_for__ '
                    '__mfIIvec__orig_hide__(let: =__mfIIvec__special_colon__;)'
                'enddef;'
                'def forsuffixes='
                    '__mfIIvec__orig_forsuffixes__ '
                    '__mfIIvec__orig_hide__(let: =__mfIIvec__special_colon__;)'
                'enddef;'
                'def forever='
                    '__mfIIvec__orig_forever__ '
                    '__mfIIvec__orig_hide__(let: =__mfIIvec__special_colon__;)'
                'enddef;'
                # In ligtable and fontdimen every colon should match the message
                # generating __mfIIvec__other_colon__ if they are not part of
                # the condition or loop structure itself.
                'let: =__mfIIvec__other_colon__;'
            'enddef;'

            ## addto
            # doublepath: "If p is not a cyclic path, this case reduces to the
            # second case, with p replaced by the doubled-up path `p & reverse p
            # & cycle' (unless p consists of only a single point, when the new
            # path is simply `p .. cycle'). On the other hand if p is a cyclic
            # path, this case reduces to two addto commands of the second type,
            # in one of which p is reversed." (The METAFONTbook, p. 119)
            'def addto text t='+m_+'addto";begingroup '
                'save also,contour,doublepath,withpen,withweight;'
                # Since also does accept a picture expression, transformers of
                # pictures need support. Use own group so transformers are not
                # redefined for paths after contour/doublepath. Group needs to
                # be closed at the end of addto command (but only for also),
                # so use a boolean.
                'boolean __mfIIvec__inside_addto_also__;__mfIIvec__inside_addto_also__:=false;'
                'def also=;'+mm_+'also";begingroup __mfIIvec__inside_addto_also__:=true;'
                    # transformer 'transformed <transform primary>' and 'zscaled <pair primary>' not supported
                    'save rotated,scaled,shifted,slanted,xscaled,yscaled;'
                    +(''.join([
                        f'def {c} primary p=;'+mm_+f'{c}";show p enddef;'
                        for c in ['rotated', 'scaled', 'shifted', 'slanted', 'xscaled', 'yscaled']
                    ]))+
                    'show str enddef;'
                'def contour expr p=;'   +mm_+'turningcheck";'  'show turningcheck;'
                                         +mm_+'turningnumber";' 'show turningnumber p;'
                                         +mm_+'contour";'       'show p enddef;'
                'def doublepath expr p=;'+mm_+'turningcheck";'  'show turningcheck;'
                                         +mm_+'turningnumber";' 'show turningnumber p;'
                                         +mm_+'doublepath";'    'show p enddef;'
                'def withpen=;'          +mm_+'withpen";'       'show enddef;'
                'def withweight=;'       +mm_+'withweight";'    'show enddef;'
                'show str t;if __mfIIvec__inside_addto_also__:endgroup fi endgroup;'+m__+
            'enddef;'

            ## cull
            'def cull text t='+m_+'cull";begingroup '
                'save keeping,dropping,withweight;'
                'def keeping=;'   +mm_+'keeping";'    'show enddef;'
                'def dropping=;'  +mm_+'dropping";'   'show enddef;'
                'def withweight=;'+mm_+'withweight";' 'show enddef;'
                'show str t;endgroup;'+m__+
            'enddef;'

            ## picture
            # Variables of type picture are the only ones which operations are
            # not processed by mf but outsourced to FontForge. Every time new
            # variables of type picture are declared, the declarations are sent
            # to FontForge by `show`ing the names of the variables to the log
            # file. Furthermore, the names of the variables are converted into
            # definitions: Every time the name of the variable name is
            # processed, its name should show up in the log file. Due to the
            # fact that mf processes picture expressions with the same
            # operators as in other expression types and these picture
            # operations needs to be sent to the log file, all operators only
            # need to be redefined inside picture equations. The operations
            # which can occur in a picture equation are := = - + (see
            # METAFONTbook, pp. 115 and 214)
            'def picture text t='+m_+'picture";'
                'forsuffixes p=t:'
                    'show str p;'
                    'vardef p text tt='
                        'if __mfIIvec__pic_eqn__:'
                            +mm_+'pic";show str p;'
                        'else:'
                            +m_+'pic_eqn";__mfIIvec__pic_eqn__:=true;begingroup '
                                'save=,:=,+,-;'
                                'def:=__mfIIvec__orig_eq__;'+mm_+'as";enddef;'
                                'def=__mfIIvec__orig_eq__;'+mm_+'eq";enddef;'
                                'def-__mfIIvec__orig_eq__;'+mm_+'mi";enddef;'
                                'def+__mfIIvec__orig_eq__;'+mm_+'pl";enddef;'
                            'show str p tt;endgroup;'
                            'boolean __mfIIvec__pic_eqn__;__mfIIvec__pic_eqn__:=false;'+m__+
                        'fi '
                    'enddef;'
                'endfor;'+m__+
            'enddef;'
            # TODO is boolean __mfIIvec__pic_eqn__; required here?
            # TODO What about totalweight?
            # TODO What about parenthesis and begingroup...endgroup (with statement list)

            # shipout\
            # - "There are four internal quantities called charwd, charht,
            #   chardp, and charic, whose values at the time of every shipout
            #   command are assumed to be the box dimensions for the character
            #   being shipped out, in units of printer's points. [...] Besides
            #   charwd and its cousins, METAFONT also has four other internal
            #   variables whose values are recorded at the time of every
            #   shipout: charcode [...] charext [...] chardx and chardy [...]."
            #   (The METAFONTbook, p. 106)
            # - "‘shipout v’ puts the pixels of positive weight, as defined by
            #   the picture expression v, into a generic font output file" (The
            #   METAFONTbook, p. 220) This is equivalent to cull currentpicture
            #   keeping (1, infinity).\
            # TODO Why __mfIIvec__pic_eqn__ ?
            'def shipout text t='
                +('cull currentpicture dropping(-infinity,0);' if self.input_options.cull_at_shipout else '')
                +m_+'shipout";__mfIIvec__pic_eqn__:=true;'
                'show hppp,'
                    'charcode,charext,'
                    'charwd,charht,chardp,charic,'
                    'chardx,chardy,xoffset,yoffset;'
                't;__mfIIvec__pic_eqn__:=false;'
                +m__+
            'enddef;'

            ## ligtable
            # Since the ligtable uses the colon as a separator, while the colon
            # is also used in the structure of conditions and loops, it has to
            # be redefined during such a structure. __mfIIvec__other_colon__ is
            # used to be able to switch between both.
            'def ligtable text t='+m_+'ligtable";show hppp;begingroup '
                'save:,::,||:,kern,=:,|=:,|=:>,=:|,=:|>,|=:|,|=:|>,|=:|>>,skipto;'
                'def __mfIIvec__other_colon__=;'+mm_+':";show enddef;'
                'def'   ':: '   '=;'+mm_+'::";'     'show enddef;'
                'def' '||: '    '=' +mm_+'pp:";'    'show enddef;' # no ; required since there is no preceding expression whose show command needs to end before the message
                'def kern'      '=;'+mm_+'kern";'   'show enddef;'
                'def'  '=: '    '=;'+mm_+'=:";'     'show enddef;'
                'def' '|=: '    '=;'+mm_+'p=:";'    'show enddef;'
                'def' '|=:> '   '=;'+mm_+'p=:g";'   'show enddef;'
                'def'  '=:| '   '=;'+mm_+'=:p";'    'show enddef;'
                'def'  '=:|> '  '=;'+mm_+'=:pg";'   'show enddef;'
                'def' '|=:| '   '=;'+mm_+'p=:p";'   'show enddef;'
                'def' '|=:|> '  '=;'+mm_+'p=:pg";'  'show enddef;'
                'def' '|=:|>> ' '=;'+mm_+'p=:pgg";' 'show enddef;'
                # skipto is always preceded by a show command and a comma (,),
                # so a normal message can't follow. Therefor the message command
                # is hidden. After the comma, the code after the skipto command
                # will be shown by the previous show command.
                'def skipto=__mfIIvec__orig_hide__('+mm_+'skipto")enddef;'
                '__mfIIvec__redef_colon__ ' # restore colon before showing t
                'show t;endgroup;'+m__+
            'enddef;'

            # fontdimen, charlist and extensible command's syntax uses of colon
            # (:). Therefor some redefinitions are needed to be used in
            # combinations with e.g. the if statement
            +(
                ''.join(
                    'def '+cmd_name+' text t='+m_+cmd_name+'";'+('show hppp;' if cmd_name == 'fontdimen' else '')+'begingroup '
                        'save:;'
                        'def __mfIIvec__other_colon__ text tt=;'+mm_+':";show tt enddef;'
                        '__mfIIvec__redef_colon__ '
                        'show t endgroup;'+m__+
                    'enddef;'
                    for cmd_name in ['fontdimen', 'charlist', 'extensible']
                )
            )
            +

            # end should show the designsize: "METAFONT looks at the value of
            # designsize only when the job ends" (The METAFONTbook, p. 320)
            'def end='+m_+'end";show designsize;'+m__+'__mfIIvec__orig_end__ enddef;'

            # tricks and redefinitions\
            # The pen tracing of paths is done by FontForge which needs the
            # Bezier curve of the pen tip's shape. Hence, every pen should be a
            # path describing it's tip. The nullpen should be a very minimal
            # path. The pencircle should be the path of a fullcircle. Since
            # every pen is a path, penoffset needs to be redefined to
            # directionpoint and the definitions makepen and makepath are no
            # longer needed.\
            # Note that fullcirlce and directionpoint are defined in plain mf.
            'let pen=path;def nullpen=((0,0)..cycle)enddef;def pencircle=fullcircle enddef;'
            'def penoffset=directionpoint enddef;' # TODO explain
            'let makepen=relax;'
            'let makepath=relax;'
            # mf is run in background, so don't display anything.
            'def display text t=enddef;'
            # nullpicture should be a variables of type picture.
            'save nullpicture;picture nullpicture;'
            # The loading of plain.mf is preceded by some saves so there will be no errors.
            'save hide,blankpicture,unitpixel,pensquare,penrazor,mm,pt,dd,bp,cm,pc,cc,in,modesetup,mode_name,mode;'
            'input plain.mf;'

            # A special mode is defined, to prepare for vector font generation.
            'mode_def mfIIvec='
                'proofing:=0;' # don't make proofs
                'fontmaking:=0;' # mf itself should not make a font
                'tracingtitles:=0;' # no titles (e.g. "The letter O") in stdout
                'pixels_per_inch:=' + str(self.ppi) + ';'
                +('pixels_per_inch:=pixels_per_inch*' + str(self.ppi_factor) + ';' if self.input_options.use_ppi_factor else '')
                +
                'blacker:=0;' # no "special correction"
                'fillin:=0;' # no pixels that could influence their neighbors
                'o_correction:=1;' # no reduction in overshoot
            'enddef;'
            'mode:=mfIIvec;'

            ## ASCII
            # In order to support glyph encoding values above 4095 or even
            # above 32767, the argument is shown so mf2ff knows the original
            # value. The original ASCII operation is carried out to support use
            # cases like `ASCII"a" - ASCII"A"' or `ASCII"A"+i'.
            +(
                'let __mfIIvec__orig_ASCII__=ASCII;'
                'vardef ASCII primary s='+m_+'ASCII";'
                    'show s;'+m__+
                    '__mfIIvec__orig_ASCII__ s '
                'enddef;'
                if self.input_options.charcode_from_last_ASCII_hex_arg else ''
            )

            # extension\
            # attachment points\
            +(
                (
                    'def ' + self.input_options.extension_attachment_points_macro_prefix + '_mark_base(text t)='
                        +m_+'attachment_point_mark_base";'
                        'show t;'
                        +m__+
                    'enddef;'
                    'def ' + self.input_options.extension_attachment_points_macro_prefix + '_mark_mark(text t)='
                        +m_+'attachment_point_mark_mark";'
                        'show t;'
                        +m__+
                    'enddef;'
                    'def ' + self.input_options.extension_attachment_points_macro_prefix + '_mkmk_basemark(text t)='
                        +m_+'attachment_point_mkmk_basemark";'
                        'show t;'
                        +m__+
                    'enddef;'
                    'def ' + self.input_options.extension_attachment_points_macro_prefix + '_mkmk_mark(text t)='
                        +m_+'attachment_point_mkmk_mark";'
                        'show t;'
                        +m__+
                    'enddef;'
                ) if self.input_options.extension_attachment_points else ''
            )
            # font
            +(
                (
                    ''.join(
                        'def ' + self.input_options.extension_font_macro_prefix + '_' + font_cmd + '='
                            +m_+'font_'+ font_cmd +'";'+m__+
                        'enddef;'
                        for font_cmd in [
                            'add_extrema', 'add_inflections',
                            'auto_hint', 'auto_instruct',
                            'round'
                        ]
                    )
                    +''.join(
                        'def ' + self.input_options.extension_font_macro_prefix + '_' + font_cmd + ' expr e='
                            +m_+'font_'+ font_cmd +'";'
                            'show e;'
                            +m__+
                        'enddef;'
                        for font_cmd in [
                            'name', 'family_name', 'full_name',
                            'weight', 'version', 'copyright', 'comment', 'fontlog',
                        ]
                    )
                    +''.join(
                        'def ' + self.input_options.extension_font_macro_prefix + '_' + font_cmd + ' expr e='
                            +m_+'font_'+ font_cmd +'";'
                            'show hppp;'
                            'show e;'
                            +m__+
                        'enddef;'
                        for font_cmd in [
                            'ascent', 'descent', 'cap_height',
                            'underline_position', 'underline_width'
                        ]
                    )
                    +''.join(
                        'def ' + self.input_options.extension_font_macro_prefix + '_' + font_cmd + '(text t)='
                            +m_+'font_'+ font_cmd +'";'
                            'show t;'
                            +m__+
                        'enddef;'
                        for font_cmd in [
                            'math_constant', 'postscript_private_dictionary'
                        ]
                    )
                ) if self.input_options.extension_font else ''
            )
            # glyph
            +(
                (
                    ''.join(
                        'def ' + self.input_options.extension_glyph_macro_prefix + '_' + glyph_cmd + '='
                            +m_+'glyph_'+ glyph_cmd +'";'+m__+
                        'enddef;'
                        for glyph_cmd in [
                            'build',
                            'add_extrema', 'add_inflections',
                            'auto_hint', 'auto_instruct',
                            'round'
                        ]
                    )
                    +''.join(
                        'def ' + self.input_options.extension_glyph_macro_prefix + '_' + glyph_cmd + ' expr e='
                            +m_+'glyph_'+ glyph_cmd +'";'
                            'show e;'
                            +m__+
                        'enddef;'
                        for glyph_cmd in ['name', 'unicode', 'comment', 'top_accent']
                    )
                    +''.join(
                        'def ' + self.input_options.extension_glyph_macro_prefix + '_' + glyph_cmd + '(text t)='
                            +m_+'glyph_'+ glyph_cmd +'";'
                            'show t;'
                            +m__+
                        'enddef;'
                        for glyph_cmd in [
                            'add_reference',
                            'add_horizontal_hint', 'add_vertical_hint', 'add_diagonal_hint',
                            'add_math_kerning_top_right', 'add_math_kerning_top_left',
                            'add_math_kerning_bottom_right', 'add_math_kerning_bottom_left',
                            'replaced_by', 'replacement_of'
                        ]
                    )
                ) if self.input_options.extension_glyph else ''
            )
            # ligature
            +(
                (
                    ''.join(
                        'def ' + self.input_options.extension_ligature_macro_prefix + '_' + ligature_cmd + '(text t)='
                            +m_+'ligature_'+ ligature_cmd +'";'
                            'show t;'
                            +m__+
                        'enddef;'
                        for ligature_cmd in ['components', 'carets']
                    )
                ) if self.input_options.extension_ligature else ''
            )
            # ligtable switch
            +(
                (
                    ''.join(
                        'def ' + self.input_options.extension_ligtable_switch_macro_prefix + '_' + ligtable_op_type + '_to_' + ligtable_ot_feature + '='
                            +m_+'ligtable_switch_'+ ligtable_op_type + '_to_' + ligtable_ot_feature +'";'+m__+
                        'enddef;'
                        for ligtable_op_type in self.supported_ligtable_ot_features
                        for ligtable_ot_feature in self.supported_ligtable_ot_features[ligtable_op_type]
                    )
                ) if self.input_options.extension_ligtable_switch else ''
            )
            # outline
            +(
                (
                    ''.join(
                        'def ' + self.input_options.extension_outline_macro_prefix + '_' + outline_cmd + '(suffix pic)='
                            +m_+'outline_'+ outline_cmd +'";'
                            'show str pic;'
                            +m__+
                        'enddef;'
                        for outline_cmd in ['sort_canonical']
                    )
                    +''.join(
                        'def ' + self.input_options.extension_outline_macro_prefix + '_' + outline_cmd + '(suffix pic)(expr e)='
                            +m_+'outline_'+ outline_cmd +'";'
                            'show str pic,e;'
                            +m__+
                        'enddef;'
                        for outline_cmd in [
                            'sort_dir',
                            'point_make_first',
                            'point_make_first_contour',
                            'point_delete',
                            'point_delete_contour'
                        ]
                    )
                    +''.join(
                        'def ' + self.input_options.extension_outline_macro_prefix + '_' + outline_cmd + '(suffix pic)(expr e,f,g)='
                            +m_+'outline_'+ outline_cmd +'";'
                            'show str pic,e,f,g;'
                            +m__+
                        'enddef;'
                        for outline_cmd in [
                            'point_name_by_coords',
                            'point_name_by_index'
                        ]
                    )
                ) if self.input_options.extension_outline else ''
            )
        )

    def show_progress(self, start_time_ff, i):
        '''shows progress bar and ETA

        Args:
            start_time_ff (float): start time of fontforge from time.time()
            i (int): index of current command (0 based)
        '''
        if not self.options.quiet:
            num_cmds = len(self.cmds)
            # simple eta formula
            eta = (time()-start_time_ff)*(num_cmds-(i+1))/(i+1)
            # find appropriate unit
            # dot and extra space to separate from FontForge warnings
            if eta < 60:
                eta_unit = 's.   '
            elif eta < 60*60:
                eta_unit = 'min. '
                eta /= 60
            elif eta < 60*60*24:
                eta_unit = 'h.   '
                eta /= 60*60
            else:
                eta_unit = 'd.   '
                eta /= 60*60*24

            n = 10 # width of progress bar (max number of '=')
            sys.stdout.write(
                '\r[{:{n}}'.format('='*int(n*((i+1)/num_cmds)), n=n)
                + '] {:>3d}'.format(int(((i+1)/num_cmds)*100)) + '%, '
                + '{:>{len_cmds}d}'.format(i+1, len_cmds=len(str(num_cmds))) + '/{:d}'.format(num_cmds) + ', '
                + 'line ' + str(self.last_known_line) + ', '
                + 'ETA: {:6.3f}'.format(eta) + ' ' + eta_unit
            )
            sys.stdout.flush()

    def set_default_math_constants(self):
        '''Set OpenType MATH table constants to fontdimen values or TeX defaults.
        '''
        sigma = self.fontdimens['family2']
        xi = self.fontdimens['family3']
        if self.font.os2_capheight == 0:
            cap_height = self.font.ascent
        else:
            cap_height = self.font.os2_capheight
        math_default_values = {
            'UpperLimitBaselineRiseMin': xi[11],
            'UpperLimitGapMin': xi[9],
            'LowerLimitGapMin': xi[10],
            'LowerLimitBaselineDropMin': xi[12],
            'StretchStackTopShiftUp': xi[11],
            'StretchStackGapAboveMin': xi[9],
            'StretchStackGapBelowMin': xi[10],
            'StretchStackBottomShiftDown': xi[12],
            'OverbarExtraAscender': xi[8],
            'OverbarRuleThickness': xi[8],
            'OverbarVerticalGap': None if xi[8] is None else 3*xi[8],
            'UnderbarVerticalGap': None if xi[8] is None else 3*xi[8],
            'UnderbarRuleThickness': xi[8],
            'UnderbarExtraDescender': xi[8],
            'FractionNumeratorDisplayStyleShiftUp': sigma[8],
            'FractionNumeratorShiftUp': sigma[9],
            'FractionNumeratorDisplayStyleGapMin': None if xi[8] is None else 3*xi[8],
            'FractionNumeratorGapMin': xi[8],
            'FractionRuleThickness': xi[8],
            'FractionDenominatorDisplayStyleGapMin': None if xi[8] is None else 3*xi[8],
            'FractionDenominatorGapMin': xi[8],
            'FractionDenominatorDisplayStyleShiftDown': sigma[11],
            'FractionDenominatorShiftDown': sigma[12],
            'StackTopDisplayStyleShiftUp': sigma[8],
            'StackTopShiftUp': sigma[10],
            'StackDisplayStyleGapMin': None if xi[8] is None else 7*xi[8],
            'StackGapMin': None if xi[8] is None else 3*xi[8],
            'StackBottomDisplayStyleShiftDown': sigma[11],
            'StackBottomShiftDown': sigma[12],
            'SuperscriptShiftUp': sigma[13],
            'SuperscriptShiftUpCramped': sigma[15],
            'SubscriptShiftDown': sigma[16],
            'SuperscriptBaselineDropMax': sigma[18],
            'SubscriptBaselineDropMin': sigma[19],
            'SuperscriptBottomMin': None if sigma[5] is None else 1/4*sigma[5],
            'SubscriptTopMax': None if sigma[5] is None else 4/5*sigma[5],
            'SubSuperscriptGapMin': None if xi[8] is None else 4*xi[8],
            'SuperscriptBottomMaxWithSubscript': None if sigma[5] is None else 4/5*sigma[5],
            'SpaceAfterScript': 0.05*self.font.em,
            'RadicalExtraAscender': xi[8],
            'RadicalRuleThickness': xi[8],
            'RadicalDisplayStyleVerticalGap': None if xi[8] is None or sigma[5] is None else xi[8] + 1/4*sigma[5],
            'RadicalVerticalGap': None if xi[8] is None else xi[8] + 1/4*xi[8],
            'RadicalKernBeforeDegree': 5/18*self.font.em,
            'RadicalKernAfterDegree': 10/18*self.font.em,
            'RadicalDegreeBottomRaisePercent': 60,
            'ScriptPercentScaleDown': 70,
            'ScriptScriptPercentScaleDown': 50,
            'DisplayOperatorMinHeight': 1.4*self.font.em,
            'DelimitedSubFormulaMinHeight': sigma[21],
            'AxisHeight': sigma[22],
            'AccentBaseHeight': sigma[5],
            'FlattenedAccentBaseHeight': cap_height,
            'MathLeading': 3/18*self.font.em,
            'MinConnectorOverlap': 0,
        }
        for name, value in math_default_values.items():
            if name not in self.specified_math_constants and value is not None:
                self.font.math.__setattr__(name, round(value))

    def to_glyph_name(self, g):
        '''converts character or code point g to glyph name

        If the font_metric_command_generalized_code option is enabled, this method can also process hexadecimal (e.g. 0x0000), Unicode (e.g. U+0000) or glyph name input.

        If g is not a hex or Unicode string and is unknown as a glyph name, use first character of g and print a warning.

        Args:
            g (str or int): character or code point, (Unicode, hexadecimal or glyph name if font_metric_command_generalized_code option is enabled)

        Returns:
            string: FontForge glyph name
        '''
        if self.input_options.font_metric_command_generalized_code:
            if isinstance(g, str):
                g_str = g
                del g

                # check for Unicode and hex string
                if g_str[:2].lower() == 'u+':
                    g_str = fontforge.nameFromUnicode(int(g_str[2:], 16))
                    return g_str
                g_hex_str = g_str
                if g_hex_str[:2].lower() == '0x':
                    g_hex_str = g_hex_str[2:]
                if len(g_hex_str) in [4, 5]: # ae, ff, etc. are valid glyph names
                    try:
                        g_int = int(g_hex_str, 16)
                    except ValueError:
                        # continue below
                        pass
                    else:
                        g_str = self.font[g_int].glyphname
                        return g_str

                # no Unicode or hex string:\
                # Use g if it can be used to access the glyph. If not, try
                # fontforge.unicodeFromName and unicodedata.lookup. If not
                # found, use first character.
                try:
                    self.font[g_str]
                    # g_str is valid name
                    return g_str
                except TypeError:
                    if fontforge.unicodeFromName(g_str) != -1:
                        g_int = fontforge.unicodeFromName(g_str)
                    else:
                        try:
                            # convert name to Unicode character and back to
                            # Fontforge glyph name
                            g_int = unicodedata.decimal(unicodedata.lookup(g_str))
                        except KeyError:
                            if len(g_str) != 1:
                                print('! \'' + g_str + '´ is not a valid glyph name. \'' + g_str[0] + '´ is assumed.')
                                g_str = g_str[0]
                            g_int = ord(g_str)
            else:
                # if g is int, use name based on current encoding
                g_int = g
                del g
        else:
            # METAFONT's behavior
            if isinstance(g, str):
                g_int = ord(g[0])
            else:
                g_int = g
        # get glyph name for g_int code point (if g was a glyph name, the name
        # was already returned above)
        try:
            g_str = self.font[g_int].glyphname
        except TypeError:
            # TODO very naive fallback
            g_str = 'NameMe.' + str(g_int)
        return g_str

    def should_skip_glyph(self, glyph_code):
        if self.input_options.only_code_points is not None:
            skip_glyph = True
            for code_range in self.input_options.only_code_points:
                if len(code_range) == 1 and glyph_code == code_range[0]:
                    skip_glyph = False
                    break
                if code_range[0] <= glyph_code <= code_range[1]:
                    skip_glyph = False
                    break
            if skip_glyph:
                return True
        if self.input_options.ignore_code_points is not None:
            for code_range in self.input_options.ignore_code_points:
                if len(code_range) == 1 and glyph_code == code_range[0]:
                    return True
                if code_range[0] <= glyph_code <= code_range[1]:
                    return True
        return False

    def reencode(self, encoding_name, encoding_options=None):
        try:
            # font.reencode not in FontForge docs
            self.font.reencode(encoding_name)
        except NameError:
            encoding_name = encoding_name.lower().replace(' ', '-')
            if encoding_options is None:
                encoding_options = {}
            if encoding_name == 'tex-text':
                tex_encodings.load_tex_text(**encoding_options)
                encoding_name = 'TeX-text'
            elif encoding_name == 'tex-text-without-f-ligatures':
                tex_encodings.load_tex_text_without_f_ligatures(**encoding_options)
                encoding_name = 'TeX-text-without-f-ligatures'
            elif encoding_name == 'tex-typewriter-text':
                tex_encodings.load_tex_typewriter_text(**encoding_options)
                encoding_name = 'TeX-typewriter-text'
            elif encoding_name == 'tex-math-italic':
                tex_encodings.load_tex_math_italic(**encoding_options)
                encoding_name = 'TeX-math-italic'
            elif encoding_name == 'tex-math-symbols':
                tex_encodings.load_tex_math_symbols(**encoding_options)
                encoding_name = 'TeX-math-symbols'
            elif encoding_name == 'tex-math-extension':
                tex_encodings.load_tex_math_extension(**encoding_options)
                encoding_name = 'TeX-math-extension'
            elif encoding_name == 'tex-extended-ascii':
                tex_encodings.load_tex_extended_ascii(**encoding_options)
                encoding_name = 'TeX-extended-ASCII'
            elif encoding_name == 'ascii-caps-and-digits':
                tex_encodings.load_ascii_caps_and_digits(**encoding_options)
                encoding_name = 'ASCII-caps-and-digits'
            else:
                # try to load encoding file
                loaded_encoding = fontforge.loadEncodingFile(encoding_name)
                if loaded_encoding is None:
                    # file not found or empty
                    raise ValueError(f'Unknown encoding \'{encoding_name}\'.')
                encoding_name = loaded_encoding
            # font.reencode not in FontForge docs
            self.font.reencode(encoding_name)

    def add_contours(self, picture, paths):
        '''adds `paths` as contours to fontforge layer `picture`

        Args:
            picture (str): The name of the picture.
            paths (list[str]): List of path definitions.
        '''
        for path in paths:
            c = fontforge.contour()
            p = self.pair_pattern.search(path)
            c.moveTo(float(p.group(1)), float(p.group(2)))
            for j in self.join_pattern.finditer(path[p.end():]):
                cycle = j.group(7) is not None # j.group(7) is cycle
                if cycle: # path is closed by connecting to first point `p`
                    end_point = (float(p.group(1)), float(p.group(2)))
                else:
                    end_point = (float(j.group(5)), float(j.group(6)))
                cp1 =  (float(j.group(1)), float(j.group(2)))
                cp2 =  (float(j.group(3)), float(j.group(4)))
                make_line = self.input_options.make_lines
                if make_line:
                    cc = fontforge.contour().moveTo(c[-1].x, c[-1].y).cubicTo(
                        *cp1,
                        *cp2,
                        *end_point
                    )
                    make_line = self.is_collinear(cc, self.options.params['make_lines']['distance_threshold'])
                if make_line:
                    c.lineTo(*end_point)
                else:
                    c.cubicTo(
                        *cp1,
                        *cp2,
                        *end_point
                    )
                if cycle:
                    c.closed = True
                    break
            self.pictures[picture] += c

    def reversed_path(self, path):
        '''reverses the given cyclic path

        Args:
            path (str): description of a cyclic path

        Returns:
            str: description of the reversed path
        '''
        p = self.pair_pattern.search(path).groups()
        j = self.join_pattern.findall(path)
        i = len(j)-1
        reversed_path = '(' + p[0] + ',' + p[1] + ')..controls (' + j[i][2] + ',' + j[i][3] + ') and (' + j[i][0] + ',' + j[i][1] + ')'
        for i in range(len(j)-2,-1,-1):
            reversed_path += ' ..(' + j[i][4] + ',' + j[i][5] + ')..controls (' + j[i][2] + ',' + j[i][3] + ') and (' + j[i][0] + ',' + j[i][1] + ')'
        reversed_path += ' ..cycle'
        return reversed_path

    def remove_overlap(self, pic, s=None):
        '''applies layer.removeOverlap() to pic or self.pictures[pic]

        Scales the layer up before and down after applying removeOverlap to
        overcome problems or inaccuracies of FontForge. Without this, some
        points might be missing and some contours might be broken.

        Args:
            pic_name (fontforge.layer or str): a layer or a name of a picture
              in self.pictures
            s (int or float, optional): scale factor to upscale before and
              downscale after removeOverlap(). Value should be much greater
              than 1. Defaults to None. None will use
              self.input_options.params['remove_overlap']['scale_factor'].
        '''
        is_self_picture = not isinstance(pic, fontforge.layer)
        if is_self_picture:
            # Duplicate so below strategy for avoiding removeOverlap() results
            # works.
            picture = self.pictures[pic].dup()
        else:
            picture = pic
        all_contours_closed = all(c.closed for c in picture)
        if not all_contours_closed:
            print('! One or more contours are open, so removing overlap may not work.')
        if s is None:
            s = self.input_options.params['remove_overlap']['scale_factor']
        picture.transform((s, 0, 0, s, 0, 0))
        picture.removeOverlap()
        picture.transform((1/s, 0, 0, 1/s, 0, 0))
        # If pic was a key to self.pictures and it had no open contours, we can
        # try to work around problems if there were any..
        if is_self_picture:
            if all_contours_closed:
                # check again if problems were introduced.
                all_contours_closed = all(c.closed for c in picture)
                if not all_contours_closed:
                    # layer.removeOverlap()'s result is bad
                    picture = fontforge.layer()
                    # Remove overlap only between two contours, one contour after
                    # the other.
                    for c in self.pictures[pic]:
                        picture += c
                        self.remove_overlap(picture, s)
            self.pictures[pic] = picture

    def correct_direction(self, pic, s=None):
        '''applies layer.correctDirection() to pic or self.pictures[pic]

        Scales the layer up before and down after applying correctDirection to
        overcome problems or inaccuracies of FontForge. Without this, some
        contours might not be corrected.

        Args:
            pic_name (fontforge.layer or str): a layer or a name of a picture
              in self.pictures
            s (int or float, optional): scale factor to upscale before and
              downscale after correctDirection(). Value should be greater
              than 1. Defaults to None. None will use
              self.input_options.params['correct_direction']['scale_factor'].
        '''
        is_self_picture = not isinstance(pic, fontforge.layer)
        if is_self_picture:
            picture = self.pictures[pic]
        else:
            picture = pic
        if s is None:
            s = self.input_options.params['correct_direction']['scale_factor']
        picture.transform((s, 0, 0, s, 0, 0))
        picture.correctDirection()
        picture.transform((1/s, 0, 0, 1/s, 0, 0))

    def fix_contours(self, layer):
        '''fixes contours by closing open contours if first and last point have the same coordinates

        Args:
            layer (fontforge.layer): layers whose contours should be fixed
        '''
        for i_c in range(len(layer)):
            c = layer[i_c]
            if c.closed:
                continue
            if c[0] == c[-1]:
                c.closed = True

    def remove_collinear(self, layer):
        '''removes points which are not needed due to collinearity

        Args:
            layer (fontforge.layer): layer whose collinear points should be
              removed
        '''
        distance_threshold = self.options.params['remove_collinear']['distance_threshold']
        i_c = 0
        while i_c < len(layer):
            c = layer[i_c]
            if not c.closed:
                # There should be no open contours, keep them for better
                # debugging.
                i_c += 1
                continue
            if self.is_collinear(c, distance_threshold):
                del layer[i_c]
                continue # don't increase by 1 below
            i_p1 = 0
            while i_p1 < len(c):
                if not c[i_p1].on_curve:
                    # only check parts of c which start with an on-curve point
                    i_p1 += 1
                    continue
                i_p2 = i_p1 + 2 # start with 3 points
                collinear_sub_c = None
                while True:
                    if i_p2 >= len(c):
                        i_p2 -= len(c)
                    if i_p2 == i_p1:
                        break
                    if not c[i_p2].on_curve:
                        # only check parts of c which end with an on-curve point
                        i_p2 += 1
                        continue
                    if i_p1 < i_p2:
                        sub_c = c[i_p1:i_p2+1]
                    else:
                        sub_c = c[i_p1:]+c[:i_p2+1]
                    if self.is_collinear(sub_c, distance_threshold):
                        # try again with next point
                        collinear_sub_c = sub_c
                        i_p2 += 1
                        continue
                    else:
                        # can't go further than i_p2 (or last on_curve point)
                        break
                # don't remove if all points are control points ( not all(not ...) == any(...) )
                if collinear_sub_c is not None and any(p.on_curve for p in collinear_sub_c[1:-1]):
                    # can't use -= 1 here since i_p2 can be increased
                    # multiple times due to control points
                    i_p2 = i_p1 + len(collinear_sub_c)-1
                    if i_p2 >= len(c):
                        i_p2 -= len(c)

                    # remove collinear points between i_p1 and i_p2
                    if i_p1 < i_p2:
                        # remove points between
                        self.del_c_i_j(c, i_p1+1, i_p2-1)
                    else:
                        if i_p1+1 < len(c):
                            self.del_c_i_j(c, i_p1+1, None)
                        if i_p2-1 >= 0:
                            self.del_c_i_j(c, None, i_p2-1)
                i_p1 += 1
            i_c += 1

    def remove_artifacts(self, layer):
        '''remove artifacts in layer to remove unnecessary (parts of) contours

        Fontforge messes up with the dish_serif of Computer Modern. Therefore
        an own cleanup is done.

        Args:
            layer (fontforge.layer): layer whose contours should be cleaned up
        '''
        point_threshold = self.options.params['remove_artifacts']['collinear']['point_threshold']
        distance_threshold = self.options.params['remove_artifacts']['collinear']['distance_threshold']
        i_c = 0
        while i_c < len(layer):
            c = layer[i_c]
            if c.closed:
                # check for collinearity c
                if self.is_collinear(c, distance_threshold):
                    del layer[i_c]
                    continue # don't increase by 1 below
                # check for collinearity of loops inside c
                # search for points with same coords
                while True:
                    for i_p1, i_p2 in permutations([i_p for i_p, p in enumerate(c) if p.on_curve], 2):
                        p1 = c[i_p1]
                        p2 = c[i_p2]
                        if 1 < abs(i_p2 - i_p1) < len(c)-1 and abs(p2.x - p1.x) < point_threshold and abs(p2.y - p1.y) < point_threshold:
                            if i_p1 < i_p2:
                                if self.is_collinear(c[i_p1:i_p2], distance_threshold):
                                    self.del_c_i_j(c, i_p1+1, i_p2)
                                    break
                            else: # end/start is between i_p1 and i_p2
                                if self.is_collinear(c[i_p1:]+c[:i_p2], distance_threshold):
                                    self.del_c_i_j(c, i_p1, None)
                                    if i_p2-1 >= 0:
                                        self.del_c_i_j(c, None, i_p2-1)
                                    break
                    else:
                        # if looped over all combinations and condition was
                        # false, i.e. for loop didn't hit break, then there is
                        # no collinear loop is in c
                        break

            i_c += 1

    def del_c_i_j(self, c, i=None, j=None):
        '''performs del c[i:j+1] without 'Segmentation fault (core dumped)'

        deletes c[j], c[j-1], ..., c[i+1], c[i]

        c will have (j-i+1) fewer points

        Args:
            c (fontforge.contour): contour which points should be deleted.
            i (int or None, optional): i is first point to delete. default to
              None. None is the first element.
            j (int or None, optional): j is last point to delete. default to
              None. None is the last element.
        '''
        if i is None:
            i = 0
        if j is None:
            j = len(c)-1

        # loop over j, j-1, ..., i+1, i
        for k in range(j, i-1, -1):
            del c[k]

    def is_collinear(self, c, collinear_distance_threshold=0.01):
        '''checks whether all points in closed contour c are collinear

        If all points in the contour c lie on a straight line, c is considered
        to be collinear. In practice, c is most often part of a larger contour.

        Args:
            c (fontforge.contour): the contour to be checked for collinearity

        Returns:
            bool: whether c is collinear or not
        '''
        x_mean = sum(p.x for p in c)/len(c)
        y_mean = sum(p.y for p in c)/len(c)
        x_var = sum((p.x - x_mean)**2 for p in c)/len(c)
        y_var = sum((p.y - y_mean)**2 for p in c)/len(c)
        if x_var < 0.01 and y_var < 0.01:
            return True
        if x_var < y_var:
            # swap x and y to get precise results for very steep or vertical
            # linear regressions
            x_mean, y_mean = y_mean, x_mean
            x_var, y_var = y_var, x_var
            xy = [(p.y, p.x) for p in c]
        else:
            xy = [(p.x, p.y) for p in c]
        # do a linear regression and check if the largest distance is below threshold
        beta = sum((x - x_mean)*(y - y_mean) for x, y in xy)/sum((x - x_mean)**2 for x, _ in xy)
        alpha = y_mean - (beta*x_mean)
        denominator = sqrt(beta**2 + 1)
        d_max = max(abs(-beta*x + 1*y - alpha)/denominator for x, y in xy)
        return d_max < collinear_distance_threshold


# __main__ part

def main():
    mf2ff = Mf2ff()
    mf2ff.options.parse_arguments(sys.argv)

    if not mf2ff.options.quiet:
        print('This is mf2ff, version ' + __version__ + '.')
        print('Run with -help option for help on using mf2ff and license information.')
        print('This program is still under development. Bugs may occur.\n')

    mf2ff.run()

if __name__ == '__main__':
    main()
