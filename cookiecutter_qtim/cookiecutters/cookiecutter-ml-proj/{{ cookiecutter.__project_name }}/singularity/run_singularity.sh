#!/usr/bin/env bash¬

SIF_FILE="{{ cookiecutter.__project_path }}/singularity.sif"
singularity shell \
    --nv \
    --writable-tmpfs \
    -B /autofs/:/autofs/ \
    $SIF_FILE
