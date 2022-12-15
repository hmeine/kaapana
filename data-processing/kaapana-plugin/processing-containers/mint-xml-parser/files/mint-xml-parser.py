import os
import subprocess
from pathlib import Path

# print(list(((Path(os.getcwd())).glob('*'))))
# print((Path(os.getcwd()) / 'workflow_dir').exists())
# os.environ["WORKFLOW_DIR"] = os.getcwd() + '/workflow_dir'
# os.environ["BATCH_NAME"] = "batch"
# os.environ["OPERATOR_IN_DIR"] = "input"
# os.environ["OPERATOR_OUT_DIR"] = "output"

path_to_saxon = Path(os.getcwd()) / 'saxon' / 'saxon-he-11.4.jar'
xsl_file = Path(os.getcwd(), "trialcsv-detailed.xsl")

# From the template
batch_folders = sorted(list(
    Path('/', os.environ['WORKFLOW_DIR'], os.environ['BATCH_NAME']).glob('*')
))

for batch_element_dir in batch_folders:

    element_input_dir = batch_element_dir / os.environ['OPERATOR_IN_DIR']
    element_output_dir = batch_element_dir / os.environ['OPERATOR_OUT_DIR']

    element_output_dir.mkdir(exist_ok=True)

    # The processing algorithm
    print(
        f'Checking {element_input_dir} for dcm files and '
        f'writing results to {element_output_dir}'
    )
    xml_files = sorted(list(element_input_dir.rglob("*.xml")))

    if len(xml_files) == 0:
        print("No xml file found!")
    else:
        for xml_file in xml_files:
            print(f'Parsing XML-file: {xml_file}')

            output_file = (element_output_dir / xml_file.name) \
                .with_suffix(".csv")

            print(f"xml_file: {xml_file}")
            print(f"output_file: {output_file}")

            command = f"java -jar {path_to_saxon} " \
                      f"-s:{xml_file} " \
                      f"-xsl:{xsl_file} " \
                      f"-o:{output_file}"
            print(command)
            try:
                subprocess.check_output(command, shell=True)
                print(f'Successfully parsed: {xml_file}')
            except Exception as e:
                print(f'Processing of {xml_file} threw an exception: ', e)
