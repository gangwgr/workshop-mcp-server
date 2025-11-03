"""
Polarion QA Assistant Tools

Tools for searching, retrieving, and summarizing test cases from Polarion ALM.
Supports both SOAP/WIQL and REST API queries.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """Represents a Polarion test case."""
    id: str
    title: str
    status: str
    description: str
    component: Optional[str] = None
    version: Optional[str] = None
    severity: Optional[str] = None
    automation_level: Optional[str] = None

class PolarionClient:
    """Client for interacting with Polarion ALM API."""
    
    def __init__(self):
        self.base_url = os.getenv('POLARION_BASE_URL', 'https://polarion-server.example.com')
        self.username = os.getenv('POLARION_USERNAME')
        self.password = os.getenv('POLARION_PASSWORD')
        self.token = os.getenv('POLARION_TOKEN')
        self.project_id = os.getenv('POLARION_PROJECT_ID', 'openshift')
        
        # Set up authentication
        if self.token:
            self.auth_headers = {'Authorization': f'Bearer {self.token}'}
        elif self.username and self.password:
            self.auth = HTTPBasicAuth(self.username, self.password)
            self.auth_headers = {}
        else:
            logger.warning("No Polarion credentials found. Set POLARION_USERNAME/PASSWORD or POLARION_TOKEN")
            self.auth = None
            self.auth_headers = {}
    
    def _make_rest_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a REST API request to Polarion."""
        url = f"{self.base_url}/polarion/rest/v2/{endpoint}"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        headers.update(self.auth_headers)
        
        try:
            if self.auth:
                response = requests.get(url, params=params, headers=headers, auth=self.auth, timeout=30)
            else:
                response = requests.get(url, params=params, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Polarion API request failed: {e}")
            return {'error': str(e)}
    
    def _make_soap_request(self, query: str, fields: List[str] = None) -> Dict[str, Any]:
        """Make a SOAP API request to Polarion (TrackerWebService)."""
        if fields is None:
            fields = ['id', 'title', 'status', 'description']
        
        soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:ns1="http://ws.polarion.com/TrackerWebService-impl">
    <soapenv:Body>
        <ns1:queryWorkItems>
            <query>{query}</query>
            <fields>{','.join(fields)}</fields>
        </ns1:queryWorkItems>
    </soapenv:Body>
</soapenv:Envelope>"""
        
        url = f"{self.base_url}/polarion/ws/services/TrackerWebService"
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'queryWorkItems'
        }
        
        try:
            if self.auth:
                response = requests.post(url, data=soap_body, headers=headers, auth=self.auth, timeout=30)
            else:
                response = requests.post(url, data=soap_body, headers=headers, timeout=30)
            
            response.raise_for_status()
            return self._parse_soap_response(response.text)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Polarion SOAP request failed: {e}")
            return {'error': str(e)}
    
    def _parse_soap_response(self, soap_response: str) -> Dict[str, Any]:
        """Parse SOAP response XML."""
        try:
            root = ET.fromstring(soap_response)
            # This is a simplified parser - adjust based on actual Polarion SOAP response structure
            work_items = []
            
            # Look for work items in the response
            for item in root.findall(".//workItem"):
                work_item = {}
                for field in item:
                    work_item[field.tag] = field.text
                work_items.append(work_item)
            
            return {'work_items': work_items}
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse SOAP response: {e}")
            return {'error': f'Failed to parse SOAP response: {e}'}

# Initialize client
polarion_client = PolarionClient()

def search_test_cases(
    keywords: str,
    component: Optional[str] = None,
    version: Optional[str] = None,
    status: Optional[str] = None,
    test_type: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for test cases in Polarion ALM using keywords and filters.
    
    Args:
        keywords: Search keywords (e.g., "upgrade rollback", "TLS 1.3")
        component: Filter by component (e.g., "api-server", "etcd", "networking")
        version: Filter by OpenShift version (e.g., "4.18", "4.17")
        status: Filter by status (e.g., "approved", "draft", "deprecated")
        test_type: Filter by test type (e.g., "integration", "e2e", "unit")
        limit: Maximum number of results to return (default: 10)
    
    Returns:
        Dictionary containing search results and metadata
    """
    try:
        # Build Polarion query (WIQL-like syntax)
        query_parts = ["type:testcase"]
        
        if keywords:
            # Search in title and description
            query_parts.append(f'title:*{keywords}* OR description:*{keywords}*')
        
        if component:
            query_parts.append(f'customComponent:"{component}"')
        
        if version:
            query_parts.append(f'customVersion:"{version}"')
        
        if status:
            query_parts.append(f'status:"{status}"')
        
        if test_type:
            query_parts.append(f'customTestType:"{test_type}"')
        
        query = " AND ".join(query_parts)
        
        logger.info(f"Polarion Query: {query}")
        
        # Try REST API first, fallback to SOAP
        rest_params = {
            'query': query,
            'limit': limit,
            'project': polarion_client.project_id
        }
        
        result = polarion_client._make_rest_request('workitems', rest_params)
        
        if 'error' in result:
            # Fallback to SOAP API
            logger.info("REST API failed, trying SOAP API")
            fields = ['id', 'title', 'status', 'description', 'customComponent', 'customVersion']
            result = polarion_client._make_soap_request(query, fields)
        
        if 'error' in result:
            return {
                'status': 'error',
                'error': result['error'],
                'query_used': query
            }
        
        # Process results
        test_cases = []
        work_items = result.get('work_items', result.get('data', []))
        
        for item in work_items[:limit]:
            test_case = TestCase(
                id=item.get('id', 'Unknown'),
                title=item.get('title', 'No title'),
                status=item.get('status', 'Unknown'),
                description=item.get('description', '')[:200] + '...' if item.get('description', '') else 'No description',
                component=item.get('customComponent'),
                version=item.get('customVersion'),
                severity=item.get('severity'),
                automation_level=item.get('customAutomationLevel')
            )
            test_cases.append(test_case.__dict__)
        
        return {
            'status': 'success',
            'query_used': query,
            'total_found': len(test_cases),
            'test_cases': test_cases,
            'summary': f"Found {len(test_cases)} test cases matching '{keywords}'"
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'query_used': query if 'query' in locals() else 'N/A'
        }

def get_test_case_details(test_case_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific test case.
    
    Args:
        test_case_id: The Polarion test case ID (e.g., "TC12345")
    
    Returns:
        Dictionary containing detailed test case information
    """
    try:
        # REST API endpoint for specific work item
        result = polarion_client._make_rest_request(f'workitems/{test_case_id}')
        
        if 'error' in result:
            return {
                'status': 'error',
                'error': result['error'],
                'test_case_id': test_case_id
            }
        
        item = result.get('data', result)
        
        # Extract detailed information
        details = {
            'id': item.get('id', test_case_id),
            'title': item.get('title', 'No title'),
            'status': item.get('status', 'Unknown'),
            'description': item.get('description', 'No description'),
            'component': item.get('customComponent'),
            'version': item.get('customVersion'),
            'severity': item.get('severity'),
            'automation_level': item.get('customAutomationLevel'),
            'test_steps': item.get('testSteps', []),
            'expected_result': item.get('expectedResult'),
            'author': item.get('author'),
            'created': item.get('created'),
            'updated': item.get('updated'),
            'tags': item.get('categories', []),
            'linked_requirements': item.get('linkedWorkItems', [])
        }
        
        return {
            'status': 'success',
            'test_case': details
        }
        
    except Exception as e:
        logger.error(f"Failed to get test case details: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'test_case_id': test_case_id
        }

def query_polarion_api(
    wiql_query: str,
    fields: Optional[List[str]] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Execute a custom WIQL (Work Item Query Language) query against Polarion.
    
    Args:
        wiql_query: Custom WIQL query (e.g., "type:testcase AND title:*upgrade*")
        fields: List of fields to retrieve (default: id, title, status, description)
        limit: Maximum number of results
    
    Returns:
        Dictionary containing query results
    """
    try:
        if fields is None:
            fields = ['id', 'title', 'status', 'description', 'customComponent']
        
        logger.info(f"Custom WIQL Query: {wiql_query}")
        
        # Try SOAP API for custom queries
        result = polarion_client._make_soap_request(wiql_query, fields)
        
        if 'error' in result:
            # Try REST API as fallback
            rest_params = {
                'query': wiql_query,
                'limit': limit,
                'project': polarion_client.project_id
            }
            result = polarion_client._make_rest_request('workitems', rest_params)
        
        if 'error' in result:
            return {
                'status': 'error',
                'error': result['error'],
                'query': wiql_query
            }
        
        work_items = result.get('work_items', result.get('data', []))
        
        return {
            'status': 'success',
            'query': wiql_query,
            'fields_requested': fields,
            'total_found': len(work_items),
            'work_items': work_items[:limit],
            'summary': f"Query returned {len(work_items)} results"
        }
        
    except Exception as e:
        logger.error(f"Custom query failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'query': wiql_query
        }

# Helper function for formatted responses (used by web GUI and CLI)
def format_search_results(results: Dict[str, Any]) -> str:
    """Format search results for display."""
    if results['status'] == 'error':
        return f"❌ Error: {results['error']}"
    
    output = f"🔍 Polarion Query: {results['query_used']}\n\n"
    output += f"📊 Results: {results['total_found']} test cases found\n\n"
    
    for i, tc in enumerate(results['test_cases'], 1):
        status_icon = '✅' if tc['status'] == 'approved' else '📝' if tc['status'] == 'draft' else '⚠️'
        
        output += f"{i}. {status_icon} **{tc['id']}** – {tc['title']} ({tc['status'].title()})\n"
        
        if tc.get('component'):
            output += f"   📦 Component: {tc['component']}\n"
        if tc.get('version'):
            output += f"   🔢 Version: {tc['version']}\n"
        
        output += f"   📝 Purpose: {tc['description']}\n\n"
    
    if results['total_found'] > 0:
        output += "💡 **Summary**: " + results['summary']
    
    return output