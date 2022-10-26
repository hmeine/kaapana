import os
from datetime import timedelta
from datetime import datetime


from airflow.models import DAG
from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule

from kaapana.blueprints.kaapana_global_variables import INSTANCE_NAME
from kaapana.operators.LocalWorkflowCleanerOperator import LocalWorkflowCleanerOperator
from kaapana.operators.ZipUnzipOperator import ZipUnzipOperator
from kaapana.operators.LocalMinioOperator import LocalMinioOperator
from bdc_federated_flwr_server.BDCFederatedFlwrServerOperator import BDCFederatedFlwrServerOperator

log = LoggingMixin().log

# FL releated
# remote_dag_id = "bdc-federated-flwr-node"     # name of DAG which should be executed in a federated way
# overview of all operators: "get_from_minio_init", "get_input", "train_val_split", "put_to_minio_split", "get_from_minio_split", "breast_density_classifier", "clean"
# skip_operators are operators which are skipped during a round of the remote_dag

# skip_operators = ['get_from_minio_split', 'breast_density_classifier', 'workflow-cleaner']     # 'workflow-cleaner', partially operators of this federated DAG, partially operators of executed "regular" DAG
# skip_operators = ['workflow-cleaner']

# federated_operators are operators which are executed during a round of the remot_dag
# federated_operators = ['breast_density_classifier']

# UI forms
ui_forms = {
    "workflow_form": {
        "type": "object",
        "properties": {
            "federated_rounds": {
                "title": "federated rounds",
                "default": 5,
                "description": "Federated communication rounds between server and node instances",
                "type": "integer",
                "required": True,
                "readOnly": False
            }
        }
    }
}

args = {
    'ui_visible': True,     # DAG can be selected in Meta-Dashboard
    # 'ui_federated': True,   # DAG can be selected in Kaapana Federated
    'ui_forms': ui_forms,
    'owner': 'kaapana',
    'start_date': days_ago(0),
    'retries': 0,
    'retry_delay': timedelta(seconds=30)
}

dag = DAG(
    dag_id='bdc-federated-flwr-server',
    default_args=args,
    concurrency=5,
    max_active_runs=1,
    schedule_interval=None
)

bdc_fl_flwr_server = BDCFederatedFlwrServerOperator(dag=dag,
                                                    # dev_server='code-server',
                                                    )

put_to_minio = LocalMinioOperator(dag=dag,
                                 action='put',
                                 action_operators=[bdc_fl_flwr_server],
                                 zip_files=True,
                                 file_white_tuples=('.zip'),
                                 )

clean = LocalWorkflowCleanerOperator(dag=dag,
                                    clean_workflow_dir=True,
                                    )


bdc_fl_flwr_server >> put_to_minio >> clean
