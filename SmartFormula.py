# SmartFormula.py
import re
import algebra

#
# The SmartFormula class allows the creation of conversion objects that will take a combination
# of terms in an equation and compute the missing term.
#
# For example, a body mass index calculator:
#
#    class BodyMassIndex(SmartFormula):
#
#        def formulas(self):
#            return [
#                     "bmi          = weightKg / (heightM**2)",
#                     "heightM      = heightInches * 0.0254",
#                    "weightKg     = weightLb / 2.20462"
#                   ]
#
# instances of BodyMassIndex can be used to compute a specific value or to obtain implicitly
# calculated terms based on the ones that were supplied at creation time:
#
#           bmi = BodyMassIndex()
#           bmi(heightM=1.75,weightKg=130)) ==> 42.44898
#           bmi.weightLb)                   ==> 286.6006
#
#           BodyMassIndex(bmi=42.45,weightKg=130).heightInches ==> # 68.8968  (1.75 Meters)
#


class SmartFormula:

    def __init__(self, **kwargs):
        self.params        = kwargs
        self.precision     = 0.000001
        self.maxIterations = 10000
        self._formulas     = [ (f.split("=",1)[0].strip(),f)      for f   in self.formulas()]
        terms = set(term for _,f in self._formulas for term in re.findall(r"\w+\(?",f) )
        terms = [ term for term in terms if "(" not in term and not term.isdigit() ]
        self._formulas    += [ (term,f"{term}=solve('{term}')") for term in terms]
        self(**kwargs)
        
    def __getattr__(self, name):       
        if name in self.params: return self.params[name]

    def __call__(self, **kwargs):
        self.params          = kwargs
        self.moreToSolve     = True
        self.params["solve"] = lambda n: self.autoSolve(n)
        self.resolve()
        return self.params.get(self._formulas[0][0],None)

    def resolve(self):
        while self.moreToSolve:
            self.moreToSolve = False
            for param,formula in self._formulas:
                if self.params.get(param,None) is not None: continue
                try: 
                    exec(formula,globals(),self.params)
                    if self.params.get(param,None) is not None:
                        self.moreToSolve = True
                except: pass

    def autoSolve(self, name):
        for resolver in [self.algebra, self.newtonRaphson]:
            for source,formula in self._formulas:
                if self.params.get(source,None) is None:
                    continue
                if not re.search(f"(^|\\W){name}($|\\W)",formula):
                    continue
                resolver(name,source,formula)
                if self.params.get(name,None) is not None:
                    return self.params[name]
            
    def algebra(self, name, source, formula):
        try:    exec(solveFor(name,formula),globals(),self.params)            
        except: pass
        
    def newtonRaphson(self, name, source,formula):
        simDict = self.params.copy()
        target  = self.params[source]
        value   = target
        for _ in range(self.maxIterations):                    
            simDict[name] = value
            try: exec(formula,globals(),simDict)
            except: break
            result        = simDict[source]
            resultDelta   = target-result
            if abs(resultDelta) < self.precision : 
                self.params[name] = round(value/self.precision/2)*self.precision*2
                return       
            value += value*resultDelta/result/2

if __name__ == "__main__":
    
    class ABCD(SmartFormula):
        def formulas(self) : return ["a=b+c*d"]
        @property
        def someProperty(self): return "Found it!"

    abcd = ABCD(a=5,b=2,c=3)
    print("abcd.d", abcd.d)  # 1.0


    import math
    class BodyMassIndex(SmartFormula):

        def formulas(self):
            return [
                     "bmi          = weightKg / (heightM**2)",
                     "heightM      = heightInches * 0.0254",
                     "weightKg     = weightLb / 2.20462"
                   ]

    bmi = BodyMassIndex()
    print("bmi",bmi(heightM=1.75,weightKg=130)) # 42.44897959183673
    print("weight",bmi.weightLb) # 286.6006

    bmi(bmi=42.45,weightKg=130)
    print("height",bmi.heightInches) # 68.8968097135968  (1.75 Meters)

    class OP(SmartFormula):

        def formulas(self):
            return [
                      "result = a+b+c+d+e+f",
                      "a = b * c - d",
                      "c = e/f"
                   ]

    r = OP(b=1,d=3,e=45,f=9).result
    print(r) # 65.0
    f = OP(a=2,c=5,d=3,e=45,result=65).f
    print(f) # 9.0        
        

