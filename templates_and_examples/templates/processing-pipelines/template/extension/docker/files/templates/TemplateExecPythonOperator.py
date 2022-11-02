from datetime import timedelta


from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator, default_registry, default_build_version


class TemplateExecPythonOperator(KaapanaBaseOperator):

    def __init__(self,
                 dag,
                 execution_timeout=timedelta(minutes=15),
                 *args, **kwargs
                 ):

        super().__init__(
            dag=dag,
            name='temp-exec-python',
            image=f"{default_registry}/python-template:{default_build_version}
            image_pull_secrets=["registry-secret"],
            execution_timeout=execution_timeout,
            *args,
            **kwargs
        )

