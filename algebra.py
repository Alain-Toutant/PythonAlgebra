# algebra.py : Python algebra solver
import re
from itertools import accumulate

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
    print(solveFor("a","b=a*Z - a*3"))  # 'a=b/(Z-3)'


### EXPERIMENTAL - ADVANCED PARSING - Incomplete code ###
"""
def getNextGroupId():
    gid = 1
    while True:
        yield f"«{gid}»"
        gid += 1
GroupID = getNextGroupId()
        
def formGroups(expression,recurse=False):
    levels  = list(accumulate(int(c=="(")-int(c==")") for c in expression))
    groups  = "".join([c,"\n"][lv==0] for c,lv in zip(expression,levels)).split("\n")
    groups  = sorted((g+")" for g in groups if g),key=len,reverse=True)
    grouped = dict()
    for group in groups:
        if group not in expression: continue
        gid = next(GroupID)
        expression = expression.replace(group,gid)
        grouped[gid] = group
        if recurse:
            groupExp,subGroups = formGroups(group[1:-1])
            grouped[gid] = f"({groupExp})"
            grouped.update(subGroups)            
    return expression,grouped

class Operation:

    def __init__(self,expression,operands=None):
        self.expression = expression
        self.operation  = ""
        self.operands   = []
        
        if operands is not None:
            self.operation = expression
            self.operands  = operands
            self.expression = self.asString
            return
        
        expression = expression.replace(" ","").replace("**","†")
        expression,self.groups = formGroups(expression)
        for oper in ["=","+","-","*","/","†"]:
            if oper in expression:
                self.operands  = [ Operation(self.expand(subExpr)) for subExpr in expression.split(oper) ]
                self.operation = oper
                break
                
    def expand(self,expr):
        if expr in self.groups: return self.groups[expr][1:-1]
        for gid,group in self.groups.items():
            expr = expr.replace(gid,group)
        return expr
    
    def info(self,level=0):
        print(("....."*level)+"OPER "+self.operation,":", self.expression)
        for operand in self.operands:
            operand.info(level+1)

    def cleanUp(self,expr):
        g,gr = formGroups(expr)
        if g in gr: expr = expr[1:-1]
        expr = expr.replace("†","**")
        expr = re.sub(r"(?<!\w)(0\-)","-",expr)
        expr = re.sub(r"1/\(1/(\w)\)",r"\g<1>",expr)
        expr = re.sub(r"\(\(([^\(]*)\)\)",r"(\g<1>)",expr)
        expr = re.sub(r"(?<!\w)\((\w*)\)",r"\g<1>",expr)
        return expr
            
    @property
    def asString(self):
        if not self.operands: return self.expression
        if self.operation == "=":
            result = "=".join( self.cleanUp(o.asString) for o in self.operands )
        else:
            result = "("+self.operation.join( o.asString for o in self.operands )+")"
        return result

    def hasTerm(self,term):
        if self.operands: return any( o.hasTerm(term) for o in self.operands )
        return re.search(f"(^|\\W){term}($|\\W)") is not None

    def isTerm(self,term):
        return not self.operands and self.expression == term

    def solveFor(self,term):
        if self.operation != "=": return None
        if self.operands[1].hasTerm(term):
            self.operands=self.operands[::-1]
        while True:
            op = self.operands[0]
            keepLeft = []
            for index,component in enumerate(op.operands):
                if component.hasTerm(term): keepLeft.append(component); continue
                self.moveTerm(term,op.component,first=i==0)               
            if len(keepLeft) == 1:
                self.operands[0] = keepLeft[0]
            else: break
        return self.asString if self.operands[0].isTerm(term) else None
            
    def moveTerm(self,term,component,first):
        
        

        
        

op = Operation("x=(y+(math.sin(1.5)/322))/(a+b)")
op.info()
        
"""




