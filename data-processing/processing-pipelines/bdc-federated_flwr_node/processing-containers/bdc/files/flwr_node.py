import flwr as fl
import torch
import numpy as np
from typing import List, Dict, Tuple, OrderedDict

from densenet import DensNet121
from centralized_main import train_epoch, val_epoch, load_data

DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'   # use "local-only/base-python-gpu"
# DEVICE = 'cpu'    # for debugging; use "local-only/base-python-cpu"

class FlwrClient(fl.client.NumPyClient):

    def __init__(
        self,
        model: DensNet121,
        trainloader: torch.utils.data.DataLoader,
        testloader: torch.utils.data.DataLoader,
        num_examples: Dict,
    ) -> None:
        self.model = model
        self.trainloader = trainloader
        self.testloader = testloader
        self.num_examples = num_examples

    def get_parameters(self, config) -> List[np.ndarray]:
        # Return model parameters as a list of NumPy ndarrays
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters: List[np.ndarray]) -> None:
        # Set model parameters from a list of NumPy ndarrays
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        self.model.load_state_dict(state_dict, strict=True)

    def fit(
        self, parameters: List[np.ndarray], config: Dict[str, str]
    ) -> Tuple[List[np.ndarray], int, Dict]:
        # Set model parameters, train model, return updated model parameters
        self.set_parameters(parameters)
        train_epoch(self.model, self.trainloader, epochs=1, device=DEVICE)
        return self.get_parameters(config={}), self.num_examples["trainset"], {}

    def evaluate(
        self, parameters: List[np.ndarray], config: Dict[str, str]
    ) -> Tuple[float, int, Dict]:
        # Set model parameters, evaluate model on local test dataset, return result
        self.set_parameters(parameters)
        loss, accuracy = val_epoch(self.model, self.testloader, device=DEVICE)
        return float(loss), self.num_examples["testset"], {"accuracy": float(accuracy)}


def main() -> None:
    """Load data, start CifarClient."""

    # Load model and data
    model = DensNet121
    model.to(DEVICE)
    trainloader, valloader, num_examples = load_data()

    # Start client
    client = FlwrClient(model, trainloader, valloader, num_examples)
    fl.client.start_numpy_client(client, server_address="10.133.193.85:8080")


if __name__ == "__main__":
    main()