import click
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import time

# Force UTF-8 encoding for Windows to prevent CP1252 crashes on Vietnamese/emoji text
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


console = Console()


@click.group()
def cli():
    """SoftGNN - AI-Powered Codebase Dependency & Impact Advisor"""
    pass


@cli.command()
@click.option('--project', required=True, help='Ten du an (luu tru du lieu rieng biet)')
@click.option('--path', default='.', help='Duong dan toi repository can quet')
def etl(project, path):
    """Quet ma nguon va lich su Git de xay dung Do thi Tri thuc"""
    console.rule(f"[bold blue]SoftGNN ETL Pipeline - Project: {project}")
    console.print(f"Scanning target: [yellow]{os.path.abspath(path)}[/yellow]")

    from softgnn_advisor.scripts.etl_run import run_etl_pipeline
    try:
        run_etl_pipeline(path, project)
        console.print("[bold green][SUCCESS] ETL Pipeline completed successfully![/bold green]")
        console.print(f"Graph data saved to [cyan]data_output/{project}/[/cyan]")
    except Exception as e:
        console.print(f"[bold red][ERROR] ETL Error: {e}[/bold red]")
        raise


@cli.command()
@click.option('--project', required=True, help='Ten du an can huan luyen')
def train(project):
    """Huan luyen loi AI HGT (Heterogeneous Graph Transformer)"""
    console.rule(f"[bold magenta]Training Core AI (HGT) - Project: {project}")

    from softgnn_advisor.scripts.train_model import run_optimization
    try:
        run_optimization(project)
        console.print("\n[bold green][SUCCESS] Training completed![/bold green]")
    except Exception as e:
        console.print(f"\n[bold red][ERROR] Training Error: {e}[/bold red]")
        raise


@cli.command()
@click.option('--project', required=True, help='Ten du an')
@click.option('--path', default='.', help='Duong dan toi repository can quet va huan luyen')
@click.option('--skip-train/--with-train', default=False, show_default=True, help='Build graph/snapshot without training the HGT model')
def prepare(project, path, skip_train):
    """Chay onboarding pipeline: ETL -> optional Train."""
    console.rule(f"[bold cyan]SoftGNN Prepare Pipeline - Project: {project}")
    console.print(f"Step 1/2: ETL for [yellow]{os.path.abspath(path)}[/yellow]")

    from softgnn_advisor.scripts.etl_run import run_etl_pipeline
    from softgnn_advisor.scripts.train_model import run_optimization
    from softgnn_advisor.core.change_provider import build_filesystem_snapshot, save_filesystem_snapshot, snapshot_path_for_project

    try:
        run_etl_pipeline(path, project)
        snapshot = build_filesystem_snapshot(path)
        save_filesystem_snapshot(snapshot_path_for_project(project), snapshot)
        console.print("[bold green][SUCCESS] ETL completed and filesystem snapshot saved.[/bold green]")

        if skip_train:
            console.print("[yellow]Skipping HGT training because --skip-train was set.[/yellow]")
            console.print(f"You can now run: [cyan]python softgnn.py pr-scan --project {project} --repo-path {os.path.abspath(path)} --change-source auto[/cyan]")
            return

        console.print("\nStep 2/2: Training HGT model")
        run_optimization(project)
        console.print("\n[bold green][SUCCESS] Prepare completed: ETL + Train done.[/bold green]")
        console.print(f"You can now run: [cyan]python softgnn.py doctor --project {project}[/cyan]")
    except Exception as e:
        console.print(f"[bold red][ERROR] Prepare failed: {e}[/bold red]")
        raise

@cli.command('generate-tests')
@click.option('--project', required=True, help='Ten du an')
@click.option('--base', default='main', show_default=True, help='Base git ref')
@click.option('--head', default='HEAD', show_default=True, help='Head git ref')
@click.option('--repo-path', default=None, help='Optional repository path override')
@click.option('--mode', type=click.Choice(['plan', 'patch']), default='plan', show_default=True, help='Generate a plan or write test files')
@click.option('--max-targets', default=3, show_default=True, help='Maximum missing-coverage targets')
@click.option('--target-id', default=None, help='Explicit function id, e.g. FUNC:HGTLinkPrediction.__init__')
@click.option('--source-file', default=None, help='Source file for explicit target id, e.g. scripts/train_model.py')
@click.option('--verify/--no-verify', default=True, show_default=True, help='Run pytest for generated files in patch mode')
@click.option('--repair-iters', default=0, show_default=True, help='Bounded heuristic repair loops after pytest failure')
@click.option('--refresh-runtime/--no-refresh-runtime', default=None, help='Run test-map automatically after pytest passes; defaults to on in patch+verify mode')
@click.option('--runtime-mode', type=click.Choice(['auto', 'dynamic-context', 'per-test']), default='auto', show_default=True, help='Runtime coverage mode for automatic refresh')
@click.option('--confirm-pr-scan/--no-confirm-pr-scan', default=True, show_default=True, help='Run pr-scan confirmation after runtime refresh')
@click.option('--keep-failing-tests/--rollback-failing-tests', default=False, show_default=True, help='Keep generated tests when verification fails instead of rolling back')
@click.option('--pytest-args', default=None, help='Override pytest args for verification and runtime refresh')
@click.option('--generation-strategy', type=click.Choice(['template', 'llm', 'auto']), default='auto', show_default=True, help='Use templates, LLM, or LLM with template fallback')
@click.option('--llm-provider', default=None, help='LLM provider override, e.g. openai-compatible')
@click.option('--llm-model', default=None, help='LLM model override')
@click.option('--llm-base-url', default=None, help='LLM base URL override')
@click.option('--llm-api-key-env', default=None, help='Name of env var containing the LLM API key')
@click.option('--llm-required/--llm-fallback', default=False, show_default=True, help='Fail if LLM is unavailable instead of falling back to templates')
@click.option('--llm-temperature', default=0.1, show_default=True, help='LLM temperature')
@click.option('--llm-max-tokens', default=4096, show_default=True, help='LLM max output tokens')
@click.option('--change-source', type=click.Choice(['auto', 'git', 'filesystem', 'full-scan']), default='auto', show_default=True, help='Detect changes from git, filesystem snapshot, or full scan')
def generate_tests(project, base, head, repo_path, mode, max_targets, target_id, source_file, verify, repair_iters, refresh_runtime, runtime_mode, confirm_pr_scan, keep_failing_tests, pytest_args, generation_strategy, llm_provider, llm_model, llm_base_url, llm_api_key_env, llm_required, llm_temperature, llm_max_tokens, change_source):
    """Generate impact-aware pytest plans or conservative test patches."""
    from softgnn_advisor.core.test_generation_agent import TestGenerationAgent

    console.rule(f"[bold cyan]SoftGNN Test Generation - Project: {project}")
    console.print(f"Range: [cyan]{base}...{head}[/cyan]")
    console.print(f"Mode: [yellow]{mode}[/yellow]")
    try:
        import os
        llm_api_key = os.getenv(llm_api_key_env) if llm_api_key_env else None
        agent = TestGenerationAgent(
            project,
            repo_path=repo_path,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
        )
        result = agent.generate(
            base=base,
            head=head,
            mode=mode,
            max_targets=max_targets,
            verify=verify,
            repair_iters=repair_iters,
            target_id=target_id,
            source_file=source_file,
            refresh_runtime=refresh_runtime,
            runtime_mode=runtime_mode,
            confirm_pr_scan=confirm_pr_scan,
            keep_failing_tests=keep_failing_tests,
            pytest_args=pytest_args,
            generation_strategy=generation_strategy,
            llm_required=llm_required,
            llm_temperature=llm_temperature,
            llm_max_tokens=llm_max_tokens,
            change_source=change_source,
        )
    except Exception as e:
        console.print(f"[bold red][ERROR] Test generation failed: {e}[/bold red]")
        raise

    markdown = agent.render_markdown(result)
    console.print(markdown)
    if result.files_written:
        console.print(f"[bold green]Wrote {len(result.files_written)} test file(s).[/bold green]")
    elif mode == 'plan':
        console.print("[bold green]Generated test plan without modifying files.[/bold green]")


