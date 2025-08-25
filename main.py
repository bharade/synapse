import argparse
from pathlib import Path
import networkx as nx
from tqdm import tqdm

from synapse.cartographer import CodeGraphBuilder   

def main():
    parser = argparse.ArgumentParser(description="Synapse: Autonomous Codebase Analysis")
    parser.add_argument("repo_path", type=str, help="The path to the target repository.")
    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    if not repo_path.is_dir():
        print(f"Error: Directory not found at {repo_path}")
        return

    print(f"Starting analysis of repository: {repo_path.name}")
    
    builder = CodeGraphBuilder(repo_path)
    
    # We can wrap the build process with tqdm for a progress bar
    # Although file processing is fast, this is good practice for later
    print("Building knowledge graph...")
    knowledge_graph = builder.build_graph()
    
    print("\nAnalysis complete.")
    print(f"  - Total nodes in graph: {knowledge_graph.number_of_nodes()}")
    print(f"  - Total edges in graph: {knowledge_graph.number_of_edges()}")

    # Save the graph to a file for later analysis or visualization
    output_path = "knowledge_graph.gml"
    nx.write_gml(knowledge_graph, output_path)
    print(f"\nKnowledge graph saved to {output_path}")

    # Example query: Find the 5 files with the most functions
    file_nodes = [n for n, d in knowledge_graph.nodes(data=True) if d['type'] == 'file']
    function_counts = {file: knowledge_graph.out_degree(file) for file in file_nodes}
    
    print("\nTop 5 files by function count:")
    sorted_files = sorted(function_counts.items(), key=lambda item: item[1], reverse=True)
    for file, count in sorted_files[:5]:
        print(f"  - {file}: {count} functions")
    
    function_nodes = [n for n, d in knowledge_graph.nodes(data=True) if d['type'] == 'function']
    
    # We use in_degree to see how many 'calls' edges point *to* a function
    call_counts = {fn: knowledge_graph.in_degree(fn) for fn in function_nodes}
    
    print("\nTop 5 most-called functions (within the same file):")
    sorted_functions = sorted(call_counts.items(), key=lambda item: item[1], reverse=True)
    
    # Filter out functions that are never called
    called_functions = [(fn, count) for fn, count in sorted_functions if count > 0]
    
    for function, count in called_functions[:5]:
        print(f"  - {function}: called {count} times")

if __name__ == "__main__":
    main()