import json
import time
import functools
import click
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Callable

class SemanticLogger:
    """JSONL audit trail of all operations."""

    def __init__(self, journal_file: Path):
        self.journal_file = Path(journal_file)
        # Ensure we use journal.jsonl for the new format
        if self.journal_file.name == "operations.log":
            self.journal_file = self.journal_file.with_name("journal.jsonl")
        self._enabled = self._check_enabled()

    def _check_enabled(self) -> bool:
        facet_dir = self.journal_file.parent
        return facet_dir.exists() and facet_dir.is_dir()

    def _log(self, operation: str, target: str, dry_run: bool = False, **kwargs) -> None:
        if not self._enabled and operation != "init":
            return

        self.journal_file.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "target": str(target),
            "dry_run": dry_run,
            **kwargs
        }

        with open(self.journal_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def log_operation(self, operation: str, target: str, status: str, duration: float, inputs: dict, result: Any = None, error: str = None):
        self._log(
            operation, 
            target, 
            status=status, 
            duration=f"{duration:.4f}s", 
            inputs=inputs, 
            result=result, 
            error=error
        )

    def log_create(self, entity_type: str, path: str, dry_run: bool = False) -> None:
        self._log("create", path, dry_run=dry_run, entity_type=entity_type)

    def log_modify(self, path: str, dry_run: bool = False) -> None:
        self._log("modify", path, dry_run=dry_run)

    def log_validate(self, path: str) -> None:
        self._log("validate", path, dry_run=False)

def semantic_command(name: Optional[str] = None):
    def decorator(f: Callable):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            op_name = name or f.__name__
            start_time = time.time()
            
            target = kwargs.get('path') or kwargs.get('target') or kwargs.get('folder_path') or kwargs.get('root') or "."
            target_path = Path(target).resolve()
            journal_path = target_path / ".facets" / "journal.jsonl"
            
            logger = SemanticLogger(journal_path)
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_operation(
                    operation=op_name,
                    target=str(target_path),
                    status="success",
                    duration=duration,
                    inputs={k: str(v) for k, v in kwargs.items() if k != 'ctx'},
                    result=str(result) if result is not None else None
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_operation(
                    operation=op_name,
                    target=str(target_path),
                    status="error",
                    duration=duration,
                    inputs={k: str(v) for k, v in kwargs.items() if k != 'ctx'},
                    error=str(e)
                )
                raise e
        return wrapper
    return decorator
