@ECHO off

set PATH=D:\Dev\Doxygen;%PATH%

cd %~DP0

mkdir build & cd build & qmake .. -r & make -j 

cd .. & doxygen 

mkdir build\doc

qhelpgenerator doc/html/index.qhp -o build\doc\qsint-0.4.0.qch

