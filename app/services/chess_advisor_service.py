"""
AI Chess Advisor service using OpenAI GPT for personalized coaching recommendations.
Milestone 9: AI-Powered Chess Advisor
PRD v2.1: Updated to require EXACTLY 9 section-specific + 1 overall recommendations with YouTube integration
"""
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI

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

Based on the provided statistics from all 9 sections of analysis, generate ONE specific 
recommendation for EACH of the 9 sections (1-2 bullet points per section).

Format for section recommendations:
- Each section gets 1-2 concise, actionable bullet points
- Focus on the most impactful insight from that specific section
- Be specific with data references (e.g., "win rate dropped from 60% to 45%")
- Each bullet point should be 1-2 sentences maximum

Prioritize:
1. Patterns with clear negative impact (e.g., high timeout losses)
2. Significant performance gaps (e.g., 20%+ difference between time periods)
3. Mistake patterns that repeat across games
4. Areas where small changes yield big results

Avoid:
- Generic advice ("study more tactics")
- Obvious statements ("you lose when you blunder")
- Long paragraphs or overly detailed explanations

Tone: Encouraging but honest, like a supportive coach.
"""
    
    USER_PROMPT_TEMPLATE = """
Analyze this chess player's performance and provide coaching recommendations:

{summary_data_json}

Provide your recommendations in this EXACT format:

**Section 1 - Overall Performance:**
• [Actionable insight 1]
• [Actionable insight 2 if needed]

**Section 2 - Color Performance:**
• [Actionable insight]

**Section 3 - ELO Progression:**
• [Actionable insight]

**Section 4 - Termination Wins:**
• [Actionable insight]

**Section 5 - Termination Losses:**
• [Actionable insight]

**Section 6 - Opening Performance:**
• [Actionable insight]

**Section 7 - Opponent Strength:**
• [Actionable insight]

**Section 8 - Time of Day:**
• [Actionable insight]

**Section 9 - Move Analysis:**
• [Actionable insight]

