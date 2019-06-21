# algebra.py: Python algebra solver
import re
from itertools import accumulate

# SIMPLE FUCTION TO SOLVE EQUATIONS (solveFor)
#
# The solveFor(term,equation) function produces an assignment statement to the term variable
# by applying algebraic transformations to the equation.  It will return None if it cannot find
# a solution
#
# for example:
#
#     solveFor("a","b = (a+3)/4") --> "a=b*4-3"
#

def findGroups(expression):
    levels = list(accumulate(int(c=="(")-int(c==")") for c in expression))
    groups = "".join([c,"\n"][lv==0] for c,lv in zip(expression,levels)).split("\n")
    groups = [ g+")" for g in groups if g ]
    return sorted(groups,key=len,reverse=True)

functionMap = [("sin","asin"),("cos","acos"),("tan","atan"),("log10","10**"),("exp","log")]
functionMap += [ (b,a) for a,b in functionMap ]
    
def solveFor(term,equation):
    equation = equation.replace(" ","").replace("**","†")
    termIn = re.compile(f"(^|\\W){term}($|\\W)")
    if len(termIn.findall(equation)) == 0: return None
    left,right = equation.split("=",1)
    if termIn.search(right): left,right = right,left

    groups = { f"#{i}#":group for i,group in enumerate(findGroups(left)) }
    for gid,group in groups.items(): left = left.replace(group,gid)
    termGroup = next((gid for gid,group in groups.items() if termIn.search(group)),"##")

    def moveTerms(leftSide,rightSide,oper,invOper):
        keepLeft = []
        for i,x in enumerate(leftSide.split(oper)):
            if termGroup in x or termIn.search(x):
                keepLeft.append(x)
                continue
            x = x or "0"
            if any(op in x for op in "+-*/"): x = "("+x+")"
            rightSide = invOper[i>0].replace("{r}",rightSide).replace("{x}",x)
        leftSide  = oper.join(keepLeft)
        return leftSide,rightSide

    def moveFunction(leftSide,rightSide,func,invFunc):
        fn = leftSide.split("#",1)[0]
        if fn.split(".")[-1] == func:
            return leftSide[len(fn):],fn.replace(func,invFunc)
        return leftSide,rightSide
        
    left,right = moveTerms(left,right,"+",["{r}-{x}"]*2)
    left,right = moveTerms(left,right,"-",["{x}-{r}","{r}+{x}"])  
    left,right = moveTerms(left,right,"*",["({r})/{x}"]*2)
    left,right = moveTerms(left,right,"/",["{x}/({r})","({r})*{x}"])  
    left,right = moveTerms(left,right,"†",["log({r})/log({x})","({r})†(1/{x})"])
    for func,invFunc in functionMap:
        left,right = moveFunction(left,right,func,f"{invFunc}({right})")
    for sqrFunc in ["math.sqrt","sqrt"]:
        left,right = moveFunction(left,right,sqrFunc,f"({right})**2")
    
    for gid,group in groups.items(): right = right.replace(gid,group)
    if left == termGroup:
        subEquation = groups[termGroup][1:-1]+"="+right
        return solveFor(term,subEquation)
    if left != term: return None
    solution = f"{left}={right}".replace("†","**")
    # expression clen-up
    solution = re.sub(r"(?<!\w)(0\-)","-",solution)
    solution = re.sub(r"1/\(1/(\w)\)",r"\g<1>",solution)
    solution = re.sub(r"\(\(([^\(]*)\)\)",r"(\g<1>)",solution)
    solution = re.sub(r"(?<!\w)\((\w*)\)",r"\g<1>",solution)
    return solution 

