from pathlib import Path
from tempfile import TemporaryDirectory

import fontforge


def load_encoding(encoding_name, glyph_name_list):
    with TemporaryDirectory() as tmp_dir_name:
        file_path = Path(tmp_dir_name) / (encoding_name+'.ps')
        with open(file_path, "w") as file:
            file.write('/' + encoding_name + ' [\n')
            for encoding_name in glyph_name_list:
                file.write(' ' + encoding_name + '\n')
            file.write('] def')
        fontforge.loadEncodingFile(str(file_path))

def load_tex_text(Delta_as_increment=False, combining_diacritical_marks=False, pound=False):
    nd = '/.notdef'
    load_encoding('TeX-text', [ # comment is last in line
        '/Gamma', ('/Delta' if Delta_as_increment else '/uni0394'), '/Theta', '/Lambda', '/Xi', '/Pi', '/Sigma', '/Upsilon', # 0x07
        '/Phi', '/Psi', '/Omega', '/ff', '/fi', '/fl', '/ffi', '/ffl', # 0x0F
        '/dotlessi', '/dotlessj'] + (
            ['/gravecomb', '/acutecomb', '/uni030C', '/uni0306', '/uni0304', '/uni030A', # 0x17
        '/uni0327']
            if combining_diacritical_marks else
            ['/grave', '/acute', '/caron', '/breve', '/macron', '/ring', # 0x17
        '/cedilla']
            ) + ['/germandbls', '/ae', '/oe', '/oslash', '/AE', '/OE', '/Oslash', # 0x1F
        ('/uni0337' if combining_diacritical_marks else nd), # ?
            '/exclam', '/quotedblright', '/numbersign', ('/sterling' if pound else '/dollar'), '/percent', '/ampersand', '/quoteright', # 0x27
        '/parenleft', '/parenright', '/asterisk', '/plus', '/comma', '/hyphen', '/period', '/slash', # 0x2F
        '/zero', '/one', '/two', '/three', '/four', '/five', '/six', '/seven', # 0x37
        '/eight', '/nine', '/colon', '/semicolon', '/exclamdown', '/equal', '/questiondown', '/question', # 0x3F
        '/at', '/A', '/B', '/C', '/D', '/E', '/F', '/G', # 0x47
        '/H', '/I', '/J', '/K', '/L', '/M', '/N', '/O', # 0x4F
        '/P', '/Q', '/R', '/S', '/T', '/U', '/V', '/W', # 0x57
        '/X', '/Y', '/Z', '/bracketleft', '/quotedblleft', '/bracketright'] + (
            ['/uni0302', '/uni0307'] # 0x5F
            if combining_diacritical_marks else
            ['/circumflex', '/dotaccent'] # 0x5F
            ) + [
        '/quoteleft', '/a', '/b', '/c', '/d', '/e', '/f', '/g', # 0x67
        '/h', '/i', '/j', '/k', '/l', '/m', '/n', '/o', # 0x6F
        '/p', '/q', '/r', '/s', '/t', '/u', '/v', '/w', # 0x77
        '/x', '/y', '/z', '/endash', '/emdash'] + (
            ['/uni030B', '/tildecomb', '/uni0308'] # 0x7F
            if combining_diacritical_marks else
            ['/hungarumlaut', '/tilde', '/dieresis'] # 0x7F
            ) + [
    ])

