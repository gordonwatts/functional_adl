# xAODProcessor

Small web service that will take an AST and return whatever it requests after running on a collection of xAOD files (the ATLAS experiment's base files).

This is designed to run in a container.

There are several python packages that are built and installed here:

- adl_func_back - back end python processor that does the heavy lifting.
- adl_func_client - tools for an analysis user

Based on the ROOT to LINQ project.

Docker Container
================

To build the docker container, from the root of the package:
```
docker build --rm -f "Docker\Dockerfile" -t gordonwatts/func_adl:v0.0.1 .
```

Example docker run:
```
PS C:\Users\gordo> docker run -it --rm gordonwatts/func_adl:v0.0.1 /bin/bash
root@50e6c11471b5:/usr/src/app# python write_ast.py 0 test.pickle
root@50e6c11471b5:/usr/src/app# mkdir cache
root@50e6c11471b5:/usr/src/app# python translate_ast_to_cpp.py test.pickle cache
Warning: assumping that the method 'xAOD::Jet.pt(...)' has return type 'double'. Use cpp_types.add_method_type_info to suppress (or correct) this warning.
10808753a6765ea3f15a10bf1b6c21a0
runner.sh
cpp_pandas_rep
localds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r9364_r9315_p3795
root@50e6c11471b5:/usr/src/app# ls cache/
10808753a6765ea3f15a10bf1b6c21a0
root@50e6c11471b5:/usr/src/app# ls cache/10808753a6765ea3f15a10bf1b6c21a0
ATestRun_eljob.py  package_CMakeLists.txt  query.cxx  query.h  rep_cache.pickle  runner.sh
```

## Development

To get testing working correctly you'll need to first get your environment setup:

    - pip install pytest-asyncio

## Debugging Tips

Add the following lines in your notebook and you can see what comes back from the server:
```
import logging
logging.basicConfig(level=logging.INFO)
```
