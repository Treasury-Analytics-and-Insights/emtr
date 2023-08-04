#!/usr/bin/env python3


from argparse import ArgumentParser
import pathlib

import yaml
from jinja2 import Template


PARSER = ArgumentParser()
PARSER.add_argument(
    'tawa_param_dir', type=pathlib.Path, 
    help='Directory with TAWA format YAML parameter files')
PARSER.add_argument(
    'output_dir', type=pathlib.Path, 
    help='Directory to write EMTR format YAML parameter files')

def main(args):
    tawa_param_files = args.tawa_param_dir.glob('*.yaml')

    # load the jinja2 template
    with open('efu_param_template.jinja2') as f:
        template = Template(f.read())

    if not args.output_dir.exists():
        args.output_dir.mkdir()

    for tawa_param_file in tawa_param_files:
        with open(tawa_param_file) as f:
            tawa_params = yaml.safe_load(f)

        print(f"Converting {tawa_param_file.name}")
        # render the template
        emtr_params = template.render(tawa_param=tawa_params)

        # write the output
        output_file = args.output_dir / tawa_param_file.name
        with open(output_file, 'w') as f:
            f.write(emtr_params)

        
        
        
        

if __name__ == '__main__':
    args = PARSER.parse_args()
    main(args)



