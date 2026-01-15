from dataclasses import dataclass
from typing import Generator, Any
from typing import Sequence
from selenium.webdriver.remote.webdriver import WebDriver
import requests

from .errors import NodePreconditionFailure, NodeDependencyFailure
from .messages import StreamableMessage, StateDetails, OrchestratorStateMessage
from .returning_generators import ReturningGenerator
import logging

node_logger = logging.getLogger("evaluators")


@dataclass
class AgentExecutionArtifact:
    """Represents the execution result and streamed messages of an agent."""
    agent: str
    messages: list[StreamableMessage]
    value: Any


class NodeExecutionHistory:
    """
    Handles the execution history of nodes in a system.

    This class is used to manage and store the execution results of nodes, represented
    by `AgentExecutionArtifact` instances. It allows adding new results, retrieving
    them, and checking if a specific agent's execution is part of the history.
    """
    def __init__(self):
        self.results: list[AgentExecutionArtifact] = []
        self._mapper: dict[str, AgentExecutionArtifact] = {}

    def add_result(self, result: AgentExecutionArtifact):
        self.results.append(result)
        self._mapper[result.agent] = result

    def __contains__(self, item) -> bool:
        return item in self._mapper

    def __getitem__(self, item) -> AgentExecutionArtifact:
        return self._mapper[item]

    def get_results(self) -> list[AgentExecutionArtifact]:
        return self.results


@dataclass
class ContextData:
    """
    Represents the context data used in various operations.

    This class encapsulates essential details such as the target URL,
    an HTTP session, a browser driver instance, and execution history.
    It is particularly useful for accessing dependent values in the
    evaluation processing framework.
    """
    url: str
    session: requests.Session
    driver: WebDriver
    history: NodeExecutionHistory


class BaseExecutionNode:
    """
    Represents a base class for execution nodes within the evaluation processing framework.

    This class provides the foundation for creating and managing execution nodes, each
    of which may have specific dependencies and processing logic. It includes functionality
    for dependency verification, dynamic subclass registration, and execution workflow
    management. Subclasses must implement the `_evaluate_impl` method to define their
    specific evaluation logic.
    """
    __node_cls_mapper__ = {}

    # List of evaluator names or classes that this evaluator depends on
    __dependencies__ = ()  # type: Sequence[str | type["BaseExecutionNode"]]

    def _ensure_dependencies(self, context: ContextData):
        self.logger.debug(f"Checking dependencies for {self.node_name}:")
        for dep in self.__dependencies__:
            if isinstance(dep, type):
                if issubclass(dep, BaseExecutionNode):
                    dep_name = dep.node_name
                else:
                    raise NodeDependencyFailure(
                        "Evaluator dependencies must be strings or subclasses of BaseExecutionNode."
                    )

            elif isinstance(dep, str):
                dep_name = dep
            else:
                raise NodeDependencyFailure(
                    "Evaluator dependencies must be strings or subclasses of BaseExecutionNode."
                )
            if dep_name not in context.history:
                raise NodeDependencyFailure(
                    f"Dependency {dep_name} is required for {self.node_name}."
                )
            self.logger.debug(f"Dependency {dep_name} found for {self.node_name}.")
            result = context.history[dep_name]
            if isinstance(result, NodePreconditionFailure):
                raise NodeDependencyFailure(
                    f"Skipping {self.node_name} since {dep_name} run failed."
                )

    def __init__(self, logger=node_logger):
        self.logger = logger

    def __init_subclass__(cls, node_name: str | None = None):
        if node_name is None:
            return

        if not isinstance(node_name, str):
            raise ValueError("Evaluator name must be a string.")

        if node_name in cls.__node_cls_mapper__:
            raise ValueError(f"Evaluator name {node_name} is already registered.")

        cls.__node_cls_mapper__[node_name] = cls
        cls.node_name = node_name

    def evaluate_without_messages(self, *args, context: ContextData = None, **kwargs) -> Any:
        """
        Evaluates expressions without emitting intermediate messages by consuming the
        evaluation generator completely. This method ensures that all dependencies are
        handled prior to processing and directly retrieves the final value of evaluation.

        :param args: Positional arguments to pass to the evaluation function.
        :param context: The contextual data for execution, supplied as an
            instance of ContextData.
        :param kwargs: Keyword arguments to pass to the evaluation function.
        :return: The final value yielded by the evaluation generator.
        """
        self._ensure_dependencies(context)
        gen = self.evaluate(*args, context=context, **kwargs)
        for _ in gen:
            pass
        return gen.value

    def _evaluate_impl(
        self, *args, context: ContextData = None, **kwargs
    ) -> Generator[StreamableMessage, None, Any]:
        raise NotImplementedError

    def evaluate(
        self, *args, context: ContextData = None, **kwargs
    ) -> ReturningGenerator[StreamableMessage, None, Any]:
        """
        Evaluates the provided input data and streams the resulting messages.

        This method processes the input arguments and utilizes the context for executing
        the evaluation logic. The evaluation generates a stream of messages which are
        returned as a generator.

        :param args: Positional arguments required for the evaluation logic.
        :param context: Optional context data of type ``ContextData`` used for evaluation.
        :param kwargs: Keyword arguments required for the evaluation logic.
        :return: A generator of providing the streamed messages,
            and the final evaluation result.
        """
        self._ensure_dependencies(context)
        return ReturningGenerator(self._evaluate_impl(*args, context=context, **kwargs))

    @classmethod
    def get_node_cls(cls, node_name: str):
        return cls.__node_cls_mapper__.get(node_name)

    @classmethod
    def get_node_instance(cls, node_name: str, *args, **kwargs):
        return cls.get_node_cls(node_name)(*args, **kwargs)

    @property
    def full_name(self):
        if hasattr(self, "node_name"):
            return self.node_name.replace("_", " ").upper()
        raise ValueError("A default full name requires node_name attribute.")


