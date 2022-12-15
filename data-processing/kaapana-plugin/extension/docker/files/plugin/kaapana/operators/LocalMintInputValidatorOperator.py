import os
from pathlib import Path

import pydicom

from kaapana.blueprints.kaapana_global_variables import WORKFLOW_DIR, BATCH_NAME
from kaapana.operators.KaapanaPythonBaseOperator import \
    KaapanaPythonBaseOperator


class LocalMintInputValidatorOperator(KaapanaPythonBaseOperator):
    def start(self, ds, **kwargs):
        run_dir = os.path.join(WORKFLOW_DIR, kwargs['dag_run'].run_id)
        batch_folders = [*Path(run_dir, BATCH_NAME).glob('*')]

        for batch_element_dir in batch_folders:
            element_input_dir = batch_element_dir / self.operator_in_dir
            element_output_dir = batch_element_dir / self.operator_out_dir

            element_output_dir.mkdir(exist_ok=True)

            # The processing algorithm
            print(
                f'Checking {element_input_dir} for dcm files '
                f'and writing results to {element_output_dir}'
            )
            dcm_files = sorted(list(element_input_dir.rglob("*.dcm")))

            if len(dcm_files) == 0:
                print("No dcm file found!")
                exit(0)
            else:
                for dcm_file in dcm_files:
                    print(f'Validating DCM-file: {dcm_file}')
                    target_file = (element_output_dir / dcm_file.name) \
                        .with_suffix('.xml')
                    print(f'Output path is {target_file}.')
                    dcm = pydicom.dcmread(dcm_file)
                    if not (
                            dcm.get('Manufacturer') == 'Mint Medical GmbH'
                            and dcm.get('Modality') == 'OT'
                    ):
                        print(
                            'DICOM does not contain Manufacturer tag '
                            'Mint Medical GmbH  and does not have the modality OT'
                        )
                        continue

                    with open(target_file, "w") as xml_file:
                        xml_file.write(
                            dcm[0x9071, 0x1000]
                                .value
                                .decode("UTF-8")
                                .replace("\x00", "")
                        )

                    print(f'Successfully extracted XML file: {xml_file}')

    def __init__(self,
                 dag,
                 name='mint-input-validator',
                 **kwargs):

        super().__init__(
            dag=dag,
            name=name,
            python_callable=self.start,
            **kwargs
        )
