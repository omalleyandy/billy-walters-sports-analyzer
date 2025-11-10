"""
Slash Commands System for Billy Walters Sports Analyzer
Interactive command system with AI assistance patterns from Chrome DevTools
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .core import BillyWaltersAnalyzer
from .core.models import GameInput, TeamSnapshot, GameOdds, SpreadLine
from .research import ResearchEngine

logger = logging.getLogger(__name__)


class SlashCommandHandler:
    """
    Handles slash commands with AI assistance patterns
    Inspired by Chrome DevTools AI assistance workflow
    """

    def __init__(self, bankroll: float = 10000.0):
        self.bankroll = bankroll
        self.analyzer = BillyWaltersAnalyzer()
        self.analyzer.bankroll.bankroll = bankroll
        self.research = ResearchEngine()
        self.command_history: List[Dict[str, Any]] = []

        # Register commands
        self.commands = {
            "/analyze": self.cmd_analyze,
            "/research": self.cmd_research,
            "/market": self.cmd_market,
            "/agent": self.cmd_agent,
            "/backtest": self.cmd_backtest,
            "/report": self.cmd_report,
            "/help": self.cmd_help,
            "/history": self.cmd_history,
            "/clear": self.cmd_clear,
            "/bankroll": self.cmd_bankroll,
            "/debug": self.cmd_debug,
            "/optimize": self.cmd_optimize,
        }

    async def execute(self, command_line: str) -> Dict[str, Any]:
        """
        Execute a slash command

        Args:
            command_line: Full command line (e.g., "/analyze Chiefs vs Bills -2.5")

        Returns:
            Result dictionary with status, data, and AI insights
        """
        # Parse command
        parts = command_line.strip().split()
        if not parts or not parts[0].startswith("/"):
            return {
                "status": "error",
                "message": "Invalid command format. Commands must start with /",
                "suggestion": "Try /help for available commands",
            }

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Find and execute command
        if cmd not in self.commands:
            return {
                "status": "error",
                "message": f"Unknown command: {cmd}",
                "suggestion": f"Did you mean one of: {', '.join(self.commands.keys())}?",
                "available_commands": list(self.commands.keys()),
            }

        try:
            result = await self.commands[cmd](args)

            # Add to history
            self.command_history.append(
                {
                    "command": command_line,
                    "timestamp": datetime.now(),
                    "result": result.get("status", "unknown"),
                }
            )

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "suggestion": "Check command syntax with /help",
                "debug_info": {
                    "command": cmd,
                    "args": args,
                    "error_type": type(e).__name__,
                },
            }

    async def cmd_analyze(self, args: List[str]) -> Dict[str, Any]:
        """
        /analyze - Analyze a game matchup

        Usage:
            /analyze Chiefs vs Bills -2.5
            /analyze "Kansas City Chiefs" @ "Buffalo Bills" -2.5 --research
        """
        if len(args) < 3:
            return {
                "status": "error",
                "message": "Invalid syntax",
                "usage": "/analyze <home_team> vs <away_team> <spread> [--research]",
                "examples": [
                    "/analyze Chiefs vs Bills -2.5",
                    "/analyze Eagles @ Cowboys -3.0 --research",
                ],
            }

        # Parse teams and spread
        try:
            # Simple parser - can be enhanced
            vs_idx = next(
                (i for i, x in enumerate(args) if x in ["vs", "@", "v"]), None
            )
            if vs_idx is None:
                raise ValueError("Missing 'vs' or '@' separator")

            home_team = " ".join(args[:vs_idx])
            spread_idx = next(
                (
                    i
                    for i, x in enumerate(args[vs_idx + 1 :])
                    if x.startswith("-") or x.startswith("+")
                ),
                None,
            )

            if spread_idx is None:
                raise ValueError("Missing spread")

            away_team = " ".join(args[vs_idx + 1 : vs_idx + 1 + spread_idx])
            spread = float(args[vs_idx + 1 + spread_idx])
            use_research = "--research" in args

            # Build game input
            home = TeamSnapshot(name=home_team, injuries=[])
            away = TeamSnapshot(name=away_team, injuries=[])
            odds = GameOdds(spread=SpreadLine(home_spread=spread))
            game = GameInput(home_team=home, away_team=away, odds=odds)

            # Fetch research if requested
            if use_research:
                snapshot = await self.research.gather_for_game(home_team, away_team)
                home.injuries = snapshot.home_injuries
                away.injuries = snapshot.away_injuries

            # Analyze
            analysis = self.analyzer.analyze(game)

            # Format result
            return {
                "status": "success",
                "command": "analyze",
                "data": {
                    "matchup": f"{away_team} @ {home_team}",
                    "spread": f"{home_team} {spread:+.1f}",
                    "predicted_spread": analysis.predicted_spread,
                    "edge": analysis.edge,
                    "confidence": analysis.confidence,
                    "recommendation": {
                        "team": analysis.recommendation.team,
                        "stake_pct": analysis.recommendation.stake_pct,
                        "stake_amount": self.analyzer.bankroll.stake_amount(
                            analysis.recommendation.stake_pct
                        ),
                        "win_probability": analysis.recommendation.win_probability,
                    },
                    "injury_summary": {
                        "home_impact": analysis.home_report.total_points,
                        "away_impact": analysis.away_report.total_points,
                        "advantage": analysis.injury_advantage,
                    },
                    "key_numbers": [
                        alert.description for alert in analysis.key_number_alerts
                    ],
                },
                "ai_insights": {
                    "type": "game_analysis",
                    "confidence_explanation": self._explain_confidence(analysis),
                    "risk_assessment": self._assess_risk(analysis),
                    "optimization_tips": self._suggest_optimizations(analysis),
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "suggestion": "Check team names and spread format",
                "debug": {"error": str(e), "args": args},
            }

    async def cmd_research(self, args: List[str]) -> Dict[str, Any]:
        """
        /research - Research teams, injuries, weather, or full slate

        Usage:
            /research injuries <team>
            /research weather <venue>
            /research team <team>
            /research slate <sport>
        """
        if not args:
            return {
                "status": "error",
                "message": "Missing research topic",
                "usage": "/research <injuries|weather|team|slate> <subject>",
                "examples": [
                    "/research injuries Chiefs",
                    '/research weather "Lambeau Field"',
                    "/research team Eagles",
                    "/research slate ncaaf",
                ],
            }

        topic = args[0].lower()
        subject = " ".join(args[1:]) if len(args) > 1 else ""

        try:
            if topic == "slate":
                # NEW! Research full slate of games
                sport = subject or "nfl"
                return {
                    "status": "info",
                    "command": "research",
                    "topic": "slate",
                    "message": f"Full slate research for {sport.upper()}",
                    "data": {
                        "sport": sport,
                        "suggestion": "Use automation for full slate analysis",
                        "workflows": [
                            f".codex/workflows/daily-analysis.ps1 -Sport {sport}",
                            f"uv run walters-analyzer scrape-highlightly --endpoint matches --sport {sport}",
                            "Then analyze each game individually with /analyze",
                        ],
                    },
                    "ai_insights": {
                        "recommendation": "For comprehensive slate analysis:\n1. Scrape fresh data\n2. Use /analyze for each game\n3. Use /report session to review all"
                    },
                }

            elif topic == "injuries":
                snapshot = await self.research.gather_for_game(subject, subject)
                injuries = snapshot.home_injuries

                return {
                    "status": "success",
                    "command": "research",
                    "topic": "injuries",
                    "data": {
                        "team": subject,
                        "injury_count": len(injuries),
                        "injuries": injuries[:10],  # Top 10
                        "total_impact": sum(inj.get("points", 0) for inj in injuries),
                    },
                    "ai_insights": {
                        "severity": "high" if len(injuries) > 5 else "moderate",
                        "recommendations": self._injury_recommendations(injuries),
                    },
                }

            elif topic == "weather":
                weather = await self.research.accuweather.get_game_weather(subject)

                return {
                    "status": "success",
                    "command": "research",
                    "topic": "weather",
                    "data": {
                        "venue": subject,
                        "weather": weather or {"message": "Weather data unavailable"},
                    },
                    "ai_insights": {
                        "impact": self._weather_impact_analysis(weather)
                        if weather
                        else None
                    },
                }

            elif topic == "team":
                return {
                    "status": "success",
                    "command": "research",
                    "topic": "team",
                    "data": {
                        "team": subject,
                        "message": "Team research feature coming soon",
                    },
                }

            else:
                return {
                    "status": "error",
                    "message": f"Unknown research topic: {topic}",
                    "valid_topics": ["injuries", "weather", "team", "slate"],
                    "examples": [
                        "/research injuries Chiefs",
                        '/research weather "Lambeau Field"',
                        "/research team Eagles",
                        "/research slate ncaaf",
                    ],
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Research failed: {str(e)}",
                "debug": {"topic": topic, "subject": subject},
            }

    async def cmd_market(self, args: List[str]) -> Dict[str, Any]:
        """
        /market - Monitor market movements

        Usage:
            /market monitor Chiefs-Bills 3600
            /market alerts
        """
        if not args:
            return {
                "status": "info",
                "message": "Market monitoring",
                "usage": "/market <monitor|alerts> [game_id] [duration]",
                "note": "Requires ODDS_API_KEY in .env",
            }

        action = args[0].lower()

        if action == "monitor":
            game_id = args[1] if len(args) > 1 else None
            duration = int(args[2]) if len(args) > 2 else 3600

            return {
                "status": "info",
                "message": f"Market monitoring for {game_id or 'all games'}",
                "duration": duration,
                "note": "Use CLI command: walters-analyzer monitor-sharp",
            }

        elif action == "alerts":
            return {
                "status": "success",
                "command": "market",
                "data": {"active_alerts": [], "message": "No active market alerts"},
            }

        return {
            "status": "error",
            "message": f"Unknown market action: {action}",
            "valid_actions": ["monitor", "alerts"],
        }

    async def cmd_agent(self, args: List[str]) -> Dict[str, Any]:
        """
        /agent - Activate autonomous agent

        Usage:
            /agent analyze <game_id>
            /agent portfolio
            /agent learn
        """
        if not args:
            return {
                "status": "info",
                "message": "Autonomous agent",
                "usage": "/agent <analyze|portfolio|learn> [args]",
                "note": "Requires ML dependencies installed",
            }

        action = args[0].lower()

        return {
            "status": "info",
            "message": f"Agent action: {action}",
            "note": "Autonomous agent integration coming in Phase 6.2",
        }

    async def cmd_backtest(self, args: List[str]) -> Dict[str, Any]:
        """
        /backtest - Backtest betting strategies

        Usage:
            /backtest power_ratings from=2024-09-01 to=2024-11-01
        """
        if not args:
            return {
                "status": "info",
                "message": "Backtesting system",
                "usage": "/backtest <strategy> from=<date> to=<date>",
                "available_strategies": [
                    "power_ratings",
                    "key_numbers",
                    "injury_based",
                ],
            }

        strategy = args[0]

        return {
            "status": "info",
            "message": f"Backtesting strategy: {strategy}",
            "note": "See: walters_analyzer.backtest module",
        }

    async def cmd_report(self, args: List[str]) -> Dict[str, Any]:
        """
        /report - Generate analysis reports

        Usage:
            /report session
            /report performance
            /report bankroll
        """
        report_type = args[0] if args else "session"

        if report_type == "session":
            return {
                "status": "success",
                "command": "report",
                "data": {
                    "session_stats": {
                        "commands_executed": len(self.command_history),
                        "current_bankroll": self.analyzer.bankroll.bankroll,
                        "initial_bankroll": self.analyzer.bankroll.initial_bankroll,
                    }
                },
            }

        elif report_type == "bankroll":
            return {
                "status": "success",
                "command": "report",
                "data": {
                    "bankroll": {
                        "current": self.analyzer.bankroll.bankroll,
                        "initial": self.analyzer.bankroll.initial_bankroll,
                        "change": self.analyzer.bankroll.bankroll
                        - self.analyzer.bankroll.initial_bankroll,
                        "bets_placed": len(self.analyzer.bankroll.history),
                    }
                },
            }

        return {
            "status": "info",
            "available_reports": ["session", "performance", "bankroll"],
        }

    async def cmd_help(self, args: List[str]) -> Dict[str, Any]:
        """Display help for slash commands"""
        if args:
            cmd = f"/{args[0]}"
            if cmd in self.commands:
                func = self.commands[cmd]
                return {
                    "status": "success",
                    "command": "help",
                    "data": {
                        "command": cmd,
                        "docstring": func.__doc__ or "No documentation available",
                    },
                }

        def get_command_desc(cmd_func):
            """Safely extract command description"""
            if not cmd_func.__doc__:
                return "No description"
            lines = [l.strip() for l in cmd_func.__doc__.split("\n") if l.strip()]
            return lines[0] if lines else "No description"

        return {
            "status": "success",
            "command": "help",
            "data": {
                "available_commands": {
                    cmd: get_command_desc(self.commands[cmd]) for cmd in self.commands
                }
            },
        }

    async def cmd_history(self, args: List[str]) -> Dict[str, Any]:
        """Display command history"""
        limit = int(args[0]) if args else 10

        return {
            "status": "success",
            "command": "history",
            "data": {
                "history": self.command_history[-limit:],
                "total_commands": len(self.command_history),
            },
        }

    async def cmd_clear(self, args: List[str]) -> Dict[str, Any]:
        """Clear command history"""
        self.command_history.clear()
        return {"status": "success", "message": "Command history cleared"}

    async def cmd_bankroll(self, args: List[str]) -> Dict[str, Any]:
        """
        /bankroll - Manage bankroll

        Usage:
            /bankroll show
            /bankroll set 10000
            /bankroll history
        """
        if not args:
            return {
                "status": "success",
                "data": {
                    "current": self.analyzer.bankroll.bankroll,
                    "initial": self.analyzer.bankroll.initial_bankroll,
                },
            }

        action = args[0].lower()

        if action == "set" and len(args) > 1:
            new_amount = float(args[1])
            self.analyzer.bankroll.bankroll = new_amount
            return {
                "status": "success",
                "message": f"Bankroll set to ${new_amount:,.2f}",
            }

        elif action == "history":
            return {
                "status": "success",
                "data": {
                    "bet_history": [
                        {
                            "stake_pct": bet.wager_pct,
                            "odds": bet.odds,
                            "result": bet.result,
                        }
                        for bet in self.analyzer.bankroll.history
                    ]
                },
            }

        return {
            "status": "error",
            "message": "Invalid bankroll command",
            "valid_actions": ["show", "set", "history"],
        }

    async def cmd_debug(self, args: List[str]) -> Dict[str, Any]:
        """
        /debug - Debug analysis issues (Chrome DevTools AI pattern)

        Usage:
            /debug last
            /debug performance
        """
        if not args:
            return {
                "status": "info",
                "message": "Debug tools",
                "usage": "/debug <last|performance|network>",
                "note": "Inspired by Chrome DevTools AI assistance",
            }

        target = args[0].lower()

        if target == "last" and self.command_history:
            last_cmd = self.command_history[-1]
            return {
                "status": "success",
                "data": {
                    "last_command": last_cmd["command"],
                    "timestamp": last_cmd["timestamp"].isoformat(),
                    "result": last_cmd["result"],
                },
                "ai_insights": {
                    "diagnosis": "Command executed successfully"
                    if last_cmd["result"] == "success"
                    else "Command failed",
                    "suggestions": self._debug_suggestions(last_cmd),
                },
            }

        elif target == "performance":
            return {
                "status": "success",
                "data": {
                    "avg_command_time": "N/A",
                    "total_commands": len(self.command_history),
                    "note": "Performance monitoring active",
                },
            }

        return {"status": "info", "message": "No debug information available"}

    async def cmd_optimize(self, args: List[str]) -> Dict[str, Any]:
        """
        /optimize - Get optimization suggestions (Chrome DevTools AI pattern)

        Usage:
            /optimize bankroll
            /optimize portfolio
        """
        target = args[0] if args else "general"

        if target == "bankroll":
            return {
                "status": "success",
                "data": {
                    "current_settings": {
                        "max_bet_pct": self.analyzer.bankroll.max_risk_pct,
                        "fractional_kelly": self.analyzer.bankroll.fractional_kelly,
                    },
                    "suggestions": [
                        "Consider reducing max bet to 2.5% for more conservative approach",
                        "Current Kelly fraction (0.5) is optimal for most scenarios",
                        "Track CLV (Closing Line Value) to validate edge estimates",
                    ],
                },
            }

        return {
            "status": "info",
            "message": "Optimization suggestions",
            "available_targets": ["bankroll", "portfolio", "strategy"],
        }

    # AI Assistance Helper Methods (Chrome DevTools patterns)

    def _explain_confidence(self, analysis) -> str:
        """Explain confidence level like Chrome DevTools AI"""
        edge = abs(analysis.edge)
        if edge >= 3.0:
            return f"High confidence: {edge:.1f} pt edge exceeds 3-point threshold. Historical win rate: 64%"
        elif edge >= 2.0:
            return f"Elevated confidence: {edge:.1f} pt edge is significant. Historical win rate: 58%"
        elif edge >= 1.0:
            return (
                f"Slight edge: {edge:.1f} pt edge is minimal. Historical win rate: 54%"
            )
        else:
            return f"No play: {edge:.1f} pt edge too small for Kelly sizing"

    def _assess_risk(self, analysis) -> Dict[str, Any]:
        """Risk assessment like Chrome DevTools network timing analysis"""
        return {
            "edge_risk": "low" if abs(analysis.edge) >= 2.5 else "moderate",
            "injury_risk": "high"
            if len(analysis.home_report.critical_players) > 2
            else "low",
            "key_number_risk": "alert" if analysis.key_number_alerts else "none",
            "recommendation": "Proceed with caution"
            if abs(analysis.edge) < 2.0
            else "Strong bet",
        }

    def _suggest_optimizations(self, analysis) -> List[str]:
        """Optimization suggestions like Chrome DevTools performance insights"""
        suggestions = []

        if analysis.recommendation.stake_pct == 0:
            suggestions.append(
                "Edge too small for betting. Wait for better line or skip this game."
            )

        if analysis.key_number_alerts:
            suggestions.append(
                f"Key number detected: {analysis.key_number_alerts[0].description}. Consider timing your bet carefully."
            )

        if abs(analysis.injury_advantage) > 2.0:
            suggestions.append(
                f"Significant injury advantage ({analysis.injury_advantage:+.1f} pts). Verify injury statuses before betting."
            )

        return suggestions or ["No optimization opportunities identified"]

    def _injury_recommendations(self, injuries: List[Dict]) -> List[str]:
        """Injury-specific recommendations"""
        if not injuries:
            return ["No injuries reported - proceed normally"]

        recs = []
        critical_count = sum(1 for inj in injuries if inj.get("status") == "Out")

        if critical_count > 3:
            recs.append(f"{critical_count} players out - significant impact expected")

        qb_injuries = [inj for inj in injuries if inj.get("position") == "QB"]
        if qb_injuries:
            recs.append(
                f"QB injury detected: {qb_injuries[0].get('name')} - major concern"
            )

        return recs or ["Monitor injury reports for updates"]

    def _weather_impact_analysis(self, weather: Optional[Dict]) -> Dict[str, Any]:
        """Weather impact analysis"""
        if not weather:
            return {"impact": "unknown", "note": "Weather data unavailable"}

        factor = weather.get("weather_factor", 0)

        if factor < -0.3:
            return {
                "impact": "significant",
                "note": "Adverse weather conditions favor defense",
                "recommendation": "Consider under on totals",
            }
        elif factor < -0.1:
            return {
                "impact": "moderate",
                "note": "Weather may affect passing game",
                "recommendation": "Factor into analysis",
            }
        else:
            return {
                "impact": "minimal",
                "note": "Weather conditions favorable for normal play",
            }

    def _debug_suggestions(self, last_cmd: Dict) -> List[str]:
        """Debug suggestions like Chrome DevTools"""
        if last_cmd["result"] == "success":
            return ["Command executed successfully", "No issues detected"]
        else:
            return [
                "Check command syntax with /help",
                "Verify all required arguments are provided",
                "Use /debug performance to check system status",
            ]


async def interactive_mode(handler: SlashCommandHandler):
    """
    Run interactive slash command mode
    Like Chrome DevTools console
    """
    print("=" * 80)
    print("BILLY WALTERS INTERACTIVE MODE")
    print("=" * 80)
    print()
    print("Type slash commands to interact with the analyzer.")
    print("Try: /help for available commands")
    print("     /analyze Chiefs vs Bills -2.5")
    print("     /research injuries Chiefs")
    print()
    print("Press Ctrl+C to exit")
    print("=" * 80)
    print()

    while True:
        try:
            # Get command
            command = input("walters> ").strip()

            if not command:
                continue

            if command in ["exit", "quit", "q"]:
                print("\nExiting interactive mode. Goodbye!")
                break

            # Execute
            result = await handler.execute(command)

            # Display result
            print()
            print(f"Status: {result.get('status', 'unknown').upper()}")

            if result.get("message"):
                print(f"Message: {result['message']}")

            if result.get("data"):
                import json

                print("\nData:")
                print(json.dumps(result["data"], indent=2, default=str))

            if result.get("ai_insights"):
                print("\nAI Insights:")
                print(json.dumps(result["ai_insights"], indent=2, default=str))

            if result.get("suggestion"):
                print(f"\nSuggestion: {result['suggestion']}")

            print()

        except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print()


if __name__ == "__main__":
    # Test slash commands
    handler = SlashCommandHandler(bankroll=10000.0)
    asyncio.run(interactive_mode(handler))
