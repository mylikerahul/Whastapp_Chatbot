# services/project_matcher.py
"""
Smart Jira Project Matching Service
Uses fuzzy matching and context awareness
"""

from models.schemas import JiraProject
from typing import List, Tuple, Optional, Dict
from difflib import SequenceMatcher
import re

class ProjectMatcherService:
    """Match user requests to Jira projects intelligently"""
    
    def __init__(self):
        self._projects: List[JiraProject] = []
        self._project_cache: Dict[str, JiraProject] = {}
    
    def set_projects(self, projects: List[JiraProject]):
        """Update available projects"""
        self._projects = projects
        self._project_cache = {p.key: p for p in projects}
        print(f"📊 Loaded {len(projects)} Jira projects")
    
    def find_best_match(
        self, 
        message: str, 
        team: str = None
    ) -> Tuple[Optional[str], float, List[Dict]]:
        """
        Find best matching project
        
        Returns:
            (project_key, match_score, alternative_suggestions)
        """
        if not self._projects:
            return None, 0.0, []
        
        scores = []
        
        for project in self._projects:
            score = self._calculate_match_score(
                message=message,
                project=project,
                team=team
            )
            
            scores.append({
                "key": project.key,
                "name": project.name,
                "score": score
            })
        
        # Sort by score
        scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Best match
        best = scores[0]
        best_key = best["key"]
        best_score = best["score"]
        
        # Alternative suggestions (top 3)
        suggestions = [
            {"key": s["key"], "name": s["name"]}
            for s in scores[:3]
            if s["score"] > 0.3
        ]
        
        return best_key, best_score, suggestions
    
    def _calculate_match_score(
        self, 
        message: str, 
        project: JiraProject,
        team: str = None
    ) -> float:
        """Calculate how well a project matches the message"""
        score = 0.0
        message_lower = message.lower()
        
        # Direct key match
        if project.key.lower() in message_lower:
            score += 1.0
        
        # Project name similarity
        name_similarity = SequenceMatcher(
            None, 
            message_lower, 
            project.name.lower()
        ).ratio()
        score += name_similarity * 0.5
        
        # Description keywords
        if project.description:
            desc_words = set(project.description.lower().split())
            message_words = set(message_lower.split())
            common = desc_words & message_words
            
            if common:
                score += len(common) * 0.2
        
        # Team context boost
        if team and project.name and team.lower() in project.name.lower():
            score += 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_project_by_key(self, key: str) -> Optional[JiraProject]:
        """Get project by key"""
        return self._project_cache.get(key.upper())
    
    def search_projects(self, query: str, limit: int = 5) -> List[JiraProject]:
        """Search projects by name or description"""
        query_lower = query.lower()
        
        matches = []
        for project in self._projects:
            if (query_lower in project.name.lower() or 
                query_lower in project.key.lower() or
                (project.description and query_lower in project.description.lower())):
                matches.append(project)
        
        return matches[:limit]


project_matcher_service = ProjectMatcherService()