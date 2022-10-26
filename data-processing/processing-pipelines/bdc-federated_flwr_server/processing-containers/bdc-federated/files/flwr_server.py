import flwr as fl
import os
import json

# for input parameter defined in Meta Dashboard's UI
MY_WORKFLOW_DIR = os.environ['WORKFLOW_DIR']
with open(os.path.join('/', MY_WORKFLOW_DIR, 'conf/conf.json'), 'r') as f:
    ui_confs = json.load(f)
num_fl_rounds = ui_confs['workflow_form']['federated_rounds']

if __name__ == "__main__":
    fl.server.start_server(server_address="10.133.193.85:8080", config=fl.server.ServerConfig(num_rounds=num_fl_rounds))