# PythonAlgebra
Python equation (assignments) resolution.

This is a simple Python equation solver that will take an assignment statement (formula) expressed in Python syntax and solve it for one of the terms on the right producing another assignment statement for the term variable.

For example:

    solveFor("a","b=(a+3)/4")

will return "a = b*4-3"

The algorithm is very naive and will only support basic operators (+, -, *, /, \**) as well as a few math functions (log, exp, sin, cos, tan, asin, acos, atan, sqrt).

The term to resolve must only appear once in the formula.



