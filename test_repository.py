"""
Test SQLAlchemy ORM Repository Operations
測試 SQLAlchemy ORM 操作與向後相容性
"""
import pytest
from datetime import datetime
from db.repository import save_review, get_recent_reviews, get_review_by_id
from db.models import Review, init_db, engine
import json


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize database before tests"""
    init_db()
    yield
    # Cleanup: delete all reviews after tests
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        db.query(Review).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def sample_review_data():
    """Sample review data for testing"""
    return {
        "verdict": "通過審查，風險可接受",
        "risks": [
            {"level": "high", "description": "High risk item"},
            {"level": "medium", "description": "Medium risk item"},
            {"level": "low", "description": "Low risk item"}
        ],
        "roles": {
            "risk_analyst": {"status": "pass"},
            "completeness_reviewer": {"status": "pass"}
        }
    }


class TestSaveReview:
    """Tests for save_review function"""
    
    def test_save_review_returns_id(self, sample_review_data):
        """Should return a new review ID when saving"""
        review_id = save_review("Test Project Alpha", sample_review_data)
        assert isinstance(review_id, int)
        assert review_id > 0
    
    def test_save_review_stores_data_correctly(self, sample_review_data):
        """Should store review data correctly in database"""
        project_name = "Test Project Beta"
        review_id = save_review(project_name, sample_review_data)
        
        # Retrieve and verify
        review = get_review_by_id(review_id)
        assert review is not None
        assert review["project"] == project_name
        assert review["verdict"] == sample_review_data["verdict"]
        assert review["result_json"] == sample_review_data
    
    def test_save_review_calculates_risk_counts(self, sample_review_data):
        """Should correctly calculate risk counts from risks array"""
        review_id = save_review("Test Project Gamma", sample_review_data)
        review = get_review_by_id(review_id)
        
        assert review["risk_high"] == 1
        assert review["risk_medium"] == 1
        assert review["risk_low"] == 1


class TestGetRecentReviews:
    """Tests for get_recent_reviews function"""
    
    def test_get_recent_reviews_returns_list(self, sample_review_data):
        """Should return a list of recent reviews"""
        # Create some test data
        save_review("Recent Project 1", sample_review_data)
        save_review("Recent Project 2", sample_review_data)
        
        reviews = get_recent_reviews(limit=5)
        assert isinstance(reviews, list)
        assert len(reviews) >= 2
    
    def test_get_recent_reviews_orders_by_date(self, sample_review_data):
        """Should order reviews by reviewed_at DESC"""
        reviews = get_recent_reviews(limit=10)
        
        # Check ordering (most recent first)
        if len(reviews) > 1:
            for i in range(len(reviews) - 1):
                # reviews[i] should be more recent or equal to reviews[i+1]
                assert reviews[i][2] >= reviews[i + 1][2] or \
                       reviews[i][2] == reviews[i + 1][2]
    
    def test_get_recent_reviews_respects_limit(self, sample_review_data):
        """Should respect the limit parameter"""
        reviews = get_recent_reviews(limit=3)
        assert len(reviews) <= 3
    
    def test_get_recent_reviews_format(self, sample_review_data):
        """Should return reviews in correct tuple format"""
        reviews = get_recent_reviews(limit=1)
        
        if reviews:
            review_tuple = reviews[0]
            # Should be tuple: (id, project, reviewed_at, risk_high, risk_medium, risk_low, verdict)
            assert len(review_tuple) == 7
            assert isinstance(review_tuple[0], int)  # id
            assert isinstance(review_tuple[1], str)  # project
            assert isinstance(review_tuple[3], int)  # risk_high
            assert isinstance(review_tuple[4], int)  # risk_medium
            assert isinstance(review_tuple[5], int)  # risk_low


class TestGetReviewById:
    """Tests for get_review_by_id function"""
    
    def test_get_review_by_id_exists(self, sample_review_data):
        """Should return review dict when ID exists"""
        review_id = save_review("Test Project Delta", sample_review_data)
        review = get_review_by_id(review_id)
        
        assert review is not None
        assert isinstance(review, dict)
        assert review["id"] == review_id
        assert "project" in review
        assert "reviewed_at" in review
        assert "result_json" in review
    
    def test_get_review_by_id_not_exists(self):
        """Should return None when ID doesn't exist"""
        review = get_review_by_id(999999)
        assert review is None
    
    def test_get_review_by_id_data_integrity(self, sample_review_data):
        """Should preserve data integrity"""
        project_name = "Test Project Epsilon"
        review_id = save_review(project_name, sample_review_data)
        review = get_review_by_id(review_id)
        
        assert review["project"] == project_name
        assert json.loads(json.dumps(review["result_json"])) == sample_review_data


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing code"""
    
    def test_repository_api_unchanged(self, sample_review_data):
        """Public API should remain unchanged"""
        # Old code should still work without modifications
        review_id = save_review("Compatibility Test", sample_review_data)
        reviews = get_recent_reviews(limit=10)
        review = get_review_by_id(review_id)
        
        # All functions should work as before
        assert review_id > 0
        assert isinstance(reviews, list)
        assert review is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
