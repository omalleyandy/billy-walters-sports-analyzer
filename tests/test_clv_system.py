"""
Unit Tests for CLV Storage System

Tests both CLVStorage and CLVReporter classes with comprehensive coverage
for the CLV tracking workflow.

Test Coverage:
- Storage persistence (JSON and CSV)
- CRUD operations on bets
- CLV calculations
- Summary generation
- Data validation
- Edge cases and error handling
"""

import pytest
from pathlib import Path
from datetime import datetime, date
from tempfile import TemporaryDirectory

from walters_analyzer.models import CLVTracking, CLVOutcome
from walters_analyzer.utils import CLVStorage, CLVReporter


# ========== Fixtures ==========

@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_data_dir):
    """Create CLVStorage instance with temporary data directory."""
    return CLVStorage(str(temp_data_dir))


@pytest.fixture
def sample_bet():
    """Standard sample bet for testing."""
    return CLVTracking(
        recommendation_id="rec_W12_001",
        game_id="2025_W12_DET_PHI",
        opening_line=3.5,
        bet_side="away",
        bet_type="spread",
        edge_percentage=8.5,
        bankroll=20000.0,
        stake_fraction=0.025,
        notes="Lions underdog value"
    )


@pytest.fixture
def multiple_bets():
    """Multiple sample bets for week testing."""
    bets = []
    for i in range(5):
        bet = CLVTracking(
            recommendation_id=f"rec_W12_{i:03d}",
            game_id=f"2025_W12_TEAM{i}_TEAM{i+1}",
            opening_line=float(i),
            bet_side="away",
            bet_type="spread",
            edge_percentage=6.0 + i,
            bankroll=20000.0,
            stake_fraction=0.025
        )
        bets.append(bet)
    return bets


# ========== Storage Persistence Tests ==========

class TestStoragePersistence:
    """Test JSON and CSV persistence mechanisms."""
    
    def test_save_bet_creates_json(self, storage, sample_bet):
        """Test that saving a bet creates JSON file."""
        storage.save_bet(sample_bet)
        
        assert storage.bets_json.exists()
    
    def test_save_bet_creates_csv(self, storage, sample_bet):
        """Test that saving a bet appends to CSV."""
        storage.save_bet(sample_bet)
        
        assert storage.history_csv.exists()
    
    def test_save_multiple_bets(self, storage, multiple_bets):
        """Test saving multiple bets."""
        for bet in multiple_bets:
            storage.save_bet(bet)
        
        # Check all bets saved
        all_bets = storage.list_all()
        assert len(all_bets) == 5
    
    def test_update_bet_in_json(self, storage, sample_bet):
        """Test that updating a bet works correctly."""
        storage.save_bet(sample_bet)
        
        # Update bet
        sample_bet.closing_line = 3.0
        storage.save_bet(sample_bet)
        
        # JSON should still have 1 bet (updated)
        all_bets = storage.list_all()
        assert len(all_bets) == 1
        assert all_bets[0].closing_line == 3.0


# ========== CRUD Operations Tests ==========

class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations."""
    
    def test_load_bet_successful(self, storage, sample_bet):
        """Test loading a saved bet."""
        storage.save_bet(sample_bet)
        loaded = storage.load_bet(sample_bet.recommendation_id)
        
        assert loaded is not None
        assert loaded.recommendation_id == sample_bet.recommendation_id
    
    def test_load_bet_not_found(self, storage):
        """Test loading non-existent bet."""
        loaded = storage.load_bet("rec_nonexistent")
        assert loaded is None
    
    def test_list_all_bets(self, storage, multiple_bets):
        """Test listing all bets."""
        for bet in multiple_bets:
            storage.save_bet(bet)
        
        all_bets = storage.list_all()
        assert len(all_bets) == 5
    
    def test_list_pending_bets(self, storage, sample_bet):
        """Test filtering pending bets."""
        storage.save_bet(sample_bet)
        
        pending = storage.list_pending()
        assert len(pending) == 1
        assert pending[0].clv_outcome == CLVOutcome.PENDING
    
    def test_delete_bet(self, storage, sample_bet):
        """Test deleting a bet."""
        storage.save_bet(sample_bet)
        
        deleted = storage.delete_bet(sample_bet.recommendation_id)
        assert deleted is True
        
        loaded = storage.load_bet(sample_bet.recommendation_id)
        assert loaded is None


# ========== CLV Calculation Tests ==========

class TestCLVCalculations:
    """Test CLV calculation and updates."""
    
    def test_update_closing_line(self, storage, sample_bet):
        """Test updating closing line."""
        storage.save_bet(sample_bet)
        
        # Opening was 3.5, closing 3.0
        updated = storage.update_closing_line("rec_W12_001", 3.0)
        
        assert updated is not None
        assert updated.closing_line == 3.0
        assert updated.clv_points is not None
    
    def test_update_result_win(self, storage, sample_bet):
        """Test updating result with win."""
        storage.save_bet(sample_bet)
        
        updated = storage.update_result("rec_W12_001", 2.5, True)
        
        assert updated is not None
        assert updated.did_bet_win is True
    
    def test_complete_workflow(self, storage, sample_bet):
        """Test complete bet lifecycle."""
        # 1. Record bet
        storage.save_bet(sample_bet)
        bet = storage.load_bet("rec_W12_001")
        assert bet.clv_outcome == CLVOutcome.PENDING
        
        # 2. Update closing line
        bet = storage.update_closing_line("rec_W12_001", 3.0)
        assert bet.clv_outcome != CLVOutcome.PENDING
        
        # 3. Update result
        bet = storage.update_result("rec_W12_001", 2.5, True)
        assert bet.is_resolved is True


# ========== Summary Generation Tests ==========

class TestSummaryGeneration:
    """Test CLVReporter summary generation."""
    
    def test_empty_summary(self):
        """Test summary with no bets."""
        summary = CLVReporter.generate_summary([])
        assert summary.total_bets == 0
    
    def test_pending_only_summary(self, sample_bet):
        """Test summary with only pending bets."""
        summary = CLVReporter.generate_summary([sample_bet])
        
        assert summary.total_bets == 1
        assert summary.bets_pending == 1
    
    def test_resolved_bets_summary(self, storage, multiple_bets):
        """Test summary with resolved bets."""
        for i, bet in enumerate(multiple_bets):
            storage.save_bet(bet)
            storage.update_closing_line(bet.recommendation_id, 3.0)
            did_win = i % 2 == 0
            storage.update_result(bet.recommendation_id, 2.5, did_win)
        
        bets = storage.list_all()
        summary = CLVReporter.generate_summary(bets)
        
        assert summary.total_bets == 5
        assert summary.bets_resolved == 5


# ========== Data Validation Tests ==========

class TestDataValidation:
    """Test input validation and error handling."""
    
    def test_save_invalid_bet_type(self, storage):
        """Test saving non-CLVTracking object."""
        with pytest.raises(ValueError):
            storage.save_bet("not a bet")
    
    def test_update_closing_line_invalid_type(self, storage, sample_bet):
        """Test updating closing line with invalid type."""
        storage.save_bet(sample_bet)
        
        with pytest.raises(ValueError):
            storage.update_closing_line("rec_W12_001", "invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