def load_tex_typewriter_text(Delta_as_increment=False, combining_diacritical_marks=False):
    load_encoding('TeX-typewriter-text', [ # comment is last in line
        '/Gamma', ('/Delta' if Delta_as_increment else '/uni0394'), '/Theta', '/Lambda', '/Xi', '/Pi', '/Sigma', '/Upsilon', # 0x07
        '/Phi', '/Psi', '/Omega', '/arrowup', '/arrowdown', '/quotesingle', '/exclamdown', '/questiondown', # 0x0F
        '/dotlessi', '/dotlessj'] + (
            ['/gravecomb', '/acutecomb', '/uni030C', '/uni0306', '/uni0304', '/uni030A', # 0x17
        '/uni0327']
            if combining_diacritical_marks else
            ['/grave', '/acute', '/caron', '/breve', '/macron', '/ring', # 0x17
        '/cedilla']
            ) + ['/germandbls', '/ae', '/oe', '/oslash', '/AE', '/OE', '/Oslash', # 0x1F
        '/uni2423', '/exclam', '/quotedbl', '/numbersign', '/dollar', '/percent', '/ampersand', '/quoteright', # 0x27
        '/parenleft', '/parenright', '/asterisk', '/plus', '/comma', '/hyphen', '/period', '/slash', # 0x2F
        '/zero', '/one', '/two', '/three', '/four', '/five', '/six', '/seven', # 0x37
        '/eight', '/nine', '/colon', '/semicolon', '/less', '/equal', '/greater', '/question', # 0x3F
        '/at', '/A', '/B', '/C', '/D', '/E', '/F', '/G', # 0x47
        '/H', '/I', '/J', '/K', '/L', '/M', '/N', '/O', # 0x4F
        '/P', '/Q', '/R', '/S', '/T', '/U', '/V', '/W', # 0x57
        '/X', '/Y', '/Z', '/bracketleft', '/backslash', '/bracketright', ('/uni0302' if combining_diacritical_marks else '/circumflex'), '/underscore', # 0x5F
        '/quoteleft', '/a', '/b', '/c', '/d', '/e', '/f', '/g', # 0x67
        '/h', '/i', '/j', '/k', '/l', '/m', '/n', '/o', # 0x6F
        '/p', '/q', '/r', '/s', '/t', '/u', '/v', '/w', # 0x77
        '/x', '/y', '/z', '/braceleft', '/bar', '/braceright'] + (
            ['/tildecomb', '/uni0308'] # 0x7F
            if combining_diacritical_marks else
            ['/tilde', '/dieresis'] # 0x7F
            ) + [
    ])

def load_tex_math_italic(swap_epsilon=False, swap_phi=False, oldstyle_as_basic=False, latin_as_basic=False, greek_as_basic=False):
    nd = '/.notdef'
    load_encoding('TeX-math-italic', [ # comment is last in line
        ] + ([
        '/uni0393', '/uni0394', '/uni0398', '/uni039B', '/uni039E', '/uni03A0', '/uni03A3', '/uni03A5', # 0x07
        '/uni03A6', '/uni03A8', '/uni03A9', '/uni03B1', '/uni03B2', '/uni03B3', '/uni03B4', ('/uni03B5' if swap_epsilon else '/uni03F5'), # 0x0F
        '/uni03B6', '/uni03B7', '/uni03B8', '/uni03B9', '/uni03BA', '/uni03BB', '/uni03BC', '/uni03BD', # 0x17
        '/uni03BE', '/uni03C0', '/uni03C1', '/uni03C3', '/uni03C4', '/uni03C5', ('/uni03C6' if swap_phi else '/uni03D5'), '/uni03C7', # 0x1F
        '/uni03C8', '/uni03C9', ('/uni03F5' if swap_epsilon else '/uni03B5'), '/u1D717', '/uni03D1', '/u1D7F1', '/uni3C2', ('/uni03D5' if swap_phi else '/uni03C6') # 0x27
        ] if greek_as_basic else [
        '/u1D6E4', '/u1D6E5', '/u1D6E9', '/u1D6EC', '/u1D6EF', '/u1D6F1', '/u1D6F4', '/u1D6F6', # 0x07
        '/u1D6F7', '/u1D6F9', '/u1D6FA', '/u1D6FC', '/u1D6FD', '/u1D6FE', '/u1D6FF', ('/u1D700' if swap_epsilon else '/u1D716'), # 0x0F
        '/u1D701', '/u1D702', '/u1D703', '/u1D704', '/u1D705', '/u1D706', '/u1D707', '/u1D708', # 0x17
        '/u1D709', '/u1D70B', '/u1D70C', '/u1D70E', '/u1D70F', '/u1D710', ('/u1D711' if swap_phi else '/u1D719'), '/u1D712', # 0x1F
        '/u1D713', '/u1D714', ('/u1D716' if swap_epsilon else '/u1D700'), '/u1D717', '/u1D71B', '/u1D71A', '/u1D70D', ('/u1D719' if swap_phi else '/u1D711') # 0x27
        ]) + [
        '/uni21BC', '/uni21BD', '/uni21C0', '/uni21C1', nd, nd, '/uni25B7', '/uni25C1', # 0x2F
        ] + ([
        '/zero', '/one', '/two', '/three', '/four', '/five', '/six', '/seven', # 0x37
        '/eight', '/nine']
        if oldstyle_as_basic else [
        nd, nd, nd, nd, nd, nd, nd, nd, # oldstyle # 0x37
        nd, nd]
            ) + ['/period', '/comma', '/less', '/slash', '/greater', '/uni22C6', # 0x3F
        '/partialdiff'] + (
            ['/A', '/B', '/C', '/D', '/E', '/F', '/G', # 0x47
        '/H', '/I', '/J', '/K', '/L', '/M', '/N', '/O', # 0x4F
        '/P', '/Q', '/R', '/S', '/T', '/U', '/V', '/W', # 0x57
        '/X', '/Y', '/Z']
            if latin_as_basic else
            ['/u1D434', '/u1D435', '/u1D436', '/u1D437', '/u1D438', '/u1D439', '/u1D43A', # 0x47
        '/u1D43B', '/u1D43C', '/u1D43D', '/u1D43E', '/u1D43F', '/u1D440', '/u1D441', '/u1D442', # 0x4F
        '/u1D443', '/u1D444', '/u1D445', '/u1D446', '/u1D447', '/u1D448', '/u1D449', '/u1D44A', # 0x57
        '/u1D44B', '/u1D44C', '/u1D44D']
            ) + ['/uni266D', '/uni266E', '/uni266F', '/uni2323', '/uni2322', # 0x5F
        '/uni2113'] + (
            ['/a', '/b', '/c', '/d', '/e', '/f', '/g', # 0x67
        '/h', '/i', '/j', '/k', '/l', '/m', '/n', '/o', # 0x6F
        '/p', '/q', '/r', '/s', '/t', '/u', '/v', '/w', # 0x77
        '/x', '/y', '/z']
            if latin_as_basic else
            ['/u1D44E', '/u1D44F', '/u1D450', '/u1D451', '/u1D452', '/u1D453', '/u1D454', # 0x67
        '/uni210E', '/u1D456', '/u1D457', '/u1D458', '/u1D459', '/u1D45A', '/u1D45B', '/u1D45C', # 0x6F
        '/u1D45D', '/u1D45E', '/u1D45F', '/u1D460', '/u1D461', '/u1D462', '/u1D463', '/u1D464', # 0x77
        '/u1D465', '/u1D466', '/u1D467']
            ) + ['/u1D6A4', '/u1D6A5', '/weierstrass', '/uni20D7', '/uni0311', # 0x7F
    ])

