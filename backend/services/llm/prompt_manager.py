"""
Prompt Manager for handling Jinja2 templates
"""

from pathlib import Path
from typing import Dict, Any, Optional, Callable
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class PromptManager:
    """Manages prompt templates using Jinja2"""

    _instances: Dict[Path, "PromptManager"] = {}

    def __new__(cls, templates_dir: Optional[Path] = None):
        """Singleton pattern"""
        if templates_dir not in cls._instances:
            cls._instances[templates_dir] = super().__new__(cls)
        return cls._instances[templates_dir]

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the PromptManager.

        Args:
            templates_dir: Path to the directory containing prompt templates.
                          Defaults to 'services/llm/prompts' relative to the project root.
        """
        if templates_dir is None:
            # Default to the prompts directory in services/llm
            templates_dir = Path(__file__).parent / "prompts"

        self.templates_dir = Path(templates_dir)

        # Create the directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,
        )

    def render(self, template_name: str, **kwargs: Any) -> str:
        """
        Render a template with the given variables.

        Args:
            template_name: Name of the template file (e.g., 'generate_scenarios.j2')
            **kwargs: Variables to pass to the template

        Returns:
            Rendered template as a string

        Raises:
            TemplateNotFound: If the template file doesn't exist
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template '{template_name}' not found in {self.templates_dir}")

    def render_string(self, template_string: str, **kwargs: Any) -> str:
        """
        Render a template from a string.

        Args:
            template_string: Template content as a string
            **kwargs: Variables to pass to the template

        Returns:
            Rendered template as a string
        """
        template = self.env.from_string(template_string)
        return template.render(**kwargs)

    def list_templates(self) -> list[str]:
        """
        List all available template files.

        Returns:
            List of template file names
        """
        if not self.templates_dir.exists():
            return []

        return [
            f.name
            for f in self.templates_dir.iterdir()
            if f.is_file() and f.suffix in [".j2", ".jinja2", ".txt"]
        ]

    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template exists.

        Args:
            template_name: Name of the template file

        Returns:
            True if the template exists, False otherwise
        """
        template_path = self.templates_dir / template_name
        return template_path.exists()

    def add_filter(self, name: str, func: Callable):
        """
        Add a custom filter to the Jinja2 environment.

        Args:
            name: Name of the filter
            func: Filter function
        """
        self.env.filters[name] = func

    def add_global(self, name: str, value: Any):
        """
        Add a global variable to the Jinja2 environment.

        Args:
            name: Name of the global variable
            value: Value of the global variable
        """
        self.env.globals[name] = value


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance"""
    return PromptManager()  # Unique instance by the singleton pattern
