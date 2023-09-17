import os
from pathlib import Path
from time import time
from urllib.request import urlopen

from mf2ff import Mf2ff

if __name__ == '__main__':
    example_dir = Path(__file__).parent
    inputs_dir = example_dir / '..' / 'example_inputs' / 'dangerous_bend_symbol'
    inputs_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(inputs_dir) # mf will search in cwd

    url = 'http://mirrors.ctan.org/fonts/manual/mf/mfman.mf'
    response = urlopen(url)
    data = response.read()
    file_content = data.decode('utf-8')
    # everything between the line after the first 'Dangerous bend symbol' and the line
    # before the next 'Figure' line is the code
    symbol_code = file_content.split('Dangerous bend symbol', 1)[1].split('\n', 1)[1].split('Figure', 1)[0].rsplit('\n', 1)[0]
    symbol_mf_str = (
        # everything before the line of the first figure is important
        file_content.split('Figure',1)[0].rsplit('\n',1)[0] 
        + '\n\n'
        + symbol_code
        # everything after the last char is important
        + file_content.rsplit('endchar;',1)[1]
    )
    input_file = inputs_dir / 'dangerous_bend_symbol.mf'
    with open(input_file, 'w') as f:
        f.write(symbol_mf_str)

    start = time()
    mf2ff = Mf2ff()
    mf2ff.options.input_file = input_file
    mf2ff.options.output_directory = example_dir
    mf2ff.options.stroke_simplify = False
    mf2ff.options.fix_contours = True
    mf2ff.options.remove_artifacts = True
    mf2ff.options.cull_at_shipout = True
    mf2ff.run()
    print(f'took {time()-start:.3f} sec')
