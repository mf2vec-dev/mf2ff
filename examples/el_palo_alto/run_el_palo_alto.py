import os
from pathlib import Path
from time import time
from urllib.request import urlopen

from mf2ff import Mf2ff

if __name__ == '__main__':
    example_dir = Path(__file__).parent
    inputs_dir = example_dir / '..' / 'example_inputs' / 'el_palo_alto'
    inputs_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(inputs_dir) # mf will search in cwd

    url = 'http://mirrors.ctan.org/fonts/manual/mf/mfman.mf'
    response = urlopen(url)
    data = response.read()
    file_content = data.decode('utf-8')
    # everything between the line after the first 'El Palo Alto' and the line
    # before the next 'Figure' line is the code
    tree_code = file_content.split('El Palo Alto', 1)[1].split('\n', 1)[1].split('Figure', 1)[0].rsplit('\n', 1)[0]
    tree_paths = tree_code.split('\n', 1)[1].rsplit('\n', 10)[0]
    tree_mf_str = (
        # everything before the line of the first figure is important
        file_content.split('Figure', 1)[0].rsplit('\n', 1)[0]
        + '\n\n'
        + 'beginchar("T", .5in#, 1.25in#, 0);\n' # see The METAFONTbook, p. 126
        + tree_paths
        + '\n' # below: see The METAFONTbook, p. 126
        + 'fill superellipse((w, .5h), (.5w, h), (0, .5h), (.5w, 0), .8);\n'
        + 'branch0 = trunk;\n'
        + 'for n = 0 upto 12:\n'
        + ' unfill branch[n] shifted (150, 50) scaled (w/300);\n'
        + 'endfor endchar;\n'
        # everything after the last char is important
        + file_content.rsplit('endchar;', 1)[1]
    ) # TODO mode
    input_file = inputs_dir / 'el_palo_alto.mf'
    with open(input_file, 'w') as f:
        f.write(tree_mf_str)

    start = time()
    mf2ff = Mf2ff()
    mf2ff.options.input_file = input_file
    mf2ff.options.output_directory = example_dir
    mf2ff.options.stroke_simplify = False
    mf2ff.options.fix_contours = True
    mf2ff.options.remove_artifacts = True
    mf2ff.options.remove_collinear = True
    mf2ff.options.cull_at_shipout = True
    mf2ff.run()
    print(f'took {time()-start:.3f} sec')
