#!/usr/bin/env python3
"""
Moltbook AI Agent - An intelligent agent that interacts with the Moltbook social network
using the Pollinations AI API for decision-making and content generation.
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MoltbookConfig:
    """Configuration for Moltbook API"""
    base_url: str = "https://www.moltbook.com/api/v1"
    api_key: Optional[str] = None


@dataclass
class AIConfig:
    """Configuration for Pollinations AI API"""
    base_url: str = "https://gen.pollinations.ai/v1/chat/completions"
    model: str = "gemini"
    temperature: float = 0.6
    reasoning_effort: str = "minimal"
    streaming: bool = True


class PollinationsAI:
    """Client for Pollinations AI API"""

    def __init__(self, config: AIConfig):
        self.config = config

    def chat(self, messages: List[Dict[str, str]], stream: bool = True) -> str:
        """Send chat completion request to Pollinations AI"""
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "reasoning_effort": self.config.reasoning_effort,
            "stream": stream
        }

        try:
            response = requests.post(
                self.config.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                stream=stream,
                timeout=60
            )
            response.raise_for_status()

            if stream:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data: '):
                            data_str = line_text[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        full_response += content
                                        print(content, end='', flush=True)
                            except json.JSONDecodeError:
                                continue
                print()  # New line after streaming
                return full_response
            else:
                data = response.json()
                return data['choices'][0]['message']['content']

        except requests.exceptions.RequestException as e:
            print(f"AI API Error: {e}")
            return ""


class MoltbookAgent:
    """AI Agent for interacting with Moltbook social network"""

    def __init__(self, moltbook_config: MoltbookConfig, ai_config: AIConfig):
        self.moltbook = moltbook_config
        self.ai = PollinationsAI(ai_config)
        self.agent_info: Optional[Dict] = None
        self.conversation_history: List[Dict[str, str]] = []

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Moltbook API"""
        if not self.moltbook.api_key:
            print("Error: API key not set. Please register or set API key.")
            return None

        url = f"{self.moltbook.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.moltbook.api_key}",
            "Content-Type": "application/json"
        }

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                print(f"Unsupported method: {method}")
                return None

            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            print(f"Moltbook API Error: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def register(self, name: str, description: str) -> Optional[Dict]:
        """Register a new agent on Moltbook"""
        data = {
            "name": name,
            "description": description
        }

        result = self._make_request("POST", "/agents/register", data=data)
        if result and 'api_key' in result:
            self.moltbook.api_key = result['api_key']
            print(f"\n✓ Agent registered successfully!")
            print(f"  Name: {name}")
            print(f"  Claim URL: {result.get('claim_url', 'N/A')}")
            print(f"  Verification Code: {result.get('verification_code', 'N/A')}")
            print(f"\n⚠ IMPORTANT: Visit the claim URL to verify your agent!")
            print(f"  API Key has been saved internally.")
        return result

    def set_api_key(self, api_key: str):
        """Set API key for authenticated requests"""
        self.moltbook.api_key = api_key
        print("✓ API key set successfully")

    def get_profile(self) -> Optional[Dict]:
        """Get agent's own profile"""
        result = self._make_request("GET", "/agents/me")
        if result:
            self.agent_info = result
        return result

    def get_feed(self, sort: str = "hot", limit: int = 25) -> Optional[List[Dict]]:
        """Get feed of posts"""
        params = {"sort": sort, "limit": limit}
        return self._make_request("GET", "/posts", params=params)

    def get_post(self, post_id: str) -> Optional[Dict]:
        """Get a specific post"""
        return self._make_request("GET", f"/posts/{post_id}")

    def create_post(self, submolt: str, title: str, content: Optional[str] = None,
                   url: Optional[str] = None) -> Optional[Dict]:
        """Create a new post"""
        data = {
            "submolt": submolt,
            "title": title
        }
        if content:
            data["content"] = content
        if url:
            data["url"] = url

        result = self._make_request("POST", "/posts", data=data)
        if result:
            print(f"✓ Post created: {title}")
        return result

    def add_comment(self, post_id: str, content: str, parent_id: Optional[str] = None) -> Optional[Dict]:
        """Add a comment to a post"""
        data = {"content": content}
        if parent_id:
            data["parent_id"] = parent_id

        result = self._make_request("POST", f"/posts/{post_id}/comments", data=data)
        if result:
            print(f"✓ Comment added")
        return result

    def upvote_post(self, post_id: str) -> Optional[Dict]:
        """Upvote a post"""
        return self._make_request("POST", f"/posts/{post_id}/upvote")

    def downvote_post(self, post_id: str) -> Optional[Dict]:
        """Downvote a post"""
        return self._make_request("POST", f"/posts/{post_id}/downvote")

    def search(self, query: str, limit: int = 20) -> Optional[List[Dict]]:
        """Semantic search for posts"""
        params = {"q": query, "limit": limit}
        return self._make_request("GET", "/search", params=params)

    def list_submolts(self) -> Optional[List[Dict]]:
        """List all submolts (communities)"""
        return self._make_request("GET", "/submolts")

    def create_submolt(self, name: str, description: str) -> Optional[Dict]:
        """Create a new submolt"""
        data = {
            "name": name,
            "description": description
        }
        return self._make_request("POST", "/submolts", data=data)

    def subscribe_submolt(self, submolt_name: str) -> Optional[Dict]:
        """Subscribe to a submolt"""
        return self._make_request("POST", f"/submolts/{submolt_name}/subscribe")

    def ask_ai(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """Ask the AI for advice or content generation"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history (last 10 messages)
        messages.extend(self.conversation_history[-10:])

        # Add new user message
        messages.append({"role": "user", "content": user_message})

        # Get AI response
        response = self.ai.chat(messages, stream=self.ai.config.streaming)

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def autonomous_browse(self):
        """Autonomously browse Moltbook and interact intelligently"""
        print("\n🤖 Starting autonomous browsing mode...\n")

        # Get profile
        profile = self.get_profile()
        if not profile:
            print("Failed to get profile. Is your agent claimed?")
            return

        agent_name = profile.get('name', 'Unknown')
        print(f"Agent: {agent_name}")

        # Get feed
        print("\n📰 Fetching feed...")
        feed = self.get_feed(sort="hot", limit=10)
        if not feed or not isinstance(feed, list):
            print("No posts found or error fetching feed")
            return

        print(f"Found {len(feed)} posts\n")

        # Analyze each post with AI
        for idx, post in enumerate(feed[:5], 1):  # Limit to 5 posts
            print(f"\n--- Post {idx}/5 ---")
            post_title = post.get('title', 'Untitled')
            post_content = post.get('content', '')
            post_id = post.get('id', '')
            submolt = post.get('submolt', 'unknown')
            score = post.get('score', 0)

            print(f"Title: {post_title}")
            print(f"Submolt: {submolt}")
            print(f"Score: {score}")

            # Ask AI to decide what to do
            context = f"""
You are an AI agent browsing Moltbook, a social network for AI agents.

Post Details:
- Title: {post_title}
- Content: {post_content[:500]}
- Submolt: {submolt}
- Score: {score}

Decide what action to take. Options:
1. UPVOTE - If the post is interesting or valuable
2. COMMENT - If you have something meaningful to add
3. SKIP - If not interesting

Respond with ONLY one of: UPVOTE, COMMENT, SKIP
Then on a new line, if COMMENT, provide the comment text (keep it concise, 1-2 sentences).
"""

            decision = self.ask_ai(context)

            if "UPVOTE" in decision.upper():
                print(f"  → AI Decision: Upvoting")
                self.upvote_post(post_id)

            elif "COMMENT" in decision.upper():
                # Extract comment from decision
                lines = decision.strip().split('\n')
                comment_text = '\n'.join(lines[1:]).strip() if len(lines) > 1 else "Interesting post!"
                print(f"  → AI Decision: Commenting")
                print(f"  Comment: {comment_text[:100]}...")
                self.add_comment(post_id, comment_text)

            else:
                print(f"  → AI Decision: Skipping")

            # Rate limiting
            time.sleep(2)

        print("\n✓ Autonomous browsing complete")

    def heartbeat(self):
        """Periodic check-in routine - browse and engage with content"""
        print(f"\n💓 Heartbeat at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get profile to verify connection
        profile = self.get_profile()
        if profile:
            print(f"✓ Connected as {profile.get('name', 'Unknown')}")

            # Autonomous activity
            self.autonomous_browse()
        else:
            print("✗ Failed to connect")

    def interactive_mode(self):
        """Interactive command-line interface"""
        print("\n" + "="*60)
        print("🤖 MOLTBOOK AI AGENT - Interactive Mode")
        print("="*60)

        if not self.moltbook.api_key:
            print("\n⚠ No API key set. Please register or set an API key first.")
            print("Commands: register, setkey, help, quit")
        else:
            print("\nType 'help' for available commands")

        while True:
            try:
                command = input("\n> ").strip().lower()

                if not command:
                    continue

                if command == "quit" or command == "exit":
                    print("Goodbye!")
                    break

                elif command == "help":
                    print("\nAvailable Commands:")
                    print("  register          - Register a new agent")
                    print("  setkey            - Set API key")
                    print("  profile           - View your profile")
                    print("  feed              - View feed")
                    print("  post              - Create a post")
                    print("  search            - Search posts")
                    print("  submolts          - List communities")
                    print("  browse            - AI autonomous browsing")
                    print("  heartbeat         - Run heartbeat routine")
                    print("  ask               - Ask AI a question")
                    print("  help              - Show this help")
                    print("  quit              - Exit")

                elif command == "register":
                    name = input("Agent name: ").strip()
                    description = input("Description: ").strip()
                    self.register(name, description)

                elif command == "setkey":
                    api_key = input("API Key: ").strip()
                    self.set_api_key(api_key)

                elif command == "profile":
                    profile = self.get_profile()
                    if profile:
                        print(f"\nProfile:")
                        print(f"  Name: {profile.get('name')}")
                        print(f"  Description: {profile.get('description')}")
                        print(f"  Karma: {profile.get('karma', 0)}")
                        print(f"  Created: {profile.get('created_at')}")

                elif command == "feed":
                    sort = input("Sort by (hot/new/top): ").strip() or "hot"
                    feed = self.get_feed(sort=sort, limit=10)
                    if feed and isinstance(feed, list):
                        print(f"\n📰 Feed ({len(feed)} posts):")
                        for post in feed:
                            print(f"\n  [{post.get('score', 0)}↑] {post.get('title')}")
                            print(f"  by {post.get('author', 'unknown')} in /{post.get('submolt')}")
                            print(f"  ID: {post.get('id')}")

                elif command == "post":
                    submolt = input("Submolt: ").strip()
                    title = input("Title: ").strip()
                    content = input("Content (optional): ").strip() or None
                    self.create_post(submolt, title, content)

                elif command == "search":
                    query = input("Search query: ").strip()
                    results = self.search(query)
                    if results and isinstance(results, list):
                        print(f"\n🔍 Search results ({len(results)} found):")
                        for post in results[:10]:
                            print(f"\n  {post.get('title')}")
                            print(f"  in /{post.get('submolt')} - Score: {post.get('score', 0)}")

                elif command == "submolts":
                    submolts = self.list_submolts()
                    if submolts and isinstance(submolts, list):
                        print(f"\n📁 Submolts ({len(submolts)} communities):")
                        for submolt in submolts:
                            print(f"  /{submolt.get('name')} - {submolt.get('description', 'No description')}")

                elif command == "browse":
                    self.autonomous_browse()

                elif command == "heartbeat":
                    self.heartbeat()

                elif command == "ask":
                    question = input("Ask AI: ").strip()
                    print("\nAI Response:")
                    response = self.ask_ai(question)
                    if not self.ai.config.streaming:
                        print(response)

                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'quit' to exit.")
            except Exception as e:
                print(f"Error: {e}")


def main():
    """Main entry point"""
    print("🚀 Moltbook AI Agent")
    print("Powered by Pollinations AI\n")

    # Check for API key in environment
    api_key = os.environ.get('MOLTBOOK_API_KEY')

    # Initialize configurations
    moltbook_config = MoltbookConfig(api_key=api_key)
    ai_config = AIConfig()

    # Create agent
    agent = MoltbookAgent(moltbook_config, ai_config)

    # Start interactive mode
    agent.interactive_mode()


if __name__ == "__main__":
    main()
