import os
import glob
from datetime import timedelta

from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator, default_registry, kaapana_build_version

class nnUNetFederatedOperator(KaapanaBaseOperator):

    def __init__(self,
                 dag,
                 name='nnunet-federated',
                 execution_timeout=timedelta(days=5),
                 *args, **kwargs
                 ):

        super().__init__(
            dag=dag,
            name=name,
            image=f"{default_registry}/nnunet-federated:{kaapana_build_version}",
            image_pull_secrets=["registry-secret"],
            execution_timeout=execution_timeout,
            ram_mem_mb=1000,
            ram_mem_mb_lmt=None,
            *args, **kwargs
        )