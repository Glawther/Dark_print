"""Application configuration - root APIRouter

Defines all FastAPI application endpoints.

Resources:
    1. https://fastapi.tiangolo.com/tutorial/bigger-applications

"""

from fastapi import APIRouter, Request

from app.controllers import ping
from app.controllers.v1 import llm, saas, video

root_api_router = APIRouter()
root_api_router.include_router(ping.router)

# v1
root_api_router.include_router(video.router)
root_api_router.include_router(llm.router)
root_api_router.include_router(saas.router)


@root_api_router.post("/saas/monetization/funnel", include_in_schema=False)
def monetization_funnel_root_alias(body: saas.MonetizationRequest, request: Request):
    return saas.get_monetization_funnel(body, request)


