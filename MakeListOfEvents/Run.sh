#!/bin/bash
wrap_python.sh ComputeRotationAngle.py "$1" "$2" >& RotationAngle`if [ -n "$2" ]; then echo "_$2"; fi`.log
wrap_python.sh MakeList.py "$1" "$2"
