FROM local-only/base-python-gpu:latest

LABEL REGISTRY="local-only"
LABEL IMAGE="base-nnunet"
LABEL VERSION="latest"
LABEL CI_IGNORE="False"

ENV OMP_NUM_THREADS=1
ENV PYTHONUNBUFFERED=1

# nnUNet
ENV BRANCH=master
ENV NNUNET_VERSION=84b6389ae3362569cef0ff685bcb6bf24b64c693
RUN mkdir -p /nnunet-pip-package
RUN git clone  --single-branch --branch ${BRANCH} https://github.com/MIC-DKFZ/nnUNet.git /nnunet-pip-package && cd /nnunet-pip-package && git checkout ${NNUNET_VERSION}

RUN cd /nnunet-pip-package && pip3 install ./

RUN pip install tensorboard==2.8.0

COPY files/patched/DatasetAnalyzer.py /opt/conda/lib/python3.8/site-packages/nnunet/experiment_planning/DatasetAnalyzer.py
COPY files/patched/network_trainer.py /opt/conda/lib/python3.8/site-packages/nnunet/training/network_training/network_trainer.py
COPY files/patched/nnUNet_plan_and_preprocess.py /opt/conda/lib/python3.8/site-packages/nnunet/experiment_planning/nnUNet_plan_and_preprocess.py
COPY files/patched/nnUNetTrainer.py /opt/conda/lib/python3.8/site-packages/nnunet/training/network_training/nnUNetTrainer.py
COPY files/patched/nnUNetTrainerV2.py /opt/conda/lib/python3.8/site-packages/nnunet/training/network_training/nnUNetTrainerV2.py
COPY files/patched/predict.py /opt/conda/lib/python3.8/site-packages/nnunet/inference/predict.py
COPY files/patched/run_training.py /opt/conda/lib/python3.8/site-packages/nnunet/run/run_training.py

WORKDIR /kaapanasrc/