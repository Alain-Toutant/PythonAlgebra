# algebra.py
Python equation (assignments) resolution.

This is a simple Python equation solver that will take an assignment statement (formula) expressed in Python syntax and solve it for one of the terms on the right producing another assignment statement for the term variable.

For example:

    solveFor("a","b=(a+3)/4")

will return "a = b*4-3"

The algorithm is very naive and will only support basic operators (+, -, *, /, \**) as well as a few math functions (log, exp, sin, cos, tan, asin, acos, atan, sqrt).

The term to resolve must only appear once in the formula.


# SmartFormula.py
Numeric conversion class to find the missing term of an equation based conversion definition.

For example, a body mass index calculator:

    class BodyMassIndex(SmartFormula):
        def formulas(self):
            return [
                     "bmi          = weightKg / (heightM**2)",
                     "heightM      = heightInches * 0.0254",
                     "weightKg     = weightLb / 2.20462"
                   ]

 instances of BodyMassIndex can be used to compute a specific value or to obtain implicitly
 calculated terms based on the ones that were supplied at creation time:

       bmi = BodyMassIndex()
       bmi(heightM=1.75,weightKg=130)) ==> 42.44898
       bmi.weightLb)                   ==> 286.6006

       BodyMassIndex(bmi=42.45,weightKg=130).heightInches ==> # 68.8968  (1.75 Meters)