if __name__ == "__main__":
    print("FUNCTION (solveFor) TESTS:")
    print(solveFor("x","y=(a+b)*x-(math.sin(1.5)/322)"))   # 'x=(y+(math.sin(1.5)/322))/(a+b)'
    print(solveFor("a","q=(a**2+b**2)*(c-d)**2"))          # 'a=(q/(c-d)**2-b**2)**(1/2)'
    print(solveFor("a","c=(a**2+b**2)**(1/2)"))            # 'a=(c**2-b**2)**(1/2)'    
    print(solveFor("a","x=((a+b)*c-d)*(23+y)"))            # 'a=(x/(23+y)+d)/c-b'

    sa = solveFor("a","y=-sin((x)-sqrt(a))")             
    sx = solveFor("x",sa)                                
    sy = solveFor("y",sx)                                
    print(sa) # 'a=(x-asin(-y))**2'
    print(sx) # 'x=a**(1/2)+asin(-y)'
    print(sy) # 'y=-sin(x-a**(1/2))'

    # tests for multi-instance terms
    print("multi-term: b=a*Z-a*3: ",solveFor("a","b=a*Z - a*3"))  # None... not supported


### EXPERIMENTAL - ADVANCED EQUATION SOLVER CLASS ###
#
#  The Equation class
#  ------------------
#  Initialized with an equality, can isolate any term into an assignment statement
#
#  Example use:
#
#      trig = Equation("c**2 = a**2 + b**2")
#      trig.isolate("a") ==> 'a=sqrt(c**2-b**2)'
#      trig.isolate("b") ==> 'b=sqrt(c**2-a**2)'
#
#  Features and limitations:
#
#  - Can combine multiple instance of sought term in equation
#  - Basic numerical operators:  + - * / **
#  - Some math functions and their inverse:  log, sin, cos, tan, sqrt
#  - Simple factorisation / expansion: a*(b+c) <--> a*b + a*c
#
#  Limitations:
#  - no resolution for multi degree polynoms (e.g. a**2 + a)
#  - Not aware of "well known" identities
#  - Supports integers and floats (no imaginary)
#  - No +/- variants when applying square root (uses positive only)    

class Operation:
    def __init__(self,expression):
        self.multiplier = 1
        self.parse(expression)
        
    @property
    def pythonOper(self): return self.operator.replace("^","**")
    
    def new(operator):
        result = Operation("0{operator}0")
        result.operands = []
        return result            

    def parse(self,expression):
        self.operator = ""
        self.operands = []
        self.term     = None
        expression = expression.replace(" ","").replace("**","^")
        expression = expression.replace("--","+").replace("+-","-")
        expression = re.sub(r"([A-Za-z_0-9])(\()",r"\g<1>ƒ\g<2>",expression)
        groups = { f"#{i}#":group for i,group in enumerate(findGroups(expression)) }
        for group,text in groups.items():
            expression = expression.replace(text,group)
        for operator in ["=","+","-","*","/","^","ƒ"]:
            parts = expression.split(operator)
            if len(parts) == 1: continue                
            self.operator = operator
            for part in parts:
                if not part: self.operands.append(Operation("0")); continue
                if part in groups:
                    part = groups[part][1:-1]
                for group,text in groups.items():
                    part = part.replace(group,text)
                self.operands.append(Operation(part))
            break
        if not self.operands:
            if expression in groups:
                expression = groups[expression][1:-1]
                self.parse(expression)
            else:
                self.term = expression
        if self.operator == "-":
            self.operator = "+"
            for oper in self.operands[1:]:
                oper.negate()
            if self.operands[0].asString == "0":
                self.operands.pop(0)
            if len(self.operands) == 1:
                self.rollUp()
            
    def rollUp(self):
        if len(self.operands) != 1: return
        rollUp          = self.operands[0]
        self.term       = rollUp.term
        self.operator   = rollUp.operator
        self.multiplier = rollUp.multiplier
        self.operands   = rollUp.operands
        
        
    def negate(self):
        self.multiplier *= -1
        if self.operator == "+" and self.multiplier < 0:
            self.multiplier = 1
            for oper in self.operands:
                oper.negate()                
        
    def print(self,indent=0):
        offset="  "*indent
        if self.operands: print(f"{offset}Operation: {self.operator}")
        else: print(f"{offset}{self.term}")
        for operand in self.operands:
            operand.print(indent+1)

    @property
    def precedence(self):
        return ["=","=","+","-","*","/","^","^","","","ƒ","ƒ"].index(self.operator)//2
        
    @property
    def asString(self):
        
        def restoreSign(s):
            if self.multiplier >= 0 or s == "0": return s
            if self.operator in ["+","-"]: return f"-({s})"
            return "-"+s
        
        if not self.operands: return restoreSign(self.term or "0")
        level  = self.precedence
        result = ""
        for i,operand in enumerate(self.operands):
            part = operand.asString
            if operand.precedence < level:
                if self.operator != "ƒ" or i>0:
                    part = f"({part})"
            if result: result += self.operator
            result += part                    
        result = result.replace("^","**")
        result = result.replace("ƒ","")
        result = result.replace("+-","-")
        result = result.replace("--","+")
        return restoreSign(result)
    
    @property
    def details(self):
        flag = "!" if self.multiplier < 0 else ""
        if self.isValue: return flag+self.term
        return flag+"[" + self.operator.join(op.details for op in self.operands)+"]"
    
    @property
    def isValue(self): return self.operator == ""

    @property
    def isNumber(self):
        return self.isValue and all(d.isdigit() for d in self.term.split(".",1))
    
    def isTerm(self,term): return not self.operands and self.term == term
    def hasTerm(self,term):
        if not self.operands: return self.isTerm(term)
        return any( operand.hasTerm(term) for operand in self.operands)

    def copy(self):
        return Operation(self.asString)

    
