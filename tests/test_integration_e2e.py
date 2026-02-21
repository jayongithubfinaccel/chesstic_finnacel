"""
End-to-End Integration Tests using Playwright
Prevents backend-frontend mismatches by testing actual user workflows.

Run with: pytest tests/test_integration_e2e.py
"""
import pytest
from playwright.sync_api import Page, expect
import time


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application."""
    return "http://127.0.0.1:5000"


@pytest.fixture(scope="function")
def page(playwright):
    """Create a new page for each test."""
    browser = playwright.chromium.launch(headless=False)  # Set to True for CI/CD
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
    browser.close()


class TestAnalyticsDashboard:
    """Test the full analytics dashboard workflow."""
    
    def test_dashboard_loads(self, page: Page, base_url: str):
        """Test that the analytics page loads without errors."""
        page.goto(f"{base_url}/")
        
        # Check page title
        expect(page).to_have_title("Chess Analytics - Analyze Your Chess.com Games")
        
        # Verify main form elements exist
        expect(page.locator("#username")).to_be_visible()
        expect(page.locator("#startDate")).to_be_visible()
        expect(page.locator("#endDate")).to_be_visible()
        expect(page.locator("#timezone")).to_be_visible()
    
    def test_form_submission_and_rendering(self, page: Page, base_url: str):
        """Test complete flow: form submission → API call → data rendering."""
        page.goto(f"{base_url}/")
        
        # Fill in form
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.select_option("#timezone", "America/New_York")
        
        # Submit form
        page.click("button[type='submit']")
        
        # Wait for loading state
        expect(page.locator("#loadingState")).to_be_visible(timeout=5000)
        
        # Wait for results (may take up to 30 seconds)
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Verify no JavaScript errors occurred
        # This is the key test that would have caught our querySelector error!
        console_errors = []
        page.on("console", lambda msg: 
            console_errors.append(msg.text) if msg.type == "error" else None
        )
        
        # Give page time to render all sections
        page.wait_for_timeout(2000)
        
        # Assert no console errors
        assert len(console_errors) == 0, f"JavaScript errors detected: {console_errors}"
    
    def test_all_sections_render(self, page: Page, base_url: str):
        """Test that all analytics sections render correctly."""
        page.goto(f"{base_url}/")
        
        # Fill and submit form
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        # Wait for results
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Verify critical sections are rendered
        sections_to_check = [
            "#overallPerformanceSection",
            "#colorPerformanceSection",
            "#eloProgressionSection",
            "#terminationWinsChart",
            "#terminationLossesChart",
            "#commonOpeningsChart",
            "#lowerRatedCard",
            "#similarRatedCard",
            "#higherRatedCard",
            "#morningCard",
            "#afternoonCard",
            "#nightCard",
        ]
        
        for selector in sections_to_check:
            element = page.locator(selector)
            expect(element).to_be_attached(), f"Element {selector} not found in DOM"
    
    def test_termination_charts_have_data(self, page: Page, base_url: str):
        """Test that termination charts render with actual data."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Check that canvas elements exist and have been drawn to
        wins_canvas = page.locator("#terminationWinsChart")
        losses_canvas = page.locator("#terminationLossesChart")
        
        expect(wins_canvas).to_be_visible()
        expect(losses_canvas).to_be_visible()
        
        # Verify legends are populated (not empty)
        wins_legend = page.locator("#terminationWinsLegend")
        expect(wins_legend).not_to_be_empty()
    
    def test_opening_performance_displays(self, page: Page, base_url: str):
        """Test that opening performance section shows data."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Check opening chart and table exist
        expect(page.locator("#commonOpeningsChart")).to_be_visible()
        expect(page.locator("#commonOpeningsTable")).to_be_visible()
        
        # Verify table has content
        opening_rows = page.locator("#commonOpeningsTable .opening-row")
        expect(opening_rows.first).to_be_visible()
    
    def test_time_of_day_cards_populate(self, page: Page, base_url: str):
        """Test that time of day cards show statistics."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Check that at least one time card has data
        time_cards = ["#morningCard", "#afternoonCard", "#nightCard"]
        
        for card_id in time_cards:
            card = page.locator(card_id)
            if card.is_visible():
                stats_div = card.locator(".time-stats")
                expect(stats_div).not_to_be_empty()


class TestAPIEndpoints:
    """Test API endpoints directly for contract validation."""
    
    def test_analyze_detailed_response_structure(self, page: Page, base_url: str):
        """Test that API returns expected JSON structure."""
        # Use Playwright's request context for API testing
        response = page.request.post(
            f"{base_url}/api/analyze/detailed",
            data={
                "username": "jay_fh",
                "start_date": "2026-02-07",
                "end_date": "2026-02-14",
                "timezone": "America/New_York",
                "include_mistake_analysis": False,
                "include_ai_advice": False
            }
        )
        
        assert response.ok, f"API returned status {response.status}"
        
        data = response.json()
        
        # Verify top-level structure
        assert "total_games" in data
        assert "sections" in data
        
        sections = data["sections"]
        
        # Verify all expected sections exist
        expected_sections = [
            "overall_performance",
            "color_performance",
            "elo_progression",
            "termination_wins",
            "termination_losses",
            "opening_performance",
            "opponent_strength",
            "time_of_day"
        ]
        
        for section in expected_sections:
            assert section in sections, f"Missing section: {section}"
        
        # Verify termination structure
        assert "breakdown" in sections["termination_wins"]
        assert "total_wins" in sections["termination_wins"]
        assert isinstance(sections["termination_wins"]["breakdown"], dict)
        
        assert "breakdown" in sections["termination_losses"]
        assert "total_losses" in sections["termination_losses"]
        assert isinstance(sections["termination_losses"]["breakdown"], dict)
        
        # Verify opening performance structure
        opening = sections["opening_performance"]
        assert "white" in opening
        assert "black" in opening
        assert "best_openings" in opening["white"]
        assert "worst_openings" in opening["white"]
        
        # Verify opponent strength structure
        opponent = sections["opponent_strength"]
        assert "by_rating_diff" in opponent
        assert "avg_opponent_rating" in opponent
        
        categories = opponent["by_rating_diff"]
        for category in ["much_lower", "lower", "similar", "higher", "much_higher"]:
            assert category in categories, f"Missing opponent category: {category}"
            assert "games" in categories[category]
            assert "win_rate" in categories[category]
        
        # Verify time of day structure
        time_data = sections["time_of_day"]
        for period in ["morning", "afternoon", "evening", "night"]:
            assert period in time_data, f"Missing time period: {period}"
            assert "games" in time_data[period]
            assert "win_rate" in time_data[period]