def load_tex_math_symbols(prime=False, script_as_basic=False):
    nd = '/.notdef'
    load_encoding('TeX-math-symbols', [ # comment is last in line
        '/minus', '/dotmath', '/multiply', '/asteriskmath', '/divide', '/uni22C4', '/plusminus', '/uni2213', # 0x07
        '/circleplus', '/uni2296', '/circlemultiply', '/uni2298', '/uni2299', '/uni20DD', '/uni2218', '/bullet',  # not /uni2219 (BULLET OPERATOR) # 0x0F
        '/uni224D', '/equivalence', '/reflexsubset', '/reflexsuperset', '/lessequal', '/greaterequal', '/uni227C', '/uni227D', # 0x17
        '/similar', '/approxequal', '/propersubset', '/propersuperset', '/uni226A', '/uni226B', '/uni227a', '/uni227B', # 0x1F
        '/arrowleft', '/arrowright', '/arrowup', '/arrowdown', '/arrowboth', '/uni2197', '/uni2198', '/uni2243', # 0x27
        '/arrowdblleft', '/arrowdblright', '/arrowdblup', '/arrowdbldown', '/arrowdblboth', '/uni2196', '/uni2199', '/proportional', # 0x2F
        ('/prime' if prime else nd), '/infinity', '/element', '/suchthat', '/uni25B3', '/uni25BD', '/uni0338', nd, # 0x37
        '/universal', '/existential', '/logicalnot', '/emptyset', '/Rfractur', '/Ifractur', '/uni22A4', '/perpendicular', # 0x3F
        '/aleph'] + (
            ['/A', '/B', '/C', '/D', '/E', '/F', '/G', # 0x47
        '/H', '/I', '/J', '/K', '/L', '/M', '/N', '/O', # 0x4F
        '/P', '/Q', '/R', '/S', '/T', '/U', '/V', '/W', # 0x57
        '/X', '/Y', '/Z']
            if script_as_basic else
            ['/u1D49C', '/uni212C', '/u1D49E', '/u1D49F', '/uni2130', '/uni2131', '/u1D4A2', # 0x47
        '/uni210B', '/uni2110', '/u1D4A5', '/u1D4A6', '/uni2112', '/uni2133', '/u1D4A9', '/u1D4AA', # 0x4F
        '/u1D4AB', '/u1D4AC', '/uni211B', '/u1D4AE', '/u1D4AF', '/u1D4B0', '/u1D4B1', '/u1D4B2', # 0x57
        '/u1D4B3', '/u1D4B4', '/u1D4B5']
            ) + ['/union', '/intersection', '/uni228E', '/logicaland', '/logicalor', # 0x5F
        '/uni22A2', '/uni22A3', '/uni230A', '/uni230B', '/uni2308', '/uni2309', '/braceleft', '/braceright', # 0x67
        '/uni27E8', '/uni27E9', '/bar', '/uni2016', '/arrowupdn', '/uni21D5', '/backslash', '/uni2240', # 0x6F
        '/radical', '/uni2A3F', '/gradient', nd, # \smallint not in unicode
            '/uni2294', '/uni2293', '/uni2291', '/uni2292', # 0x77
        '/section', '/dagger', '/daggerdbl', '/paragraph', '/club', '/uni2662', '/uni2661', '/spade', # 0x7F
    ])

