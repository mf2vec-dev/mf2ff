from pathlib import Path
from time import time
from urllib.request import urlopen

from mf2ff import Mf2ff

if __name__ == '__main__':
    example_dir = Path(__file__).parent
    inputs_dir = example_dir / '..' / 'example_inputs' / 'jofa_logo'
    inputs_dir.mkdir(parents=True, exist_ok=True)

    url = 'http://mirrors.ctan.org/fonts/manual/mf/mfman.mf'
    filename = 'jofa.mf'
    response = urlopen(url)
    data = response.read()
    file_content = data.decode('utf-8')
    # everything between the line after the first 'JofA logo' and the line
    # before the next 'Figure' line is the code
    logo_code = file_content.split('JofA logo', 1)[1].split('\n', 1)[1].split('Figure', 1)[0].rsplit('\n', 1)[0]
    logo_mf_str = (
        # everything before the line of the first figure is important
        file_content.split('Figure',1)[0].rsplit('\n',1)[0] 
        + '\n\n'
        + logo_code
        # everything after the last char is important
        + file_content.rsplit('endchar;',1)[1]
    )
    input_file = inputs_dir / 'jofa_logo.mf'
    with open(input_file, 'w') as f:
        f.write(logo_mf_str)

    start = time()
    mf2ff = Mf2ff()
    mf2ff.input_file = str(input_file)
    jobname = example_dir / 'jofa_logo'
    mf2ff.jobname = str(jobname)
    mf2ff.mf_options.append('-jobname=' + str(jobname))
    mf2ff.options['cull-at-shipout'] = True
    mf2ff.run()
    print(f'took {time()-start:.3f} sec')
