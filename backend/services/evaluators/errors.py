class NodePreconditionFailure(BaseException):
    """
    Raised when a process fails due to unrecoverable input issues
    that cannot be circumvented, making it pointless to proceed with the execution.

    Note: This is not a failure of the evaluation process itself, but rather a failure
    that prevents the evaluation from continuing due to invalid or inconsistent input.
    """

    @property
    def message(self) -> str:
        return str(self)


class NodeAssertionFailure(NodePreconditionFailure):
    """
    Represents a specific type of evaluation failure where an assertion has failed.

    This class is a subclass of `EvaluationFailure` and is designed to encapsulate
    details related to assertion failures that occur during evaluation. It retains
    additional context or parameters, if necessary, to aid in debugging or logging
    the assertion information.

    :ivar expected: The expected value in the assertion failure.
    :ivar actual: The actual value encountered that caused the failure.
    :ivar message: An optional message providing details about the failure.
    """


class NodeDependencyFailure(NodePreconditionFailure):
    """
    Represents a specific type of evaluation failure caused by dependencies.

    This class is a specialized subclass of `EvaluationFailure`. It is used
    to indicate that an evaluation process failed due to an issue with one or
    more dependencies required for the evaluation. The class provides details
    about these dependencies to assist in diagnosing and addressing the
    underlying issue.

    :ivar dependency_name: The name of the dependency that caused the failure.
    :ivar dependency_version: The version of the dependency causing the
        failure, if applicable.
    :ivar message: A descriptive message detailing the failure and the
        problematic dependency.
    """