class Equation(Operation):

    def copy(self):
        return Equation(self.asString)

    def isolate(self,term,trace=False):
        return self.solvedFor(term,trace).asString
            
    def solvedFor(self,term,trace=False):
        result = self.copy()
        self.contract(term,result)
        result.swapSides(term)
        left,right = result.operands
        if left.isTerm(term) : return result
        seen= set()
        movedOne = 1
        while movedOne:
            expr = result.asString
            if trace: print(result.details)
            if expr in seen: break
            seen.add(expr)
            movedOne = 0
            movedOne += result.moveTerm(term,"+","{r}-{x}")
            movedOne += result.swapNegation()
            movedOne += result.moveTerm(term,"-","{r}+{x}","{x}-{r}")
            movedOne += result.moveTerm(term,"*","({r})/({x})")
            movedOne += result.moveTerm(term,"/","({r})*({x})","({x})/({r})")
            movedOne += result.moveTerm(term,"^","({r})^(1/{x})","log({r})/log({x})")
            while result.moveFunctions(term): movedOne += 1
            if not movedOne:
                movedOne += self.contract(term,result)
                movedOne += result.factorize(term)
                movedOne += result.operands and self.expand(term,result)
        return result
        
    def swapSides(self,term):
        if self.operator != "=": return
        left,right = self.operands
        if not right.hasTerm(term): return
        if left.hasTerm(term):
            self.operands = [Operation(f"({left.asString})-({right.asString})"),Operation("0")]
        else:
            self.operands = [right,left]
            
    def swapNegation(self):
        left,right = self.operands
        if left.multiplier>=0: return False
        right.negate()
        left.negate()
        return True
        
    def moveTerm(self,term,oper,invOper,firstOper=None):
        movedAny = False
        left,right = self.operands
        if left.operator != oper: return movedAny
        if left.operator == "-":
            print("SHOULD NOT HAPPEN",left.asString)
        rightExp = f"({right.asString})"
        keepLeft = []       
        for i,operand in enumerate(left.operands):
            if operand.hasTerm(term):
                keepLeft.append(operand)
                continue
            pattern =  invOper if keepLeft or not firstOper else firstOper
            rightExp = pattern.replace("{r}",rightExp).replace("{x}",operand.asString)
            movedAny = True
        if movedAny:
            if len(keepLeft) == 1: left = keepLeft[0]
            else: left.operands = keepLeft
            self.operands = [left,Operation(rightExp)]
        return movedAny

    funcMap  = [ ("sin","asin"), ("cos","acos"), ("tan","atan"),("log","exp") ]
    funcMap += [ (b,a) for a,b in funcMap ]
    def moveFunctions(self,term):
        left,right = self.operands
        if left.operator != "ƒ": return False
        function = left.operands[0]
        for fn,invFn in Equation.funcMap:
            if not function.isTerm(fn): continue
            right = Operation(f"{invFn}({right.asString})")            
            left  = left.operands[1]
            self.operands = [left,right]
            return True
        if function.isTerm("sqrt"):
            right = Operation(f"({right.asString})**2")
            left  = left.operands[1]
            self.operands = [left,right]
            return True
        return False

    def factorize(self,term):
        left,right = self.operands
        if not left.operands: return False
        if not all(op.hasTerm(term) for op in left.operands): return False
        
        if self.factorizeAdditions(term): return True
        return False


    # 2*a + 3*a --> a*(2+3)
    def factorizeAdditions(self,term):
        left,right = self.operands 
        if left.operator not in ["+","-"] : return False
        terms   = []
        factors = []
        for operand in left.operands:
            if operand.isTerm(term):
                terms.append(term)
                factors.append("1")
                continue
            if operand.operator in ["*","/"]:
                termOper = ["1"]
                factOper = ["1"]
                for i,op in enumerate(operand.operands):
                    opString = op.asString
                    if operand.precedence > op.precedence:
                        opString = "("+opString+")"
                    if op.hasTerm(term):
                        if i>0 and operand.operator == "/":
                            opString = f"1/{opString}"
                        termOper.append(opString)
                    else: factOper.append(opString)
                if len(termOper) > 1: termOper.pop(0)
                if len(factOper) > 1 and operand.operator != "/": factOper.pop(0)
                terms.append("*".join(termOper))
                factors.append(operand.operator.join(factOper))
            else:
                terms.append(operand.asString)
                factors.append("1")
        if not terms or any(t != terms[0] for t in terms): return False        
        factors = left.operator.join(factors)
        left.parse(f"({terms[0]})*({factors})")
        return True


    # term*(a+term+b) -> term*a + term*term + term*b
    def expand(self,term,oper):
        if oper.operator == "=":
            return self.expand(term,oper.operands[0])
        
        # recurse
        didSome = False
        for op in oper.operands:
            if self.expand(term,op): didSome=True
            
        # term*(a+term+b) -> term*a + term*term + term*b   
        if oper.operator == "*":
            exo = next( (op for op in oper.operands \
                           if op.hasTerm(term) and not op.isTerm(term) and op.operator in ["+","-"]), None)
            if not exo: return didSome
            factor   = "*".join( f"({op.asString})" for op in oper.operands if op != exo)
            expanded = exo.operator.join(f"{factor}*({op.asString})" for op in exo.operands)
            oper.parse(expanded)
            return True
        
        return didSome

    # 3*b*term*term*7 -> 21*b*term**2
    def contract(self,term,oper):
        if oper.isValue : return False
        didSome = False
        # recurse
        for op in oper.operands:
            if self.contract(term,op): didSome = True
        if oper.operator == "=": return didSome # not the equation itself
        
        # combine number values into one
        if all(o.isNumber for o in oper.operands):
            oper.parse( str(eval(oper.asString)) )
            return True

        #merge commutative operations
        if oper.operator in ["+","*"]:
            if any(op.operator in [oper.operator] for op in oper.operands):
                merged = []
                for op in oper.operands:
                    if op.operator == oper.operator:
                        merged +=  [op] if op.isValue else op.operands
                    else:
                        merged.append(op)
                oper.operands = merged
                
        # make multiplications of term into powers
        if self.contractProducts(term,oper): didSome = True

        # clean up addition of 0
        if oper.operator == "+":
            nonZeroes = [op for op in oper.operands if op.asString != "0"]
            if len(nonZeroes)<len(oper.operands):
                if not nonZeroes: oper.parse("0")
                elif len(nonZeroes) == 1: oper.parse(nonZeroes[0].asString)
                else: oper.operands = nonZeroes
                didSome = True

        # clean up multiplications by 1 and 0
        if oper.operator == "*":
            nonOnes = [op for op in oper.operands if op.asString != "1"]
            if len(nonOnes)<len(oper.operands):
                if not nonOnes: oper.parse("1")
                elif len(nonOnes) == 1: oper.parse(nonOnes[0].asString)
                else: oper.operands = nonOnes
                didSome = True
            if any(op.asString == "0" for op in oper.operands):
                oper.parse("0")
                didSome = True
                
        # special processing of powers ( x**0.5->sqrt(x), x**1->x, x**0->1 )
        if oper.operator == "^" and len(oper.operands)==2:
            didOne = True
            if oper.operands[1].asString in ["0.5","1/2"]:
                oper.parse(f"sqrt({oper.operands[0].asString})")
            elif oper.operands[1].asString == "1":
                oper.parse(oper.operands[0].asString)
            elif oper.operands[1].asString == "0":
                oper.parse("1")
            else: didOne = False
            didSome = didSome or didOne

        # X - X ==> 0    
        if oper.operator == "-" and len(oper.operands)==2:
            if oper.operands[0].asString == oper.operands[1].asString:
                oper.parse("0")
                didSome = True

        # N / 1 ==> N
        if oper.operator == "/" and len(oper.operands)==2:
            if oper.operands[1].asString == "1":
                oper.parse(oper.operands[0].asString) 
        
        # order terms with numbers first, then other terms, then seeked term
        def sortKey(o): return (not o.isNumber, o.hasTerm(term),o.asString.rjust(10))
        skipFirst = int(oper.operator in ["-","/","^","ƒ"])
        oper.operands = oper.operands[:skipFirst] + sorted(oper.operands[skipFirst:],key=sortKey)
        
        # process number values (now first or second in line)
        i,j = 0,1
        while skipFirst==0 and len(oper.operands) > 2 \
          and oper.operands[i].isNumber and oper.operands[j].isNumber:
            v = eval(f"{oper.operands[i].term}{oper.pythonOper}{oper.operands[j].term}")
            oper.operands[j] = Operation(str(v))
            oper.operands.pop(i)
            didSome = True

        # place negative operands at the end of additions
        if oper.operator == "+":
            for _ in range(len(oper.operands)):
                if oper.operands[0].multiplier < 0:
                    oper.operands = oper.operands[1:]+oper.operands[:1]
                    didSome = True
                else: break
                
        # end of contraction       
        return didSome
       
    # 3*a*b* --> 3*b*a**2
    def contractProducts(self,term,oper):
        if oper.operator != "*" : return False
        terms   = []
        factors = []
        for op in oper.operands:
            if op.hasTerm(term): terms.append(op.asString)
            else:                factors.append(op.asString)
        if len(terms)<2 or any(t != terms[0] for t in terms): return False        
        factors = "*".join(factors)
        power = len(terms)
        if factors: powerExpr = f"({factors})*({terms[0]})**{power}"
        else:       powerExpr = f"({terms[0]})**{power}"
        oper.parse(powerExpr)
        return True
    
             



if __name__ == "__main__":
    print("EQUATION TESTS:")
    op = Equation("a=(q/(c-d)**2-b**2)**(1/2)")
    for eq,term in [ ("y=(a+b)*x-(math.sin(1.5)/322)","x"),
                     ("q=(a**2+b**2)*(c-d)**2","a"),
                     ("c=(a**2+b**2)**(1/2)","a"),
                     ("x=((a+b)*c-d)*(23+y)","a"),
                     ("y=-sin((x)-sqrt(a))","a"),
                     ("b=a*Z - a*3","a"),
                     ("b=a*Z*(a+1) - a*3","a"),
                     ("Z*a*(7*a+a)+3*a**2=b","a")
                    ]:
        print(eq, " ===> ", Equation(eq).isolate(term))

