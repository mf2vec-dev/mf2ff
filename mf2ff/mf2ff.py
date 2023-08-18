import os
import platform
import re
import subprocess
import sys
import unicodedata
from copy import deepcopy
from functools import reduce
from itertools import combinations, permutations
from math import atan2, sqrt
from time import time

try:
    import fontforge
except ImportError:
    # On windows the fontforge python module is located in the same directory as fontforge.exe.
    if platform.system() == 'Windows':
        print('! No module named \'fontforge\'. Check that fontforge is installed and that you are using ffpython (you may need to add it to your PATH).')
        sys.exit()
    else:
        print('! No module named \'fontforge\'. Check that fontforge is installed and that the module can be found in PYTHONPATH.')
        sys.exit()

__version__ = '0.3.0'

class Mf2ff():
    '''The main class of mf2ff

    Usage example:
        from mf2ff import Mf2ff
        mf2ff = Mf2ff()
        mf2ff.input_file = 'path/to/myfont.mf'
        mf2ff.run() # generates path/to/myfont.sfd
    '''

    # "[...] a complex pen is one whose boundary contains at least two points." (The METAFONTbook, p. 119)
    SIMPLE_PENS = ('(0,0) .. cycle', '(0,0)..controls (0,0) and (0,0) ..cycle')

    def __init__(self):
        self.MARKER = '@mf2vec@'
        M = self.MARKER
        # all command names which are written into the log file, g means >
        # (greater), p means | (pipe) # TODO explain why replacement is needed
        self.command_pattern = re.compile(M+
            r'(addto|also|contour|doublepath|turningcheck|turningnumber|withpen|withweight'
            r'|cull|keeping|dropping'
            r'|picture|pic_eqn|pic|as|eq|mi|pl'
            r'|shipout'
            r'|ligtable|:|::|pp:|kern|=:|p=:|p=:g|=:p|=:pg|p=:p|p=:pg|p=:pgg|skipto'
            r'|fontdimen|end)'
            r'(?:>> (?:(?:Path|Pen polygon) at line (\d+):)?(.*?))?'+M, re.DOTALL)
        # The begin of every message to the log file (also part of the above
        # pattern), used to split up multiple pieces of information written to
        # the log file by a single command.
        self.split_pattern = re.compile(r'>> (?:(?:Path|Pen polygon) at line \d+:)?')
        # patterns for pair and join, join always follows a pair of a join
        self.pair_pattern = re.compile(r'\((.*?),(.*?)\)')
        self.join_pattern = re.compile(r'\.\.controls \((.*?),(.*?)\) and \((.*?),(.*?)\) \.\.(?:\((.*?),(.*?)\)|(cycle))')
        # all information given at the shipout of a character.
        self.shipout_pattern = re.compile(r'(.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)>> (.*?)$')
        # all information in a metafont error
        self.error_pattern = re.compile(r'^! (?:.|\n)*?^l.(?:.|\n)*?\n\n', re.MULTILINE)

        self.last_known_line = 0

        # set default values
        self.cwd = os.getcwd()
        self.mf_options = ['-interaction=batchmode', '-output-directory=' + self.cwd]
        self.mf_first_line = ''
        self.jobname = ''
        self.base = ''
        self.ascent = 0
        self.comment = ''
        self.copyright = ''
        self.descent = 0
        self.designsize = 0.0
        self.encoding = 'UnicodeFull'
        self.family_name = ''
        self.ff_path = ''
        self.fontlog = ''
        self.fontname = ''
        self.font_version = '001.000'
        self.fullname = ''
        self.italicangle = 0.0
        self.ppi = 1000
        self.scripts = (
            ('cyrl', ('dflt',)),
            ('grek', ('dflt',)),
            ('latn', ('dflt',))
        )
        self.upos = -10
        self.uwidth = 2
        self.options = {
            'cull-at-shipout': False,
            'debug': False,
            'extrema': False,
            'hint': False,
            'is_type': False,
            'kerning-classes': False,
            'otf': False,
            'remove-artifacts': False,
            'sfd': True,
            'stroke-simplify': True,
            'stroke-accuracy': None, # use fontforge's default (should be 0.25)
            'time': False,
            'ttf': False,
        }
        self.input_file = ''

        self.params = {
            'remove-artefacts': {
                'collinear': {
                    'distance-threshold': 0.01,
                    'point-threshold': 0.1,
                },
            },
            'remove-overlap': {
                'scale-factor': 1000,
            },
        }

        # On Windows, ANSI Control Sequence are not available by default. They
        # can be activated by running the color command.
        if platform.system() == 'Windows':
            os.system('color')


    def run(self):
        '''run mf2ff
        '''

        M = self.MARKER

        if not self.input_file and not self.mf_first_line:
            print('! No input')
            sys.exit()

        if not self.jobname:
            if self.input_file:
                self.jobname = self.input_file
                self.mf_options.append('-jobname=' + self.jobname)
            else:
                # use plain since it's used as the jobname by mf in this case
                self.jobname = 'plain'

        # load base file if defined
        if self.base:
            input_base = 'input ' + self.base + ';'
        else:
            input_base = ''

        # If option is_type is given, add the extra definitions is_pen and
        # is_picture.
        extra_defs = ''
        if self.options['is_type']:
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
            + self.mf_first_line
            + 'input ' + self.input_file
        )

        self.run_mf()

        # open and process log file
        start_time_ff = time()
        try:
            with open(self.jobname + '.log', 'r+') as f:
                orig_log_data = f.read()
        except IOError as e:
            print('! I can\'t find file: `' + self.jobname + '.log\'.')
            print(e)
            sys.exit()

        log_data = self.error_pattern.sub('', orig_log_data)
        log_data = re.sub('\n', '', log_data)
        log_data = log_data.split(self.mf_first_line, 1)[1] # interesting info only after the input
        cmds = self.command_pattern.findall(log_data) # find all commands

        print('processing its output...')
        print('Some error messages below come directly from fontforge and cannot be muted.')
        print('Line is last known line from current file.')

        if not self.fontname:
            self.fontname = self.jobname
        if not self.family_name:
            self.family_name = self.fontname
        if not self.fullname:
            self.fullname = self.fontname

        # set up font object to be filled with
        self.font = fontforge.font()
        self.font.ascent = self.ascent
        self.font.comment = self.comment
        self.font.copyright = self.copyright
        self.font.descent = self.descent
        self.font.design_size = self.designsize
        self.font.encoding = self.encoding
        self.font.familyname = self.family_name
        self.font.fontlog = self.fontlog
        self.font.fontname = self.fontname
        self.font.version = self.font_version
        self.font.fullname = self.fullname
        self.font.italicangle = self.italicangle
        self.font.upos = self.upos
        self.font.uwidth = self.uwidth

        # picture variables are processed inside fontforge using layers.
        # A dict is used to keep track of the pictures
        self.pictures = {}
        self.pictures['nullpicture'] = fontforge.layer() # predefined empty picture

        # a separate font object with a dedicated glyph is used for
        # processing
        internal_font = fontforge.font()
        self.proc_glyph = internal_font.createChar(-1, 'proc_glyph')

        # keep a record of ligtable's skipto labels
        self.skiptos = {}

        self.process_commands(start_time_ff, cmds)

        self.apply_font_options_and_save()

        print('')

        end_time_ff = time()
        if self.options['time']:
            print('  (took ' + '%.2f' % (end_time_ff-start_time_ff) + 's)')

        pattern = re.sub(r'(\.|\*|\||\\|\(|\)|\+)', r'\\\1', '\n?'.join(self.mf_first_line), flags=re.DOTALL) \
            + '\n|\n' + '\n?'.join(M) + '.*?\n' + '\n?'.join(M)
        start_time_log = time()
        clean_log = re.sub(pattern, '', orig_log_data, flags=re.DOTALL)

        if self.options['debug']:
            extension = '.clean.log'
        else:
            extension = '.log'
        try:
            with open(self.jobname + extension, 'w') as outfile:
                outfile.write(clean_log)
        except IOError:
            print('! I can\'t find file: `' + self.jobname + extension + '\'.')
            sys.exit()
        end_time_log = time()
        print('Log file cleaned up')
        if self.options['time']:
            print('  (took ' + '%.2f' % (end_time_log-start_time_log) + 's)')
        print('Done.')

    def run_mf(self):
        '''runs METAFONT with self.mf_options and self.mf_first_line.
        stdout is devnull
        '''
        print('running METAFONT...')
        start_time_mf = time()
        subprocess.call(
            ['mf'] + self.mf_options + [self.mf_first_line],
            stdout=subprocess.DEVNULL,
            cwd=self.cwd
        )
        end_time_mf = time()
        if self.options['time']:
            print('  (took ' + '%.2f' % (end_time_mf-start_time_mf) + 's)')

    def process_commands(self, start_time_ff, cmds):
        '''processes the commands cmds

        shows progress and eta based on start_time_ff

        Args:
            start_time_ff (float): start time of fontforge from time.time()
            cmds (list[tuple[str]]): list of commands
        '''

        if self.options['kerning-classes']:
            kerning_list = {
                'left-glyphs': [],
                'right-glyphs': [],
                'offsets': []
            }

        i = 0
        while i < len(cmds):
            cmd = cmds[i]
            cmd_name = cmd[0]
            if cmd[1]:
                self.last_known_line = int(cmd[1])
            self.cmd_body = cmd[2]

            self.show_progress(start_time_ff, i, len(cmds))

            # addto\
            # TODO This section needs to be tested and maybe reworked! mf only
            # makes one line with each pen stroke so doublepath is needed for a
            # full stroke. Using contour with a pen results in an offset line,
            # left or right depending on the direction of the path. One of the
            # flags removeinternal or removeexternal might be useful to do this.

            if cmd_name == 'addto':
                addto = self.cmd_body[1:-1] # clip quotes
                if cmds[i+1][0] == 'turningcheck':
                    # turningcheck is always followed by turningnumber
                    turningcheck = int(cmds[i+1][2])
                    turningnumber = int(cmds[i+2][2])
                    j = i + 3
                else:
                    j = i + 1

                # next command is also, contour or doublepath
                addto_next_cmd_name = cmds[j][0]
                if cmds[j][1]:
                    self.last_known_line = int(cmds[j][1])
                addto_next_cmd_body = cmds[j][2]
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
                while j < len(cmds):
                    cmd = cmds[j]
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
                    self.pictures[addto] += self.pictures[cmds[j][1:-1]].reverseDirection()
                    j += 1
                elif addto_next_cmd_name == 'also':
                    self.pictures[addto] += self.pictures[addto_next_cmd_body[1:-1]]
                else: # add a path
                    # There are four basic cases of adding a path to a glyph:
                    # 1. A contour without a pen: The contour is simply added to
                    #    the glyph. (fill c;)
                    # 2. A doublepath without a pen: This will have no effect in
                    #    mf so it is ignored in FontForge too.
                    # 3. A contour with a pen: The contour is added to the glyph
                    #    with an offset. A closed path will fill an area,
                    #    without a hole, an open path will cause an error in mf
                    #    and in FontForge.
                    # 4. A doublepath with a pen: A simple pen stroke added to
                    #    the glyph. (draw p;) Since in some cases multiple paths
                    # are added, create a list of paths. The command body of the
                    # contour or doublepath command is a path.
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

                        stroke_kwargs.update({'simplify': self.options['stroke-simplify']})
                        if self.options['stroke-accuracy'] is not None: # None -> Fontforge's default value
                            stroke_kwargs.update({'accuracy': self.options['stroke-accuracy']})

                        pen_first_point = self.pair_pattern.search(pen) # TODO better with .groups ?
                        pen_joins = self.join_pattern.findall(pen[pen_first_point.end():])

                        # If the pen's path has 8 points it is to be assumed to be a circle / ellipse.
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
                        self.pictures['temp_layer'].correctDirection()
                        # add stroked layer to glyph
                        self.pictures[addto] += self.pictures['temp_layer']

                    # 2nd case: doublepath without pen
                    else:
                        # doublepath without pen has no effect
                        # TODO check
                        pass

            # cull\
            # TODO This section needs extensive testing and rework!
            elif cmd_name == 'cull':
                cull_pic_name = self.cmd_body[1:-1] # clip quotes
                keep_or_drop = cmds[i+1][0]
                a, b = [int(float(s)) for s in self.pair_pattern.search(cmds[i+1][2]).groups()]
                weight = 1 # default # TODO source
                num_paths = len(self.pictures[cull_pic_name])

                i += 1
                j = i+1
                while j < len(cmds):
                    cmd = cmds[j]
                    cmd_name = cmd[0]
                    self.cmd_body = cmd[2]

                    if cmd_name == 'withweight':
                        weight = int(round(float(self.cmd_body))) # TODO source for rounding to next integer
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
                    corrected_picture = fontforge.layer()
                    for c in self.pictures[cull_pic_name]:
                        corrected_picture += deepcopy(c)
                    corrected_picture = corrected_picture.correctDirection()
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
                    self.pictures[cull_pic_name].correctDirection()
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

            elif cmd_name == 'pic_eqn':
                j = i+1
                j_eq = [i-1]
                complex_expressions = []
                while j < len(cmds):
                    if cmds[j][0] not in ('pic', 'eq', 'as', 'pl', 'mi'):
                        break
                    elif cmds[j][0] in ('eq', 'as'):
                        if j-j_eq[-1] < 2:
                            complex_expressions.append(j)
                            if len(complex_expressions) > 1:
                                print('! ignoring complex picture expression')
                        j_eq += [j]
                    j += 1

                j_eq += [j]

                for k in j_eq[:-2]:
                    if len(complex_expressions) == 0:
                        if cmds[k-1][0] != 'mi':
                            self.pictures[cmds[k+1][2][1:-1]] = fontforge.layer()
                            for c in self.pictures[cmds[j_eq[-2]+1][2][1:-1]]:
                                self.pictures[cmds[k+1][2][1:-1]] += c
                        else:
                            self.pictures[cmds[k+1][2][1:-1]] = fontforge.layer()
                            for c in self.pictures[cmds[j_eq[-2]+1][2][1:-1]]:
                                self.pictures[cmds[k+1][2][1:-1]] += c
                            self.pictures[cmds[k+1][2][1:-1]] = self.pictures[cmds[k+1][2][1:-1]].reverseDirection()
                    else:
                        for k in range(i,j):
                            if k in complex_expressions[1:]:
                                for l in range(j_eq[k-1], j_eq[k], 2):
                                    if cmds[l][2] == 'pic':
                                        if cmds[l-1][2] in ('eq', 'as', 'pl'):
                                            self.pictures[cmds[j_eq[-1]][2][1:-1]] += self.pictures[cmds[l][2][1:-1]]
                                        elif cmds[l-1][2] == 'mi':
                                            self.pictures[cmds[j_eq[-1]][2][1:-1]] += self.pictures[cmds[l][2][1:-1]].reverseDirection()
                i = j_eq[-1]-1

            elif cmd_name == 'shipout':
                shipout = self.shipout_pattern.search(self.cmd_body)

                # "The values of xoffset, yoffset, charcode, and charext are
                # first rounded to integers, if necessary." (The METAFONTbook,
                # p. 220)
                charcode = round(float(shipout.group(1)))
                charext = round(float(shipout.group(2)))
                charwd = int(float(shipout.group(3)))
                charht = int(float(shipout.group(4)))
                chardp = int(float(shipout.group(5)))
                charic = int(float(shipout.group(6)))
                # 7 and 8 are chardx, chardy
                xoffset = round(float(shipout.group(9)))
                yoffset = round(float(shipout.group(10)))

                glyph_code = charcode + charext*256
                pic_name = cmds[i+1][2][1:-1] # clip quotes
                pic = self.pictures[pic_name]

                if self.options['remove-artifacts']:
                    self.remove_artefacts(pic)

                glyph = self.font.createChar(glyph_code,)
                glyph.layers[1] = pic

                glyph.width = charwd
                glyph.texheight = charht
                glyph.texdepth = chardp
                glyph.italicCorrection = charic

                if xoffset != 0 or yoffset != 0:
                    # "The pixels of v are shifted by (xoffset, yoffset) as they
                    # are shipped out." (The METAFONTbook, p. 220)
                    glyph.transform((1.0, 0.0, 0.0, 1.0, xoffset, yoffset))
                    pass

                if self.ascent == 0 and charht > self.font.ascent:
                    self.font.ascent = charht
                if self.descent == 0 and chardp > self.font.descent:
                    self.font.descent = chardp

                i += 1

            elif cmd_name == 'ligtable':
                cmd_body_parts = self.cmd_body.split('>> ')
                hppp = float(cmd_body_parts[0])
                self.cmd_body = cmd_body_parts[1]

                self.sub_list = []
                pos_list = []
                self.tmp_list = []

                j = i+1
                while j < len(cmds):
                    cmd = cmds[j]
                    cmd_name = cmd[0]
                    self.cmd_body = cmd[2].split('>> ')[0]
                    self.last_cmd_body = cmds[j-1][2].split('>> ')[-1]

                    if cmd_name == ':':
                        self.tmp_list.append([[self.last_cmd_body.split('"')[1] if self.last_cmd_body[0] == '"' else int(float(self.last_cmd_body))]])
                    elif cmd_name == '::':
                        if self.last_cmd_body in self.skiptos:
                            self.tmp_list += self.skiptos[self.last_cmd_body]
                    elif cmd_name == ':||':
                        print('! ligtable :|| not supported yet, ignored')
                    elif cmd_name == 'kern':
                        char = self.last_cmd_body
                        kern = self.cmd_body
                        char = char[1:-1] if char[0] == '"' else int(float(char))
                        kern = int(float(kern)*hppp)
                        pos_list += deepcopy(self.tmp_list)
                        for k in range(len(pos_list)-len(self.tmp_list),len(pos_list)):
                            pos_list[k] = [pos_list[k][0] + [char]] + [kern]
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
                        char = char[1:-1] if char[0] == '"' else int(float(char))
                        lig = lig [1:-1] if lig [0] == '"' else int(float(lig ))
                        self.sub_list += deepcopy(self.tmp_list)
                        for i in range(len(self.sub_list)-len(self.tmp_list), len(self.sub_list)):
                            self.sub_list[i] = [lig, lig_type] + [self.sub_list[i][0] + [char]]
                    elif cmd_name == 'skipto':
                        self.skiptos[self.last_cmd_body] = self.tmp_list
                    else:
                        break
                    j += 1
                i = j-1

                if len(self.sub_list) > 0:
                    for sub in self.sub_list:
                        lig = self.to_glyph_name(sub[0])
                        lig_type = sub[1]
                        char1 = self.to_glyph_name(sub[2][0])
                        char2 = self.to_glyph_name(sub[2][1])
                        if lig_type[0] == ' ' and lig_type[3] == ' ':
                            if not 'gsub_ligature' in self.font.gsub_lookups:
                                self.font.addLookup( 'gsub_ligature', 'gsub_ligature', (), (('liga', self.scripts),))
                                self.font.addLookupSubtable('gsub_ligature', 'gsub_ligature_subtable')
                            # Try to create the ligature. FontForge will
                            # raise a TypeError, if one of the
                            # characters is unknown. In that case, print
                            # a warning and continue
                            try:
                                self.font[lig].addPosSub('gsub_ligature_subtable', (char1, char2))
                            except TypeError as e:
                                print('! Error while adding ligature:', e, '(either '+repr(char1)+' or '+repr(char2)+' is unknown) Ignored.')
                        elif lig_type[0] == '|' and lig_type[3] == ' ':
                            if not 'gsub_single_after_' + char1 in self.font.gsub_lookups:
                                self.font.addLookup('gsub_single_after_' + char1, 'gsub_single', (), ())
                                self.font.addLookupSubtable('gsub_single_after_' + char1, 'gsub_single_after_' + char1 + '_subtable')
                            self.font[char2].addPosSub('gsub_single_after_' + char1 + '_subtable', lig)
                            if not 'gsub_contextchain' in self.font.gsub_lookups:
                                self.font.addLookup('gsub_contextchain', 'gsub_contextchain', (), (('calt', self.scripts),))
                            self.font.addContextualSubtable(
                                'gsub_contextchain', 'gsub_contextchain_subtable_' + char1 + '_' + char2, 'glyph',
                                char1 + ' | ' + char2 + ' @<gsub_single_after_' + char1 + '> |'
                            )
                        elif lig_type[0] == ' ' and lig_type[3] == '|':
                            if not 'gsub_single_before_' + char2 in self.font.gsub_lookups:
                                self.font.addLookup('gsub_single_before_' + char2, 'gsub_single', (), ())
                                self.font.addLookupSubtable('gsub_single_before_' + char2, 'gsub_single_before_' + char2 + '_subtable')
                            self.font[char1].addPosSub('gsub_single_before_' + char2 + '_subtable', lig)
                            if not 'gsub_contextchain' in self.font.gsub_lookups:
                                self.font.addLookup('gsub_contextchain', 'gsub_contextchain', (), (('calt', self.scripts),))
                            self.font.addContextualSubtable(
                                'gsub_contextchain', 'gsub_contextchain_subtable_' + char1 + '_' + char2, 'glyph',
                                '| ' + char1 + ' @<gsub_single_before_' + char2 + '> | ' + char2
                            )
                        elif lig_type[0] == '|' and lig_type[3] == '|':
                            if not 'gsub_multiple_between_' + char1 + '_' + char2 in self.font.gsub_lookups:
                                self.font.addLookup('gsub_multiple_between_' + char1 + '_' + char2, 'gsub_multiple', (), ())
                                self.font.addLookupSubtable('gsub_multiple_between_' + char1 + '_' + char2, 'gsub_multiple_between_' + char1 + '_' + char2 + '_subtable')
                            self.font[char2].addPosSub('gsub_multiple_between_' + char1 + '_' + char2 + '_subtable', (lig, char2))
                            if not 'gsub_contextchain' in self.font.gsub_lookups:
                                self.font.addLookup('gsub_contextchain', 'gsub_contextchain', (), (('calt', self.scripts),))
                            self.font.addContextualSubtable(
                                'gsub_contextchain', 'gsub_contextchain_subtable_' + char1 + '_' + char2, 'glyph',
                                char1 + ' | ' + char2 + ' @<gsub_multiple_between_' + char1 + '_' + char2 + '> |'
                            )

                if len(pos_list) > 0:
                    if self.options['kerning-classes']:
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
                        if not 'gpos_pair' in self.font.gpos_lookups:
                            self.font.addLookup('gpos_pair', 'gpos_pair', (), (('kern', self.scripts),))
                            self.font.addLookupSubtable('gpos_pair', 'gpos_pair_subtable')
                        for pos in pos_list:
                            char1 = self.to_glyph_name(pos[0][0])
                            char2 = self.to_glyph_name(pos[0][1])
                            kern = pos[1]
                            try:
                                self.font[char1].addPosSub('gpos_pair_subtable', char2, 0, 0, kern, 0, 0, 0, 0, 0)
                            except TypeError as e:
                                print('! Error while adding kerning pair:', e, '(either '+repr(char1)+' or '+repr(char2)+' is unknown) Ignored.')

            elif cmd_name == 'fontdimen':
                cmd_body_parts = self.cmd_body.split('>> ')
                hppp = float(cmd_body_parts[0])
                first_fontdimen = int(cmd_body_parts[1])
                params = [float(p) for p in cmds[i+1][2].split('>> ')]
                i += 1
                for j, k in enumerate(range(first_fontdimen, first_fontdimen + len(params))):
                    if k == 2:
                        self.font.createChar(32).width = int(hppp*params[j])

            # TODO: charlist, extensible

            elif cmd_name == 'end':
                design_size = int(self.cmd_body)
                if design_size != 0:
                    self.font.design_size = design_size

            else:
                print('! "' + cmd_name + '": ' + self.cmd_body + '?')
                print('  This may be a syntax error. Run file with METAFONT to find it.')
                print('  If the input is correct, consider reporting a bug.')
            i += 1

        # all commands processed, but for some commands post processing is needed
        if self.options['kerning-classes']:
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
            if not 'gpos_pair' in self.font.gpos_lookups:
                self.font.addLookup('gpos_pair', 'gpos_pair', (), (('kern', self.scripts),))
            self.font.addKerningClass('gpos_pair', 'gpos_pair_subtable', leftClasses, rightClasses, offset_flattened)

    def apply_font_options_and_save(self):
        '''apply self.options to self.font and generate font file from self.font
        based on self.options
        '''
        if self.options['extrema']:
            self.font.selection.all()
            self.font.addExtrema()
        if self.options['hint']:
            self.font.autoHint()
            self.font.autoInstr()
        if self.options['sfd']:
            self.font.save(self.jobname + '.sfd')
        if self.options['otf']:
            self.font.generate(self.jobname + '.otf')
        if self.options['ttf']:
            self.font.generate(self.jobname + '.ttf', flags='opentype')


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

    def get_redefinitions(self):
        '''return mf code containing redefinitions needed for mf2ff

        Returns:
            str: mf code
        '''
        # abbreviations for inserting log file markers for redefined tokens
        M = self.MARKER
        m_ = 'message "'+M # begin redefined token, followed by token name or identifier
        m__ = m_+'";'      # end of redefined token, possibly preceded by an expression
        mm_ = m__+m_       # end of redefined token and begin of new redefined token
        return (
            # First, some mf primitives are saved, so they are accessible even
            # after redefining them.
            'let __mfIIvec__orig_colon__ = : ;'
            'let __mfIIvec__orig_else__ = else;'
            'let __mfIIvec__orig_elseif__ = elseif;'
            'let __mfIIvec__orig_end__ = end;'
            'let __mfIIvec__orig_eq__ = = ;'
            'let __mfIIvec__orig_for__ = for;'
            'let __mfIIvec__orig_forever__ = forever;'
            'let __mfIIvec__orig_forsuffixes__ = forsuffixes;'
            'let __mfIIvec__orig_if__ = if;'
            'let __mfIIvec__orig_pen__ = pen;'
            'let __mfIIvec__orig_picture__ = picture;'
            'let __mfIIvec__orig_hide__ = hide;'

            # Numerical equations should still be processed in mf to get the
            # correct results. This is different for picture equations. They
            # need to be evaluated in fontforge using boolean operations. To
            # keep track of the type of equation, a boolean is used.
            'boolean __mfIIvec__pic_eqn__; __mfIIvec__pic_eqn__ := false;'

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
            'def __mfIIvec__redef_colon__ ='
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
                'def __mfIIvec__special_colon__ ='
                    '__mfIIvec__orig_hide__(let : = __mfIIvec__other_colon__;)'
                    '__mfIIvec__orig_colon__ '
                'enddef;'
                # The following sparks are redefined by this subroutine to
                # activate the __mfIIvec__special_colon__ (which deactivates
                # itself).
                'save if, elseif, else, for, forsuffixes, forever;'
                'def if ='
                    '__mfIIvec__orig_hide__(let : = __mfIIvec__special_colon__;)'
                    '__mfIIvec__orig_if__ '
                'enddef;'
                'def elseif ='
                    '__mfIIvec__orig_hide__(let : = __mfIIvec__special_colon__;)'
                    '__mfIIvec__orig_elseif__ '
                'enddef;'
                'def else ='
                    '__mfIIvec__orig_hide__(let : = __mfIIvec__special_colon__;)'
                    '__mfIIvec__orig_else__ '
                'enddef;'
                'def for ='
                    '__mfIIvec__orig_hide__(let : = __mfIIvec__special_colon__;)'
                    '__mfIIvec__orig_for__ '
                'enddef;'
                'def forsuffixes ='
                    '__mfIIvec__orig_hide__(let : = __mfIIvec__special_colon__;)'
                    '__mfIIvec__orig_forsuffixes__ '
                'enddef;'
                'def forever ='
                    '__mfIIvec__orig_hide__(let : = __mfIIvec__special_colon__;)'
                    '__mfIIvec__orig_forever__ '
                'enddef;'
                # In ligtable and fontdimen every colon should match the message
                # generating __mfIIvec__other_colon__ if they are not part of
                # the condition or loop structure itself.
                'let : = __mfIIvec__other_colon__;'
            'enddef;'

            ## addto
            # doublepath: "If p is not a cyclic path, this case reduces to the
            # second case, with p replaced by the doubled-up path `p & reverse p
            # & cycle' (unless p consists of only a single point, when the new
            # path is simply `p .. cycle'). On the other hand if p is a cyclic
            # path, this case reduces to two addto commands of the second type,
            # in one of which p is reversed." (The METAFONTbook, p. 119)
            'def addto text t = '+m_+'addto"; begingroup '
                'save also, contour, doublepath, withpen, withweight;'
                'def also              = ; '+mm_+'also";          show str enddef;'
                'def contour    expr p = ; '+mm_+'turningcheck";  show turningcheck;'
                                            +mm_+'turningnumber"; show turningnumber p;'
                                            +mm_+'contour";       show p   enddef;'
                'def doublepath expr p = ; '+mm_+'turningcheck";  show turningcheck;'
                                            +mm_+'turningnumber"; show turningnumber p;'
                                            +mm_+'doublepath";    show p   enddef;'
                'def withpen           = ; '+mm_+'withpen";       show     enddef;'
                'def withweight        = ; '+mm_+'withweight";    show     enddef;'
                'show str t; endgroup; '+m__+
            'enddef;'

            ## cull
            'def cull text t = '+m_+'cull"; begingroup '
                'save keeping, dropping, withweight;'
                'def keeping    = ; '+mm_+'keeping";    show enddef;'
                'def dropping   = ; '+mm_+'dropping";   show enddef;'
                'def withweight = ; '+mm_+'withweight"; show enddef;'
                'show str t; endgroup; '+m__+
            'enddef;'

            ## picture
            # Variables of type \dl{picture} are the only ones which operations
            # are not processed by mf but outsourced to FontForge. Every time
            # new variables of type picture are declared, the declarations are
            # sent to FontForge by `show`ing the names of the variables to the
            # log file. Furthermore, the names of the variables are converted
            # into definitions: Every time the name of the variable name is
            # processed, its name should show up in the log file. Due to the
            # fact that mf processes \dl{picture} expressions with the same
            # operators as in other expression types and these \dl{picture}
            # operations needs to be sent to the log file, all operators only
            # need to be redefined inside picture equations. The operations
            # which can occur in a picture equation are := = - + (see
            # METAFONTbook, pp. 115 and 214)
            'def picture text t = '+m_+'picture";'
                'forsuffixes p = t:'
                    'show str p;'
                    'vardef p text tt = '
                        'if __mfIIvec__pic_eqn__:'
                            +mm_+'pic"; show str p;'
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
                +('cull currentpicture dropping (-infinity,0);' if self.options['cull-at-shipout'] else '')
                +m_+'shipout"; __mfIIvec__pic_eqn__ := true;'
                'show charcode, charext, '
                     'charwd*hppp, charht*hppp, chardp*hppp, charic*hppp, '
                     'chardx*hppp, chardy*hppp, xoffset, yoffset;'
                't; __mfIIvec__pic_eqn__ := false;'
                +m__+
            'enddef;'

            ## ligtable
            # Since the ligtable uses the colon as a separator, while the colon
            # is also used in the structure of conditions and loops, it has to
            # be redefined during such a structure. __mfIIvec__other_colon__ is
            # used to be able to switch between both.
            'def ligtable text t = '+m_+'ligtable"; show hppp; begingroup '
                'save :, ::, ||:, kern, =:, |=:, |=:>, =:|, =:|>, |=:|, |=:|>, |=:|>>, skipto;'
                'def __mfIIvec__other_colon__ = ; '+mm_+':"; show enddef;'
                'def   ::   = ; '+mm_+'::";     show enddef;'
                'def ||:    =   '+mm_+'pp:";    show enddef;' # no ; required since there is no preceding expression whose show command needs to end before the message
                'def kern   = ; '+mm_+'kern";   show enddef;'
                'def  =:    = ; '+mm_+'=:";     show enddef;'
                'def |=:    = ; '+mm_+'p=:";    show enddef;'
                'def |=:>   = ; '+mm_+'p=:g";   show enddef;'
                'def  =:|   = ; '+mm_+'=:p";    show enddef;'
                'def  =:|>  = ; '+mm_+'=:pg";   show enddef;'
                'def |=:|   = ; '+mm_+'p=:p";   show enddef;'
                'def |=:|>  = ; '+mm_+'p=:pg";  show enddef;'
                'def |=:|>> = ; '+mm_+'p=:pgg"; show enddef;'
                # skipto is always preceded by a show command and a comma (,),
                # so a normal message can't follow. Therefor the message command
                # is hidden. After the comma, the code after the skipto command
                # will be shown by the previous show command.
                'def skipto = __mfIIvec__orig_hide__('+mm_+'skipto") enddef;'
                '__mfIIvec__redef_colon__ ' # restore colon before showing t
                'show t; endgroup; '+m__+
            'enddef;'

            # fontdimen command's syntax uses of colon (:). Therefor some
            # redefinitions are needed to be used in combinations with e.g. the
            # if statement
            'def fontdimen text t='+m_+'fontdimen"; show hppp; begingroup '
                'save:;'
                'def:text tt=;'+mm_+':";show tt enddef;' # TODO Use __mfIIvec__special_colon__ here instead of : ?
                '__mfIIvec__redef_colon__ '
                'show t endgroup; '+m__+
            'enddef;'

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
            # Note that \dl{fullcirlce} and \dl{directionpoint} are defined in
            # plain mf.
            'let pen = path; def nullpen = ((0,0)..cycle) enddef; def pencircle = fullcircle enddef;'
            'def penoffset = directionpoint enddef;' # TODO explain
            'let makepen = relax;'
            'let makepath = relax;'
            # mf is run in background, so don't display anything.
            'def display text t = enddef;'
            # nullpicture should be a variables of type \dl{picture}.
            'save nullpicture; picture nullpicture;'
            # The loading of plain.mf is preceded by some saves so there will be no errors.
            'save hide, blankpicture, unitpixel, pensquare, penrazor, mm, pt, dd, bp, cm, pc, cc, in, modesetup, mode_name, mode;'
            'input plain.mf;'

            # A special mode is defined, to prepare for vector font generation.
            'mode_def mfIIff='
                'proofing:=0;' # don't make proofs
                'fontmaking:=0;' # mf itself should not make a font
                'tracingtitles:=0;' # no titles (e.g. "The letter O") in stdout
                'pixels_per_inch:=' + str(self.ppi) + ';'
                'blacker:=0;' # no "special correction"
                'fillin:=0;' # no pixels that could influence their neighbors
                'o_correction:=1;' # no reduction in overshoot
            'enddef;'
            'mode:=mfIIff;'
        )

    def show_progress(self, start_time_ff, i, num_cmds):
        '''shows progress bar and ETA

        Args:
            start_time_ff (float): start time of fontforge from time.time()
            i (int): index of current command (0 based)
            num_cmds (int): number of commands
        '''
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

    def to_glyph_name(self, g):
        '''converts name or code point g to FontForge glyph name

        If name is unknown, use first character of name and print a warning.

        Args:
            g (str or int): glyph code point or name

        Returns:
            string: FontForge glyph name
        '''
        if isinstance(g, str):
            if fontforge.unicodeFromName(g) != -1:
                return g
            else:
                try:
                    # convert name to Unicode character and back to Fontforge glyph name
                    return fontforge.nameFromUnicode(unicodedata.decimal(unicodedata.lookup(g)))
                except KeyError:
                    print('! \'' + g + '´ is not a valid glyph name. \'' + g[0] + '´ is assumed.')
                    return g[0]
        else:
            return fontforge.nameFromUnicode(g)

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
                if j.group(7) == None: # j.group(7) is cycle
                    c.cubicTo(
                        float(j.group(1)), float(j.group(2)),
                        float(j.group(3)), float(j.group(4)),
                        float(j.group(5)), float(j.group(6))
                    )
                else: # path is closed by connecting to first point `p`
                    c.cubicTo(
                        float(j.group(1)), float(j.group(2)),
                        float(j.group(3)), float(j.group(4)),
                        float(p.group(1)), float(p.group(2))
                    )
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

    def remove_overlap(self, pic_name, s=None):
        '''applies layer.removeOverlap() to picture pic_name

        scales the image up before and down after applying removeOverlap to
        overcome problems or inaccuracies of FontForge. Without this, some
        points might be missing and some contours might be broken.

        Args:
            pic_name (str): name of a picture in self.pictures s (int or float,
            optional): scale factor to upscale before and downscale after
            removeOverlap(). Value should be much greater than 1. Defaults to
            None. None will use self.params['remove-overlap']['scale-factor'].
        '''
        if s is None:
            s = self.params['remove-overlap']['scale-factor']
        self.pictures[pic_name].transform((s, 0, 0, s, 0, 0))
        self.pictures[pic_name].removeOverlap()
        self.pictures[pic_name].transform((1/s, 0, 0, 1/s, 0, 0))

    def remove_artefacts(self, layer):
        '''remove artefacts in pic to remove unnecessary (parts of) contours

        Simplify messes up with the dish_serif of computer modern
        even when reducing the error_bound. Therefore an own
        cleanup is done.

        Args:
            pic (fontforge.layer): layers whose contours should be cleaned up
        '''
        i_c = 0
        while i_c < len(layer):
            c = layer[i_c]
            if c.closed:
                # check for collinearity c
                if self.is_collinear(c):
                    del layer[i_c]
                    continue # don't increase by 1 below
                # check for collinearity of loops inside c
                # search for points with same coords
                point_threshold = self.params['remove-artefacts']['collinear']['point-threshold']
                while True:
                    for i_p1, i_p2 in permutations([i_p for i_p, p in enumerate(c) if p.on_curve], 2):
                        p1 = c[i_p1]
                        p2 = c[i_p2]
                        if 1 < abs(i_p2 - i_p1) < len(c)-1 and abs(p2.x - p1.x) < point_threshold and abs(p2.y - p1.y) < point_threshold:
                            if i_p1 < i_p2:
                                if self.is_collinear(c[i_p1:i_p2]):
                                    # do del c[i_p1+1:i_p2] without "Segmentation fault (core dumped)"
                                    for i_p_i in range(i_p2-1, i_p1, -1):
                                        del c[i_p_i]
                                    break
                            else: # end/start is between i_p1 i_p2
                                if self.is_collinear(c[i_p1:]+c[:i_p2]):
                                    # TODO too many points removed?
                                    # do del c[i_p1:] without "Segmentation fault (core dumped)"
                                    for i_p1_i in range(len(c)-1, i_p1-1, -1):
                                        del c[i_p1_i]
                                                # do del c[:i_p2-1]
                                    for i_p2_i in range(i_p2-1, -1, -1):
                                        del c[i_p2_i]
                                    break
                    else:
                        # if looped over all combinations and
                        # condition was not, i.e. for loop didn't
                        # hit break, no collinearity loop is in c
                        break

            i_c += 1

    def is_collinear(self, c):
        '''checks whether all points in closed contour c are collinear

        If all points in the contour c are at the same position, c is considered
        to be collinear.

        Args:
            c (fontforge.contour): the contour to be checked for collinearity

        Returns:
            bool: whether c is collinear or not
        '''
        x_mean = sum(p.x for p in c)/len(c)
        y_mean = sum(p.y for p in c)/len(c)
        x_var = sum(abs(p.x - x_mean)**2 for p in c)/len(c)
        y_var = sum(abs(p.y - y_mean)**2 for p in c)/len(c)
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
        return d_max < self.params['remove-artefacts']['collinear']['distance-threshold']