class Orchestrator:
    """
    Coordinates the orchestration and execution of evaluators based on provided data.

    The `Orchestrator` class is responsible for managing the evaluation processes executed
    by a set of evaluators. It ensures that each evaluator is invoked properly, tracks execution
    history, supports URL normalization, and handles any errors or exceptions raised during
    the evaluation process. This class uses a context-based strategy to manage shared resources
    like HTTP sessions and web drivers during the evaluation.
    """
    def __init__(self, nodes: list[BaseExecutionNode]):
        """
        Initializes the instance with a list of evaluation nodes.

        :param nodes: List of evaluation nodes used for execution.
        :type nodes: list[BaseExecutionNode]
        """
        self.nodes = nodes

    def _ensure_protocol(self, url: str):
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            return f"https://{url}"
        return url

    def evaluate(
        self, url: str, session: requests.Session, driver: WebDriver, *args, **kwargs
    ) -> Generator[StreamableMessage, None, None]:
        context = ContextData(
            url=self._ensure_protocol(url),
            session=session,
            driver=driver,
            history=NodeExecutionHistory(),
        )
        for node in self.nodes:
            # Iterates evaluators; yields messages; handles exceptions
            yield OrchestratorStateMessage(
                message=f"Starting evaluation of {node.node_name}...",
                details=StateDetails(agent_id=node.node_name, agent_name=node.full_name),
            )
            messages = []
            try:
                gen = node.evaluate(*args, context=context, **kwargs)
                for message in gen:
                    if message.agent_id is None:
                        message.agent_id = node.node_name
                        message.agent_name = node.full_name
                    messages.append(message)
                    yield message
                context.history.add_result(
                    AgentExecutionArtifact(node.node_name, messages, gen.value)
                )
            except NodePreconditionFailure as err:
                yield StreamableMessage(
                    agent_id=node.node_name, agent_name=node.full_name,
                    level="error", message=err.message
                )
                context.history.add_result(
                    AgentExecutionArtifact(node.node_name, messages, err)
                )
            except Exception as e:
                node_logger.exception(e)
                yield StreamableMessage(
                    agent_id="orchestrator",
                    source="agent",
                    level="error",
                    message=f"{node.node_name} failed to run due to an unexpected error. Please contact support..",
                )
        yield OrchestratorStateMessage(message="Evaluation complete.", details=StateDetails(is_end_state=True))
