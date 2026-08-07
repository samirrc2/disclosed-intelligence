# Code Ocean capsule environment for "Disclosed Intelligence".
# Reproduction is offline and deterministic; no API keys or network are required.
# Local development: use code/requirements.txt in a virtualenv instead.
FROM registry.codeocean.com/codeocean/miniconda3:4.12.0-python3.11-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN pip install -U --no-cache-dir \
    matplotlib==3.9.2 \
    numpy==2.2.6 \
    pandas==2.2.3 \
    pytest==8.3.3 \
    scipy==1.14.1 \
    statsmodels==0.14.4
