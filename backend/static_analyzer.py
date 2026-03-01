import ast

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.loops = 0
        self.nested_loops = 0
        self.current_depth = 0
        self.function_name: str | None = None
        self.arg_count = 0

    def visit_For(self, node):
        self.current_depth += 1
        self.loops += 1
        if self.current_depth > 1:
            self.nested_loops += 1
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_While(self, node):
        self.current_depth += 1
        self.loops += 1
        if self.current_depth > 1:
            self.nested_loops += 1
        self.generic_visit(node)
        self.current_depth -= 1
    
    def visit_FunctionDef(self, node):
        # Capture the name of the first function defined
        if self.function_name is None:
            self.function_name = node.name
            self.arg_count = len(node.args.args)
        self.generic_visit(node)

def strict_complexity_check(code: str):
    try:
        tree = ast.parse(code)
        analyzer = ComplexityVisitor()
        analyzer.visit(tree)
        
        return {
            "total_loops": analyzer.loops,
            "max_nested_depth": analyzer.nested_loops + 1 if analyzer.loops > 0 else 0,
            "risk_factor": "HIGH" if analyzer.nested_loops >= 2 else "LOW",
            "function_name": analyzer.function_name or "solution",
            "arg_count": analyzer.arg_count
        }
    except SyntaxError:
        return {"error": "Syntax Error in Code"}