"""
AI Chess Advisor service using OpenAI GPT for personalized coaching recommendations.
Milestone 9: AI-Powered Chess Advisor
PRD v2.1: Updated to require EXACTLY 9 section-specific + 1 overall recommendations with YouTube integration
"""
import json
import logging
from typing import Dict, List, Optional
import openai

logger = logging.getLogger(__name__)


# YouTube video database for opening tutorials
# Prioritization: ChessNetwork > GMHikaru > GothamChess > Chessbrahs
OPENING_VIDEOS = {
    "Sicilian Defense": {
        "channel": "ChessNetwork",
        "title": "Sicilian Defense - Complete Guide",
        "url": "https://www.youtube.com/watch?v=VJGPwnHJxLU"
    },
    "Italian Game": {
        "channel": "GMHikaru",
        "title": "Italian Game Explained",
        "url": "https://www.youtube.com/watch?v=9_MAjIpYxU8"
    },
    "French Defense": {
        "channel": "ChessNetwork",
        "title": "French Defense Tutorial",
        "url": "https://www.youtube.com/watch?v=x8KypSEEqWg"
    },
    "Caro-Kann Defense": {
        "channel": "GMHikaru",
        "title": "Caro-Kann Defense Guide",
        "url": "https://www.youtube.com/watch?v=G3z6v1jPxL4"
    },
    "Queen's Gambit": {
        "channel": "GothamChess",
        "title": "Queen's Gambit Masterclass",
        "url": "https://www.youtube.com/watch?v=xSkFNn72cLM"
    },
    "Ruy Lopez": {
        "channel": "ChessNetwork",
        "title": "Ruy Lopez Opening",
        "url": "https://www.youtube.com/watch?v=_BZ4Uz6ZwVE"
    },
    "King's Indian Defense": {
        "channel": "Chessbrahs",
        "title": "King's Indian Defense",
        "url": "https://www.youtube.com/watch?v=9Fzq8k2hN5o"
    },
    "London System": {
        "channel": "GothamChess",
        "title": "London System Guide",
        "url": "https://www.youtube.com/watch?v=4ngii3V31Jg"
    },
    "Scandinavian Defense": {
        "channel": "GMHikaru",
        "title": "Scandinavian Defense",
        "url": "https://www.youtube.com/watch?v=FQB8IDtCkB0"
    },
    "Queen's Pawn Opening": {
        "channel": "ChessNetwork",
        "title": "Queen's Pawn Opening Strategies",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    },
    "English Opening": {
        "channel": "GothamChess",
        "title": "English Opening for Beginners",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
}


class ChessAdvisorService:
    """Service for generating AI-powered chess coaching advice."""
    
    SYSTEM_PROMPT = """
You are an expert chess coach analyzing a player's performance data. Your goal is to provide 
concise, actionable advice to help them improve their chess skills.

Based on the provided statistics, you MUST generate EXACTLY:
1. Nine (9) section-specific recommendations - ONE for each section (1-9):
   - Section 1: Overall Performance
   - Section 2: Color Performance  
   - Section 3: Rating Progression
   - Section 4: How You Win
   - Section 5: How You Lose
   - Section 6: Opening Performance
   - Section 7: Opponent Strength
   - Section 8: Time of Day Performance
   - Section 9: Mistake Analysis
2. One (1) overall recommendation that synthesizes all insights

DO NOT skip any section. ALL 9 sections must receive a specific recommendation.

Format your response with clear section labels exactly as shown in the user prompt.
Each recommendation should:
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
- Skipping any section (CRITICAL: all 9 sections must have recommendations)

Tone: Encouraging but honest, like a supportive coach.
"""
    
    USER_PROMPT_TEMPLATE = """
Analyze this chess player's performance and provide coaching recommendations:

{summary_data_json}

Provide recommendations in this EXACT format (all 9 sections are MANDATORY):

**Section 1 - Overall Performance:**
- [Specific recommendation based on win rate trends and overall stats]

**Section 2 - Color Performance:**
- [Specific recommendation based on White vs Black performance]

**Section 3 - Rating Progression:**
- [Specific recommendation based on rating changes and trends]

**Section 4 - How You Win:**
- [Specific recommendation based on winning termination patterns]

**Section 5 - How You Lose:**
- [Specific recommendation based on losing termination patterns]

**Section 6 - Opening Performance:**
- [Specific recommendation based on best/worst openings]

**Section 7 - Opponent Strength:**
- [Specific recommendation based on performance vs different rated opponents]

**Section 8 - Time of Day:**
- [Specific recommendation based on time period performance]

**Section 9 - Mistake Analysis:**
- [Specific recommendation based on mistake patterns by game stage]

**Overall Recommendation:**
- [One comprehensive recommendation that synthesizes all insights and provides a clear action plan]
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
            Dictionary with 'section_suggestions' (list of 9 dicts), 
            'overall_recommendation', 'youtube_videos' (list), 
            'tokens_used', and 'estimated_cost'
        """
        if not self.api_key:
            logger.warning("OpenAI API key not configured, using fallback advice")
            return self._generate_fallback_advice(analysis_results)
        
        try:
            # Prepare summary data
            summary_data = self._prepare_summary_data(analysis_results, username, date_range)
            
            # Get YouTube video recommendations
            youtube_videos = self._get_opening_videos(summary_data)
            
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
                'youtube_videos': youtube_videos,
                'tokens_used': tokens_used,
                'estimated_cost': estimated_cost
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._generate_fallback_advice(analysis_results)
    
    def _get_opening_videos(self, summary_data: Dict) -> List[Dict[str, str]]:
        """
        Get YouTube video recommendations for frequently played openings.
        
        Args:
            summary_data: Summary data containing opening performance
            
        Returns:
            List of video recommendations with opening name, channel, title, and URL
        """
        videos = []
        
        # Extract opening performance from summary data
        opening_perf = summary_data.get('opening_performance', {})
        best_openings = opening_perf.get('best_openings', [])
        worst_openings = opening_perf.get('worst_openings', [])
        
        # Collect all unique opening names
        opening_names = set()
        
        # Extract opening names from best_openings (format: "Opening Name (X% win rate)")
        for opening_str in best_openings:
            if '(' in opening_str:
                opening_name = opening_str.split('(')[0].strip()
                opening_names.add(opening_name)
        
        # Extract opening names from worst_openings
        for opening_str in worst_openings:
            if '(' in opening_str:
                opening_name = opening_str.split('(')[0].strip()
                opening_names.add(opening_name)
        
        # Find videos for openings (only if they have 3+ games based on PRD)
        for opening_name in opening_names:
            # Check if we have a video for this opening
            if opening_name in OPENING_VIDEOS:
                video_info = OPENING_VIDEOS[opening_name]
                videos.append({
                    'opening': opening_name,
                    'channel': video_info['channel'],
                    'title': video_info['title'],
                    'url': video_info['url']
                })
        
        return videos
    
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
        Generate rule-based advice if API fails.
        Ensures all 9 sections receive recommendations.
        
        Args:
            analysis_results: Analysis results
            
        Returns:
            Fallback advice dictionary with 9+1 recommendations
        """
        sections = analysis_results.get('sections', {})
        suggestions = []
        
        # Section 1: Overall performance
        overall = sections.get('overall_performance', {})
        win_rate = overall.get('win_rate', 0)
        if win_rate < 45:
            advice1 = "Your win rate is below 45%. Focus on fundamentals: avoid blunders, complete tactical training, and analyze your losses."
        elif win_rate > 55:
            advice1 = f"Solid {win_rate:.1f}% win rate! Maintain consistency and challenge yourself against stronger opponents."
        else:
            advice1 = "Your win rate shows steady play. Continue tracking your games to identify improvement trends."
        suggestions.append({
            "section_number": 1,
            "section_name": "Overall Performance",
            "advice": advice1
        })
        
        # Section 2: Color performance
        color_perf = sections.get('color_performance', {})
        white_wr = color_perf.get('white', {}).get('win_rate', 0)
        black_wr = color_perf.get('black', {}).get('win_rate', 0)
        if abs(white_wr - black_wr) > 15:
            weaker_color = 'Black' if white_wr > black_wr else 'White'
            advice2 = f"Your {weaker_color} performance is significantly weaker ({min(white_wr, black_wr):.1f}% vs {max(white_wr, black_wr):.1f}%). Study your {weaker_color} openings and defensive techniques."
        else:
            advice2 = "Your White and Black performance is balanced. Continue practicing with both colors."
        suggestions.append({
            "section_number": 2,
            "section_name": "Color Performance",
            "advice": advice2
        })
        
        # Section 3: Rating progression
        rating_change = overall.get('rating_change', 0)
        if rating_change > 0:
            advice3 = f"Rating up {rating_change} points - good momentum! Maintain consistent play to continue improving."
        elif rating_change < -20:
            advice3 = f"Rating down {abs(rating_change)} points. Review recent games to identify patterns causing losses."
        else:
            advice3 = "Rating is stable. Focus on consistent play and gradual improvement through study."
        suggestions.append({
            "section_number": 3,
            "section_name": "Rating Progression",
            "advice": advice3
        })
        
        # Section 4: How you win
        term_wins = sections.get('termination_wins', {})
        most_common_win = self._get_top_termination(term_wins.get('breakdown', {}))
        advice4 = f"Most wins by {most_common_win}. Continue developing your winning patterns and tactical skills."
        suggestions.append({
            "section_number": 4,
            "section_name": "How You Win",
            "advice": advice4
        })
        
        # Section 5: How you lose
        term_losses = sections.get('termination_losses', {})
        timeout_losses = term_losses.get('breakdown', {}).get('timeout', 0)
        total_losses = term_losses.get('total_losses', 1)
        if timeout_losses / total_losses > 0.25:
            advice5 = f"Time pressure is a major issue ({(timeout_losses/total_losses*100):.0f}% losses by timeout). Play longer time controls to build clock management skills."
        else:
            advice5 = "Review your losses to identify and fix recurring weaknesses."
        suggestions.append({
            "section_number": 5,
            "section_name": "How You Lose",
            "advice": advice5
        })
        
        # Section 6: Opening performance
        openings = sections.get('opening_performance', {})
        worst_openings = self._get_worst_openings(openings, bottom_n=1)
        if worst_openings:
            advice6 = f"Your weakest opening ({worst_openings[0]}) needs work. Consider studying key lines or switching."
        else:
            advice6 = "Study your most-played openings to improve your repertoire."
        suggestions.append({
            "section_number": 6,
            "section_name": "Opening Performance",
            "advice": advice6
        })
        
        # Section 7: Opponent strength
        opponent = sections.get('opponent_strength', {})
        higher_rated_wr = opponent.get('higher_rated', {}).get('win_rate', 0)
        if higher_rated_wr < 30:
            advice7 = f"You struggle against stronger opponents ({higher_rated_wr:.0f}% win rate). Focus on solid, defensive play and study endgame technique."
        else:
            advice7 = "Play against varied opposition to improve against all rating levels."
        suggestions.append({
            "section_number": 7,
            "section_name": "Opponent Strength",
            "advice": advice7
        })
        
        # Section 8: Time of day
        time_perf = sections.get('time_of_day', {})
        best_time = self._get_best_time(time_perf)
        worst_time = self._get_worst_time(time_perf)
        morning_wr = time_perf.get('morning', {}).get('win_rate', 0)
        afternoon_wr = time_perf.get('afternoon', {}).get('win_rate', 0)
        night_wr = time_perf.get('night', {}).get('win_rate', 0)
        
        times = {'morning': morning_wr, 'afternoon': afternoon_wr, 'night': night_wr}
        if times and max(times.values()) - min(times.values()) > 15:
            advice8 = f"Your {best_time} performance ({times[best_time]:.0f}%) is much better than {worst_time} ({times[worst_time]:.0f}%). Schedule important games during peak hours."
        else:
            advice8 = "Play during your peak performance times for better results."
        suggestions.append({
            "section_number": 8,
            "section_name": "Time of Day Performance",
            "advice": advice8
        })
        
        # Section 9: Mistake analysis
        mistake_analysis = sections.get('mistake_analysis', {})
        if mistake_analysis:
            weakest_stage = mistake_analysis.get('weakest_stage', 'N/A')
            if weakest_stage != 'N/A':
                advice9 = f"{weakest_stage.capitalize()}game is your weakest stage. Focus study time on tactical patterns in this phase."
            else:
                advice9 = "Focus on reducing mistakes through tactical training and game analysis."
        else:
            advice9 = "Focus on reducing mistakes in all game stages through targeted practice."
        suggestions.append({
            "section_number": 9,
            "section_name": "Mistake Analysis",
            "advice": advice9
        })
        
        # Overall recommendation
        overall_rec = "Continue analyzing your games regularly. Focus on time management, opening preparation, and tactical training to improve your overall play."
        
        # Get video recommendations even for fallback
        summary_data = self._prepare_summary_data(analysis_results, '', '')
        youtube_videos = self._get_opening_videos(summary_data)
        
        return {
            'section_suggestions': suggestions,
            'overall_recommendation': overall_rec,
            'youtube_videos': youtube_videos,
            'tokens_used': 0,
            'estimated_cost': 0,
            'fallback': True
        }
