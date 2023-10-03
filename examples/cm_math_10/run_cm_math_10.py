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
        'http://mirrors.ctan.org/fonts/cm/mf/bigacc.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/bigdel.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/bigop.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/calu.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/cmbase.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/cmex10.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/cmmi10.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/cmsy10.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/greekl.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/greeku.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/itall.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/italms.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/mathex.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/mathit.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/mathsy.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/olddig.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/romanu.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/romms.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/sym.mf',
        'http://mirrors.ctan.org/fonts/cm/mf/symbol.mf',
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
            'input_file': inputs_dir / 'cmmi10',
            'input_encoding': 'TeX math italic'
        },
        {
            'input_file': inputs_dir / 'cmsy10',
            'input_encoding': 'TeX math symbols'
        },
        {
            'input_file': inputs_dir / 'cmex10',
            'input_encoding': 'TeX math extension'
        }
    ]
    mf2ff.options.jobname = 'cm_math_10'
    mf2ff.options.ascent = 103
    mf2ff.options.descent = 34
    mf2ff.options.output_directory = example_dir
    mf2ff.options.stroke_simplify = False
    mf2ff.options.fix_contours = True
    mf2ff.options.remove_artifacts = True
    mf2ff.options.cull_at_shipout = True
    mf2ff.options.set_top_accent = True
    mf2ff.options.kerning_classes = False
    mf2ff.options.upm = 1000
    mf2ff.options.set_math_defaults = True
    mf2ff.run()
    print(f'took {time()-start:.3f} sec')
