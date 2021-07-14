# Generated by: Neurodocker version 0.7.0+0.gdc97516.dirty
# Latest release: Neurodocker version 0.7.0
# Timestamp: 2020/08/14 22:31:57 UTC
# 
# Thank you for using Neurodocker. If you discover any issues
# or ways to improve this software, please submit an issue or
# pull request on our GitHub repository:
# 
#     https://github.com/ReproNim/neurodocker
FROM debian:buster
USER root
ARG DEBIAN_FRONTEND="noninteractive"
ARG NPROC=1
ENV LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8" \
    ND_ENTRYPOINT="/neurodocker/startup.sh"
RUN export ND_ENTRYPOINT="/neurodocker/startup.sh" \
    && apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           apt-utils \
           bzip2 \
           ca-certificates \
           curl \
           locales \
           devtoolset-3-gcc-c++ \
           make \
           zlib-devel \           
           unzip \
           git \
           python3-pip \
           gcc \
           vim \
           nano \
           ssh-client \
           xvfb \
           x11-utils \
           ssh \
           libx11-dev \
           libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG="en_US.UTF-8" \
    && chmod 777 /opt && chmod a+s /opt \
    && mkdir -p /neurodocker \
    && if [ ! -f "$ND_ENTRYPOINT" ]; then \
         echo '#!/usr/bin/env bash' >> "$ND_ENTRYPOINT" \
    &&   echo 'set -e' >> "$ND_ENTRYPOINT" \
    &&   echo 'export USER="${USER:=`whoami`}"' >> "$ND_ENTRYPOINT" \
    &&   echo 'if [ -n "$1" ]; then "$@"; else /usr/bin/env bash; fi' >> "$ND_ENTRYPOINT"; \
    fi \
    && chmod -R 777 /neurodocker && chmod a+s /neurodocker
    && curl -fsSL https://cmake.org/files/v3.12/cmake-3.12.2.tar.gz | tar -xz \
    && cd cmake-3.12.2 \
    && source /opt/rh/devtoolset-3/enable \
    && printf "\n\n+++++++++++++++++++++++++++++++++\n\
BUILDING CMAKE WITH $NPROC PROCESS(ES)\n\
+++++++++++++++++++++++++++++++++\n\n" \
    && ./bootstrap --parallel=$NPROC -- -DCMAKE_BUILD_TYPE:STRING=Release \
    && make -j$NPROC \
    && make install \
    && cd .. \
    && rm -rf *

