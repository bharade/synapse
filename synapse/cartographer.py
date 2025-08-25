from tree_sitter import Parser
from tree_sitter_languages import get_language

from pathlib import Path
import networkx as nx
from tqdm import tqdm



PYTHON_LANGUAGE = get_language('python') 

def parse_file(file_path: Path) -> bytes:
    """
    Parses a single file using tree-sitter and returns the AST.
    """
    parser = Parser()
    parser.set_language(PYTHON_LANGUAGE)

    try:
        file_content = file_path.read_text(encoding='utf-8')
        tree = parser.parse(bytes(file_content, "utf8"))
        return tree
    except (UnicodeDecodeError, FileNotFoundError):
        print(f"Warning: Could not read or parse file {file_path}")
        return None

class CodeGraphBuilder:
    # build a graph representation of the codebase
    def __init__(self,repo_path:Path):
        self.repo_path = repo_path
        self.graph = nx.DiGraph()

    def build_graph(self):
        python_files=list(self.repo_path.rglob('*.py'))
        for file_path in python_files:
            self._process_file(file_path)
        return self.graph
    
    def _process_file(self, file_path: Path):
        relative_path=file_path.relative_to(self.repo_path)
        self.graph.add_node(str(relative_path),type='file')
        tree = parse_file(file_path)
        if not tree:
            return
        self._find_and_add_functions(tree.root_node,str(relative_path))
        self._find_and_add_calls(tree.root_node, str(relative_path))

    def _find_and_add_functions(self,start_node,file_path_str:str):
        query_str = """
        (function_definition
          name: (identifier) @function.name)
        """
        query=PYTHON_LANGUAGE.query(query_str)
        captures=query.captures(start_node)
        for node,capture_name in captures:
            function_name=node.text.decode('utf-8')
            function_id=f"{file_path_str}::{function_name}"
            self.graph.add_node(function_id,type='function',name=function_name)
            self.graph.add_edge(file_path_str,function_id,type='contains')

    def _find_and_add_calls(self, start_node, file_path_str: str):
        """
        Finds all function calls within a file and adds 'CALLS' edges.
        This approach uses two queries for clarity and robustness.
        """
        # Query 1: Find all function definitions and capture their name and body.
        func_query_str = """
        (function_definition
            name: (identifier) @caller.name
            body: (block) @caller.body)
        """
        func_query = PYTHON_LANGUAGE.query(func_query_str)
        func_captures = func_query.captures(start_node)

        # Query 2: Find all function calls.
        call_query_str = """
        (call
            function: [
                (identifier) @callee.name
                (attribute attribute: (identifier) @callee.name)
            ]
        )
        """
        call_query = PYTHON_LANGUAGE.query(call_query_str)

        # Iterate through each function found in the file
        for i in range(0, len(func_captures), 2):
            caller_node = func_captures[i][0]
            body_node = func_captures[i+1][0]
            
            caller_name = caller_node.text.decode('utf8')
            caller_id = f"{file_path_str}::{caller_name}"

            # Now, run the call query *only* within the body of the current function
            call_captures = call_query.captures(body_node)

            for call_node, capture_name in call_captures:
                if capture_name == 'callee.name':
                    callee_name = call_node.text.decode('utf8')
                    
                    # This is still a simplification: assumes callee is in the same file
                    callee_id = f"{file_path_str}::{callee_name}"

                    # Only add an edge if both nodes exist and are not the same
                    # (to prevent simple recursive calls from cluttering the graph for now)
                    if self.graph.has_node(caller_id) and self.graph.has_node(callee_id) and caller_id != callee_id:
                        self.graph.add_edge(caller_id, callee_id, type='calls')
