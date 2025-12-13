"""
AI Chess Advisor service using OpenAI GPT for personalized coaching recommendations.
Milestone 9: AI-Powered Chess Advisor
"""
import json
import logging
from typing import Dict, List, Optional
import openai

logger = logging.getLogger(__name__)


class ChessAdvisorService:
    """Service for generating AI-powered chess coaching advice."""
    
    SYSTEM_PROMPT = """
You are an expert chess coach analyzing a player's performance data. Your goal is to provide 
concise, actionable advice to help them improve their chess skills.

Based on the provided statistics, generate:
1. Section-specific recommendations (up to 7 suggestions, one per relevant section)
2. One overall recommendation that ties everything together

Format your response as bullet points. Each suggestion should:
- Be specific and actionable
- Reference concrete data from the analysis
- Provide clear next steps for improvement
- Be concise (1-2 sentences max)

Focus on the most impactful areas for improvement. Prioritize:
1. Patterns with clear negative impact (e.g., high timeout losses)
2. Significant performance gaps (e.g., 20%+ difference between time periods)
3. Mistake patterns that repeat across games
4. Areas where small changes yield big results

Avoid:
- Generic advice ("study more tactics")
- Obvious statements ("you lose when you blunder")
- Overwhelming the player with too many suggestions

Tone: Encouraging but honest, like a supportive coach.
"""
    
    USER_PROMPT_TEMPLATE = """
Analyze this chess player's performance and provide coaching recommendations:

{summary_data_json}

Provide recommendations in this format:

**Section-Specific Suggestions:**
- [Suggestion 1 based on relevant section]
- [Suggestion 2 based on relevant section]
- ... (up to 7 suggestions)

**Overall Recommendation:**
- [One key overarching advice that synthesizes all insights]
"""
    
    def __init__(self, api_key: str, model: str = 'gpt-4o-mini', 
                 max_tokens: int = 500, temperature: float = 0.7):
        """
        Initialize AI advisor service.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini for cost efficiency)
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0-1)
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        if self.api_key:
            openai.api_key = self.api_key
    
    def _prepare_summary_data(self, analysis_results: Dict, username: str, 
                              date_range: str) -> Dict:
        """
        Prepare summary data from analysis results for AI processing.
        
        Args:
            analysis_results: Complete analysis results from AnalyticsService
            username: Player's username
            date_range: Date range string
            
        Returns:
            Summarized data structure
        """
        sections = analysis_results.get('sections', {})
        
        # Overall performance
        overall = sections.get('overall_performance', {})
        
        # Color performance
        color_perf = sections.get('color_performance', {})
        white_stats = color_perf.get('white', {})
        black_stats = color_perf.get('black', {})
        
        # Terminations
        term_wins = sections.get('termination_wins', {})
        term_losses = sections.get('termination_losses', {})
        
        # Openings
        openings = sections.get('opening_performance', {})
        
        # Opponent strength
        opponent = sections.get('opponent_strength', {})
        
        # Time of day
        time_perf = sections.get('time_of_day', {})
        
        # Mistake analysis (if available)
        mistake_analysis = sections.get('mistake_analysis', {})
        
        # Build summary
        summary = {
            'username': username,
            'date_range': date_range,
            'total_games': analysis_results.get('total_games', 0),
            'overall_stats': {
                'win_rate': overall.get('win_rate', 0),
                'rating_change': overall.get('rating_change', 0),
                'rating_trend': overall.get('rating_trend', 'stable')
            },
            'color_performance': {
                'white_win_rate': white_stats.get('win_rate', 0),
                'black_win_rate': black_stats.get('win_rate', 0),
                'stronger_color': 'white' if white_stats.get('win_rate', 0) > black_stats.get('win_rate', 0) else 'black'
            },
            'termination_patterns': {
                'most_common_win_method': self._get_top_termination(term_wins.get('breakdown', {})),
                'most_common_loss_method': self._get_top_termination(term_losses.get('breakdown', {})),
                'timeout_loss_percentage': self._calculate_percentage(
                    term_losses.get('breakdown', {}).get('timeout', 0),
                    term_losses.get('total_losses', 1)
                )
            },
            'opening_performance': {
                'best_openings': self._get_top_openings(openings, top_n=2),
                'worst_openings': self._get_worst_openings(openings, bottom_n=2),
                'opening_diversity': self._assess_opening_diversity(openings)
            },
            'opponent_strength': {
                'best_against': self._get_best_opponent_category(opponent),
                'struggle_against': self._get_worst_opponent_category(opponent),
                'lower_rated_wr': opponent.get('lower_rated', {}).get('win_rate', 0),
                'similar_rated_wr': opponent.get('similar_rated', {}).get('win_rate', 0),
                'higher_rated_wr': opponent.get('higher_rated', {}).get('win_rate', 0)
            },
            'time_performance': {
                'best_time': self._get_best_time(time_perf),
                'worst_time': self._get_worst_time(time_perf),
                'morning_wr': time_perf.get('morning', {}).get('win_rate', 0),
                'afternoon_wr': time_perf.get('afternoon', {}).get('win_rate', 0),
                'night_wr': time_perf.get('night', {}).get('win_rate', 0)
            }
        }
        
        # Add mistake analysis if available
        if mistake_analysis:
            summary['mistake_analysis'] = {
                'weakest_stage': mistake_analysis.get('weakest_stage', 'N/A'),
                'early_game_mistakes': self._count_total_mistakes(mistake_analysis.get('early', {})),
                'middle_game_mistakes': self._count_total_mistakes(mistake_analysis.get('middle', {})),
                'endgame_mistakes': self._count_total_mistakes(mistake_analysis.get('endgame', {})),
                'most_common_error': self._identify_most_common_error(mistake_analysis),
                'missed_opportunities': sum([
                    mistake_analysis.get('early', {}).get('missed_opps', 0),
                    mistake_analysis.get('middle', {}).get('missed_opps', 0),
                    mistake_analysis.get('endgame', {}).get('missed_opps', 0)
                ]),
                'avg_cp_loss': {
                    'early': mistake_analysis.get('early', {}).get('avg_cp_loss', 0),
                    'middle': mistake_analysis.get('middle', {}).get('avg_cp_loss', 0),
                    'endgame': mistake_analysis.get('endgame', {}).get('avg_cp_loss', 0)
                }
            }
        
        return summary
    
    def _get_top_termination(self, breakdown: Dict) -> str:
        """Get most common termination type."""
        if not breakdown:
            return 'N/A'
        return max(breakdown, key=breakdown.get)
    
    def _calculate_percentage(self, value: int, total: int) -> float:
        """Calculate percentage."""
        if total == 0:
            return 0
        return round((value / total) * 100, 1)
    
    def _get_top_openings(self, openings: Dict, top_n: int = 2) -> List[str]:
        """Get best performing openings."""
        breakdown = openings.get('breakdown', {})
        if not breakdown:
            return []
        
        # Sort by win rate
        sorted_openings = sorted(
            breakdown.items(),
            key=lambda x: x[1].get('win_rate', 0),
            reverse=True
        )
        
        return [
            f"{name} ({data['win_rate']:.0f}% win rate)"
            for name, data in sorted_openings[:top_n]
            if data.get('games', 0) >= 3  # Only include openings with at least 3 games
        ]
    
    def _get_worst_openings(self, openings: Dict, bottom_n: int = 2) -> List[str]:
        """Get worst performing openings."""
        breakdown = openings.get('breakdown', {})
        if not breakdown:
            return []
        
        # Sort by win rate
        sorted_openings = sorted(
            breakdown.items(),
            key=lambda x: x[1].get('win_rate', 0)
        )
        
        return [
            f"{name} ({data['win_rate']:.0f}% win rate)"
            for name, data in sorted_openings[:bottom_n]
            if data.get('games', 0) >= 3  # Only include openings with at least 3 games
        ]
    
    def _assess_opening_diversity(self, openings: Dict) -> str:
        """Assess opening repertoire diversity."""
        breakdown = openings.get('breakdown', {})
        count = len(breakdown)
        
        if count >= 10:
            return 'high'
        elif count >= 5:
            return 'moderate'
        else:
            return 'low'
    
    def _get_best_opponent_category(self, opponent: Dict) -> str:
        """Get opponent category with best performance."""
        categories = {
            'lower_rated': opponent.get('lower_rated', {}).get('win_rate', 0),
            'similar_rated': opponent.get('similar_rated', {}).get('win_rate', 0),
            'higher_rated': opponent.get('higher_rated', {}).get('win_rate', 0)
        }
        
        if not any(categories.values()):
            return 'N/A'
        
        return max(categories, key=categories.get)
    
    def _get_worst_opponent_category(self, opponent: Dict) -> str:
        """Get opponent category with worst performance."""
        categories = {
            'lower_rated': opponent.get('lower_rated', {}).get('win_rate', 0),
            'similar_rated': opponent.get('similar_rated', {}).get('win_rate', 0),
            'higher_rated': opponent.get('higher_rated', {}).get('win_rate', 0)
        }
        
        if not any(categories.values()):
            return 'N/A'
        
        return min(categories, key=categories.get)
    
    def _get_best_time(self, time_perf: Dict) -> str:
        """Get best time of day."""
        times = {
            'morning': time_perf.get('morning', {}).get('win_rate', 0),
            'afternoon': time_perf.get('afternoon', {}).get('win_rate', 0),
            'night': time_perf.get('night', {}).get('win_rate', 0)
        }
        
        if not any(times.values()):
            return 'N/A'
        
        return max(times, key=times.get)
    
    def _get_worst_time(self, time_perf: Dict) -> str:
        """Get worst time of day."""
        times = {
            'morning': time_perf.get('morning', {}).get('win_rate', 0),
            'afternoon': time_perf.get('afternoon', {}).get('win_rate', 0),
            'night': time_perf.get('night', {}).get('win_rate', 0)
        }
        
        if not any(times.values()):
            return 'N/A'
        
        return min(times, key=times.get)
    
    def _count_total_mistakes(self, stage_data: Dict) -> int:
        """Count total mistakes in a stage."""
        return (
            stage_data.get('inaccuracies', 0) +
            stage_data.get('mistakes', 0) +
            stage_data.get('blunders', 0)
        )
    
    def _identify_most_common_error(self, mistake_analysis: Dict) -> str:
        """Identify most common error type and stage."""
        max_count = 0
        max_type = 'N/A'
        
        for stage_name in ['early', 'middle', 'endgame']:
            stage_data = mistake_analysis.get(stage_name, {})
            
            for error_type in ['blunders', 'mistakes', 'inaccuracies']:
                count = stage_data.get(error_type, 0)
                if count > max_count:
                    max_count = count
                    max_type = f"{error_type[:-1]} in {stage_name}game"
        
        return max_type if max_count > 0 else 'N/A'
    
    def generate_advice(self, analysis_results: Dict, username: str, 
                       date_range: str) -> Dict:
        """
        Generate personalized chess coaching advice using OpenAI.
        
        Args:
            analysis_results: Complete analysis results
            username: Player's username
            date_range: Date range string
            
        Returns:
            Dictionary with 'section_suggestions', 'overall_recommendation', 
            'tokens_used', and 'estimated_cost'
        """
        if not self.api_key:
            logger.warning("OpenAI API key not configured, using fallback advice")
            return self._generate_fallback_advice(analysis_results)
        
        try:
            # Prepare summary data
            summary_data = self._prepare_summary_data(analysis_results, username, date_range)
            
            # Build user prompt
            user_prompt = self.USER_PROMPT_TEMPLATE.format(
                summary_data_json=json.dumps(summary_data, indent=2)
            )
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            # Parse response
            advice_text = response.choices[0].message.content
            parsed_advice = self._parse_advice_response(advice_text)
            
            # Log token usage
            tokens_used = response.usage.total_tokens
            estimated_cost = self._calculate_cost(tokens_used)
            
            logger.info(f"AI advice generated: {tokens_used} tokens, ${estimated_cost:.4f}")
            
            return {
                'section_suggestions': parsed_advice['suggestions'],
                'overall_recommendation': parsed_advice['overall'],
                'tokens_used': tokens_used,
                'estimated_cost': estimated_cost
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._generate_fallback_advice(analysis_results)
    
    def _parse_advice_response(self, response_text: str) -> Dict:
        """
        Parse GPT response into structured format.
        
        Args:
            response_text: Raw response from OpenAI
            
        Returns:
            Dictionary with 'suggestions' and 'overall'
        """
        lines = response_text.strip().split("\n")
        suggestions = []
        overall = ""
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify sections
            if "Section-Specific" in line or "**Section-Specific" in line:
                current_section = "suggestions"
            elif "Overall Recommendation" in line or "**Overall Recommendation" in line:
                current_section = "overall"
            elif line.startswith("-") or line.startswith("•") or line.startswith("*"):
                suggestion = line.lstrip("-•*").strip()
                if current_section == "suggestions":
                    suggestions.append(suggestion)
                elif current_section == "overall":
                    overall = suggestion
        
        return {
            'suggestions': suggestions[:7],  # Limit to 7 suggestions
            'overall': overall
        }
    
    def _calculate_cost(self, tokens: int) -> float:
        """
        Calculate estimated cost based on token usage.
        
        GPT-4o-mini pricing (as of Dec 2024):
        - Input: ~$0.15 per 1M tokens
        - Output: ~$0.60 per 1M tokens
        
        Args:
            tokens: Total tokens used
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimate: assume 60% input, 40% output
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4
        
        cost = (input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.60)
        return round(cost, 6)
    
    def _generate_fallback_advice(self, analysis_results: Dict) -> Dict:
        """
        Generate basic rule-based advice if API fails.
        
        Args:
            analysis_results: Analysis results
            
        Returns:
            Fallback advice dictionary
        """
        sections = analysis_results.get('sections', {})
        suggestions = []
        
        # Overall performance
        overall = sections.get('overall_performance', {})
        win_rate = overall.get('win_rate', 0)
        if win_rate < 45:
            suggestions.append("Your win rate is below 45%. Focus on fundamentals: avoid blunders, complete tactical training, and analyze your losses.")
        
        # Terminations
        term_losses = sections.get('termination_losses', {})
        timeout_losses = term_losses.get('breakdown', {}).get('timeout', 0)
        total_losses = term_losses.get('total_losses', 1)
        if timeout_losses / total_losses > 0.25:
            suggestions.append("Time pressure is a major issue (25%+ losses by timeout). Practice playing longer time controls to build clock management skills.")
        
        # Color performance
        color_perf = sections.get('color_performance', {})
        white_wr = color_perf.get('white', {}).get('win_rate', 0)
        black_wr = color_perf.get('black', {}).get('win_rate', 0)
        if abs(white_wr - black_wr) > 15:
            weaker_color = 'Black' if white_wr > black_wr else 'White'
            suggestions.append(f"Your {weaker_color} performance is significantly weaker. Study your {weaker_color} openings and defensive techniques.")
        
        # Opponent strength
        opponent = sections.get('opponent_strength', {})
        higher_rated_wr = opponent.get('higher_rated', {}).get('win_rate', 0)
        if higher_rated_wr < 30:
            suggestions.append("You struggle against stronger opponents. Focus on solid, defensive play and study endgame technique to maximize drawing chances.")
        
        # Time of day
        time_perf = sections.get('time_of_day', {})
        times = {
            'morning': time_perf.get('morning', {}).get('win_rate', 0),
            'afternoon': time_perf.get('afternoon', {}).get('win_rate', 0),
            'night': time_perf.get('night', {}).get('win_rate', 0)
        }
        if times:
            worst_time = min(times, key=times.get)
            best_time = max(times, key=times.get)
            if times[best_time] - times[worst_time] > 15:
                suggestions.append(f"Your {worst_time} performance is significantly worse than {best_time}. Try to schedule games during your peak performance hours.")
        
        overall_rec = "Continue analyzing your games, focus on reducing tactical errors, and maintain consistency in your study routine."
        
        return {
            'section_suggestions': suggestions[:7],
            'overall_recommendation': overall_rec,
            'tokens_used': 0,
            'estimated_cost': 0
        }