# __main__ part

def parse_arguments(mf2ff):
    '''Parse command line arguments and set them in the mf2ff object.

    Args:
        mf2ff (Mf2ff): an instance of the Mf2ff class
    '''
    args = sys.argv

    # Arguments consists of two parts: the options starting with a \dl{-} and other arguments.
    option_args = True # keep track if still parsing options

    i = 1 # i == 0 is mf2ff
    while i < len(args):
        full_arg = args[i] # argument with leading -
        if full_arg[0] == '-' and len(full_arg) > 1: # it is an option
            if option_args: # options only before other arguments
                arg = full_arg[1:]
                # define groups of options
                font_option_names_str = ('comment', 'copyright', 'encoding', 'familyname', 'fontlog', 'fontname', 'font-version', 'fullname')
                font_option_names_int = ('ascent', 'descent', 'ppi', 'uwidth', 'upos')
                font_option_names_float = ('designsize', 'italicangle')
                # options and negatable options directly passed to mf.
                if arg in ('file-line-error', 'no-file-line-error',
                        'halt-on-error', 'ini', 'parse-first-line',
                        'no-parse-first-line', 'recorder', '8bit'):
                    mf2ff.mf_options.append(full_arg)
                # name value pairs and passed to mf
                # TODO separated by space support?
                elif arg.split('=', 1)[0] in ('interaction', 'kpathsea-debug',
                        'mktex', 'no-mktex', 'output-directory', 'translate-file'):
                    if '=' in arg:
                        mf2ff.mf_options.append(full_arg)
                    else:
                        mf2ff.mf_options.extend([full_arg, args[i+1]])
                        i += 1
                # name value pairs which are passed to mf2ff and mf
                elif arg.split('=', 1)[0] == 'jobname':
                    if '=' in arg:
                        mf2ff.jobname = arg.split('=', 1)[1]
                        mf2ff.mf_options.append(full_arg)
                    else: # the next argument is the value if no '=' is in this argument
                        mf2ff.jobname = args[i+1]
                        mf2ff.mf_options.extend([full_arg, args[i+1]])
                        i += 1
                elif arg.split('=', 1)[0] in ('base', 'progname'):
                    # progname also sets base name in mf # TODO
                    # TODO also mf_options?
                    if '=' in arg:
                        mf2ff.base = arg.split('=', 1)[1]
                    else:
                        mf2ff.base = args[i+1]
                        i += 1
                # negatable mf2ff options
                elif arg in ('cull-at-shipout', 'debug', 'extrema', 'hint', 'is_type', 'kerning-classes',
                        'otf', 'remove-artifacts', 'sfd', 'stroke-simplify', 'time', 'ttf'):
                    mf2ff.options[arg] = True
                elif arg in ('no-cull-at-shipout', 'no-debug', 'no-extrema', 'no-hint', 'no-is_type', 'no-kerning-classes',
                        'no-otf', 'no-remove-artifacts', 'no-sfd', 'no-stroke-simplify', 'no-time', 'no-ttf'):
                    mf2ff.options[full_arg[4:]] = False
                # name value option which don't need to be passed to mf (stored in options property)
                elif arg.split('=', 1)[0] == 'stroke-accuracy':
                    if '=' in arg:
                        val = arg.split('=', 1)[1]
                    else:
                        val = args[i+1]
                        i += 1
                    mf2ff.options['stroke-accuracy'] = float(val)
                # name value option which don't need to be passed to mf (stored as properties)
                elif arg.split('=', 1)[0] in font_option_names_str + font_option_names_int + font_option_names_float:
                    name = arg.split('=', 1)[0]
                    if '=' in arg:
                        val = arg.split('=', 1)[1]
                    else:
                        val = args[i+1]
                        i += 1
                    if name in font_option_names_int:
                        val = int(val)
                    elif name in font_option_names_float:
                        val = float(val)
                    mf2ff.__dict__[name] = val
                elif arg.split('=', 1)[0] == 'scripts':
                    if '=' in arg:
                        val = arg.split('=', 1)[1]
                    else:
                        val = args[i+1]
                        i += 1
                    scripts = eval(val)
                    if mf2ff.check_scripts(scripts):
                        mf2ff.scripts = scripts
                    else:
                        print('! Option -scripts cannot be processed with value `' + full_arg + '\'.')
                elif arg == 'version':
                    print('mf2ff ' + __version__)
                    print('Copyright (C) 2018--2023')
                    sys.exit()
                elif arg == 'help':
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
                        '  -ascent=NUM            set font\'s ascent\n'
                        '  -comment=STR           set font\'s comment\n'
                        '  -copyright=STR         set font\'s copyright notice\n'
                        '  -[no-]cull-at-shipout  disable/enable extra culling at shipout.\n'
                        '                           MF ships out only positive pixels which is\n'
                        '                           equivalent to cullit before shipout. (default: disabled)\n'
                        '  -[no-]debug            disable/enable debugging mode of mf2ff\n'
                        '  -descent=NUM           set font\'s descent\n'
                        '  -designsize=NUM        set font\'s design size\n'
                        '  -encoding=STR          set font\'s encoding\n'
                        '  -[no-]extrema          disable/enable extrema adding (default: disabled)\n'
                        '  -familyname=STR        set font\'s family name\n'
                        '  -fontlog=STR           set font\'s log\n'
                        '  -fontname=STR          set font\'s name\n'
                        '  -font-version=STR      set font\'s version\n'
                        '  -fullname=STR          set font\'s full name\n'
                        '  -help                  display this help\n'
                        '  -[no-]hint             disable/enable auto hinting and auto instructing (default: disabled)\n'
                        '  -[no-]is_type          disable/enable definition of is_pen and is_picture (default: disabled)\n'
                        '                           as pen and picture, respectively\n'
                        '  -italicangle=NUM       set font\'s italic angle\n'
                        '  -[no-]kerning-classes  disable/enable kerning classes instead of kerning pairs\n'
                        '                           (default: disabled = kerning pairs)'
                        '  -[no-]otf              disable/enable OpenType output generation (default: disabled)\n'
                        '  -ppi=INT               set ppi to INT\n'
                        '  -[no-]remove-artifacts disable/enable removing of artifacts (default: disabled)'
                        '  -scripts=TUPLE         set scripts for tables,\n'
                        '                           e.g. ((\'latn\',(\'dflt\',)),)\n'
                        '  -[no-]sfd              disable/enable Spline Font Database (FontForge\n'
                        '                           Project) output generation (default: enabled)\n'
                        '  -stroke-accuracy=NUM   set stroke accuracy, i.e. target for the allowed error in em-units\n'
                        '                           for layer.simplify() during layer.stoke(). Has no effect if\n'
                        '                           stroke-simplify is disabled. (default: 0.25)\n'
                        '  -[no-]stroke-simplify  disable/enable stroke simplification (default: enabled)\n'
                        '  -[no-]time             disable/enable timing (default: disabled)\n'
                        '  -[no-]ttf              disable/enable TrueType output generation (default: disabled)\n'
                        '  -upos=NUM              set the font\'s underline position\n'
                        '  -uwidth=NUM            set the font\'s underline width\n'
                        '  -version               output version information of mf2ff and exit\n'
                        '\n'
                        'The following options are also available and are passed to METAFONT:\n'
                        '  -[no-]file-line-error\n'
                        '  -halt-on-error\n'
                        '  -ini\n'
                        '  -[no-]parse-first-line\n'
                        '  -recorder\n'
                        '  -8bit\n'
                        'METAFONT\'s -version option is not passed because it only produces output on\n'
                        'the terminal.\n'
                        '\n'
                        'Please see METAFONT\'s help (run \'mf -help\') to get more information about\n'
                        'its options and for alternative usage patterns. Some of the METAFONT options\n'
                        'may have no effect in mf2ff.\n'
                        '\n'
                        '\n'
                        'It won\'t work!\n'
                        '===============\n'
                        '\n'
                        'The problem might be a non-loadable fontforge module.\n'
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
                else:
                    # current option doesn't match any of the previous cases
                    print('! Unrecognized option `' + full_arg + '\'')
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
                mf2ff.mf_first_line += arg + ' ' + ' '.join(mf2ff.args[i+1:])
                break
            else: # everything else is a filename
                mf2ff.input_file = full_arg
                if mf2ff.input_file[-3:] == '.mf':
                    # remove file extension
                    mf2ff.input_file = mf2ff.input_file[:-3]
                # Open the file and if the first line starts with %&, take this
                # as the name of the base file and tell mf to skip the first
                # line.
                try:
                    with open(mf2ff.input_file + '.mf', 'r+') as f:
                        first_line = f.readline().strip()
                        if first_line[:2] == '%&':
                            base = full_arg[2:] # TODO
                            mf2ff.mf_options.append('-no-parse-first-line')
                except IOError:
                    print('! I can\'t find file: ' + mf2ff.input_file + '.mf.')
                    sys.exit()
                break
        i += 1 # next argument

def main():
    print('This is mf2ff, version ' + __version__ + '.')
    print('Run with -help option for help with the use of mf2ff, license information and how to report bugs.')
    print('This program is still under development. Bugs may occur.\n')

    mf2ff = Mf2ff()
    parse_arguments(mf2ff)
    mf2ff.run()

if __name__ == '__main__':
    main()
