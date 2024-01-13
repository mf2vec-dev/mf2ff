import os
from pathlib import Path
from time import sleep, time
from urllib.error import URLError
from urllib.request import urlretrieve

from mf2ff import Mf2ff

if __name__ == '__main__':
    example_dir = Path(__file__).parent
    inputs_dir = example_dir / '..' / 'example_inputs' / 'cm'
    inputs_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(inputs_dir) # mf will search in cwd

    urls = [
        'http://mirrors.ctan.org/fonts/cm/mf/accent.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/cmbase.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/cmcsc10.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/cmr10.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/comlig.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/csc.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/cscspu.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/greeku.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/punct.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/romand.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/romanp.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/romanu.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/romspu.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/romsub.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/sym.mf',
    ]
    print(f'retrieving {len(urls)} mf files...')
    for i_url, url in enumerate(urls):
        filename = url.rsplit('/', 1)[1]
        i_attempt = 0
        while True:
            try:
                urlretrieve(url, inputs_dir / filename)
                break
            except URLError as e:
                if i_attempt < 5:
                    print(f'error in attempt {i_attempt+1}/5 of retrieving URL {i_url+1}/{len(urls)} ({url})')
                    sleep(5)
                    i_attempt += 1
                else:
                    print('tried 5 times, doesn\'t work')
                    raise e

    start = time()
    mf2ff = Mf2ff()
    mf2ff.options.inputs = [
        {
            'input_file': inputs_dir / 'cmr10',
            'input_encoding': 'TeX text'
        },
        {
            'input_file': inputs_dir / 'cmcsc10',
            'input_encoding': 'TeX text without f-ligatures',
            'only_code_points': [
                [25, 31], # germandbls, ae, oe, oslash, AE, OE, Oslash
                [65, 90], # A-Z
                [97, 122] # a-z
            ],
            'ot_sub_feature': 'smcp',
            'glyph_name_suffix': '.sc'
        }
    ]
    mf2ff.options.output_encoding = 'TeX text'
    mf2ff.options.jobname = 'cmr10_smcp'
    mf2ff.options.output_directory = example_dir
    mf2ff.options.stroke_simplify = False
    mf2ff.options.fix_contours = True
    mf2ff.options.remove_artifacts = True
    mf2ff.options.remove_collinear = True
    mf2ff.options.cull_at_shipout = True
    mf2ff.options.upm = 4096
    mf2ff.run()
    print(f'took {time()-start:.3f} sec')