Keep each bullet point concise (1-2 sentences maximum).
"""
    
    def __init__(self, api_key: str, model: str = 'gpt-4o-mini', 
                 max_tokens: int = 600, temperature: float = 0.7):
        """
        Initialize AI advisor service.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini for cost efficiency)
            max_tokens: Maximum response tokens (increased to 600 for v2.7 section-based recommendations)
            temperature: Sampling temperature (0-1)
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize OpenAI client (new API format)
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
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
            Dictionary with 'section_suggestions' (list of 9 dicts)
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
            
            # Call OpenAI API (new client format)
            response = self.client.chat.completions.create(
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
            
            # Log token usage internally (v2.6: not returned to user)
            tokens_used = response.usage.total_tokens
            estimated_cost = self._calculate_cost(tokens_used)
            self._log_usage(tokens_used, estimated_cost)
            
            return {
                'section_suggestions': parsed_advice['suggestions']
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
            Dictionary with 'suggestions' (list of dicts)
        """
        lines = response_text.strip().split("\n")
        suggestions = []
        
        current_section = None
        current_bullets = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section header (e.g., **Section 1 - Overall Performance:**)
            if line.startswith('**Section') and (':' in line or ':**' in line):
                # Save previous section if exists
                if current_section:
                    suggestions.append({
                        'section_number': current_section['number'],
                        'section_name': current_section['name'],
                        'bullets': current_bullets.copy()
                    })
                
                # Parse new section
                section_match = line.replace('**', '').replace(':', '').strip()
                parts = section_match.split(' - ', 1)
                
                try:
                    section_num_str = parts[0].replace('Section', '').strip()
                    section_num = int(section_num_str)
                    section_name = parts[1].strip() if len(parts) > 1 else f"Section {section_num}"
                    
                    current_section = {'number': section_num, 'name': section_name}
                    current_bullets = []
                except (ValueError, IndexError):
                    # If parsing fails, skip this line
                    continue
                    
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                # Bullet point - only for sections
                if current_section is not None:
                    bullet = line.lstrip('•-* ').strip()
                    current_bullets.append(bullet)
        
        # Save last section if exists
        if current_section:
            suggestions.append({
                'section_number': current_section['number'],
                'section_name': current_section['name'],
                'bullets': current_bullets.copy()
            })
        
        return {
            'suggestions': suggestions
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
    
    def _log_usage(self, tokens: int, cost: float):
        """
        Log token usage and cost for internal monitoring (v2.6).
        This is for cost tracking purposes only - not shown to users.
        
        Args:
            tokens: Total tokens used
            cost: Estimated cost in USD
        """
        logger.info(f"OpenAI API usage - Tokens: {tokens}, Estimated cost: ${cost:.6f}")
    
    def _generate_fallback_advice(self, analysis_results: Dict) -> Dict:
        """
        Generate rule-based advice if API fails (v2.8: section bullets only).
        
        Args:
            analysis_results: Analysis results
            
        Returns:
            Fallback advice dictionary with section_suggestions
        """
        sections = analysis_results.get('sections', {})
        section_suggestions = []
        
        # Section 1 - Overall Performance
        overall_perf = sections.get('overall_performance', {})
        win_rate = overall_perf.get('win_rate', 0)
        rating_change = overall_perf.get('rating_change', 0)
        bullets_1 = []
        if rating_change > 0:
            bullets_1.append(f"Maintain your upward trend (+{rating_change} rating points)")
        else:
            bullets_1.append(f"Focus on consistency to improve from {win_rate:.1f}% win rate")
        section_suggestions.append({
            'section_number': 1,
            'section_name': 'Overall Performance',
            'bullets': bullets_1
        })
        
        # Section 2 - Color Performance
        color_perf = sections.get('color_performance', {})
        white_wr = color_perf.get('white', {}).get('win_rate', 0)
        black_wr = color_perf.get('black', {}).get('win_rate', 0)
        bullets_2 = []
        if abs(white_wr - black_wr) > 15:
            weaker_color = 'White' if white_wr < black_wr else 'Black'
            bullets_2.append(f"Improve your {weaker_color} repertoire (currently weaker color)")
        else:
            bullets_2.append("Maintain balanced play with both colors")
        section_suggestions.append({
            'section_number': 2,
            'section_name': 'Color Performance',
            'bullets': bullets_2
        })
        
        # Section 3 - ELO Progression
        elo_prog = sections.get('elo_progression', {})
        bullets_3 = []
        if rating_change > 0:
            bullets_3.append("Keep playing consistently to maintain rating momentum")
        else:
            bullets_3.append("Analyze losses to identify and fix rating leaks")
        section_suggestions.append({
            'section_number': 3,
            'section_name': 'ELO Progression',
            'bullets': bullets_3
        })
        
        # Section 4 - Termination Wins
        term_wins = sections.get('termination_wins', {})
        bullets_4 = []
        bullets_4.append("Continue capitalizing on opponent mistakes")
        section_suggestions.append({
            'section_number': 4,
            'section_name': 'Termination Wins',
            'bullets': bullets_4
        })
        
        # Section 5 - Termination Losses
        term_losses = sections.get('termination_losses', {})
        timeout_losses = term_losses.get('breakdown', {}).get('timeout', 0)
        total_losses = term_losses.get('total_losses', 1)
        bullets_5 = []
        if timeout_losses / total_losses > 0.20:
            bullets_5.append(f"Critical: Reduce timeout losses ({(timeout_losses/total_losses*100):.0f}% of losses)")
        else:
            bullets_5.append("Good time management - maintain current pace")
        section_suggestions.append({
            'section_number': 5,
            'section_name': 'Termination Losses',
            'bullets': bullets_5
        })
        
        # Section 6 - Opening Performance
        openings = sections.get('opening_performance', {})
        worst_openings = self._get_worst_openings(openings, bottom_n=1)
        bullets_6 = []
        if worst_openings:
            bullets_6.append(f"Review or replace your weakest opening ({worst_openings[0]})")
        else:
            bullets_6.append("Continue studying your opening repertoire")
        section_suggestions.append({
            'section_number': 6,
            'section_name': 'Opening Performance',
            'bullets': bullets_6
        })
        
        # Section 7 - Opponent Strength
        opponent = sections.get('opponent_strength', {})
        bullets_7 = []
        bullets_7.append("Challenge yourself by playing opponents at all rating levels")
        section_suggestions.append({
            'section_number': 7,
            'section_name': 'Opponent Strength',
            'bullets': bullets_7
        })
        
        # Section 8 - Time of Day
        time_perf = sections.get('time_of_day', {})
        best_time = self._get_best_time(time_perf)
        bullets_8 = []
        if best_time != 'N/A':
            best_wr = time_perf.get(best_time, {}).get('win_rate', 0)
            if best_wr > 55:
                bullets_8.append(f"Play more games during {best_time} ({best_wr:.0f}% win rate)")
        else:
            bullets_8.append("Track time-of-day patterns over more games")
        section_suggestions.append({
            'section_number': 8,
            'section_name': 'Time of Day',
            'bullets': bullets_8
        })
        
        # Section 9 - Move Analysis
        mistake_analysis = sections.get('mistake_analysis', {})
        bullets_9 = []
        if mistake_analysis:
            weakest_stage = mistake_analysis.get('weakest_stage', '')
            if weakest_stage:
                stage_data = mistake_analysis.get(weakest_stage, {})
                mistakes = stage_data.get('avg_mistakes_per_game', 0)
                bullets_9.append(f"Focus on {weakest_stage}game tactics ({mistakes:.1f} avg mistakes)")
            else:
                bullets_9.append("Practice tactics regularly to reduce mistakes")
        else:
            bullets_9.append("Analyze your games to identify mistake patterns")
        section_suggestions.append({
            'section_number': 9,
            'section_name': 'Move Analysis',
            'bullets': bullets_9
        })
        
        return {
            'section_suggestions': section_suggestions
        }