@cli.command('test-map')
@click.option('--project', required=True, help='Ten du an')
@click.option('--repo-path', default=None, help='Optional repository path override')
@click.option('--pytest-args', default='tests', show_default=True, help='Arguments passed to pytest')
@click.option('--mode', type=click.Choice(['auto', 'dynamic-context', 'per-test']), default='auto', show_default=True, help='Runtime coverage mode')
@click.option('--persist/--no-persist', default=True, show_default=True, help='Persist runtime edges to graph and PyG data')
@click.option('--max-tests', default=None, type=int, help='Optional safety limit for discovered tests')
def test_map(project, repo_path, pytest_args, mode, persist, max_tests):
    """Map pytest runtime coverage to TestFunction -> executes_runtime -> Function edges."""
    from softgnn_advisor.infrastructure.pipelines.runtime_coverage_mapper import RuntimeCoverageMapper

    console.rule(f"[bold cyan]SoftGNN Runtime Test Mapping - Project: {project}")
    console.print(f"Mode: [cyan]{mode}[/cyan]")
    console.print(f"Pytest args: [yellow]{pytest_args}[/yellow]")
    try:
        mapper = RuntimeCoverageMapper(project, repo_path=repo_path)
        result = mapper.map_runtime_coverage(pytest_args=pytest_args, mode=mode, persist=persist, max_tests=max_tests)
    except Exception as e:
        console.print(f"[bold red][ERROR] Runtime coverage mapping failed: {e}[/bold red]")
        raise

    for warning in result.warnings:
        console.print(f"[yellow]{warning}[/yellow]")

    summary = Table(title="Runtime Test Mapping Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green")
    summary.add_row("Mode used", result.mode_used)
    summary.add_row("Discovered tests", str(len(result.discovered_tests)))
    summary.add_row("Mapped tests", str(result.passed_tests))
    summary.add_row("Unmapped/failed tests", str(result.failed_tests))
    summary.add_row("Runtime edges", str(len(result.runtime_edges)))
    summary.add_row("Persisted", str(result.persisted))
    console.print(summary)

    if result.runtime_edges:
        edge_table = Table(title="Runtime Coverage Edges")
        edge_table.add_column("#", justify="right", style="cyan")
        edge_table.add_column("Test", style="magenta")
        edge_table.add_column("Function", style="yellow")
        edge_table.add_column("File", style="white")
        edge_table.add_column("Covered", justify="right", style="green")
        for idx, edge in enumerate(result.runtime_edges[:30], start=1):
            edge_table.add_row(
                str(idx),
                edge.test_id,
                edge.target_id,
                edge.source_file,
                f"{edge.covered_line_count}/{edge.function_line_count} ({edge.covered_fraction:.1%})",
            )
        console.print(edge_table)

    console.print("[bold green]Runtime test mapping complete.[/bold green]")


@cli.command('pr-scan')
@click.option('--project', required=True, help='Ten du an')
@click.option('--base', default='main', show_default=True, help='Base git ref')
@click.option('--head', default='HEAD', show_default=True, help='Head git ref')
@click.option('--repo-path', default=None, help='Optional repository path override')
@click.option('--change-source', type=click.Choice(['auto', 'git', 'filesystem', 'full-scan']), default='auto', show_default=True, help='Detect changes from git, filesystem snapshot, or full scan')
@click.option('--mode', type=click.Choice(['deterministic', 'hybrid', 'gnn']), default='hybrid', show_default=True, help='Impact scoring mode')
@click.option('--gnn-types', default='File,Class,Function', show_default=True, help='Comma-separated node types for GNN impact candidates')
@click.option('--max-impact', default=30, show_default=True, help='Maximum impact hotspots to show')
@click.option('--max-reviewers', default=3, show_default=True, help='Maximum reviewers to recommend')
@click.option('--suggest-tests/--no-suggest-tests', default=True, show_default=True, help='Suggest tests for changed and impacted nodes')
def pr_scan(project, base, head, repo_path, change_source, mode, gnn_types, max_impact, max_reviewers, suggest_tests):
    """Scan a local PR/diff and recommend impact, reviewers, and tests."""
    from softgnn_advisor.core.pr_scanner import PRScanner

    console.print(Panel(
        f"Running PR Scan\n"
        f"Project: [yellow]{project}[/yellow]\n"
        f"Range: [cyan]{base}...{head}[/cyan]\n"
        f"Change source: [cyan]{change_source}[/cyan]\n"
        f"Mode: [cyan]{mode}[/cyan]"
    ))
    try:
        scanner = PRScanner(project, repo_path=repo_path)
        result = scanner.scan(base=base, head=head, mode=mode, gnn_types=gnn_types, max_impact=max_impact, max_reviewers=max_reviewers, suggest_tests=suggest_tests, change_source=change_source)
    except FileNotFoundError as e:
        console.print(f"[bold red][ERROR] {e}[/bold red]")
        return

    for warning in result.warnings:
        console.print(f"[yellow]{warning}[/yellow]")

    summary = Table(title="PR Scan Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green")
    summary.add_row("Change source", result.change_source)
    summary.add_row("Changed files", str(len(result.changed_files)))
    summary.add_row("Changed graph nodes", str(len(result.changed_nodes)))
    summary.add_row("Impact hotspots", str(len(result.impact_hotspots)))
    summary.add_row("Contract changes", str(len(result.contract_changes)))
    summary.add_row("Related tests", str(len(result.related_tests)))
    summary.add_row("Missing coverage", str(len(result.missing_coverage)))
    summary.add_row("Reviewer recommendations", str(len(result.reviewers)))
    summary.add_row("Test suggestions", str(len(result.suggested_tests)))
    console.print(summary)

    if result.changed_files:
        files_table = Table(title="Changed Files")
        files_table.add_column("#", justify="right", style="cyan")
        files_table.add_column("File", style="magenta")
        files_table.add_column("Hunks", justify="right", style="yellow")
        files_table.add_column("Status", style="blue")
        files_table.add_column("Source", style="cyan")
        files_table.add_column("+/-", style="green")
        for idx, changed_file in enumerate(result.changed_files[:20], start=1):
            files_table.add_row(str(idx), changed_file.path, str(len(changed_file.hunks)), getattr(changed_file, 'status', 'modified'), getattr(changed_file, 'source', result.change_source), f"+{changed_file.added_lines}/-{changed_file.deleted_lines}")
        console.print(files_table)

    if result.changed_nodes:
        nodes_table = Table(title="Changed Graph Nodes")
        nodes_table.add_column("#", justify="right", style="cyan")
        nodes_table.add_column("Node", style="magenta")
        nodes_table.add_column("Type", style="blue")
        nodes_table.add_column("Source File", style="white")
        for idx, node in enumerate(result.changed_nodes[:20], start=1):
            nodes_table.add_row(str(idx), node.label, node.node_type, node.source_file)
        console.print(nodes_table)

    if result.impact_hotspots:
        impact_table = Table(title="Impact Hotspots")
        impact_table.add_column("Rank", justify="right", style="cyan")
        impact_table.add_column("Node", style="magenta")
        impact_table.add_column("Type", style="blue")
        impact_table.add_column("Risk", justify="right", style="green")
        impact_table.add_column("Level", style="yellow")
        impact_table.add_column("Evidence", style="cyan")
        impact_table.add_column("Source", style="white")
        for idx, hotspot in enumerate(result.impact_hotspots[:max_impact], start=1):
            impact_table.add_row(
                str(idx), hotspot.label, hotspot.node_type,
                f"{hotspot.risk_score * 100:.1f}%",
                hotspot.risk_level,
                ', '.join(hotspot.evidence[:3]),
                hotspot.sources[0] if hotspot.sources else '-',
            )
        console.print(impact_table)

    if result.reviewers:
        reviewer_table = Table(title="Recommended Reviewers")
        reviewer_table.add_column("Rank", justify="right", style="cyan")
        reviewer_table.add_column("Reviewer", style="magenta")
        reviewer_table.add_column("Score", justify="right", style="green")
        reviewer_table.add_column("Evidence", style="white")
        for idx, reviewer in enumerate(result.reviewers, start=1):
            reviewer_table.add_row(str(idx), reviewer.developer, f"{reviewer.score * 100:.1f}%", '; '.join(reviewer.evidence[:3]))
        console.print(reviewer_table)

    if result.contract_changes:
        contract_table = Table(title="Contract Changes")
        contract_table.add_column("Function", style="magenta")
        contract_table.add_column("Signature", style="cyan")
        contract_table.add_column("Return", style="cyan")
        contract_table.add_column("Behavior", style="yellow")
        contract_table.add_column("Summary", style="white")
        for change in result.contract_changes[:20]:
            contract_table.add_row(
                change.function_id,
                "yes" if change.signature_changed else "no",
                "yes" if change.return_pattern_changed else "no",
                "yes" if change.behavior_changed else ("source-only" if change.source_only_changed else "no"),
                '; '.join(change.summary),
            )
        console.print(contract_table)

    if result.related_tests:
        related_table = Table(title="Existing Related Tests")
        related_table.add_column("Test", style="magenta")
        related_table.add_column("Relation", style="cyan")
        related_table.add_column("Target", style="yellow")
        related_table.add_column("Evidence", style="white")
        for related in result.related_tests[:20]:
            related_table.add_row(related.test_id, related.relation, related.target_id, related.evidence)
        console.print(related_table)

    if result.missing_coverage:
        missing_table = Table(title="Missing Test / Contract Coverage")
        missing_table.add_column("Target", style="magenta")
        missing_table.add_column("Reason", style="yellow")
        missing_table.add_column("Suggested Action", style="white")
        for gap in result.missing_coverage[:20]:
            missing_table.add_row(gap.target_id, gap.reason, gap.suggested_action)
        console.print(missing_table)

    if result.suggested_tests:
        tests_table = Table(title="Suggested Tests")
        tests_table.add_column("#", justify="right", style="cyan")
        tests_table.add_column("Test", style="magenta")
        tests_table.add_column("Type", style="blue")
        tests_table.add_column("Suggested File", style="yellow")
        tests_table.add_column("Reason", style="white")
        for idx, test in enumerate(result.suggested_tests, start=1):
            tests_table.add_row(str(idx), test.name, test.test_type, test.suggested_file, test.reason)
        console.print(tests_table)

    console.print("\n[bold green]PR Scan Complete.[/bold green] Results are evidence-grounded; GNN-only items are exploratory suggestions.")


