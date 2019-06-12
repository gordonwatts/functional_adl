# Build image capable of processing a xAOD file all in-process given some sort of AST somehow.

FROM atlas/analysisbase:21.2.62

# Next, install python3 (without killing python 2)
#RUN sudo yum -y install python34
#RUN sudo yum -y install python34-pip
RUN curl -O https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz; tar xf Python-3.7.3.tgz
RUN source /home/atlas/release_setup.sh; cd Python-3.7.3; ./configure --enable-optimizations; make; sudo make install
