"""
Registry Client for Supervisor-Worker Architecture
Handles agent registration, heartbeat, and inter-agent communication
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from threading import Thread, Event
import time

try:
    from src.logger import get_logger
except ImportError:
    from logger import get_logger


class RegistryClient:
    """
    Client for registering and maintaining connection with a Supervisor registry.
    Implements the Worker side of the Supervisor-Worker pattern.
    """
    
    def __init__(self,
                 agent_id: str = "loyalty_agent_001",
                 agent_name: str = "Customer Loyalty AI Agent",
                 agent_type: str = "loyalty_optimization",
                 version: str = "1.0.0",
                 api_host: str = "localhost",
                 api_port: int = 8000):
        """
        Initialize Registry Client
        
        Args:
            agent_id: Unique identifier for this agent
            agent_name: Human-readable name
            agent_type: Type/category of agent
            version: Agent version
            api_host: Host where this agent's API is running
            api_port: Port where this agent's API is running
        """
        self.logger = get_logger(__name__)
        
        # Agent metadata
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.version = version
        self.api_host = api_host
        self.api_port = api_port
        self.api_url = f"http://{api_host}:{api_port}"
        
        # Registry connection
        self.supervisor_url: Optional[str] = None
        self.is_registered = False
        self.registration_time: Optional[datetime] = None
        
        # Heartbeat mechanism
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_thread: Optional[Thread] = None
        self.heartbeat_stop_event = Event()
        
        self.logger.info(f"Registry Client initialized for agent: {agent_id}")
    
    # ==================== Agent Metadata ====================
    
    def get_metadata(self, include_status: bool = True) -> Dict[str, Any]:
        """
        Get agent metadata for registration
        
        Args:
            include_status: Whether to include dynamic status information
            
        Returns:
            Dictionary with agent metadata
        """
        metadata = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "version": self.version,
            "api_url": self.api_url,
            "capabilities": [
                "customer_segmentation",
                "churn_prediction",
                "reward_optimization",
                "rfm_analysis",
                "loyalty_scoring"
            ],
            "endpoints": {
                "analyze": f"{self.api_url}/analyze",
                "health": f"{self.api_url}/health",
                "metrics": f"{self.api_url}/metrics"
            },
            "communication_protocol": "HTTP/REST",
            "data_format": "JSON"
        }
        
        if include_status:
            metadata["status"] = "active" if self.is_registered else "inactive"
            metadata["registered_at"] = self.registration_time.isoformat() if self.registration_time else None
            metadata["last_heartbeat"] = datetime.now().isoformat()
        
        return metadata
    
    # ==================== Registration ====================
    
    def register(self, supervisor_url: str, timeout: int = 10) -> bool:
        """
        Register this agent with a supervisor registry
        
        Args:
            supervisor_url: URL of the supervisor's registry endpoint
            timeout: Request timeout in seconds
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            self.logger.info(f"Attempting to register with supervisor at {supervisor_url}")
            
            # Prepare registration payload
            payload = self.get_metadata(include_status=False)
            payload["registration_time"] = datetime.now().isoformat()
            
            # Make registration request
            response = requests.post(
                f"{supervisor_url}/register",
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Check response
            if response.status_code == 200 or response.status_code == 201:
                self.supervisor_url = supervisor_url
                self.is_registered = True
                self.registration_time = datetime.now()
                
                self.logger.info(f"Successfully registered with supervisor: {self.agent_id}")
                
                # Start heartbeat mechanism
                self.start_heartbeat()
                
                return True
            else:
                self.logger.error(f"Registration failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Registration timeout after {timeout}s")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Could not connect to supervisor at {supervisor_url}")
            return False
        except Exception as e:
            self.logger.error(f"Registration error: {str(e)}")
            return False
    
    def unregister(self, timeout: int = 10) -> bool:
        """
        Unregister this agent from the supervisor
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            True if unregistration successful, False otherwise
        """
        if not self.is_registered or not self.supervisor_url:
            self.logger.warning("Agent is not registered")
            return False
        
        try:
            self.logger.info(f"Unregistering from supervisor: {self.agent_id}")
            
            # Stop heartbeat first
            self.stop_heartbeat()
            
            # Make unregistration request
            response = requests.delete(
                f"{self.supervisor_url}/unregister/{self.agent_id}",
                timeout=timeout
            )
            
            if response.status_code == 200:
                self.is_registered = False
                self.supervisor_url = None
                self.registration_time = None
                
                self.logger.info("Successfully unregistered from supervisor")
                return True
            else:
                self.logger.error(f"Unregistration failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Unregistration error: {str(e)}")
            return False
    
    # ==================== Heartbeat Mechanism ====================
    
    def send_heartbeat(self) -> bool:
        """
        Send a heartbeat to the supervisor to indicate this agent is alive
        
        Returns:
            True if heartbeat successful, False otherwise
        """
        if not self.is_registered or not self.supervisor_url:
            return False
        
        try:
            payload = {
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            }
            
            response = requests.post(
                f"{self.supervisor_url}/heartbeat",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.debug(f"Heartbeat sent successfully")
                return True
            else:
                self.logger.warning(f"Heartbeat failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Heartbeat error: {str(e)}")
            return False
    
    def _heartbeat_loop(self):
        """Internal method for heartbeat thread loop"""
        self.logger.info(f"Heartbeat thread started (interval: {self.heartbeat_interval}s)")
        
        while not self.heartbeat_stop_event.is_set():
            self.send_heartbeat()
            
            # Wait for interval or stop event
            self.heartbeat_stop_event.wait(self.heartbeat_interval)
        
        self.logger.info("Heartbeat thread stopped")
    
    def start_heartbeat(self):
        """Start sending periodic heartbeats to supervisor"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.logger.warning("Heartbeat already running")
            return
        
        self.heartbeat_stop_event.clear()
        self.heartbeat_thread = Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        self.logger.info("Heartbeat mechanism started")
    
    def stop_heartbeat(self):
        """Stop sending heartbeats"""
        if not self.heartbeat_thread or not self.heartbeat_thread.is_alive():
            return
        
        self.heartbeat_stop_event.set()
        self.heartbeat_thread.join(timeout=5)
        
        self.logger.info("Heartbeat mechanism stopped")
    
    # ==================== Inter-Agent Communication ====================
    
    def discover_agents(self, agent_type: Optional[str] = None, timeout: int = 10) -> List[Dict[str, Any]]:
        """
        Discover other agents registered with the supervisor
        
        Args:
            agent_type: Optional filter by agent type
            timeout: Request timeout in seconds
            
        Returns:
            List of agent metadata dictionaries
        """
        if not self.supervisor_url:
            self.logger.warning("Not connected to supervisor")
            return []
        
        try:
            url = f"{self.supervisor_url}/agents"
            if agent_type:
                url += f"?type={agent_type}"
            
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                self.logger.info(f"Discovered {len(agents)} agents")
                return agents
            else:
                self.logger.error(f"Agent discovery failed: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Agent discovery error: {str(e)}")
            return []
    
    def call_agent(self, agent_id: str, endpoint: str, data: Dict[str, Any], 
                   method: str = "POST", timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Call another agent's endpoint
        
        Args:
            agent_id: ID of the agent to call
            endpoint: Endpoint path (e.g., "/analyze")
            data: Data to send
            method: HTTP method (POST, GET, etc.)
            timeout: Request timeout in seconds
            
        Returns:
            Response data or None if failed
        """
        try:
            # Get agent info from supervisor
            agents = self.discover_agents()
            target_agent = None
            
            for agent in agents:
                if agent.get("agent_id") == agent_id:
                    target_agent = agent
                    break
            
            if not target_agent:
                self.logger.error(f"Agent {agent_id} not found")
                return None
            
            # Construct URL
            base_url = target_agent.get("api_url", "")
            url = f"{base_url}{endpoint}"
            
            self.logger.info(f"Calling agent {agent_id} at {url}")
            
            # Make request
            if method.upper() == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            elif method.upper() == "GET":
                response = requests.get(url, params=data, timeout=timeout)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code == 200:
                self.logger.info(f"Successfully called agent {agent_id}")
                return response.json()
            else:
                self.logger.error(f"Agent call failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling agent {agent_id}: {str(e)}")
            return None
    
    # ==================== Status & Monitoring ====================
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of this registry client
        
        Returns:
            Dictionary with status information
        """
        uptime = None
        if self.registration_time:
            uptime = (datetime.now() - self.registration_time).total_seconds()
        
        return {
            "agent_id": self.agent_id,
            "is_registered": self.is_registered,
            "supervisor_url": self.supervisor_url,
            "registration_time": self.registration_time.isoformat() if self.registration_time else None,
            "uptime_seconds": uptime,
            "heartbeat_active": self.heartbeat_thread is not None and self.heartbeat_thread.is_alive(),
            "heartbeat_interval": self.heartbeat_interval,
            "api_url": self.api_url
        }
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop_heartbeat()


# ==================== Example Usage ====================

if __name__ == "__main__":
    """Test the Registry Client"""
    print("\n" + "=" * 60)
    print("Registry Client Test")
    print("=" * 60 + "\n")
    
    # Initialize client
    client = RegistryClient(
        agent_id="loyalty_agent_test",
        agent_name="Test Loyalty Agent",
        api_host="localhost",
        api_port=8000
    )
    
    # Display metadata
    print("Agent Metadata:")
    print("-" * 60)
    metadata = client.get_metadata()
    print(json.dumps(metadata, indent=2))
    
    # Test registration (will fail if no supervisor running)
    print("\n\nTesting Registration:")
    print("-" * 60)
    supervisor_url = "http://localhost:9000"  # Example supervisor URL
    
    print(f"Attempting to register with {supervisor_url}...")
    success = client.register(supervisor_url)
    
    if success:
        print("✓ Registration successful")
        
        # Wait a bit to test heartbeat
        print("\nWaiting 5 seconds to test heartbeat...")
        time.sleep(5)
        
        # Get status
        print("\nAgent Status:")
        status = client.get_status()
        print(json.dumps(status, indent=2))
        
        # Unregister
        print("\nUnregistering...")
        client.unregister()
        print("✓ Unregistered")
    else:
        print("✗ Registration failed (supervisor may not be running)")
        print("  This is expected if you don't have a supervisor server")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60 + "\n")
