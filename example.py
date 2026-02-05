#!/usr/bin/env python3
"""
Example usage of the Moltbook AI Agent
"""

from moltbook_agent import MoltbookAgent, MoltbookConfig, AIConfig


def example_autonomous_agent():
    """Example: Fully autonomous agent"""
    print("Example 1: Autonomous Agent\n")

    # Configure with your API key
    moltbook_config = MoltbookConfig(api_key="your_moltbook_api_key_here")
    ai_config = AIConfig()

    # Create agent
    agent = MoltbookAgent(moltbook_config, ai_config)

    # Get profile
    profile = agent.get_profile()
    if profile:
        print(f"Logged in as: {profile['name']}\n")

    # Run autonomous browsing
    agent.autonomous_browse()


def example_guided_posting():
    """Example: AI-assisted post creation"""
    print("Example 2: AI-Assisted Posting\n")

    moltbook_config = MoltbookConfig(api_key="your_moltbook_api_key_here")
    ai_config = AIConfig()

    agent = MoltbookAgent(moltbook_config, ai_config)

    # Ask AI to generate post content
    system_prompt = """You are creating content for Moltbook, a social network for AI agents.
Generate a thoughtful post about AI collaboration."""

    response = agent.ask_ai(
        "Create a post about how AI agents can work together effectively. "
        "Include a catchy title and 2-3 paragraph content.",
        system_prompt=system_prompt
    )

    print(f"\nAI Generated:\n{response}")

    # Parse and post (you would extract title/content from response)
    # agent.create_post("general", "AI Collaboration", response)


def example_search_and_engage():
    """Example: Search for relevant content and engage"""
    print("Example 3: Search and Engage\n")

    moltbook_config = MoltbookConfig(api_key="your_moltbook_api_key_here")
    ai_config = AIConfig()

    agent = MoltbookAgent(moltbook_config, ai_config)

    # Search for posts about a topic
    results = agent.search("machine learning")

    if results:
        print(f"Found {len(results)} posts about machine learning\n")

        # Use AI to decide which to engage with
        for post in results[:3]:
            prompt = f"""
Should I engage with this post? Answer YES or NO and explain why.

Title: {post.get('title')}
Content: {post.get('content', '')[:200]}
Score: {post.get('score', 0)}
"""
            decision = agent.ask_ai(prompt)
            print(f"\nPost: {post['title']}")
            print(f"AI Decision: {decision}")


def example_heartbeat_routine():
    """Example: Periodic heartbeat routine"""
    print("Example 4: Heartbeat Routine\n")

    moltbook_config = MoltbookConfig(api_key="your_moltbook_api_key_here")
    ai_config = AIConfig()

    agent = MoltbookAgent(moltbook_config, ai_config)

    # Run heartbeat (could be scheduled with cron or systemd timer)
    agent.heartbeat()


if __name__ == "__main__":
    print("="*60)
    print("Moltbook AI Agent - Examples")
    print("="*60)
    print("\nNote: Set your API key in the examples before running\n")

    # Uncomment the example you want to run:

    # example_autonomous_agent()
    # example_guided_posting()
    # example_search_and_engage()
    # example_heartbeat_routine()

    print("\nEdit example.py and uncomment an example to run it!")
