"""
Loyalty AI Agent - HTTP API
FastAPI server exposing agent endpoints for customer analysis and metrics
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import sys
import os
from pathlib import Path
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.loyalty_agent import LoyaltyAgent
    from src.memory import MemoryManager
    from src.logger import get_logger
    from src.validators import CustomerNotFoundError
except ImportError:
    print("Error: Could not import required modules. Make sure all Phase 1 components are complete.")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Loyalty AI Agent API",
    description="AI-powered customer loyalty optimization with real-time analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust for production security)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
logger = get_logger(__name__)

# Get absolute paths for data files (works in serverless environment)
base_dir = Path(__file__).parent.parent
customers_file = str(base_dir / "data" / "customers.json")
transactions_file = str(base_dir / "data" / "transactions.json")

# Initialize agent with error handling for serverless environment
try:
    agent = LoyaltyAgent(customers_file=customers_file, transactions_file=transactions_file)
    logger.info(f"Agent initialized successfully with {len(agent.customers)} customers")
except Exception as e:
    logger.error(f"Error initializing agent: {e}")
    # Create minimal agent for health checks
    agent = None

try:
    memory = MemoryManager()
except Exception as e:
    logger.error(f"Error initializing memory: {e}")
    memory = None

# Track API metrics
api_start_time = datetime.now()
request_count = 0
error_count = 0


# ==================== Request/Response Models ====================

class AnalyzeRequest(BaseModel):
    """Request model for customer analysis"""
    customer_id: str = Field(..., description="Unique customer identifier")
    include_history: bool = Field(default=False, description="Include past recommendations in response")
    
    @field_validator('customer_id')
    @classmethod
    def validate_customer_id(cls, v):
        if not v or not v.strip():
            raise ValueError("customer_id cannot be empty")
        return v.strip()


class AnalyzeResponse(BaseModel):
    """Response model for customer analysis"""
    customer_id: str
    recommended_reward: str
    predicted_retention: float
    segment: str
    rfm_score: float
    churn_risk: str
    timestamp: str
    history: Optional[List[Dict[str, Any]]] = None


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    uptime_seconds: float
    uptime_human: str
    total_requests: int
    total_errors: int
    error_rate: float
    customers_loaded: int
    transactions_loaded: int
    timestamp: str
    environment: str


class MetricsResponse(BaseModel):
    """Response model for agent metrics"""
    total_customers: int
    avg_retention_rate: float
    avg_churn_risk: float
    segment_distribution: Dict[str, int]
    loyalty_tier_distribution: Dict[str, int]
    reward_recommendations_summary: Dict[str, int]
    timestamp: str


class RegisterRequest(BaseModel):
    """Request model for agent registration"""
    supervisor_url: str = Field(..., description="URL of the supervisor registry")
    agent_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional agent metadata")


class RegisterResponse(BaseModel):
    """Response model for registration"""
    status: str
    agent_id: str
    registered_at: str
    message: str


# ==================== Helper Functions ====================

def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"


def get_agent_metadata() -> Dict[str, Any]:
    """Get agent metadata for registration"""
    return {
        "agent_id": "loyalty_agent_001",
        "agent_name": "Customer Loyalty AI Agent",
        "agent_type": "loyalty_optimization",
        "version": "1.0.0",
        "capabilities": [
            "customer_segmentation",
            "churn_prediction",
            "reward_optimization",
            "rfm_analysis"
        ],
        "endpoints": {
            "analyze": "/analyze",
            "health": "/health",
            "metrics": "/metrics"
        },
        "status": "active",
        "registered_at": datetime.now().isoformat()
    }


# ==================== API Endpoints ====================

@app.get("/", summary="Root endpoint")
async def root():
    """Welcome endpoint with API information"""
    return {
        "message": "Welcome to Loyalty AI Agent API",
        "version": "1.0.0",
        "status": "online",
        "deployed": True,
        "environment": os.getenv("ENVIRONMENT", "production"),
        "documentation": "/docs",
        "endpoints": {
            "analyze": "POST /analyze",
            "health": "GET /health",
            "metrics": "GET /metrics",
            "register": "POST /register"
        }
    }


@app.post("/analyze", response_model=AnalyzeResponse, summary="Analyze customer and get recommendations")
async def analyze_customer(request: AnalyzeRequest):
    """
    Analyze a customer and return personalized loyalty recommendations
    
    - **customer_id**: Unique identifier for the customer
    - **include_history**: Whether to include past recommendation history
    
    Returns customer segment, churn risk, RFM score, and recommended reward.
    """
    global request_count, error_count
    request_count += 1
    
    if not agent:
        error_count += 1
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent is not initialized. Service temporarily unavailable."
        )
    
    try:
        logger.info(f"Analyzing customer: {request.customer_id}")
        
        # Get recommendation from agent
        result = agent.optimize_loyalty(request.customer_id)
        
        # Store in memory
        memory.store_short_term(request.customer_id, result)
        memory.store_long_term(request.customer_id, result)
        
        # Build response
        response_data = {
            "customer_id": result["customer_id"],
            "recommended_reward": result["recommended_reward"],
            "predicted_retention": result["predicted_retention"],
            "segment": result["segment"],
            "rfm_score": result["rfm_score"],
            "churn_risk": result["churn_risk"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Include history if requested
        if request.include_history:
            history = memory.get_long_term_history(request.customer_id)
            response_data["history"] = history
        
        logger.info(f"Successfully analyzed customer {request.customer_id}")
        return AnalyzeResponse(**response_data)
        
    except CustomerNotFoundError as e:
        error_count += 1
        logger.warning(f"Customer not found: {request.customer_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {request.customer_id} not found"
        )
    except Exception as e:
        error_count += 1
        logger.error(f"Error analyzing customer {request.customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse, summary="Health check endpoint")
async def health_check():
    """
    Check the health and status of the agent
    
    Returns uptime, request statistics, and data load status.
    """
    try:
        uptime_seconds = (datetime.now() - api_start_time).total_seconds()
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0.0
        
        customers_count = len(agent.customers) if agent else 0
        transactions_count = len(agent.transactions) if agent else 0
        
        return HealthResponse(
            status="healthy" if agent else "degraded",
            uptime_seconds=uptime_seconds,
            uptime_human=format_uptime(uptime_seconds),
            total_requests=request_count,
            total_errors=error_count,
            error_rate=round(error_rate, 2),
            customers_loaded=customers_count,
            transactions_loaded=transactions_count,
            timestamp=datetime.now().isoformat(),
            environment=os.getenv("ENVIRONMENT", "production")
        )
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@app.get("/metrics", response_model=MetricsResponse, summary="Get agent performance metrics")
async def get_metrics():
    """
    Get comprehensive metrics about the agent's performance and customer base
    
    Returns customer statistics, segmentation data, and retention metrics.
    """
    try:
        logger.info("Calculating agent metrics")
        
        # Calculate metrics
        total_customers = len(agent.customers)
        
        # Segment distribution
        segment_dist = {}
        loyalty_tier_dist = {}
        total_retention = 0
        total_churn_risk = 0
        
        for customer in agent.customers:
            # Count segments
            segment = customer.get('segment', 'Unknown')
            segment_dist[segment] = segment_dist.get(segment, 0) + 1
            
            # Count loyalty tiers
            tier = customer.get('loyalty_tier', 'Unknown')
            loyalty_tier_dist[tier] = loyalty_tier_dist.get(tier, 0) + 1
        
        # Get retention metrics from recent recommendations
        recent_recommendations = memory.get_all_short_term()
        reward_summary = {}
        
        if recent_recommendations:
            for rec in recent_recommendations.values():
                if isinstance(rec, dict):
                    total_retention += rec.get('predicted_retention', 0)
                    
                    # Count churn risks
                    churn_risk = rec.get('churn_risk', 'Unknown')
                    if churn_risk == 'High':
                        total_churn_risk += 1
                    elif churn_risk == 'Medium':
                        total_churn_risk += 0.5
                    
                    # Count reward types
                    reward = rec.get('recommended_reward', 'Unknown')
                    reward_summary[reward] = reward_summary.get(reward, 0) + 1
        
        avg_retention = (total_retention / len(recent_recommendations)) if recent_recommendations else 0.0
        avg_churn_risk = (total_churn_risk / len(recent_recommendations)) if recent_recommendations else 0.0
        
        return MetricsResponse(
            total_customers=total_customers,
            avg_retention_rate=round(avg_retention, 4),
            avg_churn_risk=round(avg_churn_risk, 4),
            segment_distribution=segment_dist,
            loyalty_tier_distribution=loyalty_tier_dist,
            reward_recommendations_summary=reward_summary,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate metrics: {str(e)}"
        )


@app.post("/register", response_model=RegisterResponse, summary="Register agent with supervisor")
async def register_with_supervisor(request: RegisterRequest):
    """
    Register this agent with a supervisor registry
    
    - **supervisor_url**: URL of the supervisor's registry endpoint
    - **agent_metadata**: Optional additional metadata to include
    
    This enables the Supervisor-Worker architecture pattern.
    """
    try:
        logger.info(f"Registering with supervisor at {request.supervisor_url}")
        
        # Get agent metadata
        metadata = get_agent_metadata()
        
        # Merge with any additional metadata
        if request.agent_metadata:
            metadata.update(request.agent_metadata)
        
        # In a real implementation, you would make an HTTP POST to the supervisor_url
        # For now, we'll simulate successful registration
        # TODO: Implement actual HTTP call to supervisor registry
        
        # import requests
        # response = requests.post(
        #     f"{request.supervisor_url}/register",
        #     json=metadata,
        #     timeout=10
        # )
        # if response.status_code != 200:
        #     raise HTTPException(status_code=response.status_code, detail="Registration failed")
        
        agent_id = metadata["agent_id"]
        registered_at = metadata["registered_at"]
        
        logger.info(f"Successfully registered as {agent_id}")
        
        return RegisterResponse(
            status="registered",
            agent_id=agent_id,
            registered_at=registered_at,
            message=f"Agent successfully registered with supervisor at {request.supervisor_url}"
        )
        
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


# ==================== Exception Handlers ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Actions to perform on API startup"""
    logger.info("=" * 60)
    logger.info("Loyalty AI Agent API Starting...")
    logger.info(f"Customers loaded: {len(agent.customers)}")
    logger.info(f"Transactions loaded: {len(agent.transactions)}")
    logger.info(f"API Documentation: http://localhost:8000/docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on API shutdown"""
    logger.info("Shutting down Loyalty AI Agent API...")
    # Persist any remaining short-term memory
    memory.persist_all()
    logger.info("Shutdown complete")


# ==================== Main Entry Point ====================

# For Vercel serverless deployment
handler = app

if __name__ == "__main__":
    """Run the API server locally"""
    print("\n" + "=" * 60)
    print("Starting Loyalty AI Agent API Server")
    print("=" * 60)
    print("\nAPI will be available at:")
    print("  - Base URL: http://localhost:8000")
    print("  - Docs: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        "agent_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