def load_tex_math_extension():
    nd = '/.notdef'
    load_encoding('TeX-math-extension', [ # comment is last in line
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x07
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x0F
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x17
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x1F
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x27
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x2F
        '/uni239B', '/uni239E', '/uni23A1', '/uni23A4', '/uni23A3', '/uni23A6', '/uni23A2', '/uni23A5', # 0x37
        '/uni23A7', '/uni23AB', '/uni23A9', '/uni23AD', '/uni23A8', '/uni23AC', '/uni23AA', nd, # 0x3F
        '/uni239D', '/uni23A0', '/uni239C', '/uni239F', nd, nd, '/2A06', nd, # 0x47
        '/uni222E', nd, '/uni2A00', nd, '/uni2A01', nd, '/uni2A02', nd, # 0x4F
        '/summation', '/product', '/integral', '/uni22C3', '/uni22C2', '/uni2A04', '/uni22C0', '/uni22C1', # 0x57
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x5F
        '/uni2210', nd, nd, nd, nd, nd, nd, nd, # 0x67
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x6F
        nd, nd, nd, nd, '/uni23B7', '/uni20D3', # ? radical extension
            nd, nd, # 0x77
        nd, nd, nd, nd, nd, nd, nd, nd, # 0x7F
    ])

def load_tex_extended_ascii(apostrophe=False, minus=False, combining_diacritical_marks=False, grave=False, integral=False):
    nd = '/.notdef'
    load_encoding('TeX-extended-ASCII', [ # comment is last in line
        '/dotmath', '/arrowdown', '/alpha', '/beta', '/logicaland', '/logicalnot', '/element', '/pi', # 0x07
        '/lambda', '/gamma', '/delta', '/arrowup', '/plusminus', '/circleplus', '/infinity', '/partialdiff', # 0x0F
        '/propersubset', '/propersuperset', '/intersection', '/union', '/universal', '/existential', '/circlemultiply', '/uni21C6', # 0x17
        '/arrowleft', '/arrowright', '/notequal', '/uni22C4', '/lessequal', '/greaterequal', '/equivalence', '/logicalor', # 0x1F
        '/space', '/exclam', '/quotedbl', '/numbersign', '/dollar', '/percent', '/ampersand', ('/quoteright' if apostrophe else '/quotesingle'), # 0x27
        '/parenleft', '/parenright', '/asterisk', '/plus', '/comma', ('/minus' if minus else '/hyphen'), '/period', '/slash', # 0x2F
        '/zero', '/one', '/two', '/three', '/four', '/five', '/six', '/seven', # 0x37
        '/eight', '/nine', '/colon', '/semicolon', '/less', '/equal', '/greater', '/question', # 0x3F
        '/at', '/A', '/B', '/C', '/D', '/E', '/F', '/G', # 0x47
        '/H', '/I', '/J', '/K', '/L', '/M', '/N', '/O', # 0x4F
        '/P', '/Q', '/R', '/S', '/T', '/U', '/V', '/W', # 0x57
        '/X', '/Y', '/Z', '/bracketleft', '/backslash', '/bracketright', ('/uni0302' if combining_diacritical_marks else '/circumflex'), '/underscore', # 0x5F
        (('/gravecomb' if combining_diacritical_marks else '/grave') if grave else '/quoteleft'), '/a', '/b', '/c', '/d', '/e', '/f', '/g', # 0x67
        '/h', '/i', '/j', '/k', '/l', '/m', '/n', '/o', # 0x6F
        '/p', '/q', '/r', '/s', '/t', '/u', '/v', '/w', # 0x77
        '/x', '/y', '/z', '/braceleft', '/bar', '/braceright', ('/tildecomb'if combining_diacritical_marks else '/tilde'), ('/integral' if integral else nd), # 0x7F
    ])
