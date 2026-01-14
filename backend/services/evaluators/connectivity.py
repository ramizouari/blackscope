from typing import Generator, Any, Literal

import requests

from .base import (
    BaseExecutionNode,
    StreamableMessage,
    ContextData,
    NodePreconditionFailure,
)

PLAUSIBLE_CONTENT_TYPES = ["text/html", "application/xhtml+xml"]


class AccessCheckNode(BaseExecutionNode, node_name="access_check"):

    def _inspect_content_type(self, response: requests.Response, method: Literal["GET", "OPTIONS"]):
        if "Content-Type" not in response.headers:
            yield StreamableMessage(
                message=f"Content-Type header missing in {method} response.", level="bug"
            )
        else:
            for content_type in PLAUSIBLE_CONTENT_TYPES:
                if response.headers["Content-Type"].startswith(content_type):
                    break
            else:
                yield StreamableMessage(
                    message=f"Invalid Content-Type header in {method} response.", level="error"
                )

    def _evaluate_impl(
        self, *args, context: ContextData = None, **kwargs
    ) -> Generator[StreamableMessage, None, Any]:
        shake = context.session.options(context.url)
        if not shake.ok:
            yield StreamableMessage(
                message="Failed to pre-fetch the website via OPTIONS.", level="error"
            )

        yield from self._inspect_content_type(shake, "OPTIONS")
        response = context.session.get(context.url)
        if not response.ok:
            raise NodePreconditionFailure("Failed to connect to the website")
        else:
            yield from self._inspect_content_type(response, "GET")
            if response.headers["Content-Type"] != shake.headers["Content-Type"]:
                yield StreamableMessage(
                    message="Content-Type header mismatch between pre-fetch and fetch",
                    level="warning",
                )
            yield StreamableMessage(
                message="Successfully connected to the website.", level="info"
            )
        return response


class DriverAccessNode(BaseExecutionNode, node_name="driver_access"):
    __dependencies__ = (AccessCheckNode,)

    def _evaluate_impl(
        self, *args, context: ContextData = None, **kwargs
    ) -> Generator[StreamableMessage, None, Any]:
        context.driver.get(context.url)
        yield StreamableMessage(
            message="Successfully loaded the website into AI-powered browser.", level="info"
        )
        return None
