"""
Format Detector for TeXFlow.

Intelligently detects the optimal document format based on content analysis
and user intent, removing the need for users to understand technical details.
"""

import re
from typing import Dict, List, Optional, Tuple, Any


class FormatDetector:
    """Detects optimal document format based on content and intent."""
    
    def __init__(self):
        """Initialize format detection rules."""
        self.format_rules = self._initialize_rules()
        
    def detect(self, content: str, intent: Optional[str] = None, 
               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect the optimal format for document content.
        
        Args:
            content: Document content to analyze
            intent: User's stated intent (e.g., "write a paper", "quick note")
            context: Additional context (e.g., project type, previous formats)
            
        Returns:
            Dictionary with format recommendation and reasoning
        """
        scores = {
            "markdown": 0,
            "latex": 0
        }
        
        reasons = {
            "markdown": [],
            "latex": []
        }
        
        # Analyze intent
        if intent:
            intent_analysis = self._analyze_intent(intent)
            scores[intent_analysis["suggested_format"]] += intent_analysis["weight"]
            reasons[intent_analysis["suggested_format"]].append(intent_analysis["reason"])
        
        # Analyze content
        content_analysis = self._analyze_content(content)
        for format_type, score in content_analysis["scores"].items():
            scores[format_type] += score
            if content_analysis["reasons"].get(format_type):
                reasons[format_type].extend(content_analysis["reasons"][format_type])
        
        # Consider context
        if context:
            context_analysis = self._analyze_context(context)
            scores[context_analysis["suggested_format"]] += context_analysis["weight"]
            if context_analysis.get("reason"):
                reasons[context_analysis["suggested_format"]].append(context_analysis["reason"])
        
        # Determine winner
        recommended_format = "markdown" if scores["markdown"] >= scores["latex"] else "latex"
        
        # Check if escalation is needed
        escalation_triggers = self._check_escalation_triggers(content, recommended_format)
        
        return {
            "format": recommended_format,
            "confidence": self._calculate_confidence(scores),
            "scores": scores,
            "reasons": reasons[recommended_format],
            "alternative_format": "latex" if recommended_format == "markdown" else "markdown",
            "escalation_suggested": bool(escalation_triggers),
            "escalation_triggers": escalation_triggers
        }
    
    def _initialize_rules(self) -> Dict[str, Any]:
        """Initialize format detection rules."""
        return {
            "intent_keywords": {
                "latex": {
                    "keywords": ["paper", "thesis", "dissertation", "academic", "scientific", 
                                "journal", "article", "publication", "research"],
                    "weight": 10
                },
                "markdown": {
                    "keywords": ["note", "quick", "simple", "draft", "todo", "list", 
                                "readme", "documentation", "blog"],
                    "weight": 8
                }
            },
            "content_patterns": {
                "latex": {
                    "strong_indicators": [
                        (r'\\documentclass', 20),
                        (r'\\begin\{document\}', 20),
                        (r'\\usepackage', 15),
                        (r'\\cite\{', 10),
                        (r'\\ref\{', 10),
                        (r'\\label\{', 8)
                    ],
                    "math_indicators": [
                        (r'\$\$[^$]+\$\$', 8),  # Display math
                        (r'\$[^$]+\$', 5),      # Inline math
                        (r'\\\\[([]', 8),        # Math delimiters
                        (r'\\int', 5),
                        (r'\\sum', 5),
                        (r'\\frac\{', 5),
                        (r'\\sqrt\{', 5)
                    ],
                    "structure_indicators": [
                        (r'\\chapter\{', 8),
                        (r'\\section\{', 5),
                        (r'\\subsection\{', 3),
                        (r'\\bibliography', 10)
                    ]
                },
                "markdown": {
                    "indicators": [
                        (r'^#+\s', 3),          # Headers
                        (r'^\*\s', 2),          # Lists
                        (r'^\d+\.\s', 2),       # Numbered lists
                        (r'\[.*\]\(.*\)', 2),   # Links
                        (r'```', 3),            # Code blocks
                        (r'^\>\s', 2)           # Quotes
                    ]
                }
            }
        }
    
    def _analyze_intent(self, intent: str) -> Dict[str, Any]:
        """Analyze user intent for format hints."""
        intent_lower = intent.lower()
        
        # Check LaTeX intent keywords
        latex_score = sum(
            self.format_rules["intent_keywords"]["latex"]["weight"]
            for keyword in self.format_rules["intent_keywords"]["latex"]["keywords"]
            if keyword in intent_lower
        )
        
        # Check Markdown intent keywords
        markdown_score = sum(
            self.format_rules["intent_keywords"]["markdown"]["weight"]
            for keyword in self.format_rules["intent_keywords"]["markdown"]["keywords"]
            if keyword in intent_lower
        )
        
        if latex_score > markdown_score:
            return {
                "suggested_format": "latex",
                "weight": latex_score,
                "reason": f"Intent suggests academic/formal document: '{intent}'"
            }
        else:
            return {
                "suggested_format": "markdown",
                "weight": markdown_score or 5,  # Default weight for markdown
                "reason": f"Intent suggests simple document: '{intent}'"
            }
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content for format indicators."""
        scores = {"markdown": 0, "latex": 0}
        reasons = {"markdown": [], "latex": []}
        
        # Check LaTeX patterns
        for pattern_type, patterns in self.format_rules["content_patterns"]["latex"].items():
            for pattern, weight in patterns:
                matches = len(re.findall(pattern, content, re.MULTILINE))
                if matches:
                    scores["latex"] += weight * min(matches, 3)  # Cap at 3 matches
                    if pattern_type == "strong_indicators":
                        reasons["latex"].append("Contains LaTeX commands")
                    elif pattern_type == "math_indicators":
                        reasons["latex"].append("Contains mathematical expressions")
                    elif pattern_type == "structure_indicators":
                        reasons["latex"].append("Uses LaTeX document structure")
        
        # Check Markdown patterns
        for pattern, weight in self.format_rules["content_patterns"]["markdown"]["indicators"]:
            matches = len(re.findall(pattern, content, re.MULTILINE))
            if matches:
                scores["markdown"] += weight * min(matches, 5)  # Cap at 5 matches
        
        if scores["markdown"] > 0 and not reasons["markdown"]:
            reasons["markdown"].append("Uses markdown formatting")
        
        # Default to markdown if no strong indicators
        if scores["latex"] == 0 and scores["markdown"] == 0:
            scores["markdown"] = 5
            reasons["markdown"].append("Simple text content")
        
        return {
            "scores": scores,
            "reasons": reasons
        }
    
    def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context for format preferences."""
        # Check project type
        project_info = context.get("project_info", {})
        if "thesis" in str(project_info).lower() or "paper" in str(project_info).lower():
            return {
                "suggested_format": "latex",
                "weight": 5,
                "reason": "Project type suggests formal document"
            }
        
        # Check previous format usage
        last_format = context.get("last_format")
        if last_format:
            return {
                "suggested_format": last_format,
                "weight": 3,
                "reason": f"Continuing with previously used format: {last_format}"
            }
        
        return {
            "suggested_format": "markdown",
            "weight": 0
        }
    
    def _check_escalation_triggers(self, content: str, current_format: str) -> List[str]:
        """Check if content has features that suggest format escalation."""
        if current_format == "latex":
            return []  # Already at highest capability
        
        triggers = []
        content_lower = content.lower()
        
        # Check for features that markdown struggles with
        escalation_patterns = {
            "complex_math": ["equation", "integral", "derivative", "matrix", "theorem"],
            "citations": ["cite", "bibliography", "references", "citation"],
            "precise_layout": ["exact spacing", "precise margins", "page layout"],
            "advanced_tables": ["multicolumn", "multirow", "complex table"],
            "cross_references": ["see figure", "see table", "see equation", "as shown in"]
        }
        
        for trigger_type, patterns in escalation_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                triggers.append(trigger_type)
        
        return triggers
    
    def _calculate_confidence(self, scores: Dict[str, float]) -> str:
        """Calculate confidence level of format detection."""
        total = sum(scores.values())
        if total == 0:
            return "low"
        
        max_score = max(scores.values())
        ratio = max_score / total if total > 0 else 0
        
        if ratio > 0.8:
            return "high"
        elif ratio > 0.6:
            return "medium"
        else:
            return "low"
    
    def suggest_escalation(self, current_format: str, triggers: List[str]) -> Dict[str, Any]:
        """Suggest format escalation based on triggers."""
        if not triggers or current_format == "latex":
            return {"escalate": False}
        
        suggestions = {
            "complex_math": "LaTeX provides professional mathematical typesetting",
            "citations": "LaTeX has built-in bibliography management with BibTeX",
            "precise_layout": "LaTeX offers precise control over document layout",
            "advanced_tables": "LaTeX supports complex table structures",
            "cross_references": "LaTeX automatically manages numbered references"
        }
        
        benefits = [suggestions.get(trigger, "") for trigger in triggers if trigger in suggestions]
        
        return {
            "escalate": True,
            "from_format": current_format,
            "to_format": "latex",
            "triggers": triggers,
            "benefits": benefits,
            "message": f"Your document uses {', '.join(triggers)} which would benefit from LaTeX"
        }