class TestMistakeAnalysis:
    """Test mistake analysis section visibility and rendering (v2.7+)."""
    
    def test_mistake_table_is_visible(self, page: Page, base_url: str):
        """Test that mistake analysis table container is visible after loading."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        # Wait for results
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Wait for mistake analysis to complete (async task, may take 10-20 seconds)
        # The table will have content when analysis is complete
        table_body = page.locator("#mistakeTableBody")
        expect(table_body).not_to_be_empty(timeout=30000)
        
        # Critical test: table container must be visible (not display:none)
        table_container = page.locator(".table-container")
        expect(table_container).to_be_visible()
        
        # Verify inline style doesn't have display:none
        display_style = table_container.evaluate("el => window.getComputedStyle(el).display")
        assert display_style != "none", "Table container has display:none - CSS visibility bug!"
    
    def test_number_of_games_row_visible(self, page: Page, base_url: str):
        """Test that 'Number of games' row exists and is visible in table."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Wait for mistake analysis to complete
        expect(page.locator("#mistakeTableBody")).not_to_be_empty(timeout=30000)
        
        # Check for games count row (v2.7 feature)
        games_row = page.locator("tr.games-count-row")
        expect(games_row).to_be_visible()
        
        # Verify it contains "Number of games" text
        row_text = games_row.inner_text()
        assert "Number of games" in row_text, "Missing 'Number of games' label"
        
        # Verify it has a numeric count
        assert any(char.isdigit() for char in row_text), "No game count found in row"
    
    def test_mistake_summary_cards_visible(self, page: Page, base_url: str):
        """Test that mistake summary cards are visible after loading."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Wait for mistake analysis to complete
        expect(page.locator("#mistakeTableBody")).not_to_be_empty(timeout=30000)
        
        # Check summary cards are visible (not display:none)
        summary_cards = page.locator("#mistakeSummary")
        expect(summary_cards).to_be_visible()
        
        display_style = summary_cards.evaluate("el => window.getComputedStyle(el).display")
        assert display_style != "none", "Summary cards have display:none - CSS visibility bug!"
        
        # Verify key cards exist
        expect(page.locator("#weakestStage")).to_be_visible()
        expect(page.locator("#totalMistakes")).to_be_visible()
    
    def test_ai_recommendations_visible(self, page: Page, base_url: str):
        """Test that AI recommendations section displays correctly."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Wait for mistake analysis and AI advice to complete
        expect(page.locator("#mistakeTableBody")).not_to_be_empty(timeout=30000)
        page.wait_for_timeout(2000)  # AI advice renders after table
        
        # Check AI advisor section exists
        ai_section = page.locator("#aiAdvisorSection")
        expect(ai_section).to_be_attached()
        
        # Check for section suggestions (v2.7 feature)
        sections_container = page.locator("#aiSectionsContainer")
        expect(sections_container).to_be_attached()
    
    def test_mistake_table_has_stage_rows(self, page: Page, base_url: str):
        """Test that mistake table contains all stage rows (early, middle, endgame)."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        expect(page.locator("#dashboardResults")).to_be_visible(timeout=30000)
        
        # Wait for mistake analysis to complete
        expect(page.locator("#mistakeTableBody")).not_to_be_empty(timeout=30000)
        
        # Check table body has content
        table_body = page.locator("#mistakeTableBody")
        expect(table_body).not_to_be_empty()
        
        # Should have 4 rows total: 1 games row + 3 stage rows
        rows = table_body.locator("tr")
        row_count = rows.count()
        assert row_count == 4, f"Expected 4 table rows, found {row_count}"


class TestErrorHandling:
    """Test error scenarios and edge cases."""
    
    def test_invalid_username(self, page: Page, base_url: str):
        """Test error handling for invalid username."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "nonexistentuser12345")
        page.fill("#startDate", "2026-02-07")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        # Should show error message
        error_element = page.locator("#error")
        expect(error_element).to_be_visible(timeout=10000)
    
    def test_date_range_too_large(self, page: Page, base_url: str):
        """Test handling of large date ranges."""
        page.goto(f"{base_url}/")
        
        page.fill("#username", "jay_fh")
        page.fill("#startDate", "2025-01-01")
        page.fill("#endDate", "2026-02-14")
        page.click("button[type='submit']")
        
        # App should either show warning or handle gracefully
        # This is a good place to add date range validation
        page.wait_for_timeout(1000)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
