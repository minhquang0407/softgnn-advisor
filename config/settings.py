import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data_output"

CLEAN_DATA_DIR = DATA_DIR / "cleaned"
for d in [CLEAN_DATA_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def get_project_paths(project_name: str) -> dict:
    project_dir = DATA_DIR / project_name
    
    graph_dir = project_dir / "graph"
    training_dir = project_dir / "training"
    models_dir = project_dir / "models"
    
    for d in [project_dir, graph_dir, training_dir, models_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    return {
        "GRAPH_PATH": graph_dir / "relationship_graph.pkl",
        "NODES_DATA_PATH": project_dir / "nodes_data.csv",
        "PYG_DATA_PATH": training_dir / "pyg_data.pt",
        "MODEL_PATH": models_dir / "model.pt",
        "METADATA_PATH": project_dir / "metadata.json",
        "DEVELOPER_ALIASES_PATH": project_dir / "developer_aliases.json",
        "CONTRACTS_PATH": project_dir / "contracts.json",
        "TEST_COVERAGE_EDGES_PATH": project_dir / "test_coverage_edges.json",
        "RUNTIME_TEST_COVERAGE_EDGES_PATH": project_dir / "runtime_test_coverage_edges.json",
        "FILESYSTEM_SNAPSHOT_PATH": project_dir / "filesystem_snapshot.json",
        "COVERAGE_WORK_DIR": project_dir / "coverage",
    }

INPUT_DIM = 385
HIDDEN_DIM = 256
OUTPUT_DIM = 128
LEARNING_RATE = 0.01
EPOCHS = 100
BATCH_SIZE = 2048
MIN_EDGE_COUNT = 500
