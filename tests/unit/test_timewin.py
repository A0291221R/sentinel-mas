import pytest
from datetime import datetime, timedelta
import pytz
from sentinel_mas.timewin import resolve_time_window, SGT

class TestTimeWindow:
    """Unit tests for time window resolution"""
    
    def setup_method(self):
        """Set up a fixed base date for consistent testing"""
        self.base_date = SGT.localize(datetime(2024, 3, 15, 14, 30))  # 2:30 PM SGT
    
    def test_last_n_minutes(self):
        """Test 'last N minutes' patterns"""
        start, end, label = resolve_time_window("last 15 minutes", self.base_date)
        expected_end = int(self.base_date.timestamp() * 1000)
        expected_start = int((self.base_date - timedelta(minutes=15)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        assert "SGT" in label
    
    def test_last_n_hours(self):
        """Test 'last N hours' patterns"""
        start, end, label = resolve_time_window("last 3 hours", self.base_date)
        expected_end = int(self.base_date.timestamp() * 1000)
        expected_start = int((self.base_date - timedelta(hours=3)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_today(self):
        """Test 'today' keyword"""
        start, end, label = resolve_time_window("today", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 0, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 16, 0, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        assert "2024-03-15" in label
    
    def test_yesterday(self):
        """Test 'yesterday' keyword"""
        start, end, label = resolve_time_window("yesterday", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 14, 0, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 0, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_tomorrow(self):
        """Test 'tomorrow' keyword"""
        start, end, label = resolve_time_window("tomorrow", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 16, 0, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 17, 0, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_dayparts(self):
        """Test daypart keywords (morning, afternoon, evening, night)"""
        # Morning (6:00-12:00)
        start, end, label = resolve_time_window("this morning", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 6, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 12, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        # Afternoon (12:00-18:00)
        start, end, label = resolve_time_window("afternoon", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 12, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 18, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        # Evening (18:00-22:00)
        start, end, label = resolve_time_window("evening", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 18, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 22, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        # Night (22:00-06:00 next day)
        start, end, label = resolve_time_window("tonight", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 22, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 16, 6, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_time_range_with_ampm_suffix(self):
        """Test time ranges with AM/PM suffix (e.g., '2-4pm')"""
        start, end, label = resolve_time_window("2-4pm", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 14, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 16, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        # Test with 'am'
        start, end, label = resolve_time_window("8-10am", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 8, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 10, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_time_range_with_explicit_ampm(self):
        """Test time ranges where each time has explicit AM/PM"""
        start, end, label = resolve_time_window("2pm-4pm", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 14, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 16, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        start, end, label = resolve_time_window("9am-11am", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 9, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 11, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_time_range_with_minutes(self):
        """Test time ranges with minutes"""
        start, end, label = resolve_time_window("2:30-4:45pm", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 14, 30)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 16, 45)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_single_time(self):
        """Test single time specification"""
        start, end, label = resolve_time_window("3pm", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 15, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 16, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        start, end, label = resolve_time_window("14:30", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 14, 30)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 15, 30)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_date_formats(self):
        """Test various date formats"""
        # DD-MM-YYYY
        start, end, label = resolve_time_window("15-03-2024", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 0, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 16, 0, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        # YYYY-MM-DD (ISO)
        start, end, label = resolve_time_window("2024-03-15", self.base_date)
        assert start == expected_start
        assert end == expected_end
        
        # DD/MM/YYYY
        start, end, label = resolve_time_window("15/03/2024", self.base_date)
        assert start == expected_start
        assert end == expected_end
        
        # Text month
        start, end, label = resolve_time_window("15-Mar-2024", self.base_date)
        assert start == expected_start
        assert end == expected_end
    
    def test_combined_date_and_time(self):
        """Test combinations of date and time"""
        start, end, label = resolve_time_window("15-03-2024 2-4pm", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 14, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 16, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        start, end, label = resolve_time_window("yesterday 10am-12pm", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 14, 10, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 14, 12, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_cross_midnight_range(self):
        """Test time ranges that cross midnight"""
        start, end, label = resolve_time_window("11pm-2am", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 23, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 16, 2, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_now_keyword(self):
        """Test 'now' keyword in time ranges"""
        start, end, label = resolve_time_window("now to 5pm", self.base_date)
        expected_start = int(self.base_date.timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 17, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        start, end, label = resolve_time_window("2pm to now", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 14, 0)).timestamp() * 1000)
        expected_end = int(self.base_date.timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
    
    def test_range_separators(self):
        """Test different range separators (to, and, -, –, —)"""
        test_cases = [
            "2 to 4pm",
            "2 and 4pm", 
            "2-4pm",
            "2–4pm",
            "2—4pm",
            "between 2 and 4pm"
        ]
        
        for text in test_cases:
            start, end, label = resolve_time_window(text, self.base_date)
            expected_start = int(SGT.localize(datetime(2024, 3, 15, 14, 0)).timestamp() * 1000)
            expected_end = int(SGT.localize(datetime(2024, 3, 15, 16, 0)).timestamp() * 1000)
            assert start == expected_start
            assert end == expected_end
    
    def test_invalid_input(self):
        """Test that invalid input raises ValueError"""
        with pytest.raises(ValueError):
            resolve_time_window("invalid time specification", self.base_date)
        
        with pytest.raises(ValueError):
            resolve_time_window("", self.base_date)

    def test_edge_cases(self):
        """Test edge cases"""
        # 12am (midnight) to 1am
        start, end, label = resolve_time_window("12am-1am", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 0, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 1, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end
        
        # 12pm (noon) to 1pm
        start, end, label = resolve_time_window("12pm-1pm", self.base_date)
        expected_start = int(SGT.localize(datetime(2024, 3, 15, 12, 0)).timestamp() * 1000)
        expected_end = int(SGT.localize(datetime(2024, 3, 15, 13, 0)).timestamp() * 1000)
        assert start == expected_start
        assert end == expected_end

if __name__ == "__main__":
    pytest.main([__file__, "-v"])