RUN echo "Compiling ANTs version 2.2.0" \
    && git clone git://github.com/stnava/ANTs.git ants \
    && cd ants \
    && git fetch origin --tags \
    && git checkout 2.2.0 \
    && mkdir build \
    && cd build \
    && source /opt/rh/devtoolset-3/enable \
    && printf "\n\n++++++++++++++++++++++++++++++++\n\
BUILDING ANTS WITH $NPROC PROCESS(ES)\n\
++++++++++++++++++++++++++++++++\n\n" \
    && cmake -DCMAKE_INSTALL_PREFIX="/opt/ants" .. \
    && make -j$NPROC \
    && if [ -d /src/ants/build/ANTS-build ]; then \
            \
            cd /src/ants/build/ANTS-build \
            && make install; \
       else \
            \
            mkdir -p /opt/ants \
            && mv bin/* /opt/ants \
            && mv ../Scripts/* /opt/ants; \
       fi
COPY --from=builder /opt/ants /opt/ants

ENV ANTSPATH=/opt/ants/ \
    PATH=/opt/ants:/opt/ants/bin:$PATH
ENTRYPOINT ["/neurodocker/startup.sh"]

ENV FSLDIR="/opt/fsl-6.0.3" \
    PATH="/opt/fsl-6.0.3/bin:$PATH" \
    FSLOUTPUTTYPE="NIFTI_GZ" \
    FSLMULTIFILEQUIT="TRUE" \
    FSLTCLSH="/opt/fsl-6.0.3/bin/fsltclsh" \
    FSLWISH="/opt/fsl-6.0.3/bin/fslwish" \
    FSLLOCKDIR="" \
    FSLMACHINELIST="" \
    FSLREMOTECALL="" \
    FSLGECUDAQ="cuda.q"

RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           dc \
           file \
           libfontconfig1 \
           libfreetype6 \
           libgl1-mesa-dev \
           libgl1-mesa-dri \
           libglu1-mesa-dev \
           libgomp1 \
           libice6 \
           libxcursor1 \
           libxft2 \
           libxinerama1 \
           libxrandr2 \
           libxrender1 \
           libxt6 \
           sudo \
           wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* 
    
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           libgomp1 \
           libxmu6 \
           libxt6 \
           perl \
           tcsh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Downloading FSL ..." \
    && mkdir -p /opt/fsl-6.0.3 \
    && curl -fsSL --retry 5 https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-6.0.3-centos6_64.tar.gz \
    | tar -xz -C /opt/fsl-6.0.3 --strip-components 1 \
    && sed -i '$iecho Some packages in this Docker container are non-free' $ND_ENTRYPOINT \
    && sed -i '$iecho If you are considering commercial use of this container, please consult the relevant license:' $ND_ENTRYPOINT \
    && sed -i '$iecho https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Licence' $ND_ENTRYPOINT \
    && sed -i '$isource $FSLDIR/etc/fslconf/fsl.sh' $ND_ENTRYPOINT \
    && echo "Installing FSL conda environment ..." \
    && bash /opt/fsl-6.0.3/etc/fslconf/fslpython_install.sh -f /opt/fsl-6.0.3

#RUN test "$(getent passwd neuro)" || useradd --no-user-group --create-home --shell /bin/bash neuro
RUN useradd -ms /bin/bash neuro
WORKDIR /home/neuro
ENV CONDA_DIR="/opt/miniconda-latest" \
    PATH="/opt/miniconda-latest/bin:$PATH"
RUN export PATH="/opt/miniconda-latest/bin:$PATH" \
    && echo "Downloading Miniconda installer ..." \
    && conda_installer="/tmp/miniconda.sh" \
    && curl -fsSL --retry 5 -o "$conda_installer" https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash "$conda_installer" -b -p /opt/miniconda-latest \
    && rm -f "$conda_installer" \
    && conda update -yq -nbase conda \
    && conda config --system --prepend channels conda-forge \
    && conda config --system --set auto_update_conda false \    
    && conda config --system --set show_channel_urls true \
    && sync && conda clean -y --all && sync \
    && conda install -yq scikit-learn scipy meshio nibabel \ 
    && conda install -c mrtrix3 mrtrix3 \
    && conda install vtk matplotlib pandas numpy nilearn powerlaw Cython \
    && sync && conda clean -y --all && sync \
    && rm -rf ~/.cache/pip* \
    && sync

USER root
RUN mkdir /data && chmod 777 /data && chmod a+s /data
RUN mkdir /output && chmod 777 /output && chmod a+s /output
RUN mkdir /home/neuro/repo && chmod 777 /home/neuro/repo && chmod a+s /home/neuro/repo
RUN rm -rf /opt/conda/pkgs/*
USER neuro 
#https://github.com/moby/moby/issues/22832
ARG SSH_KEY
ENV SSH_KEY=$SSH_KEY
RUN mkdir /home/neuro/.ssh/
RUN echo "$SSH_KEY" > /home/neuro/.ssh/id_ed25519
RUN chmod 600 /home/neuro/.ssh/id_ed25519
RUN touch /home/neuro/.ssh/known_hosts
RUN ssh-keyscan github.com >> /home/neuro/.ssh/known_hosts
ARG CACHE_DATE
RUN git clone git@github.com:hptaylor/connectome_harmonic_core.git /home/neuro/repo ;'bash'
WORKDIR /home/neuro
ENTRYPOINT ["python","/home/neuro/repo/entrypoint_script.py"]
