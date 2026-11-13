from sap_cloud_sdk.aicore import set_aicore_config

set_aicore_config()

import logging
import os
import sys

# Ensure app/ is on sys.path so bare intra-package imports work whether this
# module is executed as a script (python main.py) or as a module (python -m app.main).
_app_dir = os.path.dirname(os.path.abspath(__file__))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from sap_cloud_sdk import bootstrap
from starlette.middleware.base import BaseHTTPMiddleware

from agent_executor import AgentExecutor
from mcp_providers.agw import set_user_token, reset_user_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))


@click.command()
@click.option("--host", default=HOST)
@click.option("--port", default=PORT)
def main(host: str, port: int):
    skill = AgentSkill(
        id="ec-payroll-audit-agent",
        name="ec-payroll-audit-agent",
        description="Generates a consolidated EC Payroll infotypes changes audit report for the current month, categorized by P2P EC-to-ECP, Inbound, and Manual updates, with before/after values for the top 100 highest-salaried employees.",
        tags=["ec", "payroll", "audit", "infotypes", "hr"],
        examples=["Generate the EC Payroll audit report for this month", "Show me all payroll infotype changes for the current month categorized by source"],
    )
    agent_card = AgentCard(
        name="ec-payroll-audit-agent",
        description="Generates a consolidated EC Payroll infotypes changes audit report for the current month, categorized by P2P EC-to-ECP, Inbound, and Manual updates, with before/after values for the top 100 highest-salaried employees.",
        url=os.environ.get("AGENT_PUBLIC_URL", f"http://{host}:{port}/"),
        version="1.0.0",
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True, push_notifications=False),
        skills=[skill],
    )
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=AgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )
    app = server.build()

    class JWTContextMiddleware(BaseHTTPMiddleware):
        """Extracts JWT token from Authorization header and sets it in context."""

        async def dispatch(self, request, call_next):
            auth_header = request.headers.get("authorization", "")
            token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
            token_ctx = set_user_token(token)
            try:
                return await call_next(request)
            finally:
                reset_user_token(token_ctx)

    app.add_middleware(JWTContextMiddleware)

    bootstrap(app)

    logger.info(f"Starting A2A server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter  # type: ignore[call-arg]
