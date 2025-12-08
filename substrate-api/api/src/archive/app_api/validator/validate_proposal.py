"""
Validator API endpoint for mandatory proposal validation.

Implements Governance Sacred Principle #3: Agent validation is mandatory for all proposals.
"""

from fastapi import APIRouter, HTTPException
from uuid import UUID
from typing import List, Dict, Any

from app.agents.pipeline.validator_agent import P1ValidatorAgent, ProposalValidationRequest, ProposalOperation

router = APIRouter()
validator_agent = P1ValidatorAgent()


@router.post("/validate-proposal")
async def validate_proposal(request_data: Dict[str, Any]):
    """
    Validate a proposal before governance review.
    
    Required for all proposals per Governance Sacred Principle #3.
    """
    try:
        # Parse request
        validation_request = ProposalValidationRequest(
            basket_id=UUID(request_data['basket_id']),
            workspace_id=UUID(request_data['workspace_id']),
            ops=[
                ProposalOperation(type=op['type'], data=op.get('data', {}))
                for op in request_data['operations']
            ],
            origin=request_data.get('origin', 'human'),
            provenance=[UUID(p) for p in request_data.get('provenance', [])]
        )
        
        # Validate with P1 Validator Agent
        validation_report = await validator_agent.validate_proposal(validation_request)
        
        return validation_report.dict()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/agent-info")
async def get_validator_info():
    """Get validator agent information."""
    return validator_agent.get_agent_info()