@cli.command()
@click.option('--project', required=True, help='Ten du an')
@click.option('--mode', type=click.Choice(['deterministic', 'hybrid', 'gnn']), default='deterministic', show_default=True, help='Impact scoring mode')
@click.option('--gnn-types', default='File,Class,Function', show_default=True, help='Comma-separated node types for GNN impact candidates')
@click.argument('function_name')
def impact(project, mode, gnn_types, function_name):
    """Du bao ham/file co nguy co bi anh huong khi thay doi target."""
    from softgnn_advisor.core.impact_engine import ImpactEngine

    console.print(Panel(
        f"Running Change Impact Analysis for: [bold cyan]{function_name}[/bold cyan]\n"
        f"Project: [yellow]{project}[/yellow]\n"
        f"Mode: [cyan]{mode}[/cyan]"
    ))

    try:
        engine = ImpactEngine(project)
    except FileNotFoundError as e:
        console.print(f"[bold red][ERROR] {e}[/bold red]")
        return

    def status_callback(fn):
        with console.status("Computing GNN impact proximity...", spinner="dots"):
            return fn()

    result = engine.analyze(function_name, mode=mode, gnn_types=gnn_types, limit=10, status_callback=status_callback)
    if result is None:
        console.print(f"[bold red][ERROR] Cannot find any File/Function/Class matching '{function_name}'[/bold red]")
        return

    for warning in result.warnings:
        console.print(f"[yellow]{warning}[/yellow]")

    console.print(f"Target identified: [bold green]{result.target.full_id}[/bold green] (Type: {result.target.node_type})")

    if result.internal_members:
        internal_table = Table(title="Internal Members / Direct Definitions")
        internal_table.add_column("#", justify="right", style="cyan", no_wrap=True)
        internal_table.add_column("Node", style="magenta")
        internal_table.add_column("Type", style="blue")
        internal_table.add_column("Relation", style="yellow")
        internal_table.add_column("Path", style="white")
        for idx, (key, relation, path) in enumerate(result.internal_members[:12], start=1):
            internal_table.add_row(str(idx), engine.display_node_label(key), key[0], relation, path)
        console.print(internal_table)

    if not result.candidates:
        console.print("[yellow]No downstream impact candidates found. If this graph was built before symbol-use edges existed, rerun ETL/prepare.[/yellow]")
        return

    table = Table(title="Downstream Dependents / Impact Candidates")
    table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
    table.add_column("Node", style="magenta")
    table.add_column("Type", style="blue")
    if result.mode in {'hybrid', 'gnn'}:
        table.add_column("Final", justify="right", style="green")
        table.add_column("Rule", justify="right", style="yellow")
        table.add_column("GNN", justify="right", style="blue")
    else:
        table.add_column("Impact", justify="right", style="green")
    table.add_column("Evidence", style="cyan")
    table.add_column("Relation", style="yellow")
    table.add_column("Path", style="white")

    for idx, candidate in enumerate(result.candidates, start=1):
        evidence = ', '.join(candidate.tiers[:2])
        relation = ', '.join(candidate.relations)
        path = candidate.paths[0] if candidate.paths else '-'
        if result.mode in {'hybrid', 'gnn'}:
            table.add_row(
                str(idx), candidate.label, candidate.node_type,
                f"{candidate.final_score * 100:.1f}%",
                f"{candidate.rule_score * 100:.1f}%",
                f"{candidate.gnn_score * 100:.1f}%",
                evidence, relation, path,
            )
        else:
            table.add_row(str(idx), candidate.label, candidate.node_type, f"{candidate.final_score * 100:.1f}%", evidence, relation, path)

    console.print(table)
    console.print("\n[bold]Evidence legend:[/bold] Direct = node directly depends on target; Context = file/class containing a direct dependent; Historical = Git co-change fallback; GNN-suggested = embedding-proximity suggestion without a deterministic path.")
    if result.mode == 'hybrid':
        console.print("[bold]Hybrid scoring:[/bold] with rule evidence: Final = 85% Rule + 15% GNN; GNN-only: Final = 20% GNN.")
    elif result.mode == 'gnn':
        console.print(f"[bold]GNN scoring:[/bold] Final = GNN embedding proximity rank percentile over candidate types: {', '.join(sorted(result.gnn_type_filter))}. Use this for exploratory suggestions, not hard dependency evidence.")
    if result.direct_count == 0:
        console.print("[yellow]No direct code dependency found; results are historical/GNN suggestions only.[/yellow]")
    console.print("\n[bold green]Analysis Complete.[/bold green] Internal definitions are separated from downstream impact evidence.")


