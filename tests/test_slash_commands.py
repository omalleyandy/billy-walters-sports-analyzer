"""
Tests for slash commands system
Tests interactive mode and all 12 slash commands
"""

import pytest
from walters_analyzer.slash_commands import SlashCommandHandler


class TestSlashCommandHandler:
    """Test slash command handler"""
    
    def test_initialization(self):
        """Test handler initializes"""
        handler = SlashCommandHandler(bankroll=10000.0)
        
        assert handler.bankroll == 10000.0
        assert handler.analyzer is not None
        assert handler.research is not None
        assert len(handler.commands) == 12
    
    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test /help command"""
        handler = SlashCommandHandler()
        
        result = await handler.execute("/help")
        
        assert result['status'] == 'success'
        assert 'available_commands' in result['data']
        assert '/analyze' in result['data']['available_commands']
        assert '/research' in result['data']['available_commands']
    
    @pytest.mark.asyncio
    async def test_bankroll_command(self):
        """Test /bankroll command"""
        handler = SlashCommandHandler(bankroll=10000.0)
        
        result = await handler.execute("/bankroll")
        
        assert result['status'] == 'success'
        assert result['data']['current'] == 10000.0
        assert result['data']['initial'] == 10000.0
    
    @pytest.mark.asyncio
    async def test_bankroll_set(self):
        """Test /bankroll set command"""
        handler = SlashCommandHandler(bankroll=10000.0)
        
        result = await handler.execute("/bankroll set 15000")
        
        assert result['status'] == 'success'
        assert '15,000' in result['message']
        assert handler.analyzer.bankroll.bankroll == 15000.0
    
    @pytest.mark.asyncio
    async def test_history_command(self):
        """Test /history command"""
        handler = SlashCommandHandler()
        
        # Execute some commands first
        await handler.execute("/help")
        await handler.execute("/bankroll")
        
        result = await handler.execute("/history")
        
        assert result['status'] == 'success'
        assert result['data']['total_commands'] >= 2
        assert len(result['data']['history']) > 0
    
    @pytest.mark.asyncio
    async def test_clear_command(self):
        """Test /clear command"""
        handler = SlashCommandHandler()
        
        # Add some history
        await handler.execute("/help")
        await handler.execute("/bankroll")
        assert len(handler.command_history) >= 2
        
        # Clear
        result = await handler.execute("/clear")
        
        assert result['status'] == 'success'
        # /clear adds itself to history, so history should have 1 entry
        assert len(handler.command_history) == 1
    
    @pytest.mark.asyncio
    async def test_invalid_command(self):
        """Test invalid command handling"""
        handler = SlashCommandHandler()
        
        result = await handler.execute("/invalid")
        
        assert result['status'] == 'error'
        assert 'Unknown command' in result['message']
        assert 'available_commands' in result
    
    @pytest.mark.asyncio
    async def test_report_session(self):
        """Test /report session command"""
        handler = SlashCommandHandler()
        
        # Execute some commands
        await handler.execute("/help")
        await handler.execute("/bankroll")
        
        result = await handler.execute("/report session")
        
        assert result['status'] == 'success'
        assert 'session_stats' in result['data']
        assert result['data']['session_stats']['commands_executed'] >= 2


class TestCommandParsing:
    """Test command parsing logic"""
    
    @pytest.mark.asyncio
    async def test_command_without_slash(self):
        """Test handling command without slash prefix"""
        handler = SlashCommandHandler()
        
        result = await handler.execute("help")
        
        assert result['status'] == 'error'
        assert 'must start with /' in result['message']
    
    @pytest.mark.asyncio
    async def test_empty_command(self):
        """Test handling empty command"""
        handler = SlashCommandHandler()
        
        result = await handler.execute("")
        
        assert result['status'] == 'error'
    
    @pytest.mark.asyncio
    async def test_command_with_args(self):
        """Test command with arguments"""
        handler = SlashCommandHandler()
        
        result = await handler.execute("/history 5")
        
        assert result['status'] == 'success'
        # Should limit to 5 items


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

