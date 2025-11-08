"""
Unit tests for Anthropic service
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.services.anthropic_svc import AnthropicService
from app.models.schemas import AnalyzeResponse


class TestAnthropicService:
    """Test suite for AnthropicService"""

    @pytest.fixture
    def service(self):
        """Create a service instance with mocked client"""
        with patch('app.services.anthropic_svc.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            service = AnthropicService()
            service.client = mock_client
            service.client.api_key = "test-key"
            return service

    def test_analyze_resume_valid_response(self, service):
        """Test analyze_resume with valid response"""
        # Mock valid response
        mock_response = {
            "score": 75,
            "strengths": [
                "Strong React experience",
                "Excellent problem-solving",
                "Good communication"
            ],
            "weaknesses": [
                "Limited cloud experience",
                "Need system design knowledge"
            ],
            "skills": [
                {"name": "React", "level": "core", "status": "have"},
                {"name": "TypeScript", "level": "core", "status": "have"},
                {"name": "AWS", "level": "adjacent", "status": "gap"}
            ],
            "suggestedRoles": [
                "Senior Frontend Engineer",
                "Full Stack Developer"
            ]
        }
        
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps(mock_response, separators=(',', ':'))
        mock_message.content = [mock_content]
        
        service.client.messages.create.return_value = mock_message
        
        result = service.analyze_resume("Test resume text")
        
        assert result["score"] == 75
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100
        assert len(result["strengths"]) > 0
        assert len(result["weaknesses"]) > 0
        assert len(result["skills"]) > 0
        assert len(result["suggestedRoles"]) > 0
        
        # Validate all skills have required fields
        for skill in result["skills"]:
            assert "name" in skill
            assert "level" in skill
            assert "status" in skill
            assert skill["level"] in ["core", "adjacent", "advanced"]
            assert skill["status"] in ["have", "gap", "learning"]

    def test_analyze_resume_score_range(self, service):
        """Test that score is always between 0 and 100"""
        test_scores = [0, 50, 100]
        
        for score in test_scores:
            mock_response = {
                "score": score,
                "strengths": ["Test"],
                "weaknesses": ["Test"],
                "skills": [{"name": "Test", "level": "core", "status": "have"}],
                "suggestedRoles": ["Test Role"]
            }
            
            mock_message = MagicMock()
            mock_content = MagicMock()
            mock_content.text = json.dumps(mock_response, separators=(',', ':'))
            mock_message.content = [mock_content]
            
            service.client.messages.create.return_value = mock_message
            
            result = service.analyze_resume("Test resume")
            assert 0 <= result["score"] <= 100

    def test_analyze_resume_with_target_role(self, service):
        """Test analyze_resume with target role"""
        mock_response = {
            "score": 80,
            "strengths": ["Test"],
            "weaknesses": ["Test"],
            "skills": [{"name": "Test", "level": "core", "status": "have"}],
            "suggestedRoles": ["Senior Engineer"]
        }
        
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps(mock_response, separators=(',', ':'))
        mock_message.content = [mock_content]
        
        service.client.messages.create.return_value = mock_message
        
        result = service.analyze_resume("Test resume", target_role="Senior Engineer")
        
        assert result["score"] == 80
        # Verify the prompt included target role
        call_args = service.client.messages.create.call_args
        assert "Senior Engineer" in call_args[1]["messages"][0]["content"]

    def test_analyze_resume_retry_on_json_error(self, service):
        """Test that service retries on JSON decode error"""
        # First call returns invalid JSON
        mock_message_invalid = MagicMock()
        mock_content_invalid = MagicMock()
        mock_content_invalid.text = "Invalid JSON {"
        mock_message_invalid.content = [mock_content_invalid]
        
        # Second call returns valid JSON
        mock_response = {
            "score": 75,
            "strengths": ["Test"],
            "weaknesses": ["Test"],
            "skills": [{"name": "Test", "level": "core", "status": "have"}],
            "suggestedRoles": ["Test Role"]
        }
        
        mock_message_valid = MagicMock()
        mock_content_valid = MagicMock()
        mock_content_valid.text = json.dumps(mock_response, separators=(',', ':'))
        mock_message_valid.content = [mock_content_valid]
        
        service.client.messages.create.side_effect = [mock_message_invalid, mock_message_valid]
        
        result = service.analyze_resume("Test resume")
        
        assert result["score"] == 75
        assert service.client.messages.create.call_count == 2

    def test_analyze_resume_retry_on_validation_error(self, service):
        """Test that service retries on validation error"""
        # First call returns invalid schema (score out of range)
        mock_response_invalid = {
            "score": 150,  # Invalid: > 100
            "strengths": ["Test"],
            "weaknesses": ["Test"],
            "skills": [{"name": "Test", "level": "core", "status": "have"}],
            "suggestedRoles": ["Test Role"]
        }
        
        mock_message_invalid = MagicMock()
        mock_content_invalid = MagicMock()
        mock_content_invalid.text = json.dumps(mock_response_invalid, separators=(',', ':'))
        mock_message_invalid.content = [mock_content_invalid]
        
        # Second call returns valid response
        mock_response_valid = {
            "score": 75,
            "strengths": ["Test"],
            "weaknesses": ["Test"],
            "skills": [{"name": "Test", "level": "core", "status": "have"}],
            "suggestedRoles": ["Test Role"]
        }
        
        mock_message_valid = MagicMock()
        mock_content_valid = MagicMock()
        mock_content_valid.text = json.dumps(mock_response_valid, separators=(',', ':'))
        mock_message_valid.content = [mock_content_valid]
        
        service.client.messages.create.side_effect = [mock_message_invalid, mock_message_valid]
        
        result = service.analyze_resume("Test resume")
        
        assert result["score"] == 75
        assert 0 <= result["score"] <= 100
        assert service.client.messages.create.call_count == 2

    def test_analyze_resume_removes_markdown_code_blocks(self, service):
        """Test that service removes markdown code blocks from response"""
        mock_response = {
            "score": 75,
            "strengths": ["Test"],
            "weaknesses": ["Test"],
            "skills": [{"name": "Test", "level": "core", "status": "have"}],
            "suggestedRoles": ["Test Role"]
        }
        
        # Response wrapped in markdown code block
        json_text = json.dumps(mock_response, separators=(',', ':'))
        wrapped_response = f"```json\n{json_text}\n```"
        
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = wrapped_response
        mock_message.content = [mock_content]
        
        service.client.messages.create.return_value = mock_message
        
        result = service.analyze_resume("Test resume")
        
        assert result["score"] == 75

    def test_analyze_resume_missing_api_key(self):
        """Test that service raises error when API key is missing"""
        with patch('app.services.anthropic_svc.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_client.api_key = None
            mock_anthropic.return_value = mock_client
            
            service = AnthropicService()
            service.client = mock_client
            
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is not set"):
                service.analyze_resume("Test resume")

    def test_analyze_resume_all_required_fields(self, service):
        """Test that response contains all required fields"""
        mock_response = {
            "score": 75,
            "strengths": ["Strength 1", "Strength 2"],
            "weaknesses": ["Weakness 1", "Weakness 2"],
            "skills": [
                {"name": "Skill 1", "level": "core", "status": "have"},
                {"name": "Skill 2", "level": "adjacent", "status": "gap"}
            ],
            "suggestedRoles": ["Role 1", "Role 2", "Role 3"]
        }
        
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps(mock_response, separators=(',', ':'))
        mock_message.content = [mock_content]
        
        service.client.messages.create.return_value = mock_message
        
        result = service.analyze_resume("Test resume")
        
        # Verify all required fields are present
        assert "score" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "skills" in result
        assert "suggestedRoles" in result
        
        # Verify field types
        assert isinstance(result["score"], int)
        assert isinstance(result["strengths"], list)
        assert isinstance(result["weaknesses"], list)
        assert isinstance(result["skills"], list)
        assert isinstance(result["suggestedRoles"], list)

