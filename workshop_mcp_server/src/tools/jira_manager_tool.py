"""
Jira Manager Tool

AI Test Engineer integration with Jira for generating test artifacts.
Supports fetching issues, analyzing requirements, and generating test cases.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
import requests
from requests.auth import HTTPBasicAuth
import json
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class JiraIssue:
    """Represents a Jira issue with relevant fields for test generation."""
    key: str
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    assignee: Optional[str]
    reporter: str
    created: str
    updated: str
    project: str
    components: List[str]
    labels: List[str]
    acceptance_criteria: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    linked_issues: List[str] = None

class JiraClient:
    """Client for interacting with Jira REST API."""
    
    def __init__(self, base_url=None, username=None, api_token=None, password=None, use_sso=False):
        # Try provided parameters first, then environment variables, then defaults
        self.base_url = base_url or os.getenv('JIRA_BASE_URL', 'https://your-company.atlassian.net')
        self.username = username or os.getenv('JIRA_USERNAME')
        self.api_token = api_token or os.getenv('JIRA_API_TOKEN')
        self.password = password or os.getenv('JIRA_PASSWORD')
        self.use_sso = use_sso
        self.session = requests.Session() if use_sso else None
        
        # Set up authentication
        if self.api_token and self.username:
            self.auth = HTTPBasicAuth(self.username, self.api_token)
            self.auth_configured = True
        elif self.username and self.password:
            self.auth = HTTPBasicAuth(self.username, self.password)
            self.auth_configured = True
        else:
            logger.warning("No Jira credentials found. Provide credentials via GUI or set environment variables")
            self.auth = None
            self.auth_configured = False
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, api_version: str = "3") -> Dict[str, Any]:
        """Make a REST API request to Jira."""
        # Ensure base_url doesn't end with slash to avoid double slashes
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/rest/api/{api_version}/{endpoint}"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            logger.info(f"Making Jira API request to: {url}")
            
            # Simple proxy configuration
            proxies = {}
            import os
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            if http_proxy:
                proxies['http'] = http_proxy
            if https_proxy:
                proxies['https'] = https_proxy
                
                # Try without proxy first (other MCP services work)
                logger.info("Other MCP services work - trying direct connection to Jira first")
            
            # Since other MCP services work, try different approaches for Jira
            request_configs = [
                # Config 1: Direct connection (since other APIs work)
                {
                    'proxies': None,
                    'verify': True,
                    'headers': headers
                },
                # Config 2: With system proxy if available
                {
                    'proxies': proxies if proxies else None,
                    'verify': True, 
                    'headers': headers
                },
                # Config 3: Different headers for Jira compatibility
                {
                    'proxies': None,
                    'verify': True,
                    'headers': {
                        **headers,
                        'User-Agent': 'MCP-Jira-Client/1.0',
                        'X-Atlassian-Token': 'no-check'
                    }
                }
            ]
            
            last_error = None
            
            for i, config in enumerate(request_configs):
                try:
                    logger.info(f"Trying Jira request configuration {i+1}/3")
                    
                    # Use session for SSO, regular requests for other auth
                    if self.use_sso:
                        response = self.session.get(
                            url, 
                            params=params, 
                            timeout=30,
                            **config
                        )
                    else:
                        response = requests.get(
                            url, 
                            params=params, 
                            auth=self.auth, 
                            timeout=30,
                            **config
                        )
                    
                    # If we get here, the request succeeded
                    logger.info(f"Jira request succeeded with configuration {i+1}")
                    break
                    
                except requests.exceptions.ProxyError as e:
                    logger.info(f"Config {i+1} failed with proxy error: {str(e)[:100]}")
                    last_error = e
                    continue
                except requests.exceptions.SSLError as e:
                    logger.info(f"Config {i+1} failed with SSL error: {str(e)[:100]}")
                    last_error = e
                    continue
                except requests.exceptions.ConnectionError as e:
                    logger.info(f"Config {i+1} failed with connection error: {str(e)[:100]}")
                    last_error = e
                    continue
                except Exception as e:
                    logger.info(f"Config {i+1} failed with error: {str(e)[:100]}")
                    last_error = e
                    continue
            else:
                # All configs failed, use the last error
                if last_error:
                    raise last_error
                else:
                    raise Exception("All connection configurations failed")
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {response.status_code}: {response.reason}"
            
            # Try to get more detailed error from response
            try:
                error_detail = response.json()
                if 'errorMessages' in error_detail:
                    error_msg += f" - {'; '.join(error_detail['errorMessages'])}"
                elif 'message' in error_detail:
                    error_msg += f" - {error_detail['message']}"
            except:
                error_msg += f" - {response.text[:200]}"
            
            # Handle specific API migration cases
            if response.status_code == 410:
                if 'search' in endpoint and api_version == "2":
                    # This is the old search endpoint, suggest using search/jql
                    error_msg += " | SOLUTION: This API has been deprecated. The system should automatically use the new search/jql endpoint."
                elif api_version == "3" and 'search/jql' not in endpoint:
                    # Try the search/jql endpoint for search operations
                    if 'search' in endpoint:
                        logger.info("API v3 search returned 410, trying search/jql endpoint...")
                        new_endpoint = endpoint.replace('search', 'search/jql')
                        return self._make_request(new_endpoint, params, "3")
                    else:
                        # Try API v2 for non-search endpoints
                        logger.info("API v3 returned 410, trying API v2...")
                        return self._make_request(endpoint, params, "2")
            
            logger.error(f"Jira API HTTP error: {error_msg}")
            return {'error': error_msg}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API request failed: {e}")
            return {'error': str(e)}
    
    def _make_request_v3_search(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the new API v3 search/jql endpoint."""
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/rest/api/3/search/jql"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            logger.info(f"Making Jira API v3 POST request to: {url}")
            logger.info(f"Search params: {search_params}")
            
            # Configure proxy settings for corporate environments  
            proxies = {}
            
            # Try to use system proxy settings
            import os
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            # For Jira specifically, try without proxy first (corporate may block Jira domains)
            if 'redhat.atlassian.net' in url.lower():
                logger.info("RedHat Jira detected. Trying direct connection first (proxy may block Jira domains).")
                proxies = None  # Try direct connection first
            elif http_proxy:
                proxies['http'] = http_proxy
                if https_proxy:
                    proxies['https'] = https_proxy
            
            # Use session for SSO, regular requests for other auth
            if self.use_sso:
                response = self.session.post(
                    url,
                    json=search_params,
                    headers=headers,
                    timeout=30,
                    proxies=proxies if proxies else None,
                    verify=True
                )
            else:
                response = requests.post(
                    url,
                    json=search_params,
                    headers=headers,
                    auth=self.auth,
                    timeout=30,
                    proxies=proxies if proxies else None,
                    verify=True
                )
            
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {response.status_code}: {response.reason}"
            
            # Get detailed error from response
            try:
                error_detail = response.json()
                if 'errorMessages' in error_detail:
                    error_msg += f" - {'; '.join(error_detail['errorMessages'])}"
                elif 'message' in error_detail:
                    error_msg += f" - {error_detail['message']}"
            except:
                error_msg += f" - {response.text[:200]}"
            
            logger.error(f"Jira API v3 search error: {error_msg}")
            return {'error': error_msg}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API v3 search request failed: {e}")
            return {'error': str(e)}
    
    def _adf_to_text(self, adf: Dict[str, Any]) -> str:
        """Convert Atlassian Document Format (ADF) to plain text."""
        texts = []
        if not isinstance(adf, dict):
            return str(adf) if adf else ''
        for node in adf.get('content', []):
            node_type = node.get('type', '')
            if node_type == 'paragraph':
                para_text = ''.join(
                    c.get('text', '') for c in node.get('content', []) if c.get('type') == 'text'
                )
                texts.append(para_text)
            elif node_type == 'heading':
                heading_text = ''.join(
                    c.get('text', '') for c in node.get('content', []) if c.get('type') == 'text'
                )
                texts.append(heading_text)
            elif node_type in ('bulletList', 'orderedList'):
                for item in node.get('content', []):
                    for para in item.get('content', []):
                        item_text = ''.join(
                            c.get('text', '') for c in para.get('content', []) if c.get('type') == 'text'
                        )
                        texts.append(f"- {item_text}")
            elif node_type == 'codeBlock':
                code_text = ''.join(
                    c.get('text', '') for c in node.get('content', []) if c.get('type') == 'text'
                )
                texts.append(code_text)
        return '\n'.join(texts)

    def _parse_issue(self, issue_data: Dict[str, Any]) -> JiraIssue:
        """Parse Jira issue JSON into JiraIssue object."""
        fields = issue_data.get('fields', {})
        
        # Extract common fields
        key = issue_data.get('key', '')
        summary = fields.get('summary', '')
        raw_desc = fields.get('description', '')
        # Jira API v3 returns description as ADF (dict); convert to plain text
        if isinstance(raw_desc, dict):
            description = self._adf_to_text(raw_desc)
        else:
            description = raw_desc or ''
        
        # Extract structured fields (handle None values from API)
        issue_type = (fields.get('issuetype') or {}).get('name', '')
        status = (fields.get('status') or {}).get('name', '')
        priority = (fields.get('priority') or {}).get('name', 'Medium')
        
        # Extract people
        assignee = None
        if fields.get('assignee'):
            assignee = fields['assignee'].get('displayName', '')
        
        reporter = (fields.get('reporter') or {}).get('displayName', '')
        
        # Extract dates
        created = fields.get('created', '')
        updated = fields.get('updated', '')
        
        # Extract project info
        project = fields.get('project', {}).get('key', '')
        
        # Extract components and labels
        components = [c.get('name', '') for c in fields.get('components', [])]
        labels = fields.get('labels', [])
        
        # Extract custom fields (common patterns)
        acceptance_criteria = None
        steps_to_reproduce = None
        expected_behavior = None
        actual_behavior = None
        
        # Try to extract these from description or custom fields
        if description:
            # Simple parsing for acceptance criteria
            if 'acceptance criteria' in description.lower():
                parts = description.lower().split('acceptance criteria')
                if len(parts) > 1:
                    acceptance_criteria = parts[1].split('\n')[0:5]  # First 5 lines
                    acceptance_criteria = '\n'.join(acceptance_criteria).strip()
            
            # Extract steps to reproduce for bugs
            if issue_type.lower() == 'bug':
                if 'steps to reproduce' in description.lower():
                    parts = description.lower().split('steps to reproduce')
                    if len(parts) > 1:
                        steps_to_reproduce = parts[1].split('expected')[0] if 'expected' in parts[1] else parts[1][:500]
                
                if 'expected' in description.lower() and 'actual' in description.lower():
                    desc_lower = description.lower()
                    expected_start = desc_lower.find('expected')
                    actual_start = desc_lower.find('actual')
                    
                    if expected_start != -1:
                        expected_end = actual_start if actual_start > expected_start else len(description)
                        expected_behavior = description[expected_start:expected_end].strip()
                    
                    if actual_start != -1:
                        actual_behavior = description[actual_start:actual_start+300].strip()
        
        # Extract linked issues (simplified)
        linked_issues = []
        if 'issuelinks' in fields:
            for link in fields['issuelinks']:
                if 'outwardIssue' in link:
                    linked_issues.append(link['outwardIssue'].get('key', ''))
                if 'inwardIssue' in link:
                    linked_issues.append(link['inwardIssue'].get('key', ''))
        
        return JiraIssue(
            key=key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            status=status,
            priority=priority,
            assignee=assignee,
            reporter=reporter,
            created=created,
            updated=updated,
            project=project,
            components=components,
            labels=labels,
            acceptance_criteria=acceptance_criteria,
            steps_to_reproduce=steps_to_reproduce,
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior,
            linked_issues=linked_issues
        )

    def add_comment(self, issue_key: str, comment_text: str) -> Dict[str, Any]:
        """Add a comment to a Jira issue."""
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/rest/api/2/issue/{issue_key}/comment"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        try:
            response = requests.post(url, json={"body": comment_text}, auth=self.auth, headers=headers, timeout=15)
            if response.status_code == 201:
                return {'status': 'success', 'message': f'Comment added to {issue_key}'}
            else:
                return {'status': 'error', 'error': f'Failed ({response.status_code}): {response.text[:200]}'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_comments(self, issue_key: str) -> Dict[str, Any]:
        """Get comments for a Jira issue."""
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/rest/api/2/issue/{issue_key}/comment"
        headers = {'Accept': 'application/json'}
        try:
            response = requests.get(url, auth=self.auth, headers=headers, timeout=15)
            if response.status_code == 200:
                raw_comments = response.json().get('comments', [])
                comments = []
                for c in raw_comments:
                    comments.append({
                        'author': (c.get('author') or {}).get('displayName', 'Unknown'),
                        'body': c.get('body', ''),
                        'created': c.get('created', ''),
                        'updated': c.get('updated', '')
                    })
                return {'status': 'success', 'comments': comments, 'total': len(comments)}
            else:
                return {'status': 'error', 'error': f'Failed ({response.status_code})'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available transitions for an issue."""
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
        headers = {'Accept': 'application/json'}
        try:
            response = requests.get(url, auth=self.auth, headers=headers, timeout=15)
            if response.status_code == 200:
                transitions = response.json().get('transitions', [])
                return {'status': 'success', 'transitions': [
                    {'id': t['id'], 'name': t['name'], 'to': t.get('to', {}).get('name', '')}
                    for t in transitions
                ]}
            else:
                return {'status': 'error', 'error': f'Failed ({response.status_code})'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def transition_issue(self, issue_key: str, transition_id: str, comment: str = "") -> Dict[str, Any]:
        """Transition an issue to a new status."""
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        data = {"transition": {"id": transition_id}}
        if comment:
            data["update"] = {"comment": [{"add": {"body": comment}}]}
        try:
            response = requests.post(url, json=data, auth=self.auth, headers=headers, timeout=15)
            if response.status_code == 204:
                return {'status': 'success', 'message': f'Issue {issue_key} transitioned'}
            else:
                return {'status': 'error', 'error': f'Failed ({response.status_code}): {response.text[:200]}'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def assign_issue(self, issue_key: str, assignee: str) -> Dict[str, Any]:
        """Assign an issue to a user."""
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/rest/api/2/issue/{issue_key}/assignee"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        try:
            response = requests.put(url, json={"name": assignee}, auth=self.auth, headers=headers, timeout=15)
            if response.status_code == 204:
                return {'status': 'success', 'message': f'Issue {issue_key} assigned to {assignee}'}
            else:
                return {'status': 'error', 'error': f'Failed ({response.status_code}): {response.text[:200]}'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_my_issues(self, issue_type: str = "assigned", status_filter: str = None, max_results: int = 50) -> Dict[str, Any]:
        """Get issues based on relationship to the current user."""
        username = self.username
        if issue_type == "assigned":
            jql = f'assignee = "{username}" ORDER BY updated DESC'
        elif issue_type == "qa_contact":
            jql = f'"QA Contact" = "{username}" AND resolution = Unresolved ORDER BY status DESC, updated DESC'
        elif issue_type == "reported":
            jql = f'reporter = "{username}" ORDER BY updated DESC'
        elif issue_type == "all_mine":
            jql = f'(assignee = "{username}" OR reporter = "{username}") ORDER BY updated DESC'
        else:
            jql = f'assignee = "{username}" ORDER BY updated DESC'

        if status_filter and status_filter.strip():
            jql = jql.replace(' ORDER BY', f' AND status = "{status_filter}" ORDER BY')

        base_url = self.base_url.rstrip('/')
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        fields = 'key,summary,status,priority,assignee,reporter,created,updated,issuetype,project'

        # Try API v3 search/jql first (newer Jira instances require it)
        try:
            url_v3 = f"{base_url}/rest/api/3/search/jql"
            params_v3 = {'jql': jql, 'maxResults': max_results, 'fields': fields}
            response = requests.get(url_v3, params=params_v3, auth=self.auth, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
            elif response.status_code in (404, 405):
                # Fallback to v2 search
                url_v2 = f"{base_url}/rest/api/2/search"
                params_v2 = {'jql': jql, 'maxResults': max_results, 'fields': fields}
                response = requests.get(url_v2, params=params_v2, auth=self.auth, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                else:
                    return {'status': 'error', 'error': f'Search failed ({response.status_code}): {response.text[:200]}'}
            else:
                return {'status': 'error', 'error': f'Search failed ({response.status_code}): {response.text[:200]}'}

            issues = []
            for issue in data.get('issues', []):
                f = issue.get('fields', {})
                issues.append({
                    'key': issue.get('key', ''),
                    'summary': f.get('summary', ''),
                    'status': (f.get('status') or {}).get('name', ''),
                    'priority': (f.get('priority') or {}).get('name', ''),
                    'assignee': (f.get('assignee') or {}).get('displayName', 'Unassigned'),
                    'reporter': (f.get('reporter') or {}).get('displayName', ''),
                    'issue_type': (f.get('issuetype') or {}).get('name', ''),
                    'project': (f.get('project') or {}).get('key', ''),
                    'updated': f.get('updated', ''),
                    'url': f"{base_url}/browse/{issue.get('key', '')}"
                })
            return {'status': 'success', 'issues': issues, 'total': data.get('total', 0), 'jql': jql}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

# Initialize default client (can be overridden)
jira_client = JiraClient()

def _get_jira_client(base_url: str = None, username: str = None, api_token: str = None, password: str = None) -> JiraClient:
    """Get appropriate Jira client - custom if credentials provided, otherwise default."""
    if any([base_url, username, api_token, password]):
        return JiraClient(base_url, username, api_token, password)
    return jira_client

def test_jira_connection(base_url: str, username: str = None, api_token: str = None, password: str = None, use_sso: bool = False) -> Dict[str, Any]:
    """
    Test Jira connection with provided credentials.
    
    Args:
        base_url: Jira server URL
        username: Jira username (optional for SSO)
        api_token: Jira API token (for cloud)
        password: Jira password (for server)
        use_sso: Use SSO authentication
    
    Returns:
        Dictionary containing connection test results
    """
    try:
        # Create test client
        test_client = JiraClient(base_url, username, api_token, password, use_sso=use_sso)
        
        if not test_client.auth_configured:
            return {
                'status': 'error',
                'error': 'Authentication not properly configured. Provide username + (api_token OR password)'
            }
        
        # For RedHat corporate Jira, try different endpoints in order
        endpoints_to_try = ['myself', 'serverInfo', 'permissions']
        
        result = None
        last_error = None
        
        # Try simple connectivity test first
        logger.info(f"Testing API connectivity to: {base_url}")
        
        for endpoint in endpoints_to_try:
            logger.info(f"Trying endpoint: {endpoint}")
            
            # Try API v2 first for corporate instances (more commonly supported)
            try:
                result = test_client._make_request(endpoint, api_version="2")
                
                if 'error' not in result:
                    logger.info(f"Successfully connected using v2 endpoint: {endpoint}")
                    break
                else:
                    logger.info(f"v2 {endpoint} failed: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                logger.info(f"v2 {endpoint} exception: {str(e)}")
                
            # Try API v3 as fallback
            try:
                result_v3 = test_client._make_request(endpoint, api_version="3")
                if 'error' not in result_v3:
                    result = result_v3
                    logger.info(f"Successfully connected using v3 endpoint: {endpoint}")
                    break
                else:
                    logger.info(f"v3 {endpoint} failed: {result_v3.get('error', 'Unknown')}")
                    
            except Exception as e:
                logger.info(f"v3 {endpoint} exception: {str(e)}")
                
            last_error = result.get('error', 'Unknown error') if result else 'No response'
        
        if 'error' in result:
            error_msg = last_error or result['error']
            
            # Provide helpful suggestions for common issues
            suggestions = []
            
            if 'ProxyError' in error_msg or 'proxy' in error_msg.lower():
                suggestions.append("🌐 Corporate proxy is blocking the connection.")
                suggestions.append("🔌 Try connecting to RedHat VPN if not already connected.")
                suggestions.append("🏢 Contact your IT administrator about Jira API proxy settings.")
                suggestions.append("🔧 You may need to configure proxy settings for API access.")
            
            if '403' in error_msg or 'Forbidden' in error_msg:
                suggestions.append("🚫 Your account may not have API access permissions.")
                suggestions.append("👨‍💼 Contact your Jira administrator to enable API access.")
                suggestions.append("🆔 Try using your RedHat SSO credentials instead.")
            
            if '410' in error_msg:
                suggestions.append("📡 API endpoint may be deprecated in your corporate instance.")
                suggestions.append("📋 Try checking your Jira server's API documentation.")
            
            if '401' in error_msg or 'Unauthorized' in error_msg:
                suggestions.append("🔑 Check your username and API token/password.")
                suggestions.append("📧 For Atlassian Cloud, use your email as username.")
                suggestions.append("🏢 For corporate Jira, try your domain username.")
            
            if 'redhat.atlassian.net' in base_url.lower():
                suggestions.append("🔴 For RedHat Jira specifically:")
                suggestions.append("   • Use your RedHat SSO email (rgangwar@redhat.com)")
                suggestions.append("   • Generate API token from RedHat Atlassian account")
                suggestions.append("   • Ensure you're connected to RedHat VPN")
                suggestions.append("   • Contact RedHat IT if proxy issues persist")
            
            return {
                'status': 'error',
                'error': f'Connection failed: {error_msg}',
                'suggestions': suggestions
            }
        
        return {
            'status': 'success',
            'message': 'Connection successful!',
            'user_info': {
                'display_name': result.get('displayName', 'Unknown'),
                'email': result.get('emailAddress', 'Unknown'),
                'account_id': result.get('accountId', 'Unknown')
            },
            'server_info': {
                'base_url': base_url,
                'auth_type': 'API Token' if api_token else 'Password',
                'api_version': 'v3 (with v2 fallback)'
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to test Jira connection: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_jira_projects(base_url: str, username: str, api_token: str = None, password: str = None) -> Dict[str, Any]:
    """
    Fetch all accessible Jira projects for the user.
    
    Args:
        base_url: Jira server URL
        username: Jira username  
        api_token: Jira API token (for cloud)
        password: Jira password (for server)
    
    Returns:
        Dictionary containing projects list
    """
    try:
        # Create client
        client = JiraClient(base_url, username, api_token, password)
        
        if not client.auth_configured:
            return {
                'status': 'error',
                'error': 'Authentication not properly configured. Provide username + (api_token OR password)'
            }
        
        logger.info("Fetching Jira projects...")
        
        # First try API v3
        projects_result = client._make_request('project', api_version="3")
        
        # Fallback to API v2 if needed
        if 'error' in projects_result:
            logger.info("API v3 failed for projects, trying v2...")
            projects_result = client._make_request('project', api_version="2")
        
        if 'error' in projects_result:
            return {
                'status': 'error',
                'error': projects_result['error']
            }
        
        # Process projects data
        projects = []
        raw_projects = projects_result if isinstance(projects_result, list) else projects_result.get('values', [])
        
        for project in raw_projects:
            # Get project info
            key = project.get('key', '')
            name = project.get('name', '')
            project_type = project.get('projectTypeKey', 'unknown')
            
            # Skip if no key
            if not key:
                continue
                
            # Assign emoji based on project key or type
            emoji = get_project_emoji(key, name, project_type)
            
            projects.append({
                'key': key,
                'name': name,
                'display_name': f"{emoji} {key} - {name}",
                'type': project_type,
                'emoji': emoji
            })
        
        # Sort projects by key
        projects.sort(key=lambda x: x['key'])
        
        logger.info(f"Found {len(projects)} accessible projects")
        
        return {
            'status': 'success',
            'projects': projects,
            'total': len(projects),
            'message': f'Found {len(projects)} accessible projects'
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch Jira projects: {e}")
        return {
            'status': 'error',
            'error': f'Failed to fetch projects: {str(e)}'
        }

def get_project_emoji(key: str, name: str, project_type: str) -> str:
    """Get appropriate emoji for project based on key, name, or type."""
    key_lower = key.lower()
    name_lower = name.lower()
    
    # Specific project mappings
    emoji_map = {
        # OpenShift/RedHat specific
        'ushift': '🚀',
        'ocpqe': '🧪', 
        'ocpbugs': '🐛',
        'wrklds': '💼',
        'ota': '🔄',
        'splat': '🛠️',
        'ocpstrat': '📋',
        'build': '🏗️',
        'console': '🖥️',
        'auth': '🔐',
        'network': '🌐',
        'storage': '💾',
        'etcd': '🗄️',
        'installer': '⚙️',
        'logging': '📝',
        'monitoring': '📊',
        'cluster': '🎯',
        'kube': '☸️',
        'openshift': '🔴',
        'api': '🔌',
        'operator': '🎛️',
        'security': '🔒',
        'node': '🖧',
        'registry': '📦'
    }
    
    # Check key first
    for keyword, emoji in emoji_map.items():
        if keyword in key_lower:
            return emoji
    
    # Check name
    for keyword, emoji in emoji_map.items():
        if keyword in name_lower:
            return emoji
    
    # Default based on project type
    type_emojis = {
        'software': '💻',
        'business': '💼', 
        'service_desk': '🎫',
        'ops': '⚙️'
    }
    
    return type_emojis.get(project_type, '📁')

def fetch_all_jira_issues(base_url: str, username: str, api_token: str = None, password: str = None, max_results: int = 500) -> Dict[str, Any]:
    """
    Fetch all accessible Jira issues for client-side filtering.
    
    Args:
        base_url: Jira server URL
        username: Jira username  
        api_token: Jira API token (for cloud)
        password: Jira password (for server)
        max_results: Maximum number of issues to fetch
    
    Returns:
        Dictionary containing all issues for client-side filtering
    """
    try:
        # Create client
        client = JiraClient(base_url, username, api_token, password)
        
        if not client.auth_configured:
            return {
                'status': 'error',
                'error': 'Authentication not properly configured. Provide username + (api_token OR password)'
            }
        
        logger.info(f"Fetching all Jira issues (max: {max_results})...")
        
        # Build query to get all accessible issues, ordered by updated date
        # This gets issues from all projects the user has access to
        jql_query = "order by updated DESC"
        
        all_issues = []
        start_at = 0
        batch_size = min(100, max_results)  # Fetch in batches of 100 or less
        
        while len(all_issues) < max_results:
            remaining = max_results - len(all_issues)
            current_batch_size = min(batch_size, remaining)
            
            # Prepare search parameters
            params_v3 = {
                'jql': jql_query,
                'startAt': start_at,
                'maxResults': current_batch_size,
                'fields': [
                    'key', 'summary', 'status', 'priority', 'issuetype', 
                    'assignee', 'created', 'updated', 'project', 'reporter',
                    'description', 'labels', 'components'
                ]
            }
            
            logger.info(f"Fetching batch {start_at//batch_size + 1}: issues {start_at+1}-{start_at+current_batch_size}")
            
            # Try API v3 first
            result = client._make_request_v3_search(params_v3)
            
            # Fallback to API v2 if needed
            if 'error' in result:
                logger.info("API v3 failed, trying v2...")
                params_v2 = {
                    'jql': jql_query,
                    'startAt': start_at,
                    'maxResults': current_batch_size,
                    'fields': 'key,summary,status,priority,issuetype,assignee,created,updated,project,reporter,description,labels,components'
                }
                result = client._make_request('search', params_v2, api_version="2")
            
            if 'error' in result:
                return {
                    'status': 'error',
                    'error': result['error']
                }
            
            # Process issues from this batch
            batch_issues = result.get('issues', [])
            
            if not batch_issues:
                break  # No more issues
            
            for issue in batch_issues:
                processed_issue = {
                    'key': issue.get('key', ''),
                    'summary': issue.get('fields', {}).get('summary', ''),
                    'status': issue.get('fields', {}).get('status', {}).get('name', 'Unknown'),
                    'priority': issue.get('fields', {}).get('priority', {}).get('name', 'Undefined') if issue.get('fields', {}).get('priority') else 'Undefined',
                    'issue_type': issue.get('fields', {}).get('issuetype', {}).get('name', 'Unknown'),
                    'project': issue.get('fields', {}).get('project', {}).get('key', 'Unknown'),
                    'project_name': issue.get('fields', {}).get('project', {}).get('name', 'Unknown'),
                    'assignee': issue.get('fields', {}).get('assignee', {}).get('displayName', None) if issue.get('fields', {}).get('assignee') else None,
                    'assignee_email': issue.get('fields', {}).get('assignee', {}).get('emailAddress', None) if issue.get('fields', {}).get('assignee') else None,
                    'reporter': issue.get('fields', {}).get('reporter', {}).get('displayName', None) if issue.get('fields', {}).get('reporter') else None,
                    'created': issue.get('fields', {}).get('created', ''),
                    'updated': issue.get('fields', {}).get('updated', ''),
                    'description': issue.get('fields', {}).get('description', '') or '',
                    'labels': issue.get('fields', {}).get('labels', []),
                    'components': [comp.get('name', '') for comp in issue.get('fields', {}).get('components', [])]
                }
                
                all_issues.append(processed_issue)
            
            # Check if we got all available issues
            total_issues = result.get('total', 0)
            if start_at + len(batch_issues) >= total_issues:
                logger.info(f"Reached end of available issues (total: {total_issues})")
                break
            
            # Prepare for next batch
            start_at += len(batch_issues)
        
        # Calculate filter counts for better UX
        filter_counts = calculate_filter_counts(all_issues)
        
        logger.info(f"Successfully fetched {len(all_issues)} issues for client-side filtering")
        
        return {
            'status': 'success',
            'issues': all_issues,
            'total': len(all_issues),
            'filter_counts': filter_counts,
            'message': f'Loaded {len(all_issues)} issues for filtering'
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch all Jira issues: {e}")
        return {
            'status': 'error',
            'error': f'Failed to fetch issues: {str(e)}'
        }

def calculate_filter_counts(issues):
    """Calculate counts for each filter option to show in UI."""
    counts = {
        'projects': {},
        'assignees': {},
        'statuses': {},
        'priorities': {},
        'issue_types': {},
        'total': len(issues)
    }
    
    for issue in issues:
        # Project counts
        project = issue.get('project', 'Unknown')
        counts['projects'][project] = counts['projects'].get(project, 0) + 1
        
        # Assignee counts
        assignee = issue.get('assignee', 'Unassigned')
        if assignee is None:
            assignee = 'Unassigned'
        counts['assignees'][assignee] = counts['assignees'].get(assignee, 0) + 1
        
        # Status counts
        status = issue.get('status', 'Unknown')
        counts['statuses'][status] = counts['statuses'].get(status, 0) + 1
        
        # Priority counts
        priority = issue.get('priority', 'Undefined')
        counts['priorities'][priority] = counts['priorities'].get(priority, 0) + 1
        
        # Issue type counts
        issue_type = issue.get('issue_type', 'Unknown')
        counts['issue_types'][issue_type] = counts['issue_types'].get(issue_type, 0) + 1
    
    return counts

def get_issue(issue_id: str, base_url: str = None, username: str = None, api_token: str = None, password: str = None) -> Dict[str, Any]:
    """
    Fetch a specific Jira issue by ID.
    
    Args:
        issue_id: Jira issue key (e.g., 'ABC-123')
        base_url: Jira server URL (optional, uses env if not provided)
        username: Jira username (optional, uses env if not provided)
        api_token: Jira API token (optional, uses env if not provided) 
        password: Jira password (optional, uses env if not provided)
    
    Returns:
        Dictionary containing issue details and parsed data
    """
    try:
        logger.info(f"Fetching Jira issue: {issue_id}")
        
        # Get appropriate client
        client = _get_jira_client(base_url, username, api_token, password)
        
        if not client.auth_configured:
            return {
                'status': 'error',
                'error': 'No Jira credentials configured. Please provide credentials via GUI or environment variables.',
                'issue_id': issue_id
            }
        
        result = client._make_request(f'issue/{issue_id}')
        
        if 'error' in result:
            return {
                'status': 'error',
                'error': result['error'],
                'issue_id': issue_id
            }
        
        # Parse the issue
        issue = client._parse_issue(result)
        
        return {
            'status': 'success',
            'issue_id': issue_id,
            'issue': issue.__dict__,
            'raw_data': result  # Include raw data for advanced use
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch Jira issue {issue_id}: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'issue_id': issue_id
        }

def search_issues(query: str, max_results: int = 20, base_url: str = None, username: str = None, api_token: str = None, password: str = None) -> Dict[str, Any]:
    """
    Search Jira issues using JQL (Jira Query Language).
    
    Args:
        query: JQL query string
        max_results: Maximum number of results to return
        base_url: Jira server URL (optional)
        username: Jira username (optional)
        api_token: Jira API token (optional)
        password: Jira password (optional)
    
    Returns:
        Dictionary containing search results
    """
    try:
        logger.info(f"Searching Jira issues: {query}")
        
        # Get appropriate client
        client = _get_jira_client(base_url, username, api_token, password)
        
        if not client.auth_configured:
            return {
                'status': 'error',
                'error': 'No Jira credentials configured. Please provide credentials via GUI or environment variables.',
                'query': query
            }
        
        # Try API v3 search/jql endpoint first (new format)
        params_v3 = {
            'jql': query,
            'maxResults': max_results,
            'fields': ['key','summary','status','priority','issuetype','assignee','created','updated','project']
        }
        
        logger.info("Trying API v3 search/jql endpoint...")
        result = client._make_request_v3_search(params_v3)
        
        # Fallback to legacy API v2 search if v3 fails
        if 'error' in result:
            logger.info("API v3 failed, trying legacy API v2 search endpoint...")
            params_v2 = {
                'jql': query,
                'maxResults': max_results,
                'fields': 'key,summary,status,priority,issuetype,assignee,created,updated,project'
            }
            result = client._make_request('search', params_v2, api_version="2")
        
        if 'error' in result:
            return {
                'status': 'error',
                'error': result['error'],
                'query': query
            }
        
        issues = []
        for issue_data in result.get('issues', []):
            issue = jira_client._parse_issue(issue_data)
            issues.append(issue.__dict__)
        
        return {
            'status': 'success',
            'query': query,
            'total': result.get('total', 0),
            'max_results': max_results,
            'issues': issues,
            'summary': f"Found {len(issues)} issues matching query"
        }
        
    except Exception as e:
        logger.error(f"Failed to search Jira issues: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'query': query
        }

def get_high_priority_bugs(team: str = None, days: int = 30, base_url: str = None, username: str = None, api_token: str = None, password: str = None) -> Dict[str, Any]:
    """
    Get high priority bugs for a team or project.
    
    Args:
        team: Team name or project key
        days: Number of days to look back (default: 30)
        base_url: Jira server URL (optional)
        username: Jira username (optional)
        api_token: Jira API token (optional)
        password: Jira password (optional)
    
    Returns:
        Dictionary containing high priority bugs
    """
    try:
        # Build JQL query
        jql_parts = [
            'type = Bug',
            'priority in (High, Highest, Critical)',
            f'created >= -{days}d'
        ]
        
        if team:
            # Try both project key and component name
            jql_parts.append(f'(project = "{team}" OR component = "{team}")')
        
        jql_query = ' AND '.join(jql_parts) + ' ORDER BY priority DESC, created DESC'
        
        logger.info(f"Getting high priority bugs for team: {team}")
        
        return search_issues(jql_query, max_results=50, base_url=base_url, username=username, api_token=api_token, password=password)
        
    except Exception as e:
        logger.error(f"Failed to get high priority bugs: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'team': team
        }

def get_team_issues(team_name: str, status: str = None, days: int = 14, base_url: str = None, username: str = None, api_token: str = None, password: str = None) -> Dict[str, Any]:
    """
    Get issues assigned to a specific team or project.
    
    Args:
        team_name: Team name, project key, or component name
        status: Filter by status (optional)
        days: Number of days to look back (default: 14)
        base_url: Jira server URL (optional)
        username: Jira username (optional)
        api_token: Jira API token (optional)
        password: Jira password (optional)
    
    Returns:
        Dictionary containing team issues
    """
    try:
        # Build JQL query
        jql_parts = [
            f'(project = "{team_name}" OR component = "{team_name}" OR assignee in membersOf("{team_name}"))',
            f'updated >= -{days}d'
        ]
        
        if status:
            jql_parts.append(f'status = "{status}"')
        
        jql_query = ' AND '.join(jql_parts) + ' ORDER BY updated DESC'
        
        logger.info(f"Getting issues for team: {team_name}")
        
        return search_issues(jql_query, max_results=50, base_url=base_url, username=username, api_token=api_token, password=password)
        
    except Exception as e:
        logger.error(f"Failed to get team issues: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'team_name': team_name
        }

def generate_test_cases_from_jira(issue_id: str, test_types: List[str] = None, base_url: str = None, username: str = None, api_token: str = None, password: str = None) -> Dict[str, Any]:
    """
    Generate comprehensive test cases from a Jira issue.
    
    Args:
        issue_id: Jira issue key
        test_types: Types of tests to generate (functional, edge, negative, regression)
        base_url: Jira server URL (optional, uses env if not provided)
        username: Jira username (optional, uses env if not provided)
        api_token: Jira API token (optional, uses env if not provided)
        password: Jira password (optional, uses env if not provided)
    
    Returns:
        Dictionary containing generated test cases
    """
    try:
        if test_types is None:
            test_types = ['functional', 'edge', 'negative', 'regression']
        
        # First, fetch the issue
        issue_result = get_issue(issue_id, base_url=base_url, username=username, api_token=api_token, password=password)
        
        if issue_result['status'] == 'error':
            return issue_result
        
        issue = issue_result['issue']
        
        # Generate test cases based on issue type
        test_cases = []
        
        if issue['issue_type'].lower() == 'bug':
            test_cases.extend(_generate_bug_test_cases(issue, test_types))
        else:
            test_cases.extend(_generate_feature_test_cases(issue, test_types))
        
        return {
            'status': 'success',
            'issue_id': issue_id,
            'issue_summary': issue['summary'],
            'issue_type': issue['issue_type'],
            'total_test_cases': len(test_cases),
            'test_cases': test_cases,
            'test_types_generated': test_types
        }
        
    except Exception as e:
        logger.error(f"Failed to generate test cases for {issue_id}: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'issue_id': issue_id
        }

def _generate_bug_test_cases(issue: Dict[str, Any], test_types: List[str]) -> List[Dict[str, Any]]:
    """Generate test cases specifically for bug issues."""
    test_cases = []
    
    # Reproduction test case
    if 'functional' in test_types or 'regression' in test_types:
        test_cases.append({
            'id': f"{issue['key']}_REPRO",
            'title': f"Reproduce Bug: {issue['summary']}",
            'type': 'Bug Reproduction',
            'priority': 'High',
            'preconditions': f"System is in the state described in {issue['key']}",
            'test_steps': issue.get('steps_to_reproduce', 'Follow the steps described in the bug report'),
            'expected_result': issue.get('actual_behavior', 'Bug should be reproduced as described'),
            'description': f"Verify that the bug described in {issue['key']} can be reproduced"
        })
    
    # Fix validation test case
    if 'functional' in test_types:
        test_cases.append({
            'id': f"{issue['key']}_VALIDATION",
            'title': f"Validate Fix: {issue['summary']}",
            'type': 'Fix Validation',
            'priority': 'High',
            'preconditions': f"Fix for {issue['key']} has been deployed",
            'test_steps': issue.get('steps_to_reproduce', 'Perform the same steps that previously caused the bug'),
            'expected_result': issue.get('expected_behavior', 'Bug should not occur; system should behave as expected'),
            'description': f"Verify that the bug {issue['key']} has been fixed"
        })
    
    # Regression test cases
    if 'regression' in test_types:
        for component in issue.get('components', ['Related Areas']):
            test_cases.append({
                'id': f"{issue['key']}_REGRESSION_{component.upper().replace(' ', '_')}",
                'title': f"Regression Test: {component} after {issue['key']} fix",
                'type': 'Regression',
                'priority': 'Medium',
                'preconditions': f"Fix for {issue['key']} has been deployed",
                'test_steps': f"Test core functionality of {component} component",
                'expected_result': f"{component} functionality should work as before the fix",
                'description': f"Ensure fix for {issue['key']} didn't break {component} functionality"
            })
    
    # Edge case tests
    if 'edge' in test_types:
        test_cases.append({
            'id': f"{issue['key']}_EDGE",
            'title': f"Edge Cases: {issue['summary']}",
            'type': 'Edge Case',
            'priority': 'Medium',
            'preconditions': 'System is in various boundary conditions',
            'test_steps': 'Test the scenario with boundary values, empty inputs, maximum limits',
            'expected_result': 'System should handle edge cases gracefully without the original bug',
            'description': f"Test edge cases related to the bug scenario in {issue['key']}"
        })
    
    return test_cases

def _generate_feature_test_cases(issue: Dict[str, Any], test_types: List[str]) -> List[Dict[str, Any]]:
    """Generate test cases for feature/story issues."""
    test_cases = []
    
    # Functional test cases
    if 'functional' in test_types:
        test_cases.append({
            'id': f"{issue['key']}_FUNCTIONAL",
            'title': f"Functional Test: {issue['summary']}",
            'type': 'Functional',
            'priority': 'High',
            'preconditions': 'System is ready for testing the new feature',
            'test_steps': issue.get('acceptance_criteria', 'Follow the acceptance criteria defined in the issue'),
            'expected_result': 'Feature should work as described in the requirements',
            'description': f"Verify the main functionality described in {issue['key']}"
        })
    
    # Positive test cases
    if 'functional' in test_types:
        test_cases.append({
            'id': f"{issue['key']}_POSITIVE",
            'title': f"Positive Scenarios: {issue['summary']}",
            'type': 'Positive',
            'priority': 'High',
            'preconditions': 'Valid test data is available',
            'test_steps': 'Execute the feature with valid inputs and typical user workflows',
            'expected_result': 'Feature should complete successfully with expected outputs',
            'description': f"Test happy path scenarios for {issue['key']}"
        })
    
    # Negative test cases
    if 'negative' in test_types:
        test_cases.append({
            'id': f"{issue['key']}_NEGATIVE",
            'title': f"Negative Scenarios: {issue['summary']}",
            'type': 'Negative',
            'priority': 'Medium',
            'preconditions': 'System is ready for negative testing',
            'test_steps': 'Test with invalid inputs, unauthorized access, malformed data',
            'expected_result': 'System should handle errors gracefully with appropriate error messages',
            'description': f"Test error handling and validation for {issue['key']}"
        })
    
    # Edge case tests
    if 'edge' in test_types:
        test_cases.append({
            'id': f"{issue['key']}_EDGE",
            'title': f"Edge Cases: {issue['summary']}",
            'type': 'Edge Case',
            'priority': 'Medium',
            'preconditions': 'System supports boundary testing',
            'test_steps': 'Test with minimum/maximum values, empty inputs, special characters',
            'expected_result': 'System should handle boundary conditions appropriately',
            'description': f"Test boundary conditions and edge cases for {issue['key']}"
        })
    
    # Integration test cases
    if 'regression' in test_types:
        for component in issue.get('components', ['System Integration']):
            test_cases.append({
                'id': f"{issue['key']}_INTEGRATION_{component.upper().replace(' ', '_')}",
                'title': f"Integration Test: {issue['summary']} with {component}",
                'type': 'Integration',
                'priority': 'Medium',
                'preconditions': f"Both the new feature and {component} are available",
                'test_steps': f"Test interaction between the new feature and {component}",
                'expected_result': f"Feature should integrate properly with {component}",
                'description': f"Verify integration between {issue['key']} and {component}"
            })
    
    return test_cases

def generate_test_plan_from_jira(issue_id: str, base_url: str = None, username: str = None, api_token: str = None, password: str = None) -> Dict[str, Any]:
    """
    Generate a comprehensive test plan from a Jira issue.
    
    Args:
        issue_id: Jira issue key
        base_url: Jira server URL (optional, uses env if not provided)
        username: Jira username (optional, uses env if not provided)
        api_token: Jira API token (optional, uses env if not provided)
        password: Jira password (optional, uses env if not provided)
    
    Returns:
        Dictionary containing generated test plan
    """
    try:
        # Fetch the issue
        issue_result = get_issue(issue_id, base_url=base_url, username=username, api_token=api_token, password=password)
        
        if issue_result['status'] == 'error':
            return issue_result
        
        issue = issue_result['issue']
        
        # Generate test cases
        test_cases_result = generate_test_cases_from_jira(issue_id, base_url=base_url, username=username, api_token=api_token, password=password)
        test_cases = test_cases_result.get('test_cases', [])
        
        # Build comprehensive test plan
        test_plan = {
            'issue_id': issue_id,
            'feature_summary': issue['summary'],
            'description': issue['description'][:500] + '...' if len(issue['description']) > 500 else issue['description'],
            'scope': {
                'in_scope': [
                    'Core functionality testing',
                    'Integration testing',
                    'Error handling validation',
                    'Performance impact assessment'
                ],
                'out_of_scope': [
                    'Third-party integrations (unless specified)',
                    'Load testing (unless performance critical)',
                    'Security testing (unless security feature)'
                ]
            },
            'test_strategy': {
                'approach': 'Risk-based testing with focus on critical paths',
                'test_types': ['Functional', 'Integration', 'Regression', 'Edge Cases'],
                'automation_target': '70% for regression, 50% for new features'
            },
            'test_scenarios': {
                'functional': len([tc for tc in test_cases if tc['type'] in ['Functional', 'Positive']]),
                'edge_cases': len([tc for tc in test_cases if tc['type'] == 'Edge Case']),
                'negative': len([tc for tc in test_cases if tc['type'] == 'Negative']),
                'integration': len([tc for tc in test_cases if tc['type'] == 'Integration']),
                'regression': len([tc for tc in test_cases if tc['type'] in ['Regression', 'Bug Reproduction']])
            },
            'risk_areas': _identify_risk_areas(issue),
            'dependencies': issue.get('linked_issues', []),
            'test_data_requirements': _generate_test_data_requirements(issue),
            'estimated_effort': f"{len(test_cases) * 2} hours (2 hours per test case average)",
            'coverage_target': '85% of acceptance criteria',
            'test_cases': test_cases
        }
        
        return {
            'status': 'success',
            'issue_id': issue_id,
            'test_plan': test_plan
        }
        
    except Exception as e:
        logger.error(f"Failed to generate test plan for {issue_id}: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'issue_id': issue_id
        }

def _identify_risk_areas(issue: Dict[str, Any]) -> List[str]:
    """Identify potential risk areas based on issue details."""
    risks = []
    
    # Priority-based risks
    if issue.get('priority', '').lower() in ['high', 'highest', 'critical']:
        risks.append('High priority change - increased regression risk')
    
    # Component-based risks
    components = issue.get('components', [])
    if any('api' in comp.lower() for comp in components):
        risks.append('API changes - backward compatibility risk')
    if any('database' in comp.lower() or 'db' in comp.lower() for comp in components):
        risks.append('Database changes - data integrity risk')
    if any('security' in comp.lower() or 'auth' in comp.lower() for comp in components):
        risks.append('Security component - security vulnerability risk')
    
    # Type-based risks
    if issue.get('issue_type', '').lower() == 'bug':
        risks.append('Bug fix - potential for introducing new bugs')
    
    # Description-based risks
    description = issue.get('description', '').lower()
    if 'breaking change' in description:
        risks.append('Breaking change - compatibility risk')
    if 'performance' in description:
        risks.append('Performance impact - scalability risk')
    
    return risks if risks else ['Standard functionality risk - low to medium']

def _generate_test_data_requirements(issue: Dict[str, Any]) -> List[str]:
    """Generate test data requirements based on issue details."""
    requirements = ['Valid user accounts for testing']
    
    # Component-based requirements
    components = issue.get('components', [])
    for component in components:
        if 'user' in component.lower():
            requirements.append('Test user accounts with various permission levels')
        if 'order' in component.lower() or 'transaction' in component.lower():
            requirements.append('Sample transaction/order data')
        if 'product' in component.lower():
            requirements.append('Product catalog test data')
        if 'payment' in component.lower():
            requirements.append('Test payment methods and billing data')
    
    # Description-based requirements
    description = issue.get('description', '').lower()
    if 'file' in description or 'upload' in description:
        requirements.append('Test files of various formats and sizes')
    if 'email' in description:
        requirements.append('Test email addresses and email templates')
    if 'report' in description:
        requirements.append('Historical data for report generation')
    
    return list(set(requirements))  # Remove duplicates

# Helper function for formatting results
def format_jira_results(result: Dict[str, Any]) -> str:
    """Format Jira results for display."""
    if result['status'] == 'error':
        return f"❌ Error: {result['error']}"
    
    if 'issues' in result:
        # Search results
        output = f"🔍 Jira Search Results\n\n"
        output += f"📊 Query: {result['query']}\n"
        output += f"📈 Found: {result['total']} issues\n\n"
        
        for issue in result['issues'][:10]:  # Show first 10
            priority_icon = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', 'Highest': '🔴', 'Critical': '🔴'}.get(issue['priority'], '⚪')
            status_icon = {'Done': '✅', 'In Progress': '🔄', 'To Do': '📋', 'Open': '📋'}.get(issue['status'], '📄')
            
            output += f"{priority_icon} **{issue['key']}** - {issue['summary']}\n"
            output += f"   {status_icon} Status: {issue['status']} | Priority: {issue['priority']}\n"
            output += f"   📁 Project: {issue['project']} | 👤 Assignee: {issue['assignee'] or 'Unassigned'}\n\n"
        
    elif 'issue' in result:
        # Single issue result
        issue = result['issue']
        output = f"📋 Jira Issue Details\n\n"
        output += f"**{issue['key']}** - {issue['summary']}\n"
        output += f"📝 Type: {issue['issue_type']} | 🎯 Priority: {issue['priority']}\n"
        output += f"📊 Status: {issue['status']} | 👤 Assignee: {issue['assignee'] or 'Unassigned'}\n\n"
        
        if issue['description']:
            output += f"📄 **Description:**\n{issue['description'][:300]}{'...' if len(issue['description']) > 300 else ''}\n\n"
        
        if issue['acceptance_criteria']:
            output += f"✅ **Acceptance Criteria:**\n{issue['acceptance_criteria']}\n\n"
        
        if issue['components']:
            output += f"🧩 **Components:** {', '.join(issue['components'])}\n"
    
    return output