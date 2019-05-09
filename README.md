# xAODProcessor

Small web service that will take an AST and return whatever it requests after running on a collection of xAOD files (the ATLAS experiment's base files).

This is designed to run in a container.

There are several python packages that are built and installed here:

- ADLBackend - back end python processor that does the heavy lifting.
- ADLFront - tools for an analysis user

Based on the ROOT to LINQ project.
