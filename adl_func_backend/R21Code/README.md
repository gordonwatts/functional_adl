# R21 Code

This contains demo code to use a starting framework for building the coding back end. It has
code that does the following:

- Runs against a R21 analysis release in docker
- Runs on one file
- Dumps a ROOT file that contains a TTree with one branch: jet PT.
- Jets are calibrated.

Everything is automated - in the sense that once you start the docker container with the script, nothing
else needs to be changed. There are some things hardwired here which are not in this repro:

- name of the xAOD input data file

At some point this will all be out of date as it will be generated in parts.

## Usage

To run this test do the following:

- ``docker run --rm -v I:/gwatts/Code/calratio2019/BDTTrainingAnalysisLanguage/R21Code:/scripts -v I:/gwatts/Code/calratio2019/BDTTrainingAnalysisLanguage:/results -v G:/mc16_13TeV:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh``

To run interactive (for testing, etc.) add the flags ``-it``, and remove the ``/scripts/runner.sh``. When the container starts up, you can then source the ``runner.sh`` file to have it correctly setup the release, etc.