"""
Advanced Jira Integration Service - FIXED VERSION
Complete ticket lifecycle management with better error handling
"""

from jira import JIRA
from jira.exceptions import JIRAError
from config.settings import settings
from models.schemas import JiraProject, Priority, TicketPreview
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

class JiraService:
    def __init__(self):
        try:
            self.client = JIRA(
                server=settings.JIRA_HOST,
                basic_auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
            )
            self.default_project = settings.JIRA_PROJECT_KEY
            print(f"✅ Jira client initialized: {settings.JIRA_HOST}")
        except Exception as e:
            print(f"❌ Jira initialization failed: {e}")
            self.client = None
    
    async def test_jira_connection(self) -> bool:
        """Test Jira connection"""
        try:
            if not self.client:
                return False
            
            # Try to fetch current user info
            user = self.client.myself()
            print(f"✅ Jira connected as: {user.get('displayName', 'Unknown')}")
            return True
        except JIRAError as e:
            print(f"❌ Jira connection test failed: {e.status_code} - {e.text}")
            return False
        except Exception as e:
            print(f"❌ Jira connection error: {e}")
            return False
    
    def _get_project_issue_types(self, project_key: str) -> List[str]:
        """Get available issue types for a project"""
        try:
            project = self.client.project(project_key)
            issue_types = [it.name for it in project.issueTypes]
            print(f"📋 Available issue types for {project_key}: {issue_types}")
            return issue_types
        except Exception as e:
            print(f"⚠️ Could not fetch issue types: {e}")
            return ["Task", "Bug", "Story"]
    
    def _get_valid_issue_type(self, project_key: str, requested_type: str = "Task") -> str:
        """Get a valid issue type for the project"""
        available_types = self._get_project_issue_types(project_key)
        
        # Check if requested type is available
        if requested_type in available_types:
            return requested_type
        
        # Try common alternatives
        for alt_type in ["Task", "Bug", "Story", "Epic"]:
            if alt_type in available_types:
                print(f"⚠️ Using {alt_type} instead of {requested_type}")
                return alt_type
        
        # Return first available type
        if available_types:
            print(f"⚠️ Using {available_types[0]} as fallback")
            return available_types[0]
        
        return "Task"  # Ultimate fallback
    
    def _get_project_priorities(self, project_key: str) -> List[str]:
        """Get available priorities"""
        try:
            priorities = self.client.priorities()
            priority_names = [p.name for p in priorities]
            print(f"🎯 Available priorities: {priority_names}")
            return priority_names
        except Exception as e:
            print(f"⚠️ Could not fetch priorities: {e}")
            return ["Medium", "High", "Low"]
    
    def _get_valid_priority(self, requested_priority: Priority) -> Optional[str]:
        """Get a valid priority name or None if not supported"""
        available_priorities = self._get_project_priorities(self.default_project)
        
        # Map Priority enum to Jira priority names
        priority_mapping = {
            "Critical": ["Critical", "Highest", "P1"],
            "High": ["High", "P2"],
            "Medium": ["Medium", "P3"],
            "Low": ["Low", "Lowest", "P4"]
        }
        
        # Try to find matching priority
        for jira_priority in priority_mapping.get(requested_priority.value, []):
            if jira_priority in available_priorities:
                return jira_priority
        
        # If no match, try the exact value
        if requested_priority.value in available_priorities:
            return requested_priority.value
        
        print(f"⚠️ Priority {requested_priority.value} not supported in this Jira instance")
        return None
    
    async def get_all_projects(self) -> List[JiraProject]:
        """Fetch all accessible Jira projects"""
        try:
            if not self.client:
                print("❌ Jira client not initialized")
                return []
            
            projects = self.client.projects()
            
            project_list = []
            for p in projects:
                try:
                    project_list.append(
                        JiraProject(
                            key=p.key,
                            name=p.name,
                            description=getattr(p, 'description', None),
                            lead=getattr(p.lead, 'displayName', None) if hasattr(p, 'lead') else None
                        )
                    )
                except Exception as e:
                    print(f"⚠️  Error parsing project {p.key}: {e}")
                    continue
            
            print(f"📊 Fetched {len(project_list)} Jira projects")
            return project_list
            
        except JIRAError as e:
            print(f"❌ Failed to fetch Jira projects: {e.status_code} - {e.text}")
            return []
        except Exception as e:
            print(f"❌ Error fetching projects: {e}")
            return []
    
    async def create_ticket(
        self,
        summary: str,
        description: str,
        project_key: str,
        priority: Priority = Priority.MEDIUM,
        assignee: Optional[str] = None,
        reporter: Optional[str] = None,
        issue_type: str = "Task"
    ) -> Dict[str, Any]:
        """Create a new Jira ticket with improved error handling"""
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Jira client not initialized'
                }
            
            # Validate project exists
            try:
                project = self.client.project(project_key)
                print(f"✅ Project validated: {project.name}")
            except JIRAError as e:
                return {
                    'success': False,
                    'error': f'Project {project_key} not found or not accessible'
                }
            
            # Get valid issue type
            valid_issue_type = self._get_valid_issue_type(project_key, issue_type)
            
            # Prepare minimal issue dictionary (only required fields)
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary[:255],  # Jira has 255 char limit for summary
                'issuetype': {'name': valid_issue_type}
            }
            
            # Add description only if it's supported
            if description:
                issue_dict['description'] = description
            
            # Add priority if supported
            valid_priority = self._get_valid_priority(priority)
            if valid_priority:
                issue_dict['priority'] = {'name': valid_priority}
            
            # IMPORTANT: Don't add assignee/reporter unless you have valid account IDs
            # Most 400 errors come from invalid assignee/reporter values
            
            print(f"📝 Creating issue with fields:")
            print(f"   Project: {project_key}")
            print(f"   Summary: {summary[:50]}...")
            print(f"   Issue Type: {valid_issue_type}")
            print(f"   Priority: {valid_priority}")
            
            # Create the issue
            new_issue = self.client.create_issue(fields=issue_dict)
            
            print(f"✅ Jira ticket created: {new_issue.key}")
            
            # Try to assign after creation (safer approach)
            if assignee:
                try:
                    self.client.assign_issue(new_issue, assignee)
                    print(f"✅ Assigned to {assignee}")
                except Exception as e:
                    print(f"⚠️ Could not assign to {assignee}: {e}")
            
            return {
                'success': True,
                'ticket_key': new_issue.key,
                'ticket_url': f"{settings.JIRA_HOST}/browse/{new_issue.key}",
                'summary': summary,
                'status': 'To Do',
                'project': project_key
            }
            
        except JIRAError as e:
            # Enhanced error parsing
            error_msg = f"Jira API Error: {e.status_code}"
            
            # Try to extract detailed error message
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    
                    # Parse error messages
                    if 'errorMessages' in error_data and error_data['errorMessages']:
                        error_msg = error_data['errorMessages'][0]
                    elif 'errors' in error_data:
                        # Field-specific errors
                        errors = error_data['errors']
                        error_details = ', '.join([f"{k}: {v}" for k, v in errors.items()])
                        error_msg = f"Field errors: {error_details}"
                    
                    print(f"❌ Detailed error: {json.dumps(error_data, indent=2)}")
                except:
                    error_msg = e.text
            
            print(f"❌ Failed to create Jira ticket: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_ticket_status(self, ticket_key: str) -> Dict[str, Any]:
        """Get current status of a ticket"""
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Jira client not initialized'
                }
            
            issue = self.client.issue(ticket_key)
            
            # Parse dates
            created = issue.fields.created
            updated = issue.fields.updated
            
            try:
                created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created_str = created_dt.strftime('%Y-%m-%d %H:%M')
            except:
                created_str = created
            
            try:
                updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                updated_str = updated_dt.strftime('%Y-%m-%d %H:%M')
            except:
                updated_str = updated
            
            return {
                'success': True,
                'ticket_key': ticket_key,
                'summary': issue.fields.summary,
                'status': issue.fields.status.name,
                'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                'created': created_str,
                'updated': updated_str,
                'description': issue.fields.description or 'No description',
                'url': f"{settings.JIRA_HOST}/browse/{ticket_key}"
            }
            
        except JIRAError as e:
            if e.status_code == 404:
                error_msg = f"Ticket {ticket_key} not found"
            else:
                error_msg = f"Jira API Error: {e.status_code}"
            
            print(f"❌ Failed to fetch ticket {ticket_key}: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            print(f"❌ Error fetching ticket {ticket_key}: {e}")
            return {
                'success': False,
                'error': f"Ticket {ticket_key} not found or inaccessible"
            }
    
    async def update_ticket(
        self,
        ticket_key: str,
        comment: Optional[str] = None,
        priority: Optional[Priority] = None,
        assignee: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing ticket"""
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Jira client not initialized'
                }
            
            issue = self.client.issue(ticket_key)
            
            # Add comment
            if comment:
                self.client.add_comment(issue, comment)
                print(f"✅ Comment added to {ticket_key}")
            
            # Update fields
            update_fields = {}
            
            if priority:
                valid_priority = self._get_valid_priority(priority)
                if valid_priority:
                    update_fields['priority'] = {'name': valid_priority}
            
            if assignee:
                update_fields['assignee'] = {'accountId': assignee}
            
            if update_fields:
                issue.update(fields=update_fields)
                print(f"✅ Fields updated for {ticket_key}")
            
            # Transition status if requested
            if status:
                transitions = self.client.transitions(issue)
                transition_id = None
                
                for t in transitions:
                    if t['name'].lower() == status.lower():
                        transition_id = t['id']
                        break
                
                if transition_id:
                    self.client.transition_issue(issue, transition_id)
                    print(f"✅ Status changed to {status} for {ticket_key}")
                else:
                    print(f"⚠️  Status '{status}' not available for {ticket_key}")
            
            return {
                'success': True,
                'ticket_key': ticket_key,
                'message': 'Ticket updated successfully'
            }
            
        except JIRAError as e:
            error_msg = f"Jira API Error: {e.status_code}"
            print(f"❌ Failed to update ticket {ticket_key}: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            print(f"❌ Error updating ticket {ticket_key}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close_ticket(self, ticket_key: str, resolution: str = "Done") -> Dict[str, Any]:
        """Close/resolve a ticket"""
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Jira client not initialized'
                }
            
            issue = self.client.issue(ticket_key)
            
            # Get available transitions
            transitions = self.client.transitions(issue)
            
            # Find "Done" or "Closed" transition
            done_transition = None
            for t in transitions:
                t_name = t['name'].lower()
                if any(keyword in t_name for keyword in ['done', 'closed', 'resolved', 'complete', 'finish']):
                    done_transition = t['id']
                    print(f"✅ Found transition: {t['name']}")
                    break
            
            if done_transition:
                self.client.transition_issue(issue, done_transition)
                
                # Try to set resolution
                try:
                    issue.update(fields={'resolution': {'name': resolution}})
                except:
                    print(f"⚠️  Could not set resolution to {resolution}")
                
                print(f"✅ Ticket {ticket_key} closed")
                return {
                    'success': True,
                    'ticket_key': ticket_key,
                    'message': f'Ticket {ticket_key} has been closed'
                }
            else:
                available = [t['name'] for t in transitions]
                error_msg = f"No close transition found. Available: {', '.join(available)}"
                print(f"⚠️  {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
        except JIRAError as e:
            error_msg = f"Jira API Error: {e.status_code}"
            print(f"❌ Failed to close ticket {ticket_key}: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            print(f"❌ Error closing ticket {ticket_key}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def add_attachment(self, ticket_key: str, file_path: str, filename: str = None) -> Dict[str, Any]:
        """Attach file to ticket"""
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Jira client not initialized'
                }
            
            issue = self.client.issue(ticket_key)
            
            with open(file_path, 'rb') as f:
                attachment = self.client.add_attachment(
                    issue=issue, 
                    attachment=f,
                    filename=filename
                )
            
            print(f"✅ Attachment added to {ticket_key}: {filename or file_path}")
            return {
                'success': True,
                'ticket_key': ticket_key,
                'message': 'Attachment added successfully',
                'attachment_id': attachment.id if hasattr(attachment, 'id') else None
            }
            
        except JIRAError as e:
            error_msg = f"Jira API Error: {e.status_code}"
            print(f"❌ Failed to add attachment to {ticket_key}: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            print(f"❌ Error adding attachment to {ticket_key}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def search_tickets(
        self, 
        user_phone: str = None, 
        project_key: str = None,
        status: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search tickets by various criteria"""
        try:
            if not self.client:
                print("❌ Jira client not initialized")
                return []
            
            # Build JQL query
            jql_parts = []
            
            if user_phone:
                jql_parts.append(f'(description ~ "{user_phone}" OR summary ~ "{user_phone}")')
            
            if project_key:
                jql_parts.append(f'project = {project_key}')
            
            if status:
                jql_parts.append(f'status = "{status}"')
            
            if not jql_parts:
                jql_parts.append('project IS NOT EMPTY')
            
            jql = ' AND '.join(jql_parts) + ' ORDER BY created DESC'
            
            print(f"🔍 JQL Query: {jql}")
            
            issues = self.client.search_issues(jql, maxResults=limit)
            
            results = []
            for issue in issues:
                try:
                    results.append({
                        'key': issue.key,
                        'summary': issue.fields.summary,
                        'status': issue.fields.status.name,
                        'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                        'created': issue.fields.created,
                        'url': f"{settings.JIRA_HOST}/browse/{issue.key}"
                    })
                except Exception as e:
                    print(f"⚠️  Error parsing issue {issue.key}: {e}")
                    continue
            
            print(f"✅ Found {len(results)} tickets")
            return results
            
        except JIRAError as e:
            print(f"❌ Failed to search tickets: {e.status_code} - {e.text}")
            return []
        except Exception as e:
            print(f"❌ Error searching tickets: {e}")
            return []
    
    async def get_ticket_comments(self, ticket_key: str) -> List[Dict]:
        """Get all comments from a ticket"""
        try:
            if not self.client:
                return []
            
            issue = self.client.issue(ticket_key)
            comments = self.client.comments(issue)
            
            result = []
            for comment in comments:
                try:
                    result.append({
                        'id': comment.id,
                        'author': comment.author.displayName if hasattr(comment.author, 'displayName') else 'Unknown',
                        'body': comment.body,
                        'created': comment.created,
                        'updated': comment.updated
                    })
                except Exception as e:
                    print(f"⚠️  Error parsing comment: {e}")
                    continue
            
            return result
            
        except Exception as e:
            print(f"❌ Error fetching comments for {ticket_key}: {e}")
            return []


# Global instance
jira_service = JiraService()