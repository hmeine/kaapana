FROM local-only/base-nnunet:latest

LABEL IMAGE="nnunet-gpu"
LABEL VERSION="03-22"
LABEL CI_IGNORE="False"

COPY files/ /kaapanasrc/
WORKDIR /kaapanasrc/
CMD ["bash","/kaapanasrc/start_nnunet.sh"]