"""
Intent Analysis System for understanding user goals beyond literal requests.
Analyzes prompts to extract true intent, context, and implicit requirements.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class ComponentIntent(Enum):
    """High-level intents for component generation."""

    LANDING_PAGE = "landing_page"
    MARKETING = "marketing"
    DATA_DISPLAY = "data_display"
    USER_INPUT = "user_input"
    NAVIGATION = "navigation"
    AUTHENTICATION = "authentication"
    DASHBOARD = "dashboard"
    E_COMMERCE = "e_commerce"
    CONTENT = "content"
    UTILITY = "utility"


class UserGoal(Enum):
    """Ultimate goals the user is trying to achieve."""

    CONVERSION = "conversion"  # Drive user action
    INFORMATION = "information"  # Present data/content
    INTERACTION = "interaction"  # Enable user input
    NAVIGATION = "navigation"  # Help users navigate
    BRANDING = "branding"  # Establish brand presence
    FUNCTIONALITY = "functionality"  # Provide specific features


@dataclass
class IntentContext:
    """Extracted intent and context from user prompt."""

    primary_intent: ComponentIntent
    user_goals: List[UserGoal]
    target_audience: Optional[str] = None
    business_context: Optional[str] = None
    urgency_level: str = "normal"  # urgent, normal, exploratory
    complexity_level: str = "medium"  # simple, medium, complex
    key_features: List[str] = None
    implicit_requirements: List[str] = None
    suggested_clarifications: List[str] = None
    confidence_score: float = 0.0


class IntentAnalyzer:
    """Analyzes user prompts to understand true intent and context."""

    def __init__(self):
        self._initialize_patterns()
        self._initialize_intent_mappings()

    def _initialize_patterns(self):
        """Initialize regex patterns for intent detection."""
        self.patterns = {
            # Landing page patterns
            "landing": r"\b(landing\s*page|hero\s*section|above\s*the\s*fold|homepage)\b",
            "marketing": r"\b(marketing|promotional|campaign|conversion|cta|call\s*to\s*action)\b",
            # E-commerce patterns
            "pricing": r"\b(pricing|price|tier|plan|subscription|package)\b",
            "product": r"\b(product|item|catalog|shop|store|e-?commerce)\b",
            "checkout": r"\b(checkout|cart|payment|purchase|buy)\b",
            # Dashboard patterns
            "dashboard": r"\b(dashboard|admin|analytics|metrics|statistics)\b",
            "data_viz": r"\b(chart|graph|visualization|data\s*display|metrics)\b",
            # User interaction patterns
            "form": r"\b(form|input|field|submit|contact|feedback)\b",
            "auth": r"\b(login|signup|register|authentication|auth|sign\s*in)\b",
            # Navigation patterns
            "nav": r"\b(navigation|navbar|menu|header|sidebar)\b",
            "footer": r"\b(footer|bottom|copyright|links)\b",
            # Urgency indicators
            "urgent": r"\b(asap|urgent|immediately|quickly|fast|now)\b",
            "exploratory": r"\b(maybe|could|might|explore|experiment|try)\b",
        }

    def _initialize_intent_mappings(self):
        """Map keywords to intents and goals."""
        self.intent_mappings = {
            ComponentIntent.LANDING_PAGE: [
                "hero",
                "landing",
                "homepage",
                "above the fold",
                "first impression",
            ],
            ComponentIntent.MARKETING: [
                "conversion",
                "cta",
                "promotional",
                "campaign",
                "lead generation",
            ],
            ComponentIntent.E_COMMERCE: [
                "pricing",
                "product",
                "shop",
                "cart",
                "checkout",
                "payment",
            ],
            ComponentIntent.DASHBOARD: [
                "dashboard",
                "admin",
                "analytics",
                "metrics",
                "overview",
            ],
            ComponentIntent.DATA_DISPLAY: [
                "table",
                "list",
                "grid",
                "chart",
                "visualization",
                "data",
            ],
            ComponentIntent.USER_INPUT: [
                "form",
                "input",
                "survey",
                "feedback",
                "contact",
            ],
            ComponentIntent.AUTHENTICATION: [
                "login",
                "signup",
                "register",
                "auth",
                "sign in",
            ],
            ComponentIntent.NAVIGATION: [
                "nav",
                "menu",
                "header",
                "sidebar",
                "breadcrumb",
            ],
        }

        self.goal_mappings = {
            UserGoal.CONVERSION: [
                "convert",
                "cta",
                "action",
                "signup",
                "purchase",
                "subscribe",
            ],
            UserGoal.INFORMATION: [
                "display",
                "show",
                "present",
                "list",
                "overview",
                "summary",
            ],
            UserGoal.INTERACTION: [
                "input",
                "form",
                "submit",
                "interact",
                "engage",
                "feedback",
            ],
            UserGoal.BRANDING: [
                "brand",
                "identity",
                "impression",
                "professional",
                "modern",
            ],
        }

    def analyze_intent(
        self, prompt: str, project_context: Dict = None
    ) -> IntentContext:
        """Analyze user prompt to extract intent and context."""
        prompt_lower = prompt.lower()

        # Extract primary intent
        primary_intent = self._extract_primary_intent(prompt_lower)

        # Extract user goals
        user_goals = self._extract_user_goals(prompt_lower)

        # Extract implicit requirements
        implicit_requirements = self._extract_implicit_requirements(
            prompt_lower, primary_intent, project_context
        )

        # Analyze complexity
        complexity_level = self._analyze_complexity(prompt_lower)

        # Generate clarifying questions
        clarifications = self._generate_clarifications(
            primary_intent, prompt_lower, project_context
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            primary_intent, user_goals, prompt_lower
        )

        # Extract key features
        key_features = self._extract_key_features(prompt_lower, primary_intent)

        # Detect urgency
        urgency = self._detect_urgency(prompt_lower)

        # Infer business context
        business_context = self._infer_business_context(prompt_lower, primary_intent)

        return IntentContext(
            primary_intent=primary_intent,
            user_goals=user_goals,
            target_audience=self._infer_target_audience(prompt_lower),
            business_context=business_context,
            urgency_level=urgency,
            complexity_level=complexity_level,
            key_features=key_features,
            implicit_requirements=implicit_requirements,
            suggested_clarifications=clarifications,
            confidence_score=confidence,
        )

    def _extract_primary_intent(self, prompt: str) -> ComponentIntent:
        """Extract the primary intent from the prompt."""
        intent_scores = {}

        for intent, keywords in self.intent_mappings.items():
            score = sum(1 for keyword in keywords if keyword in prompt)
            if score > 0:
                intent_scores[intent] = score

        if intent_scores:
            return max(intent_scores, key=intent_scores.get)

        # Default based on common patterns
        if re.search(self.patterns["landing"], prompt):
            return ComponentIntent.LANDING_PAGE
        elif re.search(self.patterns["pricing"], prompt):
            return ComponentIntent.E_COMMERCE
        elif re.search(self.patterns["form"], prompt):
            return ComponentIntent.USER_INPUT

        return ComponentIntent.CONTENT  # Default

    def _extract_user_goals(self, prompt: str) -> List[UserGoal]:
        """Extract user goals from the prompt."""
        goals = []

        for goal, keywords in self.goal_mappings.items():
            if any(keyword in prompt for keyword in keywords):
                goals.append(goal)

        # Infer goals from intent if none explicitly found
        if not goals:
            if "pricing" in prompt or "buy" in prompt:
                goals.append(UserGoal.CONVERSION)
            elif "display" in prompt or "show" in prompt:
                goals.append(UserGoal.INFORMATION)
            elif "form" in prompt or "input" in prompt:
                goals.append(UserGoal.INTERACTION)

        return goals or [UserGoal.FUNCTIONALITY]

    def _extract_implicit_requirements(
        self, prompt: str, intent: ComponentIntent, context: Dict = None
    ) -> List[str]:
        """Extract requirements that aren't explicitly stated but are implied."""
        requirements = []

        # Intent-based implicit requirements
        if intent == ComponentIntent.E_COMMERCE:
            if "pricing" in prompt:
                requirements.extend(
                    [
                        "Clear pricing comparison",
                        "Trust indicators (testimonials, guarantees)",
                        "Mobile-optimized layout",
                        "Accessible CTAs",
                    ]
                )

        elif intent == ComponentIntent.LANDING_PAGE:
            requirements.extend(
                [
                    "Fast loading performance",
                    "SEO-friendly structure",
                    "Responsive design",
                    "Clear value proposition",
                ]
            )

        elif intent == ComponentIntent.DASHBOARD:
            requirements.extend(
                [
                    "Data visualization best practices",
                    "Real-time update capability",
                    "Export functionality",
                    "Filtering and sorting",
                ]
            )

        # Context-based requirements
        if context and context.get("is_saas"):
            requirements.append("SaaS design patterns")

        if context and context.get("has_authentication"):
            requirements.append("Authenticated state handling")

        return requirements

    def _analyze_complexity(self, prompt: str) -> str:
        """Analyze the complexity level of the request."""
        complexity_indicators = {
            "simple": ["basic", "simple", "quick", "minimal"],
            "complex": [
                "advanced",
                "complex",
                "sophisticated",
                "multiple",
                "integrated",
            ],
        }

        for level, indicators in complexity_indicators.items():
            if any(indicator in prompt for indicator in indicators):
                return level

        # Count features mentioned
        feature_count = len(re.findall(r"\b(with|including|and|plus)\b", prompt))
        if feature_count > 3:
            return "complex"
        elif feature_count > 1:
            return "medium"

        return "medium"  # Default

    def _generate_clarifications(
        self, intent: ComponentIntent, prompt: str, context: Dict = None
    ) -> List[str]:
        """Generate intelligent clarifying questions based on intent."""
        questions = []

        if intent == ComponentIntent.E_COMMERCE:
            if "pricing" in prompt:
                questions.extend(
                    [
                        "What's your pricing model (one-time, subscription, usage-based)?",
                        "Do you have existing pricing data or should I use placeholders?",
                        "What's your primary value proposition?",
                        "Should this integrate with a payment processor?",
                    ]
                )
            elif "product" in prompt:
                questions.extend(
                    [
                        "What type of products are you selling?",
                        "Do you need filtering and sorting capabilities?",
                        "Should this include a quick view feature?",
                        "What product information is most important to display?",
                    ]
                )

        elif intent == ComponentIntent.LANDING_PAGE:
            questions.extend(
                [
                    "What's your main call-to-action?",
                    "Who is your target audience?",
                    "Do you have brand assets (logo, images) to include?",
                    "What's the key message you want to convey?",
                ]
            )

        elif intent == ComponentIntent.DASHBOARD:
            questions.extend(
                [
                    "What metrics are most important to display?",
                    "Who will be using this dashboard?",
                    "Do you need real-time data updates?",
                    "Should users be able to customize the view?",
                ]
            )

        # Filter questions based on what's already in the prompt
        filtered_questions = []
        for question in questions:
            # Don't ask about things already specified
            key_words = re.findall(r"\b(\w+)\b", question.lower())
            if not any(word in prompt.lower() for word in key_words[:3]):
                filtered_questions.append(question)

        return filtered_questions[:3]  # Limit to top 3 most relevant

    def _calculate_confidence(
        self, intent: ComponentIntent, goals: List[UserGoal], prompt: str
    ) -> float:
        """Calculate confidence score for the intent analysis."""
        confidence = 0.5  # Base confidence

        # Increase confidence for clear intent signals
        intent_keywords = self.intent_mappings.get(intent, [])
        intent_matches = sum(1 for keyword in intent_keywords if keyword in prompt)
        confidence += min(0.3, intent_matches * 0.1)

        # Increase confidence for clear goals
        if goals:
            confidence += min(0.2, len(goals) * 0.1)

        # Decrease confidence for ambiguous prompts
        if len(prompt.split()) < 5:
            confidence -= 0.2

        return max(0.0, min(1.0, confidence))

    def _extract_key_features(self, prompt: str, intent: ComponentIntent) -> List[str]:
        """Extract key features mentioned or implied in the prompt."""
        features = []

        # Feature patterns
        feature_patterns = {
            "responsive": r"\b(responsive|mobile|tablet|desktop)\b",
            "animation": r"\b(animate|animation|transition|effect)\b",
            "gradient": r"\b(gradient|color\s*transition)\b",
            "grid": r"\b(grid|layout|columns|rows)\b",
            "carousel": r"\b(carousel|slider|slideshow)\b",
            "modal": r"\b(modal|popup|dialog|overlay)\b",
            "search": r"\b(search|filter|find)\b",
            "sort": r"\b(sort|order|arrange)\b",
        }

        for feature, pattern in feature_patterns.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                features.append(feature)

        # Intent-specific implicit features
        if intent == ComponentIntent.E_COMMERCE and "pricing" in prompt:
            features.extend(["comparison", "highlight-popular", "cta-buttons"])
        elif intent == ComponentIntent.DASHBOARD:
            features.extend(["data-visualization", "filters", "export"])

        return list(set(features))  # Remove duplicates

    def _detect_urgency(self, prompt: str) -> str:
        """Detect urgency level from the prompt."""
        if re.search(self.patterns["urgent"], prompt):
            return "urgent"
        elif re.search(self.patterns["exploratory"], prompt):
            return "exploratory"
        return "normal"

    def _infer_target_audience(self, prompt: str) -> Optional[str]:
        """Infer target audience from the prompt."""
        audience_patterns = {
            "enterprise": r"\b(enterprise|corporate|business|b2b)\b",
            "consumer": r"\b(consumer|customer|user|b2c)\b",
            "developer": r"\b(developer|technical|api|documentation)\b",
            "startup": r"\b(startup|saas|mvp|lean)\b",
        }

        for audience, pattern in audience_patterns.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                return audience

        return None

    def _infer_business_context(
        self, prompt: str, intent: ComponentIntent
    ) -> Optional[str]:
        """Infer business context from prompt and intent."""
        if intent == ComponentIntent.E_COMMERCE:
            if "subscription" in prompt:
                return "subscription_business"
            elif "marketplace" in prompt:
                return "marketplace"
            else:
                return "e_commerce"

        elif intent == ComponentIntent.DASHBOARD:
            if "analytics" in prompt:
                return "analytics_platform"
            elif "admin" in prompt:
                return "admin_panel"

        elif intent == ComponentIntent.LANDING_PAGE:
            if "saas" in prompt or "software" in prompt:
                return "saas_marketing"
            elif "agency" in prompt:
                return "agency_portfolio"

        return None

    def get_intent_summary(self, context: IntentContext) -> str:
        """Generate a human-readable summary of the intent analysis."""
        summary_parts = [
            f"Intent: {context.primary_intent.value.replace('_', ' ').title()}",
            f"Goals: {', '.join(g.value for g in context.user_goals)}",
            f"Complexity: {context.complexity_level}",
            f"Confidence: {context.confidence_score:.0%}",
        ]

        if context.target_audience:
            summary_parts.append(f"Audience: {context.target_audience}")

        if context.key_features:
            summary_parts.append(f"Features: {', '.join(context.key_features[:3])}")

        return " | ".join(summary_parts)
