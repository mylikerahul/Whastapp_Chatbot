"""
🎯 Advanced Team Detection Service - Real Estate & Tech Support
Intelligent team routing with context awareness and fuzzy matching
"""

from typing import Tuple, Dict, List, Optional
import re
from collections import defaultdict
from difflib import SequenceMatcher

class TeamDetectionService:
    """
    🔥 ENHANCED: Intelligent team detection with context awareness
    """
    
    def __init__(self):
        # ==========================================
        # COMPREHENSIVE TEAM KEYWORDS
        # ==========================================
        self._team_keywords = {
            "Salesforce Team": {
                "high_priority": [  # Weight: 3.0
                    "salesforce", "sfdc", "crm system", "sales cloud",
                    "service cloud", "marketing cloud", "apex", "visualforce"
                ],
                "medium_priority": [  # Weight: 2.0
                    "lead", "opportunity", "contact", "account",
                    "campaign", "workflow", "process builder", "flow"
                ],
                "low_priority": [  # Weight: 1.0
                    "sync", "integration", "customer data", "pipeline",
                    "forecast", "quote", "contract", "case"
                ]
            },
            
            "Marketing Team": {
                "high_priority": [
                    "campaign", "marketing report", "ai report", "kpi",
                    "roi", "conversion", "marketing analytics", "campaign performance"
                ],
                "medium_priority": [
                    "email blast", "newsletter", "social media", "content",
                    "branding", "creative", "design", "collateral"
                ],
                "low_priority": [
                    "metrics", "engagement", "impressions", "clicks",
                    "leads generated", "attribution", "funnel"
                ]
            },
            
            "Development Team": {
                "high_priority": [
                    "api", "backend", "server down", "deployment failed",
                    "production issue", "critical bug", "system crash"
                ],
                "medium_priority": [
                    "website", "portal", "application", "code",
                    "feature", "endpoint", "database", "query"
                ],
                "low_priority": [
                    "error", "timeout", "performance", "latency",
                    "authentication", "authorization", "cors", "ssl"
                ]
            },
            
            "Data Team": {
                "high_priority": [
                    "dashboard", "power bi", "tableau", "data warehouse",
                    "etl", "data pipeline", "analytics platform"
                ],
                "medium_priority": [
                    "report", "analytics", "insights", "visualization",
                    "metrics", "kpi dashboard", "data export"
                ],
                "low_priority": [
                    "sql", "query", "database report", "data quality",
                    "aggregation", "calculation", "formula"
                ]
            },
            
            "IT Team": {
                "high_priority": [
                    "laptop", "computer", "hardware", "network",
                    "wifi", "vpn", "printer", "monitor"
                ],
                "medium_priority": [
                    "keyboard", "mouse", "screen", "device",
                    "workstation", "connection", "internet"
                ],
                "low_priority": [
                    "software installation", "windows", "mac",
                    "office 365", "teams", "zoom"
                ]
            },
            
            "Admin Team": {
                "high_priority": [
                    "access denied", "permission", "user role",
                    "account locked", "password reset", "can't login"
                ],
                "medium_priority": [
                    "access request", "new user", "user management",
                    "profile", "privileges", "admin rights"
                ],
                "low_priority": [
                    "configuration", "settings", "preferences",
                    "notification", "email signature"
                ]
            },
            
            "Support Team": {
                "high_priority": [
                    "urgent", "critical", "emergency", "down"
                ],
                "medium_priority": [
                    "help", "support", "assistance", "question"
                ],
                "low_priority": [
                    "inquiry", "general", "how to", "clarification"
                ]
            }
        }
        
        # ==========================================
        # CONTEXTUAL PATTERNS (Regex + Weight)
        # ==========================================
        self._contextual_patterns = {
            "Marketing Team": [
                (r"(?:campaign|marketing)\s+report", 5.0),
                (r"(?:ai|automated)\s+report.*campaign", 5.0),
                (r"kpi.*(?:calculation|metric|analysis)", 4.0),
                (r"(?:email|social)\s+(?:campaign|blast|marketing)", 4.0),
                (r"(?:four seasons|autumn|spring|summer|winter)\s+campaign", 5.0),
                (r"roi.*(?:report|analysis|calculation)", 4.0),
                (r"conversion.*(?:rate|funnel|tracking)", 3.0),
                (r"(?:brand|creative|design)\s+(?:asset|material|content)", 3.0)
            ],
            
            "Salesforce Team": [
                (r"(?:lead|contact|account).*(?:sync|not syncing|missing)", 5.0),
                (r"salesforce.*(?:down|not working|error|issue)", 5.0),
                (r"crm.*(?:integration|connection|api)", 4.0),
                (r"(?:opportunity|deal|pipeline).*(?:missing|wrong|error)", 4.0),
                (r"workflow.*(?:not triggering|failed|stuck)", 3.0),
                (r"(?:validation|apex|trigger).*error", 3.0)
            ],
            
            "Development Team": [
                (r"(?:api|endpoint).*(?:down|failing|error|404|500)", 5.0),
                (r"(?:website|portal|app).*(?:down|not loading|crashed)", 5.0),
                (r"(?:database|db).*(?:connection|timeout|slow)", 4.0),
                (r"(?:deployment|build).*(?:failed|error)", 4.0),
                (r"(?:authentication|login).*(?:not working|failed|error)", 4.0),
                (r"(?:bug|error|exception).*(?:production|live|critical)", 5.0)
            ],
            
            "Data Team": [
                (r"(?:dashboard|report).*(?:not loading|wrong data|error)", 5.0),
                (r"(?:power bi|tableau|analytics).*(?:issue|not working)", 5.0),
                (r"(?:data|metric).*(?:incorrect|missing|wrong)", 4.0),
                (r"(?:export|download).*(?:data|report|csv|excel)", 3.0),
                (r"(?:kpi|metric).*(?:calculation|formula|aggregation)", 4.0)
            ],
            
            "IT Team": [
                (r"(?:laptop|computer|pc).*(?:issue|problem|not working)", 5.0),
                (r"(?:keyboard|mouse|screen|monitor).*(?:broken|not working)", 5.0),
                (r"(?:network|wifi|internet).*(?:down|slow|not connecting)", 5.0),
                (r"(?:vpn|printer|hardware).*(?:issue|problem)", 4.0),
                (r"(?:device|equipment).*(?:malfunction|broken)", 4.0)
            ],
            
            "Admin Team": [
                (r"(?:access|permission|privilege).*(?:denied|needed|request)", 5.0),
                (r"(?:password|account).*(?:reset|locked|expired)", 5.0),
                (r"(?:login|sign in).*(?:can't|unable|not working)", 4.0),
                (r"(?:user|profile).*(?:create|delete|modify|manage)", 4.0),
                (r"(?:role|access level).*(?:change|update|assign)", 3.0)
            ]
        }
        
        # ==========================================
        # ENTITY-BASED DETECTION
        # ==========================================
        self._entity_patterns = {
            "campaign_names": [
                r"(?:four seasons|autumn|spring|summer|winter|holiday)\s+(?:campaign|promotion)",
                r"(?:saadiyat|jumeirah|marina|downtown)\s+campaign",
                r"(?:new|launch|seasonal)\s+campaign"
            ],
            "systems": [
                r"salesforce|sfdc|crm",
                r"power bi|tableau|analytics",
                r"jira|confluence|slack"
            ],
            "hardware": [
                r"laptop|computer|pc|workstation",
                r"keyboard|mouse|monitor|screen",
                r"printer|scanner|device"
            ]
        }
        
        # ==========================================
        # TEAM PRIORITIES (for ties)
        # ==========================================
        self._team_priority = {
            "Salesforce Team": 6,
            "Marketing Team": 7,
            "Development Team": 5,
            "Data Team": 4,
            "IT Team": 3,
            "Admin Team": 2,
            "Support Team": 1
        }
        
        # ==========================================
        # JIRA PROJECT MAPPING
        # ==========================================
        self._team_jira_mapping = {
            "Salesforce Team": "SUP",
            "Marketing Team": "SUP",
            "Development Team": "SUP",
            "Data Team": "SUP",
            "IT Team": "SUP",
            "Admin Team": "SUP",
            "Support Team": "SUP"
        }
    
    # ==========================================
    # MAIN DETECTION METHOD
    # ==========================================
    
    def detect_team(self, message: str) -> Tuple[str, float]:
        """
        🔥 ENHANCED: Intelligent team detection with multi-factor scoring
        
        Args:
            message: User's message
        
        Returns:
            (team_name, confidence_score)
        """
        
        message_lower = message.lower()
        
        # Initialize scores
        team_scores: Dict[str, float] = defaultdict(float)
        
        # ==========================================
        # 1. KEYWORD MATCHING (Weighted)
        # ==========================================
        for team, priority_keywords in self._team_keywords.items():
            # High priority keywords
            for keyword in priority_keywords.get("high_priority", []):
                if keyword in message_lower:
                    team_scores[team] += 3.0
                    print(f"   🎯 High-priority keyword '{keyword}' → {team} (+3.0)")
            
            # Medium priority keywords
            for keyword in priority_keywords.get("medium_priority", []):
                if keyword in message_lower:
                    team_scores[team] += 2.0
                    print(f"   🎯 Medium-priority keyword '{keyword}' → {team} (+2.0)")
            
            # Low priority keywords
            for keyword in priority_keywords.get("low_priority", []):
                if keyword in message_lower:
                    team_scores[team] += 1.0
                    print(f"   🎯 Low-priority keyword '{keyword}' → {team} (+1.0)")
        
        # ==========================================
        # 2. CONTEXTUAL PATTERN MATCHING
        # ==========================================
        for team, patterns in self._contextual_patterns.items():
            for pattern, weight in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    team_scores[team] += weight
                    print(f"   🔍 Pattern matched '{pattern[:40]}...' → {team} (+{weight})")
        
        # ==========================================
        # 3. ENTITY DETECTION
        # ==========================================
        entities_found = {
            "campaigns": [],
            "systems": [],
            "hardware": []
        }
        
        # Campaign detection
        for pattern in self._entity_patterns["campaign_names"]:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            if matches:
                entities_found["campaigns"].extend(matches)
                team_scores["Marketing Team"] += 5.0
                print(f"   📊 Campaign entity detected → Marketing Team (+5.0)")
        
        # System detection
        for pattern in self._entity_patterns["systems"]:
            if re.search(pattern, message_lower, re.IGNORECASE):
                if "salesforce" in pattern or "crm" in pattern:
                    team_scores["Salesforce Team"] += 3.0
                    print(f"   💼 Salesforce system detected → Salesforce Team (+3.0)")
                elif "power bi" in pattern or "tableau" in pattern:
                    team_scores["Data Team"] += 3.0
                    print(f"   📈 BI system detected → Data Team (+3.0)")
        
        # Hardware detection
        for pattern in self._entity_patterns["hardware"]:
            if re.search(pattern, message_lower, re.IGNORECASE):
                team_scores["IT Team"] += 4.0
                print(f"   💻 Hardware entity detected → IT Team (+4.0)")
        
        # ==========================================
        # 4. FUZZY MATCHING (for typos)
        # ==========================================
        words = message_lower.split()
        for team, priority_keywords in self._team_keywords.items():
            all_keywords = (
                priority_keywords.get("high_priority", []) +
                priority_keywords.get("medium_priority", [])
            )
            
            for word in words:
                if len(word) > 4:  # Only match longer words
                    for keyword in all_keywords:
                        similarity = SequenceMatcher(None, word, keyword).ratio()
                        if similarity > 0.85:  # 85% similar
                            team_scores[team] += 0.5
                            print(f"   🔤 Fuzzy match '{word}' ≈ '{keyword}' → {team} (+0.5)")
        
        # ==========================================
        # 5. CALCULATE FINAL SCORES
        # ==========================================
        if not team_scores:
            # No matches found - use intelligent default
            default_team = self._determine_default_team(message_lower)
            print(f"   ⚠️ No matches - defaulting to {default_team}")
            return default_team, 0.5
        
        # Get best match
        best_team = max(team_scores, key=team_scores.get)
        max_score = team_scores[best_team]
        
        # Calculate confidence
        total_score = sum(team_scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.5
        
        # Apply minimum confidence threshold
        if confidence < 0.4:
            # If confidence too low, check second-best
            sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_teams) > 1:
                first_score = sorted_teams[0][1]
                second_score = sorted_teams[1][1]
                
                # If very close, use priority tiebreaker
                if abs(first_score - second_score) < 1.0:
                    first_priority = self._team_priority.get(sorted_teams[0][0], 0)
                    second_priority = self._team_priority.get(sorted_teams[1][0], 0)
                    
                    if second_priority > first_priority:
                        best_team = sorted_teams[1][0]
                        confidence = 0.6
                        print(f"   🔀 Priority tiebreaker: {best_team}")
        
        # Boost confidence if very clear
        if max_score >= 10.0:
            confidence = min(confidence * 1.2, 0.99)
        
        print(f"\n🎯 TEAM DETECTION RESULT:")
        print(f"   Team: {best_team}")
        print(f"   Score: {max_score:.1f}")
        print(f"   Confidence: {confidence:.2f}")
        
        return best_team, confidence
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _determine_default_team(self, message: str) -> str:
        """Intelligent default team selection"""
        
        # Check for question patterns
        if any(q in message for q in ["?", "how to", "what is", "who is", "where"]):
            return "Support Team"
        
        # Check for urgency
        if any(u in message for u in ["urgent", "critical", "asap", "emergency"]):
            return "Development Team"
        
        # Check for access/login
        if any(a in message for a in ["access", "login", "password", "permission"]):
            return "Admin Team"
        
        # Default to Support Team
        return "Support Team"
    
    def suggest_alternative_teams(
        self,
        message: str,
        top_n: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Get top N team suggestions with confidence scores
        
        Returns:
            List of (team_name, confidence) tuples
        """
        
        # Reuse detection logic but return multiple results
        message_lower = message.lower()
        team_scores: Dict[str, float] = defaultdict(float)
        
        # Score all teams
        for team, priority_keywords in self._team_keywords.items():
            for keyword in priority_keywords.get("high_priority", []):
                if keyword in message_lower:
                    team_scores[team] += 3.0
            
            for keyword in priority_keywords.get("medium_priority", []):
                if keyword in message_lower:
                    team_scores[team] += 2.0
        
        # Add pattern scores
        for team, patterns in self._contextual_patterns.items():
            for pattern, weight in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    team_scores[team] += weight
        
        # Sort and return top N
        sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate confidences
        total_score = sum(team_scores.values())
        results = []
        
        for team, score in sorted_teams[:top_n]:
            confidence = score / total_score if total_score > 0 else 0.5
            results.append((team, confidence))
        
        return results
    
    def get_team_jira_mapping(self) -> Dict[str, str]:
        """Get mapping of teams to Jira project keys"""
        return self._team_jira_mapping.copy()
    
    def get_all_teams(self) -> List[str]:
        """Get list of all available teams"""
        return list(self._team_keywords.keys())
    
    def get_team_description(self, team_name: str) -> str:
        """Get description of what a team handles"""
        
        descriptions = {
            "Salesforce Team": "Handles CRM, lead management, campaigns, and Salesforce integrations",
            "Marketing Team": "Manages campaigns, reports, KPIs, email marketing, and creative content",
            "Development Team": "Resolves API issues, bugs, deployments, and system errors",
            "Data Team": "Handles dashboards, reports, analytics, Power BI, and data exports",
            "IT Team": "Manages hardware, laptops, network, printers, and device issues",
            "Admin Team": "Handles access requests, permissions, user management, and login issues",
            "Support Team": "General support and inquiries"
        }
        
        return descriptions.get(team_name, "General support team")


# Global instance
team_detection_service = TeamDetectionService()