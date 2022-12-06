from datetime import timedelta
from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator, default_registry, default_platform_abbr, default_platform_version


class Itk2DcmOperator(KaapanaBaseOperator):

    def __init__(self,
                 dag,
                 name=None,
                 execution_timeout=timedelta(minutes=90),
                 *args, **kwargs
                 ) -> None:

        name = name if name is not None else "itk2dcm-converter"

        super().__init__(
            dag=dag,
            name=name,
            image=f"{default_registry}/itk2dcm-dev:0.1.0",
            image_pull_policy="Always",
            image_pull_secrets=["registry-secret"],
            execution_timeout=execution_timeout,
            *args,
            **kwargs
        )