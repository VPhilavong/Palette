"""
Generation Quality Learning System.
Learns from generation quality over time to continuously improve LLM performance
through feedback analysis, pattern recognition, and adaptive optimization.
"""

import json
import sqlite3
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union
import statistics
from collections import defaultdict, Counter

from ..errors.decorators import handle_errors


class FeedbackType(Enum):
    """Types of feedback for learning."""
    USER_RATING = "user_rating"  # Direct user rating (1-5 stars)
    USER_EDIT = "user_edit"      # User manually edited the generated code
    COMPILATION_ERROR = "compilation_error"  # Code failed to compile
    RUNTIME_ERROR = "runtime_error"        # Code had runtime errors
    LINT_VIOLATION = "lint_violation"      # Code quality issues
    ACCESSIBILITY_ISSUE = "accessibility_issue"  # A11y problems
    PERFORMANCE_ISSUE = "performance_issue"      # Performance problems
    DESIGN_INCONSISTENCY = "design_inconsistency"  # Design system violations
    POSITIVE_REUSE = "positive_reuse"      # Code was reused/copied by user
    TEST_FAILURE = "test_failure"          # Generated tests failed
    MANUAL_VALIDATION = "manual_validation"  # Manual quality assessment


class QualityDimension(Enum):
    """Dimensions of code quality to track."""
    FUNCTIONALITY = "functionality"
    DESIGN_CONSISTENCY = "design_consistency"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    USER_EXPERIENCE = "user_experience"
    CODE_STYLE = "code_style"


class LearningPattern(Enum):
    """Types of patterns the system can learn."""
    PROMPT_EFFECTIVENESS = "prompt_effectiveness"
    MODEL_PERFORMANCE = "model_performance"
    CONTEXT_IMPORTANCE = "context_importance"
    COMPONENT_COMPLEXITY = "component_complexity"
    USER_PREFERENCES = "user_preferences"
    ERROR_PATTERNS = "error_patterns"
    SUCCESS_PATTERNS = "success_patterns"


@dataclass
class QualityFeedback:
    """Feedback record for a generation."""
    generation_id: str
    feedback_type: FeedbackType
    dimension: QualityDimension
    score: float  # 0.0 to 1.0
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRecord:
    """Record of a code generation attempt."""
    generation_id: str
    prompt: str
    context: Dict[str, Any]
    generated_code: str
    model_used: str
    strategy_used: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    token_usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Quality scores (updated as feedback comes in)
    overall_quality: float = 0.0
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    feedback_count: int = 0


@dataclass
class LearningInsight:
    """An insight learned from quality patterns."""
    insight_type: LearningPattern
    description: str
    confidence: float
    supporting_evidence: List[str]
    actionable_recommendation: str
    impact_estimate: float  # Expected improvement
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QualityTrend:
    """Quality trend analysis over time."""
    dimension: QualityDimension
    trend_direction: str  # "improving", "declining", "stable"
    trend_strength: float  # How strong the trend is
    recent_average: float
    historical_average: float
    sample_size: int
    time_period: str


