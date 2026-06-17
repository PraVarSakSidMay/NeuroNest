"""
Reflection API routes.

Provides endpoints for generating AI-powered emotional reflections,
listing past reflections, and deleting reflections.
"""

from fastapi import APIRouter, HTTPException, Query, Depends

from app.schemas.reflection import (
    ReflectionGenerateRequest,
    ReflectionListResponse,
    ReflectionResponse,
)
from app.services import reflection_service
from app.core.security import get_current_user

router = APIRouter(prefix="/api/reflections", tags=["Reflections"])


@router.post("/generate", response_model=ReflectionResponse, status_code=201)
async def generate_reflection(
    data: ReflectionGenerateRequest, 
    current_user_id: str = Depends(get_current_user)
) -> ReflectionResponse:
    """Generate a new AI-powered emotional reflection.

    Analyses journal entries within the specified date range and returns
    an empathetic summary with patterns, observations, insights, and suggestions.

    Args:
        data: The reflection generation request with range type and optional dates.
        current_user_id: The ID of the authenticated user.

    Returns:
        The generated reflection.

    Raises:
        HTTPException: 400 if no entries found or invalid date range.
        HTTPException: 500 if AI generation fails.
    """
    try:
        result = await reflection_service.generate_reflection(data, current_user_id)
        return ReflectionResponse(
            id=result["id"],
            summary=result.get("generated_summary", ""),
            emotional_patterns=result.get("emotional_patterns", []),
            positive_observations=result.get("positive_observations", []),
            gentle_insights=result.get("gentle_insights", []),
            growth_suggestions=result.get("growth_suggestions", []),
            selected_range=result.get("selected_range", ""),
            created_at=result["created_at"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate reflection: {str(exc)}"
        ) from exc


@router.get("/", response_model=ReflectionListResponse)
async def list_reflections(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Reflections per page"),
    current_user_id: str = Depends(get_current_user),
) -> ReflectionListResponse:
    """List past emotional reflections with pagination.

    Args:
        page: Page number (1-indexed).
        page_size: Number of reflections per page (1-100).
        current_user_id: The ID of the authenticated user.

    Returns:
        Paginated list of reflections.
    """
    try:
        reflections, total = await reflection_service.get_reflections(
            current_user_id, page=page, page_size=page_size
        )

        reflection_responses = [
            ReflectionResponse(
                id=r["id"],
                summary=r.get("generated_summary", ""),
                emotional_patterns=r.get("emotional_patterns", []),
                positive_observations=r.get("positive_observations", []),
                gentle_insights=r.get("gentle_insights", []),
                growth_suggestions=r.get("growth_suggestions", []),
                selected_range=r.get("selected_range", ""),
                created_at=r["created_at"],
            )
            for r in reflections
        ]

        return ReflectionListResponse(
            reflections=reflection_responses,
            total=total,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/{reflection_id}", status_code=200)
async def delete_reflection(
    reflection_id: str, 
    current_user_id: str = Depends(get_current_user)
) -> dict:
    """Delete an emotional reflection by its ID.

    Args:
        reflection_id: The MongoDB ObjectId string of the reflection.
        current_user_id: The ID of the authenticated user.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: 404 if the reflection is not found.
    """
    deleted = await reflection_service.delete_reflection(reflection_id, current_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reflection not found.")
    return {"message": "Reflection deleted successfully."}