@cli.command()
@click.option('--project', required=True, help='Ten du an')
@click.argument('bug_description')
def triage(project, bug_description):
    """De xuat ky su phu hop nhat de sua mot Bug moi"""
    import pandas as pd
    import re
    try:
        import torch
        import torch_geometric.transforms as T
        from softgnn_advisor.core.ai.predicter import Predictor
        from softgnn_advisor.core.ai.gnn_architecture import HGTLinkPrediction
    except ImportError as exc:
        raise click.ClickException(
            "triage requires GNN dependencies and a trained model. Install with: "
            "pip install \"softgnn-advisor[gnn]\""
        ) from exc
    from softgnn_advisor.config.settings import get_project_paths
    from softgnn_advisor.core.file_filters import is_source_code_file, is_valid_developer_name
    from softgnn_advisor.core.metadata_utils import load_metadata
    from softgnn_advisor.core.developer_aliases import load_developer_aliases, resolve_developer_identity
    from softgnn_advisor.infrastructure.pipelines.feature_encoder import CodebaseFeatureEncoder

    console.print(Panel(
        f"[SEARCH] Bug Triage Analysis\n"
        f"Project: [yellow]{project}[/yellow]\n"
        f"Bug: [italic]{bug_description}[/italic]"
    ))

    paths = get_project_paths(project)
    PYG_DATA_PATH = paths['PYG_DATA_PATH']
    MODEL_PATH = paths['MODEL_PATH']
    NODES_DATA_PATH = paths['NODES_DATA_PATH']
    METADATA_PATH = paths['METADATA_PATH']
    metadata = load_metadata(METADATA_PATH)
    source_path = metadata.get('source_path')
    developer_aliases = load_developer_aliases(paths['DEVELOPER_ALIASES_PATH'])

    if not os.path.exists(MODEL_PATH) or not os.path.exists(PYG_DATA_PATH):
        console.print(f"[bold red][ERROR] Model or Data not found for project '{project}'.[/bold red]")
        console.print("Run [cyan]softgnn etl[/cyan] and [cyan]softgnn train[/cyan] first.")
        return

    # 1. Encode bug description into a feature vector
    with console.status("Encoding bug semantics...", spinner="dots"):
        encoder = CodebaseFeatureEncoder()
        bug_vec = encoder.model.encode([bug_description], convert_to_numpy=True)[0]
    console.print(f"Bug encoded as vector of dimension [cyan]{len(bug_vec)}[/cyan]")

    # 2. Load graph + model (same transform as training)
    data = torch.load(PYG_DATA_PATH, map_location='cpu', weights_only=False)
    data = T.ToUndirected()(data)

    model = HGTLinkPrediction(128, 128, data=data, dropout=0.0)
    model.load_state_dict(torch.load(MODEL_PATH, map_location='cpu', weights_only=True))

    # 3. Build Predictor (computes all embeddings via full-batch forward pass)
    predictor = Predictor(model, data=data)
    device = predictor.device

    # 4. Project bug vector into the same 128-dim embedding space as the graph nodes.
    #    We reuse the 'Commit' projection layer because a bug report is semantically
    #    closest to a commit description (both describe code changes in natural language).
    bug_tensor = torch.tensor(bug_vec, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        projected_bug = predictor.model.encoder.lin_dict['Commit'](bug_tensor).relu_()

    # 5. Score all Developer nodes against the projected bug vector (GNN component)
    df = pd.read_csv(NODES_DATA_PATH)
    dev_df = df[df['type'] == 'Developer'].copy()

    if dev_df.empty:
        console.print("[yellow]No Developer nodes found in the graph. Run ETL on a Git repo first.[/yellow]")
        return

    with console.status("Querying Developer subgraph...", spinner="dots"):
        if 'Developer' not in predictor.embeddings:
            console.print("[yellow]No Developer embeddings found in model.[/yellow]")
            return

        dev_embeddings = predictor.embeddings['Developer'].to(device)
        decoder_key = '__authored_by__'
        if decoder_key not in predictor.model.decoders:
            decoder_key = list(predictor.model.decoders.keys())[0]
        decoder = predictor.model.decoders[decoder_key]

        batch_src = projected_bug.expand(dev_embeddings.size(0), -1)
        with torch.no_grad():
            logits = decoder(batch_src, dev_embeddings)
            gnn_scores = torch.sigmoid(logits).view(-1).detach().cpu().numpy()

    def lexical_file_relevance(rel_path):
        """Lightweight source-content boost for short bug reports."""
        if not source_path:
            return 0.0
        full_path = os.path.join(source_path, rel_path.replace('/', os.sep))
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read(20000).lower()
        except Exception:
            return 0.0

        bug_text = bug_description.lower()
        bug_terms = set(re.findall(r"[a-zA-Z_]+", bug_text))
        file_loading_intent = any(term in bug_text for term in ['file', 'load', 'loading', 'read', 'upload', 'download', 'tải', 'tai'])
        if file_loading_intent:
            terms = [
                'open(', 'read(', 'read_csv', 'read_excel', 'json.load', 'yaml.safe_load',
                'uploaded_file', 'file_uploader', 'upload', 'download', 'load', 'loads',
                'parse', 'extract', 'path', 'filepath', 'filename', 'csv', 'json', 'pickle'
            ]
        else:
            terms = list(bug_terms)

        hits = sum(1 for term in terms if term and term in text)
        path_bonus = sum(1 for term in terms if term and term.replace('(', '') in rel_path.lower())
        return min(1.0, (hits + path_bonus) / 8.0)

    # 6. Semantic bug -> File matching component
    file_df = df[df['type'] == 'File'].copy()
    file_df['rel_path'] = file_df['id'].astype(str).str.replace('FILE:', '', regex=False)
    # For semantic bug matching, prefer real source files only.
    # Ownership graph can still contain config/docs, but semantic matching should stay focused.
    file_df = file_df[file_df['rel_path'].apply(is_source_code_file)]
    if source_path:
        file_df = file_df[file_df['rel_path'].apply(lambda p: os.path.exists(os.path.join(source_path, p.replace('/', os.sep))))]
    file_semantic_scores = {}
    top_related_files = []
    if 'File' in data.node_types and not file_df.empty:
        file_x = data['File'].x.float()
        bug_feature = torch.tensor(bug_vec, dtype=torch.float32).view(1, -1)
        if file_x.size(1) == bug_feature.size(1):
            sims = torch.nn.functional.cosine_similarity(file_x, bug_feature.expand(file_x.size(0), -1), dim=1)
            for _, row in file_df.iterrows():
                pyg_id = int(row['pyg_id'])
                if pyg_id < len(sims):
                    file_id = str(row['id']).replace('FILE:', '')
                    semantic_score = float((sims[pyg_id].item() + 1.0) / 2.0)
                    lexical_score = lexical_file_relevance(file_id)
                    combined_score = (0.65 * semantic_score) + (0.35 * lexical_score)
                    file_semantic_scores[pyg_id] = combined_score
                    top_related_files.append((file_id, combined_score, semantic_score, lexical_score, pyg_id))
            top_related_files.sort(key=lambda x: x[1], reverse=True)
            top_related_files = top_related_files[:5]

    # 7. Git ownership component: Developer -> Commit -> File
    commit_to_devs = {}
    if ('Developer', 'authored_by', 'Commit') in data.edge_types:
        for src, dst in data[('Developer', 'authored_by', 'Commit')].edge_index.t().tolist():
            commit_to_devs[int(dst)] = int(src)

    dev_ownership_raw = {}
    dev_direct_evidence = {}
    dev_broad_evidence = {}
    if ('Commit', 'modifies', 'File') in data.edge_types:
        related_file_ids = {pyg_id for _, _, _, _, pyg_id in top_related_files}
        file_name_by_pyg = {
            int(row['pyg_id']): str(row['id']).replace('FILE:', '')
            for _, row in file_df.iterrows()
        }
        for commit_id, file_id in data[('Commit', 'modifies', 'File')].edge_index.t().tolist():
            commit_id = int(commit_id)
            file_id = int(file_id)
            dev_id = commit_to_devs.get(commit_id)
            if dev_id is None:
                continue

            sem = file_semantic_scores.get(file_id, 0.0)
            is_direct = file_id in related_file_ids
            # Direct top-related files should dominate ownership scoring.
            # Other source files only provide weak fallback ownership context.
            contribution = sem if is_direct else sem * 0.10
            dev_ownership_raw[dev_id] = dev_ownership_raw.get(dev_id, 0.0) + max(contribution, 0.001)

            fname = file_name_by_pyg.get(file_id)
            if fname:
                target = dev_direct_evidence if is_direct else dev_broad_evidence
                target.setdefault(dev_id, {})[fname] = target.setdefault(dev_id, {}).get(fname, 0) + 1

    max_ownership = max(dev_ownership_raw.values()) if dev_ownership_raw else 1.0

    # Fixed initial weights approved by user
    W_GNN = 0.45
    W_GIT = 0.35
    W_SEM = 0.20

    best_by_name = {}
    for _, row in dev_df.iterrows():
        dev_pyg_id = int(row['pyg_id'])
        dev_name = resolve_developer_identity(str(row['name']), '', developer_aliases)
        if not is_valid_developer_name(dev_name):
            continue
        gnn_score = float(gnn_scores[dev_pyg_id]) if dev_pyg_id < len(gnn_scores) else 0.0
        git_score = float(dev_ownership_raw.get(dev_pyg_id, 0.0) / max_ownership) if max_ownership else 0.0
        direct_evidence = dev_direct_evidence.get(dev_pyg_id, {})
        broad_evidence = dev_broad_evidence.get(dev_pyg_id, {})
        sem_score = 0.0
        if direct_evidence and top_related_files:
            touched_related = set(direct_evidence.keys())
            top_file_names = {name for name, _, _, _, _ in top_related_files}
            sem_score = len(touched_related & top_file_names) / max(len(top_file_names), 1)
        final_score = (W_GNN * gnn_score) + (W_GIT * git_score) + (W_SEM * sem_score)

        current = best_by_name.get(dev_name)
        if current is None or final_score > current['final_score']:
            best_by_name[dev_name] = {
                'final_score': final_score,
                'gnn_score': gnn_score,
                'git_score': git_score,
                'sem_score': sem_score,
                'direct_evidence': direct_evidence,
                'broad_evidence': broad_evidence,
            }

    ranked = sorted(best_by_name.items(), key=lambda x: x[1]['final_score'], reverse=True)

    if top_related_files:
        related_table = Table(title="Bug-related Files (Hybrid Relevance)")
        related_table.add_column("Rank", justify="right", style="cyan")
        related_table.add_column("File", style="magenta")
        related_table.add_column("Relevance", justify="right", style="green")
        related_table.add_column("Semantic", justify="right", style="blue")
        related_table.add_column("Lexical", justify="right", style="yellow")
        for idx, (fname, relevance, semantic_score, lexical_score, _) in enumerate(top_related_files, start=1):
            related_table.add_row(
                str(idx),
                fname,
                f"{relevance * 100:.1f}%",
                f"{semantic_score * 100:.1f}%",
                f"{lexical_score * 100:.1f}%",
            )
        console.print(related_table)

    table = Table(title="Top Recommended Developers (Hybrid Scoring)")
    table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
    table.add_column("Developer", style="magenta")
    table.add_column("Final", justify="right", style="green")
    table.add_column("GNN", justify="right", style="blue")
    table.add_column("Git", justify="right", style="yellow")
    table.add_column("Evidence", style="white")

    for rank, (dev_name, info) in enumerate(ranked[:3], start=1):
        evidence_source = info['direct_evidence'] or info['broad_evidence']
        evidence_items = sorted(evidence_source.items(), key=lambda x: x[1], reverse=True)[:3]
        if info['direct_evidence']:
            evidence_prefix = "Direct: "
        elif evidence_items:
            evidence_prefix = "Fallback: "
        else:
            evidence_prefix = ""
        evidence_text = evidence_prefix + ", ".join([f"{f} x{c}" for f, c in evidence_items]) if evidence_items else "No direct file evidence"
        table.add_row(
            str(rank),
            dev_name,
            f"{info['final_score'] * 100:.1f}%",
            f"{info['gnn_score'] * 100:.1f}%",
            f"{info['git_score'] * 100:.1f}%",
            evidence_text,
        )

    console.print(table)
    console.print("\n[bold green]Triage Complete.[/bold green]")


@cli.command()
@click.option('--project', required=True, help='Ten du an can kiem tra')
def inspect(project):
    """Kiem tra chat luong Do thi Tri thuc cua mot du an"""
    try:
        import torch
        import torch_geometric.transforms as T
    except ImportError as exc:
        raise click.ClickException(
            "inspect currently requires GNN artifacts. Install with: "
            "pip install \"softgnn-advisor[gnn]\""
        ) from exc
    import pandas as pd
    from softgnn_advisor.config.settings import get_project_paths

    console.rule(f"[bold cyan]Graph Inspection - Project: {project}")

    paths = get_project_paths(project)
    PYG_DATA_PATH = paths['PYG_DATA_PATH']
    NODES_DATA_PATH = paths['NODES_DATA_PATH']
    MODEL_PATH = paths['MODEL_PATH']

    # --- 1. File existence check ---
    console.print("\n[bold]--- Artifact Files ---[/bold]")
    for label, path in [
        ("nodes_data.csv", NODES_DATA_PATH),
        ("pyg_data.pt",    PYG_DATA_PATH),
        ("model.pt",       MODEL_PATH),
    ]:
        exists = "[green]FOUND[/green]" if os.path.exists(path) else "[red]MISSING[/red]"
        console.print(f"  {label:<20} {exists}  ({path})")

    if not os.path.exists(PYG_DATA_PATH):
        console.print("\n[red][ERROR] PyG data missing — run `softgnn etl` first.[/red]")
        return

    # --- 2. Node inventory ---
    console.print("\n[bold]--- Node Inventory (nodes_data.csv) ---[/bold]")
    df = pd.read_csv(NODES_DATA_PATH)
    node_counts = df['type'].value_counts()
    node_table = Table(show_header=True, header_style="bold magenta")
    node_table.add_column("Node Type", style="cyan")
    node_table.add_column("Count", justify="right", style="green")
    for ntype, cnt in node_counts.items():
        node_table.add_row(ntype, str(cnt))
    console.print(node_table)

    if 'kind' in df.columns and 'Function' in set(df['type']):
        console.print("\n[bold]--- Function Kind Inventory ---[/bold]")
        func_df = df[df['type'] == 'Function'].copy()
        kind_counts = func_df['kind'].fillna('unknown').value_counts()
        kind_table = Table(show_header=True, header_style="bold magenta")
        kind_table.add_column("Function Kind", style="cyan")
        kind_table.add_column("Count", justify="right", style="green")
        total_functions = max(len(func_df), 1)
        noisy = 0
        for kind, cnt in kind_counts.items():
            if kind in {'builtin', 'external', 'unknown'}:
                noisy += int(cnt)
            kind_table.add_row(str(kind), str(cnt))
        console.print(kind_table)
        noise_ratio = noisy / total_functions
        console.print(f"  Noise ratio (builtin/external/unknown): [cyan]{noise_ratio * 100:.1f}%[/cyan]")
        if noise_ratio > 0.5:
            console.print("  [yellow][INFO] Most Function nodes are external/builtin/unknown calls, which is normal for AST call graphs.[/yellow]")
            console.print("  Impact/triage should prioritize project-defined functions using the `kind` metadata.")

    # --- 3. Raw graph statistics ---
    console.print("\n[bold]--- Raw PyG Graph (before ToUndirected) ---[/bold]")
    data = torch.load(PYG_DATA_PATH, map_location='cpu', weights_only=False)
    console.print(f"  Total nodes : [cyan]{data.num_nodes}[/cyan]")
    console.print(f"  Total edges : [cyan]{data.num_edges}[/cyan]")
    console.print(f"  Node types  : {data.node_types}")

    edge_table = Table(show_header=True, header_style="bold magenta")
    edge_table.add_column("Edge Type (src, rel, dst)", style="yellow")
    edge_table.add_column("# Edges", justify="right", style="green")
    edge_table.add_column("Diagnosis", style="cyan")

    WARN_THRESHOLD = 5   # fewer than this = sparse / problematic

    for et in data.edge_types:
        n = data[et].edge_index.size(1)
        if et[1].startswith('rev_'):
            continue  # skip reverse edges for clarity
        diagnosis = "[green]OK[/green]" if n >= WARN_THRESHOLD else "[red]SPARSE[/red]"
        edge_table.add_row(str(et), str(n), diagnosis)

    console.print(edge_table)

    # --- 4. After ToUndirected ---
    data_u = T.ToUndirected()(data)
    console.print(f"\n[bold]After ToUndirected:[/bold] {data_u.num_edges} total edges ({len(data_u.edge_types)} types)")

    # --- 5. Developer-centric diagnosis ---
    console.print("\n[bold]--- Developer Connectivity Diagnosis ---[/bold]")
    dev_count = node_counts.get('Developer', 0)
    commit_count = node_counts.get('Commit', 0)
    console.print(f"  Developers : [cyan]{dev_count}[/cyan]")
    console.print(f"  Commits    : [cyan]{commit_count}[/cyan]")

    authored_edges = 0
    for et in data.edge_types:
        if 'authored_by' in et[1] or 'modifies' in et[1]:
            authored_edges += data[et].edge_index.size(1)
    console.print(f"  Git edges (authored_by + modifies): [cyan]{authored_edges}[/cyan]")

    if dev_count == 0:
        console.print("\n  [red][WARN] No Developer nodes found![/red]")
        console.print("  Git history may not have been parsed. Check that the --path points to a Git repo.")
    elif authored_edges < dev_count * 2:
        console.print(f"\n  [yellow][WARN] Very few Git edges per Developer ({authored_edges}/{dev_count}).[/yellow]")
        console.print("  The Triage model will underperform. Consider scanning a repo with richer commit history.")
    else:
        console.print("\n  [green][OK] Developer graph looks healthy for training.[/green]")

    # --- 6. Model status ---
    if os.path.exists(MODEL_PATH):
        size_mb = os.path.getsize(MODEL_PATH) / 1024 / 1024
        console.print(f"\n[bold]--- Trained Model ---[/bold]")
        console.print(f"  model.pt size: [cyan]{size_mb:.2f} MB[/cyan]")
        console.print(f"  [green][OK] Model is ready for inference.[/green]")
    else:
        console.print(f"\n  [yellow]No trained model yet — run `softgnn train --project {project}`[/yellow]")

    console.rule("[bold cyan]Inspection Complete")


@cli.command()
@click.option('--project', required=True, help='Ten du an')
@click.option('--developer', required=True, help='Ten developer can giai thich')
def explain(project, developer):
    """Giai thich vi sao mot developer duoc de xuat"""
    import pandas as pd
    try:
        import torch
    except ImportError as exc:
        raise click.ClickException(
            "explain currently requires GNN artifacts. Install with: "
            "pip install \"softgnn-advisor[gnn]\""
        ) from exc
    from collections import Counter, defaultdict
    from softgnn_advisor.config.settings import get_project_paths
    from softgnn_advisor.core.developer_aliases import load_developer_aliases, resolve_developer_identity

    console.rule(f"[bold cyan]Developer Explanation - Project: {project}")
    console.print(Panel(
        f"Developer: [bold magenta]{developer}[/bold magenta]\n"
        "Evidence source: Git graph (Developer -> Commit -> File)"
    ))

    paths = get_project_paths(project)
    PYG_DATA_PATH = paths['PYG_DATA_PATH']
    NODES_DATA_PATH = paths['NODES_DATA_PATH']

    if not os.path.exists(PYG_DATA_PATH) or not os.path.exists(NODES_DATA_PATH):
        console.print("[bold red][ERROR] Missing project data. Run ETL first.[/bold red]")
        return

    df = pd.read_csv(NODES_DATA_PATH)
    data = torch.load(PYG_DATA_PATH, map_location='cpu', weights_only=False)
    developer_aliases = load_developer_aliases(paths['DEVELOPER_ALIASES_PATH'])
    canonical_query = resolve_developer_identity(developer, '', developer_aliases).lower()
    dev_df_all = df[df['type'] == 'Developer'].copy()
    dev_df_all['canonical_name'] = dev_df_all['name'].apply(lambda n: resolve_developer_identity(str(n), '', developer_aliases))

    dev_matches = dev_df_all[
        dev_df_all['canonical_name'].str.lower().str.contains(canonical_query, case=False, na=False)
    ]

    if dev_matches.empty:
        console.print(f"[bold red][ERROR] Cannot find Developer matching '{developer}'[/bold red]")
        available = dev_df_all['canonical_name'].drop_duplicates().tolist()
        console.print("Available developers:")
        for name in available:
            console.print(f"  - {name}")
        return

    # Build quick lookup maps: (type, pyg_id) -> row
    lookup = {}
    for _, row in df.iterrows():
        lookup[(row['type'], int(row['pyg_id']))] = row

    dev_pyg_ids = set(int(x) for x in dev_matches['pyg_id'].tolist())
    authored_commits = []

    # Developer -> Commit
    edge_type = ('Developer', 'authored_by', 'Commit')
    if edge_type in data.edge_types:
        edge_index = data[edge_type].edge_index
        for src, dst in edge_index.t().tolist():
            if src in dev_pyg_ids:
                commit_row = lookup.get(('Commit', int(dst)))
                if commit_row is not None:
                    authored_commits.append({
                        'developer_pyg_id': src,
                        'commit_pyg_id': int(dst),
                        'commit_name': commit_row['name'],
                        'commit_id': commit_row['id'],
                    })

    if not authored_commits:
        console.print("[yellow]No authored commits found for this developer in graph.[/yellow]")
        return

    commit_ids = set(c['commit_pyg_id'] for c in authored_commits)
    commit_to_files = defaultdict(list)
    file_counter = Counter()

    # Commit -> File
    edge_type = ('Commit', 'modifies', 'File')
    if edge_type in data.edge_types:
        edge_index = data[edge_type].edge_index
        for src, dst in edge_index.t().tolist():
            if int(src) in commit_ids:
                file_row = lookup.get(('File', int(dst)))
                if file_row is not None:
                    file_name = str(file_row['name'])
                    file_id = str(file_row['id']).replace('FILE:', '')
                    commit_to_files[int(src)].append(file_id)
                    file_counter[file_id] += 1

    # Summary
    unique_files = len(file_counter)
    console.print(f"[bold]Summary[/bold]")
    console.print(f"  Matching developer identities : [cyan]{len(dev_matches)}[/cyan]")
    console.print(f"  Authored commits              : [cyan]{len(authored_commits)}[/cyan]")
    console.print(f"  Modified files                : [cyan]{unique_files}[/cyan]")

    # Top files table
    file_table = Table(title="Most Frequently Modified Files")
    file_table.add_column("Rank", justify="right", style="cyan")
    file_table.add_column("File", style="magenta")
    file_table.add_column("Touches", justify="right", style="green")

    for rank, (file_id, count) in enumerate(file_counter.most_common(10), start=1):
        file_table.add_row(str(rank), file_id, str(count))
    console.print(file_table)

    # Recent/evidence commits table (graph order is not guaranteed, so show first 10 collected)
    commit_table = Table(title="Evidence Commits")
    commit_table.add_column("#", justify="right", style="cyan")
    commit_table.add_column("Commit", style="yellow")
    commit_table.add_column("Touched Files", style="magenta")

    for idx, commit in enumerate(authored_commits[:10], start=1):
        files = commit_to_files.get(commit['commit_pyg_id'], [])
        files_preview = ", ".join(files[:3]) if files else "(no File edge)"
        if len(files) > 3:
            files_preview += f" ... +{len(files) - 3} more"
        commit_table.add_row(str(idx), str(commit['commit_name']), files_preview)
    console.print(commit_table)

    console.print("\n[bold green]Explanation Complete.[/bold green]")


@cli.command()
@click.option('--project', required=True, help='Ten du an can kiem tra')
def doctor(project):
    """Kiem tra moi truong, metadata va tinh hop le cua model/graph"""
    try:
        import torch
        import torch_geometric.transforms as T
        has_gnn_deps = True
    except ImportError:
        torch = None
        T = None
        has_gnn_deps = False
    from softgnn_advisor.config.settings import get_project_paths
    from softgnn_advisor.core.metadata_utils import compute_graph_schema_hash, load_metadata

    console.rule(f"[bold cyan]SoftGNN Doctor - Project: {project}")
    paths = get_project_paths(project)
    PYG_DATA_PATH = paths['PYG_DATA_PATH']
    NODES_DATA_PATH = paths['NODES_DATA_PATH']
    MODEL_PATH = paths['MODEL_PATH']
    METADATA_PATH = paths['METADATA_PATH']

    def ok(msg): console.print(f"[green][OK][/green] {msg}")
    def warn(msg): console.print(f"[yellow][WARN][/yellow] {msg}")
    def err(msg): console.print(f"[red][ERROR][/red] {msg}")

    ok(f"Python: {sys.version.split()[0]}")
    if has_gnn_deps:
        ok(f"Torch: {torch.__version__}")
        if torch.cuda.is_available():
            ok(f"CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            warn("CUDA not available; CPU mode will be used")
    else:
        warn("GNN dependencies not installed; deterministic/core features are available")
        warn("Install GNN extras with: pip install \"softgnn-advisor\\[gnn]\"")

    for label, path in [
        ('nodes_data.csv', NODES_DATA_PATH),
        ('pyg_data.pt', PYG_DATA_PATH),
        ('model.pt', MODEL_PATH),
        ('metadata.json', METADATA_PATH),
    ]:
        if os.path.exists(path):
            ok(f"{label} found")
        else:
            warn(f"{label} missing: {path}")

    metadata = load_metadata(METADATA_PATH)
    if not metadata:
        warn("metadata.json is missing or unreadable. Run ETL again to create metadata.")
    else:
        ok(f"ETL metadata loaded. Schema hash: {metadata.get('schema_hash', 'N/A')}")
        if metadata.get('train_finished_at'):
            ok(f"Training metadata found. Test AUC: {metadata.get('test_auc', 'N/A')}")
        else:
            warn("No training metadata found. Run setup --train after installing GNN extras if you need GNN ranking.")

    if os.path.exists(PYG_DATA_PATH) and has_gnn_deps:
        try:
            data = torch.load(PYG_DATA_PATH, map_location='cpu', weights_only=False)
            current_hash = compute_graph_schema_hash(data)
            model_current_hash = compute_graph_schema_hash(T.ToUndirected()(data))
            ok(f"Current graph loaded: {data.num_nodes} nodes, {data.num_edges} edges")
            ok(f"Current raw schema hash: {current_hash}")
            ok(f"Current training/inference schema hash: {model_current_hash}")

            if metadata.get('schema_hash') and metadata.get('schema_hash') != current_hash:
                warn("metadata schema_hash differs from current graph. Run ETL again.")
            if metadata.get('model_schema_hash'):
                if metadata['model_schema_hash'] == model_current_hash:
                    ok("model schema hash matches current training/inference graph")
                else:
                    err("model schema hash does NOT match current graph. Re-run train.")

            devs = int(data['Developer'].num_nodes) if 'Developer' in data.node_types else 0
            commits = int(data['Commit'].num_nodes) if 'Commit' in data.node_types else 0
            files = int(data['File'].num_nodes) if 'File' in data.node_types else 0
            modifies = 0
            if ('Commit', 'modifies', 'File') in data.edge_types:
                modifies = int(data[('Commit', 'modifies', 'File')].edge_index.size(1))
            ok(f"Graph inventory: {devs} developers, {commits} commits, {files} files, {modifies} commit-file edges")
            if devs == 0 or commits == 0:
                warn("Developer/Commit graph is empty; triage will be weak")
            if modifies < 10:
                warn("Commit -> File edges are sparse; Git ownership will be weak")
        except Exception as e:
            err(f"Could not load pyg_data.pt: {e}")
    elif os.path.exists(PYG_DATA_PATH) and not has_gnn_deps:
        warn("pyg_data.pt exists but cannot be inspected without GNN dependencies")
    else:
        warn("pyg_data.pt missing; this is expected for core-only setup without GNN extras")

    if not os.environ.get('HF_TOKEN'):
        warn("HF_TOKEN not set; HuggingFace downloads may be slower or rate-limited")

    console.rule("[bold cyan]Doctor Complete")


def _default_project_name(repo_path):
    return os.path.basename(os.path.abspath(repo_path).rstrip(os.sep)) or 'default'


def _repo_path_for_project(project):
    from softgnn_advisor.config.settings import get_project_paths
    from softgnn_advisor.core.metadata_utils import load_metadata
    metadata = load_metadata(get_project_paths(project)['METADATA_PATH'])
    repo_path = metadata.get('source_path')
    if not repo_path:
        raise click.ClickException(f"No source_path found for project '{project}'. Run: python softgnn.py setup C:\\path\\to\\repo --project {project}")
    if not os.path.exists(repo_path):
        raise click.ClickException(f"Stored source_path does not exist for project '{project}': {repo_path}")
    return repo_path


def _render_generation(agent, result):
    markdown = agent.render_markdown(result)
    console.print(markdown)
    if result.files_written:
        console.print(f"[bold green]Wrote {len(result.files_written)} test file(s).[/bold green]")
    return markdown


@cli.command('setup')
@click.argument('repo_path')
@click.option('--project', default=None, help='Project name; defaults to repository folder name')
@click.option('--train/--no-train', default=False, show_default=True, help='Run experimental HGT training after graph build')
def simple_setup(repo_path, project, train):
    """Beginner setup: build graph and filesystem snapshot."""
    project = project or _default_project_name(repo_path)
    console.rule(f"[bold cyan]SoftGNN Setup - Project: {project}")
    from softgnn_advisor.scripts.etl_run import run_etl_pipeline
    from softgnn_advisor.core.change_provider import build_filesystem_snapshot, save_filesystem_snapshot, snapshot_path_for_project

    run_etl_pipeline(repo_path, project)
    snapshot = build_filesystem_snapshot(repo_path)
    save_filesystem_snapshot(snapshot_path_for_project(project), snapshot)
    console.print("[bold green]Graph and filesystem snapshot saved.[/bold green]")
    if train:
        try:
            from softgnn_advisor.scripts.train_model import run_optimization
        except ImportError as exc:
            raise click.ClickException(
                "Training requires GNN dependencies. Install with: pip install \"softgnn-advisor[gnn]\" "
                "or pip install \"softgnn-advisor[all]\""
            ) from exc
        run_optimization(project)
        console.print("[bold green]Training completed.[/bold green]")
    else:
        console.print("[yellow]Training skipped. Use --train if you want experimental GNN ranking.[/yellow]")


@cli.command('scan')
@click.option('--project', required=True, help='Project name created by setup/prepare')
@click.option('--repo-path', default=None, help='Optional override; otherwise read from project metadata')
@click.option('--base', default='main', show_default=True)
@click.option('--head', default='HEAD', show_default=True)
@click.option('--source', type=click.Choice(['auto', 'git', 'filesystem', 'full-scan']), default='auto', show_default=True)
@click.option('--mode', type=click.Choice(['deterministic', 'hybrid', 'gnn']), default='hybrid', show_default=True)
@click.option('--max-impact', default=30, show_default=True)
def simple_scan(project, repo_path, base, head, source, mode, max_impact):
    """Beginner scan: detect changes and suggest coverage targets without LLM calls."""
    repo_path = repo_path or _repo_path_for_project(project)
    console.print("[cyan]LLM: not used | Writes: none | Pytest: not run[/cyan]")
    from softgnn_advisor.core.pr_scanner import PRScanner
    scanner = PRScanner(project, repo_path=repo_path)
    result = scanner.scan(base=base, head=head, mode=mode, max_impact=max_impact, change_source=source)
    for warning in result.warnings:
        console.print(f"[yellow]{warning}[/yellow]")
    summary = Table(title="Scan Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green")
    summary.add_row("Project", project)
    summary.add_row("Change source", result.change_source)
    summary.add_row("Changed files", str(len(result.changed_files)))
    summary.add_row("Changed nodes", str(len(result.changed_nodes)))
    summary.add_row("Missing coverage", str(len(result.missing_coverage)))
    summary.add_row("Suggested tests", str(len(result.suggested_tests)))
    console.print(summary)


@cli.command('plan')
@click.option('--project', required=True, help='Project name created by setup/prepare')
@click.option('--repo-path', default=None, help='Optional override; otherwise read from project metadata')
@click.option('--base', default='main', show_default=True)
@click.option('--head', default='HEAD', show_default=True)
@click.option('--target', default=None, help='Target id, e.g. FUNC:foo')
@click.option('--file', 'source_file', default=None, help='Source file for explicit target')
@click.option('--max-targets', default=3, show_default=True)
@click.option('--strategy', type=click.Choice(['template', 'llm', 'auto']), default='llm', show_default=True)
@click.option('--no-llm', is_flag=True, help='Do not call LLM; generate template tests')
@click.option('--source', type=click.Choice(['auto', 'git', 'filesystem', 'full-scan']), default='auto', show_default=True)
@click.option('--llm-required/--llm-fallback', default=True, show_default=True)
@click.option('--save-plan/--no-save-plan', default=True, show_default=True)
def simple_plan(project, repo_path, base, head, target, source_file, max_targets, strategy, no_llm, source, llm_required, save_plan):
    """Beginner plan: scan, generate proposed tests with LLM by default, and save a reusable plan bundle."""
    repo_path = repo_path or _repo_path_for_project(project)
    if no_llm:
        strategy = 'template'
        llm_required = False
    console.print("[cyan]LLM: enabled by default | Writes: plan cache only | Pytest: not run[/cyan]")
    from softgnn_advisor.core.test_generation_agent import TestGenerationAgent
    from softgnn_advisor.core.plan_cache import save_plan_bundle
    agent = TestGenerationAgent(project, repo_path=repo_path)
    result = agent.generate(
        base=base,
        head=head,
        mode='plan',
        max_targets=max_targets,
        target_id=target,
        source_file=source_file,
        refresh_runtime=False,
        generation_strategy=strategy,
        llm_required=llm_required,
        change_source=source,
    )
    _render_generation(agent, result)
    if save_plan and result.plans:
        plan_path, latest_path, _ = save_plan_bundle(project, result, repo_path, base=base, head=head, change_source=source, llm_config=agent.llm_config)
        console.print(f"[bold green]Plan saved:[/bold green] {plan_path}")
        console.print(f"[bold green]Latest plan:[/bold green] {latest_path}")
        console.print(f"Next: [cyan]python softgnn.py apply --project {project}[/cyan]")


@cli.command('apply')
@click.option('--project', required=True, help='Project name created by setup/prepare')
@click.option('--repo-path', default=None, help='Optional override; otherwise read from project metadata')
@click.option('--base', default='main', show_default=True)
@click.option('--head', default='HEAD', show_default=True)
@click.option('--plan', 'plan_ref', default=None, help='Plan id or path; defaults to latest saved plan')
@click.option('--ignore-plan', is_flag=True, help='Generate fresh instead of using a saved plan')
@click.option('--force-stale-plan', is_flag=True, help='Apply saved plan even if source files changed')
@click.option('--target', default=None, help='Target id for fresh generation')
@click.option('--file', 'source_file', default=None, help='Source file for explicit target')
@click.option('--max-targets', default=3, show_default=True)
@click.option('--strategy', type=click.Choice(['template', 'llm', 'auto']), default='llm', show_default=True)
@click.option('--no-llm', is_flag=True, help='Do not call LLM when generating fresh because no saved plan exists')
@click.option('--llm-provider', default=None, help='LLM provider override, e.g. openai-compatible')
@click.option('--llm-model', default=None, help='LLM model override')
@click.option('--llm-base-url', default=None, help='LLM base URL override')
@click.option('--llm-api-key-env', default=None, help='Name of env var containing the LLM API key')
@click.option('--llm-required/--llm-fallback', default=False, show_default=True, help='Fail if LLM is unavailable instead of falling back to templates')
@click.option('--llm-temperature', default=0.1, show_default=True, help='LLM temperature')
@click.option('--llm-max-tokens', default=4096, show_default=True, help='LLM max output tokens')
@click.option('--source', type=click.Choice(['auto', 'git', 'filesystem', 'full-scan']), default='auto', show_default=True)
@click.option('--repair', default=2, show_default=True)
@click.option('--pytest', 'pytest_args', default=None, help='Override pytest args')
@click.option('--keep-failing-tests/--rollback-failing-tests', default=False, show_default=True)
@click.option('--partial-rollback/--batch-rollback', default=True, show_default=True, help='Keep passing generated tests and roll back only failing generated tests')
@click.option('--pytest-stream/--no-pytest-stream', default=True, show_default=True, help='Stream pytest output while verification runs')
def simple_apply(project, repo_path, base, head, plan_ref, ignore_plan, force_stale_plan, target, source_file, max_targets, strategy, no_llm, llm_provider, llm_model, llm_base_url, llm_api_key_env, llm_required, llm_temperature, llm_max_tokens, source, repair, pytest_args, keep_failing_tests, partial_rollback, pytest_stream):
    """Beginner apply: generate LLM tests by default, then patch, verify, map runtime, and confirm."""
    repo_path = repo_path or _repo_path_for_project(project)
    console.print("[cyan]Writes: tests only | Pytest: yes | Runtime map: yes[/cyan]")
    from softgnn_advisor.core.test_generation_agent import TestGenerationAgent
    from softgnn_advisor.core.plan_cache import bundle_to_generation_plans, load_plan_bundle, validate_plan_bundle
    if no_llm:
        strategy = 'template' if strategy == 'llm' else strategy
        llm_required = False
    else:
        llm_required = True if strategy == 'llm' else llm_required
    llm_api_key = os.getenv(llm_api_key_env) if llm_api_key_env else None
    agent = TestGenerationAgent(
        project,
        repo_path=repo_path,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
    )
    if not ignore_plan:
        try:
            bundle, loaded_path = load_plan_bundle(project, plan_ref)
            validation = validate_plan_bundle(bundle, repo_path)
            if validation.valid or force_stale_plan:
                if not validation.valid:
                    for warning in validation.warnings:
                        console.print(f"[yellow]{warning}[/yellow]")
                    console.print("[yellow]Applying stale plan because --force-stale-plan was set.[/yellow]")
                plans = bundle_to_generation_plans(bundle)
                console.print(f"[bold green]Loaded saved plan:[/bold green] {loaded_path}")
                console.print("[cyan]Skipping pre-scan and LLM generation.[/cyan]")
                result = agent.apply_saved_plans(
                    plans,
                    base=base,
                    head=head,
                    verify=True,
                    repair_iters=repair,
                    refresh_runtime=True,
                    runtime_mode='per-test',
                    confirm_pr_scan=True,
                    keep_failing_tests=keep_failing_tests,
                    pytest_args=pytest_args,
                    generation_strategy=strategy,
                    llm_required=llm_required,
                    llm_temperature=llm_temperature,
                    llm_max_tokens=llm_max_tokens,
                    change_source=source,
                    partial_rollback=partial_rollback,
                    pytest_stream=pytest_stream,
                )
                _render_generation(agent, result)
                return
            for warning in validation.warnings:
                console.print(f"[yellow]{warning}[/yellow]")
            console.print("[yellow]Saved plan is stale. Re-run plan or use --force-stale-plan. Generating fresh apply flow instead.[/yellow]")
        except FileNotFoundError:
            console.print("[yellow]No saved plan found. Generating fresh apply flow.[/yellow]")
    result = agent.generate(
        base=base,
        head=head,
        mode='patch',
        max_targets=max_targets,
        target_id=target,
        source_file=source_file,
        verify=True,
        repair_iters=repair,
        refresh_runtime=True,
        runtime_mode='per-test',
        confirm_pr_scan=True,
        keep_failing_tests=keep_failing_tests,
        pytest_args=pytest_args,
        generation_strategy=strategy,
        llm_required=llm_required,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        change_source=source,
        partial_rollback=partial_rollback,
        pytest_stream=pytest_stream,
    )
    _render_generation(agent, result)


@cli.command('map')
@click.option('--project', required=True, help='Project name created by setup/prepare')
@click.option('--repo-path', default=None, help='Optional override; otherwise read from project metadata')
@click.option('--pytest', 'pytest_args', default='tests', show_default=True)
@click.option('--mode', type=click.Choice(['auto', 'dynamic-context', 'per-test']), default='per-test', show_default=True)
@click.option('--persist/--no-persist', default=True, show_default=True)
@click.option('--max-tests', default=None, type=int)
def simple_map(project, repo_path, pytest_args, mode, persist, max_tests):
    """Beginner map: run pytest runtime coverage mapping."""
    repo_path = repo_path or _repo_path_for_project(project)
    from softgnn_advisor.infrastructure.pipelines.runtime_coverage_mapper import RuntimeCoverageMapper
    mapper = RuntimeCoverageMapper(project, repo_path=repo_path)
    result = mapper.map_runtime_coverage(pytest_args=pytest_args, mode=mode, persist=persist, max_tests=max_tests)
    for warning in result.warnings:
        console.print(f"[yellow]{warning}[/yellow]")
    console.print(f"[bold green]Runtime edges:[/bold green] {len(result.runtime_edges)} | Persisted: {result.persisted}")


if __name__ == '__main__':
    cli()