class GenerationQualityLearner:
    """
    System that learns from generation quality to improve future outputs.
    Uses feedback analysis, pattern recognition, and adaptive optimization.
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path.home() / ".palette" / "quality_learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database for persistent storage
        self.db_path = self.data_dir / "quality_learning.db"
        self._init_database()
        
        # In-memory caches for performance
        self.recent_generations: Dict[str, GenerationRecord] = {}
        self.quality_insights: List[LearningInsight] = []
        self.learned_patterns: Dict[str, Any] = {}
        
        # Learning configuration
        self.max_memory_records = 1000
        self.insight_confidence_threshold = 0.7
        self.learning_rate = 0.1
        
        # Load existing insights
        self._load_insights()
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generations (
                    generation_id TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    context TEXT NOT NULL,
                    generated_code TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    strategy_used TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    token_usage TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    overall_quality REAL DEFAULT 0.0,
                    dimension_scores TEXT DEFAULT '{}',
                    feedback_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generation_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    score REAL NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (generation_id) REFERENCES generations (generation_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    supporting_evidence TEXT NOT NULL,
                    actionable_recommendation TEXT NOT NULL,
                    impact_estimate REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    pattern_key TEXT PRIMARY KEY,
                    pattern_data TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def _load_insights(self):
        """Load existing insights from database."""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT insight_type, description, confidence, supporting_evidence,
                           actionable_recommendation, impact_estimate, timestamp
                    FROM learning_insights
                    WHERE confidence >= ?
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (self.insight_confidence_threshold,))
                
                for row in cursor.fetchall():
                    insight = LearningInsight(
                        insight_type=LearningPattern(row[0]),
                        description=row[1],
                        confidence=row[2],
                        supporting_evidence=json.loads(row[3]),
                        actionable_recommendation=row[4],
                        impact_estimate=row[5],
                        timestamp=datetime.fromisoformat(row[6])
                    )
                    self.quality_insights.append(insight)
                    
        except Exception as e:
            print(f"⚠️ Failed to load insights: {e}")
    
    @handle_errors(reraise=True)
    def record_generation(self, generation_record: GenerationRecord):
        """Record a new code generation attempt."""
        
        # Store in memory cache
        self.recent_generations[generation_record.generation_id] = generation_record
        
        # Limit memory usage
        if len(self.recent_generations) > self.max_memory_records:
            oldest_id = min(self.recent_generations.keys(), 
                          key=lambda x: self.recent_generations[x].timestamp)
            del self.recent_generations[oldest_id]
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO generations (
                    generation_id, prompt, context, generated_code, model_used,
                    strategy_used, execution_time, timestamp, token_usage, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                generation_record.generation_id,
                generation_record.prompt,
                json.dumps(generation_record.context),
                generation_record.generated_code,
                generation_record.model_used,
                generation_record.strategy_used,
                generation_record.execution_time,
                generation_record.timestamp.isoformat(),
                json.dumps(generation_record.token_usage),
                json.dumps(generation_record.metadata)
            ))
            conn.commit()
    
    @handle_errors(reraise=True)
    def record_feedback(self, feedback: QualityFeedback):
        """Record quality feedback for a generation."""
        
        # Store feedback in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO quality_feedback (
                    generation_id, feedback_type, dimension, score, description,
                    timestamp, user_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.generation_id,
                feedback.feedback_type.value,
                feedback.dimension.value,
                feedback.score,
                feedback.description,
                feedback.timestamp.isoformat(),
                feedback.user_id,
                json.dumps(feedback.metadata)
            ))
            
            # Update generation record quality scores
            self._update_generation_quality(feedback.generation_id)
            conn.commit()
        
        # Update in-memory record if present
        if feedback.generation_id in self.recent_generations:
            record = self.recent_generations[feedback.generation_id]
            self._update_record_quality(record, feedback)
        
        # Trigger learning analysis
        self._analyze_feedback_patterns(feedback)
    
    def _update_generation_quality(self, generation_id: str):
        """Update quality scores for a generation based on all feedback."""
        
        with sqlite3.connect(self.db_path) as conn:
            # Get all feedback for this generation
            cursor = conn.execute("""
                SELECT dimension, AVG(score) as avg_score, COUNT(*) as count
                FROM quality_feedback
                WHERE generation_id = ?
                GROUP BY dimension
            """, (generation_id,))
            
            dimension_scores = {}
            total_score = 0.0
            total_weight = 0.0
            
            for row in cursor.fetchall():
                dimension = row[0]
                avg_score = row[1]
                count = row[2]
                
                dimension_scores[dimension] = avg_score
                
                # Weight by feedback count (more feedback = more reliable)
                weight = min(count, 5) / 5.0  # Cap weight at 5 feedback items
                total_score += avg_score * weight
                total_weight += weight
            
            overall_quality = total_score / total_weight if total_weight > 0 else 0.0
            feedback_count = sum(row[2] for row in cursor.fetchall())
            
            # Update generation record
            conn.execute("""
                UPDATE generations
                SET overall_quality = ?, dimension_scores = ?, feedback_count = ?
                WHERE generation_id = ?
            """, (
                overall_quality,
                json.dumps(dimension_scores),
                feedback_count,
                generation_id
            ))
    
    def _update_record_quality(self, record: GenerationRecord, feedback: QualityFeedback):
        """Update in-memory record quality scores."""
        
        # Update dimension score
        dimension = feedback.dimension.value
        if dimension in record.dimension_scores:
            # Exponential moving average
            alpha = self.learning_rate
            record.dimension_scores[dimension] = (
                alpha * feedback.score + 
                (1 - alpha) * record.dimension_scores[dimension]
            )
        else:
            record.dimension_scores[dimension] = feedback.score
        
        # Update overall quality
        if record.dimension_scores:
            record.overall_quality = statistics.mean(record.dimension_scores.values())
        
        record.feedback_count += 1
    
    def _analyze_feedback_patterns(self, feedback: QualityFeedback):
        """Analyze feedback to identify learning patterns."""
        
        # Get generation record
        generation = self._get_generation_record(feedback.generation_id)
        if not generation:
            return
        
        # Analyze patterns based on feedback type
        if feedback.feedback_type == FeedbackType.USER_EDIT:
            self._analyze_user_edit_pattern(generation, feedback)
        elif feedback.feedback_type == FeedbackType.COMPILATION_ERROR:
            self._analyze_compilation_error_pattern(generation, feedback)
        elif feedback.feedback_type == FeedbackType.USER_RATING:
            self._analyze_user_rating_pattern(generation, feedback)
        elif feedback.feedback_type == FeedbackType.POSITIVE_REUSE:
            self._analyze_positive_reuse_pattern(generation, feedback)
    
    def _analyze_user_edit_pattern(self, generation: GenerationRecord, feedback: QualityFeedback):
        """Analyze patterns in user edits to learn preferences."""
        
        # Extract edit patterns from metadata
        edit_info = feedback.metadata.get("edit_info", {})
        lines_changed = edit_info.get("lines_changed", 0)
        change_type = edit_info.get("change_type", "unknown")
        
        # Learn from significant edits
        if lines_changed > 5:  # Significant edit
            pattern_key = f"user_edit_{change_type}_{generation.model_used}"
            self._update_learned_pattern(pattern_key, {
                "model": generation.model_used,
                "change_type": change_type,
                "prompt_keywords": self._extract_keywords(generation.prompt),
                "context_features": self._extract_context_features(generation.context),
                "frequency": 1
            })
    
    def _analyze_compilation_error_pattern(self, generation: GenerationRecord, feedback: QualityFeedback):
        """Analyze compilation error patterns."""
        
        error_type = feedback.metadata.get("error_type", "unknown")
        error_message = feedback.description
        
        pattern_key = f"compilation_error_{error_type}_{generation.model_used}"
        self._update_learned_pattern(pattern_key, {
            "model": generation.model_used,
            "error_type": error_type,
            "error_message": error_message,
            "prompt_keywords": self._extract_keywords(generation.prompt),
            "strategy": generation.strategy_used,
            "frequency": 1
        })
    
    def _analyze_user_rating_pattern(self, generation: GenerationRecord, feedback: QualityFeedback):
        """Analyze user rating patterns."""
        
        if feedback.score >= 0.8:  # High rating
            pattern_key = f"high_rating_{generation.model_used}_{generation.strategy_used}"
            self._update_learned_pattern(pattern_key, {
                "model": generation.model_used,
                "strategy": generation.strategy_used,
                "prompt_keywords": self._extract_keywords(generation.prompt),
                "context_features": self._extract_context_features(generation.context),
                "score": feedback.score,
                "frequency": 1
            })
    
    def _analyze_positive_reuse_pattern(self, generation: GenerationRecord, feedback: QualityFeedback):
        """Analyze patterns in positively reused code."""
        
        pattern_key = f"positive_reuse_{generation.model_used}"
        self._update_learned_pattern(pattern_key, {
            "model": generation.model_used,
            "strategy": generation.strategy_used,
            "prompt_keywords": self._extract_keywords(generation.prompt),
            "code_patterns": self._extract_code_patterns(generation.generated_code),
            "reuse_count": feedback.metadata.get("reuse_count", 1),
            "frequency": 1
        })
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        
        # Simple keyword extraction
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = text.lower().split()
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        
        # Return most common keywords
        counter = Counter(keywords)
        return [word for word, count in counter.most_common(10)]
    
    def _extract_context_features(self, context: Dict[str, Any]) -> List[str]:
        """Extract important features from generation context."""
        
        features = []
        
        if "framework" in context:
            features.append(f"framework_{context['framework']}")
        
        if "styling_approach" in context:
            features.append(f"styling_{context['styling_approach']}")
        
        if "component_type" in context:
            features.append(f"component_{context['component_type']}")
        
        if "design_token_analysis" in context:
            tokens = context["design_token_analysis"]
            if tokens.get("specific_recommendations"):
                features.append("has_design_tokens")
        
        if "asset_recommendations" in context:
            assets = context["asset_recommendations"]
            if assets.get("recommended_assets"):
                features.append("has_asset_recommendations")
        
        return features
    
    def _extract_code_patterns(self, code: str) -> List[str]:
        """Extract important code patterns."""
        
        patterns = []
        
        # React patterns
        if "useState" in code:
            patterns.append("uses_state")
        if "useEffect" in code:
            patterns.append("uses_effect")
        if "interface" in code:
            patterns.append("has_interface")
        if "type " in code:
            patterns.append("has_types")
        
        # Accessibility patterns
        if "aria-" in code:
            patterns.append("has_aria")
        if "role=" in code:
            patterns.append("has_roles")
        
        # Styling patterns
        if "className" in code:
            patterns.append("uses_classnames")
        if "styled" in code:
            patterns.append("uses_styled_components")
        
        return patterns
    
    def _update_learned_pattern(self, pattern_key: str, pattern_data: Dict[str, Any]):
        """Update a learned pattern with new data."""
        
        if pattern_key in self.learned_patterns:
            existing = self.learned_patterns[pattern_key]
            
            # Update frequency
            existing["frequency"] = existing.get("frequency", 0) + pattern_data.get("frequency", 1)
            
            # Merge other data
            for key, value in pattern_data.items():
                if key != "frequency":
                    if isinstance(value, (int, float)):
                        # Average numeric values
                        existing[key] = (existing.get(key, 0) + value) / 2
                    elif isinstance(value, list):
                        # Combine lists
                        existing[key] = list(set(existing.get(key, []) + value))
                    else:
                        # Use new value
                        existing[key] = value
        else:
            self.learned_patterns[pattern_key] = pattern_data
        
        # Persist to database
        self._persist_learned_pattern(pattern_key, self.learned_patterns[pattern_key])
    
    def _persist_learned_pattern(self, pattern_key: str, pattern_data: Dict[str, Any]):
        """Persist learned pattern to database."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO learned_patterns (pattern_key, pattern_data, last_updated)
                VALUES (?, ?, ?)
            """, (
                pattern_key,
                json.dumps(pattern_data),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def _get_generation_record(self, generation_id: str) -> Optional[GenerationRecord]:
        """Get generation record by ID."""
        
        # Check memory first
        if generation_id in self.recent_generations:
            return self.recent_generations[generation_id]
        
        # Check database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM generations WHERE generation_id = ?
            """, (generation_id,))
            
            row = cursor.fetchone()
            if row:
                return GenerationRecord(
                    generation_id=row[0],
                    prompt=row[1],
                    context=json.loads(row[2]),
                    generated_code=row[3],
                    model_used=row[4],
                    strategy_used=row[5],
                    execution_time=row[6],
                    timestamp=datetime.fromisoformat(row[7]),
                    token_usage=json.loads(row[8] or "{}"),
                    metadata=json.loads(row[9] or "{}"),
                    overall_quality=row[10],
                    dimension_scores=json.loads(row[11] or "{}"),
                    feedback_count=row[12]
                )
        
        return None
    
    def generate_insights(self, force_analysis: bool = False) -> List[LearningInsight]:
        """Generate new learning insights from patterns."""
        
        print("🧠 Analyzing patterns to generate learning insights...")
        
        new_insights = []
        
        # Analyze model performance patterns
        model_insights = self._analyze_model_performance_patterns()
        new_insights.extend(model_insights)
        
        # Analyze prompt effectiveness patterns
        prompt_insights = self._analyze_prompt_effectiveness_patterns()
        new_insights.extend(prompt_insights)
        
        # Analyze error patterns
        error_insights = self._analyze_error_patterns()
        new_insights.extend(error_insights)
        
        # Analyze user preference patterns
        preference_insights = self._analyze_user_preference_patterns()
        new_insights.extend(preference_insights)
        
        # Filter by confidence threshold
        high_confidence_insights = [
            insight for insight in new_insights 
            if insight.confidence >= self.insight_confidence_threshold
        ]
        
        # Store new insights
        for insight in high_confidence_insights:
            self._persist_insight(insight)
            self.quality_insights.append(insight)
        
        print(f"✨ Generated {len(high_confidence_insights)} new insights")
        
        return high_confidence_insights
    
    def _analyze_model_performance_patterns(self) -> List[LearningInsight]:
        """Analyze patterns in model performance."""
        
        insights = []
        
        # Get model performance data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT model_used, AVG(overall_quality) as avg_quality, COUNT(*) as count
                FROM generations
                WHERE feedback_count > 0
                GROUP BY model_used
                HAVING count >= 5
            """)
            
            model_performance = cursor.fetchall()
        
        if len(model_performance) > 1:
            # Find best performing model
            best_model = max(model_performance, key=lambda x: x[1])
            worst_model = min(model_performance, key=lambda x: x[1])
            
            performance_gap = best_model[1] - worst_model[1]
            
            if performance_gap > 0.2:  # Significant difference
                insight = LearningInsight(
                    insight_type=LearningPattern.MODEL_PERFORMANCE,
                    description=f"Model {best_model[0]} consistently outperforms {worst_model[0]} by {performance_gap:.2f} points",
                    confidence=0.8,
                    supporting_evidence=[
                        f"{best_model[0]}: {best_model[1]:.2f} average quality ({best_model[2]} samples)",
                        f"{worst_model[0]}: {worst_model[1]:.2f} average quality ({worst_model[2]} samples)"
                    ],
                    actionable_recommendation=f"Prefer {best_model[0]} for similar tasks to improve generation quality",
                    impact_estimate=performance_gap
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_prompt_effectiveness_patterns(self) -> List[LearningInsight]:
        """Analyze patterns in prompt effectiveness."""
        
        insights = []
        
        # Analyze prompts with high vs low quality
        high_quality_patterns = self._get_patterns_for_quality_range(0.8, 1.0)
        low_quality_patterns = self._get_patterns_for_quality_range(0.0, 0.4)
        
        # Find keywords that correlate with high quality
        high_quality_keywords = self._extract_common_keywords(high_quality_patterns)
        low_quality_keywords = self._extract_common_keywords(low_quality_patterns)
        
        # Find keywords unique to high quality
        effective_keywords = [
            kw for kw in high_quality_keywords 
            if kw not in low_quality_keywords and high_quality_keywords[kw] >= 3
        ]
        
        if effective_keywords:
            insight = LearningInsight(
                insight_type=LearningPattern.PROMPT_EFFECTIVENESS,
                description=f"Prompts containing {', '.join(effective_keywords[:3])} tend to produce higher quality results",
                confidence=0.75,
                supporting_evidence=[f"Keyword '{kw}' appears in {count} high-quality generations" 
                                   for kw, count in Counter(effective_keywords).most_common(3)],
                actionable_recommendation=f"Include keywords like {', '.join(effective_keywords[:3])} in prompts for better results",
                impact_estimate=0.15
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_error_patterns(self) -> List[LearningInsight]:
        """Analyze patterns in errors to prevent them."""
        
        insights = []
        
        # Get common error patterns
        error_patterns = {}
        for pattern_key, pattern_data in self.learned_patterns.items():
            if "error" in pattern_key and pattern_data.get("frequency", 0) >= 3:
                error_patterns[pattern_key] = pattern_data
        
        if error_patterns:
            most_common_error = max(error_patterns.items(), key=lambda x: x[1]["frequency"])
            error_key, error_data = most_common_error
            
            insight = LearningInsight(
                insight_type=LearningPattern.ERROR_PATTERNS,
                description=f"Common error pattern: {error_data.get('error_type', 'unknown')} with {error_data['model']}",
                confidence=0.8,
                supporting_evidence=[
                    f"Occurred {error_data['frequency']} times",
                    f"Model: {error_data['model']}",
                    f"Common context: {error_data.get('prompt_keywords', [])}"
                ],
                actionable_recommendation=f"Avoid using {error_data['model']} for prompts containing {error_data.get('prompt_keywords', [])}",
                impact_estimate=0.3
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_user_preference_patterns(self) -> List[LearningInsight]:
        """Analyze patterns in user preferences."""
        
        insights = []
        
        # Get high-rating patterns
        high_rating_patterns = {}
        for pattern_key, pattern_data in self.learned_patterns.items():
            if "high_rating" in pattern_key and pattern_data.get("frequency", 0) >= 3:
                high_rating_patterns[pattern_key] = pattern_data
        
        if high_rating_patterns:
            # Find most preferred combination
            best_pattern = max(high_rating_patterns.items(), key=lambda x: x[1]["score"])
            pattern_key, pattern_data = best_pattern
            
            insight = LearningInsight(
                insight_type=LearningPattern.USER_PREFERENCES,
                description=f"Users prefer {pattern_data['model']} with {pattern_data['strategy']} strategy",
                confidence=0.85,
                supporting_evidence=[
                    f"Average rating: {pattern_data['score']:.2f}",
                    f"Frequency: {pattern_data['frequency']} times",
                    f"Context features: {pattern_data.get('context_features', [])}"
                ],
                actionable_recommendation=f"Use {pattern_data['model']} with {pattern_data['strategy']} for similar contexts",
                impact_estimate=0.2
            )
            insights.append(insight)
        
        return insights
    
    def _get_patterns_for_quality_range(self, min_quality: float, max_quality: float) -> List[GenerationRecord]:
        """Get generation records within a quality range."""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM generations
                WHERE overall_quality >= ? AND overall_quality <= ? AND feedback_count > 0
            """, (min_quality, max_quality))
            
            records = []
            for row in cursor.fetchall():
                record = GenerationRecord(
                    generation_id=row[0],
                    prompt=row[1],
                    context=json.loads(row[2]),
                    generated_code=row[3],
                    model_used=row[4],
                    strategy_used=row[5],
                    execution_time=row[6],
                    timestamp=datetime.fromisoformat(row[7]),
                    overall_quality=row[10],
                    feedback_count=row[12]
                )
                records.append(record)
            
            return records
    
    def _extract_common_keywords(self, records: List[GenerationRecord]) -> Counter:
        """Extract common keywords from generation records."""
        
        all_keywords = []
        for record in records:
            keywords = self._extract_keywords(record.prompt)
            all_keywords.extend(keywords)
        
        return Counter(all_keywords)
    
    def _persist_insight(self, insight: LearningInsight):
        """Persist insight to database."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO learning_insights (
                    insight_type, description, confidence, supporting_evidence,
                    actionable_recommendation, impact_estimate, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                insight.insight_type.value,
                insight.description,
                insight.confidence,
                json.dumps(insight.supporting_evidence),
                insight.actionable_recommendation,
                insight.impact_estimate,
                insight.timestamp.isoformat()
            ))
            conn.commit()
    
    def get_quality_trends(self, days: int = 30) -> List[QualityTrend]:
        """Analyze quality trends over time."""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        trends = []
        
        for dimension in QualityDimension:
            trend = self._analyze_dimension_trend(dimension, cutoff_date)
            if trend:
                trends.append(trend)
        
        return trends
    
    def _analyze_dimension_trend(self, dimension: QualityDimension, cutoff_date: datetime) -> Optional[QualityTrend]:
        """Analyze trend for a specific quality dimension."""
        
        with sqlite3.connect(self.db_path) as conn:
            # Get recent scores
            cursor = conn.execute("""
                SELECT qf.score, g.timestamp
                FROM quality_feedback qf
                JOIN generations g ON qf.generation_id = g.generation_id
                WHERE qf.dimension = ? AND g.timestamp >= ?
                ORDER BY g.timestamp
            """, (dimension.value, cutoff_date.isoformat()))
            
            scores_and_dates = cursor.fetchall()
        
        if len(scores_and_dates) < 5:  # Need minimum data
            return None
        
        scores = [row[0] for row in scores_and_dates]
        recent_scores = scores[-10:]  # Last 10 scores
        historical_scores = scores[:-10] if len(scores) > 10 else scores[:5]
        
        recent_avg = statistics.mean(recent_scores)
        historical_avg = statistics.mean(historical_scores)
        
        # Determine trend
        diff = recent_avg - historical_avg
        if abs(diff) < 0.05:
            trend_direction = "stable"
            trend_strength = 0.0
        elif diff > 0:
            trend_direction = "improving"
            trend_strength = min(diff / 0.5, 1.0)  # Normalize to 0-1
        else:
            trend_direction = "declining"
            trend_strength = min(abs(diff) / 0.5, 1.0)
        
        return QualityTrend(
            dimension=dimension,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            recent_average=recent_avg,
            historical_average=historical_avg,
            sample_size=len(scores),
            time_period=f"{len(scores_and_dates)} samples over {(datetime.now() - cutoff_date).days} days"
        )
    
    def get_recommendations_for_context(self, context: Dict[str, Any]) -> List[str]:
        """Get personalized recommendations based on learned patterns."""
        
        recommendations = []
        context_features = self._extract_context_features(context)
        
        # Check insights for relevant recommendations
        for insight in self.quality_insights:
            if insight.impact_estimate > 0.1:  # Significant impact
                # Check if insight is relevant to current context
                if self._is_insight_relevant(insight, context_features):
                    recommendations.append(insight.actionable_recommendation)
        
        # Check learned patterns
        relevant_patterns = self._find_relevant_patterns(context_features)
        for pattern_key, pattern_data in relevant_patterns:
            if pattern_data.get("frequency", 0) >= 3:
                if "high_rating" in pattern_key:
                    recommendations.append(
                        f"Use {pattern_data['model']} with {pattern_data['strategy']} strategy "
                        f"(has {pattern_data['frequency']} positive examples)"
                    )
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _is_insight_relevant(self, insight: LearningInsight, context_features: List[str]) -> bool:
        """Check if an insight is relevant to the current context."""
        
        # Simple relevance checking - could be more sophisticated
        insight_text = insight.description.lower()
        for feature in context_features:
            if feature.lower() in insight_text:
                return True
        
        return False
    
    def _find_relevant_patterns(self, context_features: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
        """Find learned patterns relevant to the current context."""
        
        relevant = []
        for pattern_key, pattern_data in self.learned_patterns.items():
            pattern_features = pattern_data.get("context_features", [])
            
            # Check for feature overlap
            overlap = set(context_features) & set(pattern_features)
            if overlap or any(feature in pattern_key for feature in context_features):
                relevant.append((pattern_key, pattern_data))
        
        return relevant
    
    def export_learning_analysis(self) -> Dict[str, Any]:
        """Export comprehensive learning analysis."""
        
        return {
            "total_generations": len(self.recent_generations),
            "total_insights": len(self.quality_insights),
            "learned_patterns": len(self.learned_patterns),
            "quality_trends": [asdict(trend) for trend in self.get_quality_trends()],
            "top_insights": [
                {
                    "type": insight.insight_type.value,
                    "description": insight.description,
                    "confidence": insight.confidence,
                    "impact": insight.impact_estimate
                }
                for insight in sorted(self.quality_insights, key=lambda x: x.confidence, reverse=True)[:10]
            ],
            "model_preferences": self._get_model_preference_summary(),
            "error_frequency": self._get_error_frequency_summary()
        }
    
    def _get_model_preference_summary(self) -> Dict[str, float]:
        """Get summary of model preferences from high-rating patterns."""
        
        model_scores = defaultdict(list)
        
        for pattern_key, pattern_data in self.learned_patterns.items():
            if "high_rating" in pattern_key:
                model = pattern_data.get("model")
                score = pattern_data.get("score", 0.0)
                frequency = pattern_data.get("frequency", 1)
                
                if model:
                    # Weight by frequency
                    weighted_score = score * frequency
                    model_scores[model].append(weighted_score)
        
        # Calculate averages
        return {
            model: statistics.mean(scores)
            for model, scores in model_scores.items()
        }
    
    def _get_error_frequency_summary(self) -> Dict[str, int]:
        """Get summary of error frequencies."""
        
        error_counts = defaultdict(int)
        
        for pattern_key, pattern_data in self.learned_patterns.items():
            if "error" in pattern_key:
                error_type = pattern_data.get("error_type", "unknown")
                frequency = pattern_data.get("frequency", 1)
                error_counts[error_type] += frequency
        
        return dict(error_counts)


# Global instance
_quality_learner_instance = None

def get_quality_learner(data_dir: str = None) -> GenerationQualityLearner:
    """Get the global quality learner instance."""
    global _quality_learner_instance
    if _quality_learner_instance is None:
        _quality_learner_instance = GenerationQualityLearner(data_dir)
    return _quality_learner_instance