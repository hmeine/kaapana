from datetime import timedelta

from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator, \
    default_registry, kaapana_build_version


class MintXmlParserOperator(KaapanaBaseOperator):
    execution_timeout = timedelta(minutes=10)

    def __init__(self,
                 dag,
                 name="mint-xml-parser",
                 env_vars={},
                 execution_timeout=execution_timeout,
                 **kwargs
                 ):
        super().__init__(
            dag=dag,
            image=f"{default_registry}/mint-xml-parser:{kaapana_build_version}",
            name=name,
            image_pull_secrets=["registry-secret"],
            execution_timeout=execution_timeout,
            keep_parallel_id=False,
            env_vars=env_vars,
            ram_mem_mb=5000,
            **kwargs
        )
