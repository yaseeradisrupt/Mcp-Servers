import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI()
    # methods will go here

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        print("Available tools in session:", response.tools)
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": tool.inputSchema.get("type", "object"),  # Default to "object" if "type" is not present
                    "properties": tool.inputSchema.get("properties", {}),
                    "required": tool.inputSchema.get("required", [])
                }
            },
        } for tool in response.tools]

        print("\nAvailable tools:", available_tools)
        # Initial Claude API call
        response = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=available_tools,
        )
        print("Claude response:", response)
        for choice in response.choices:
            print("Choice:", choice)
            if choice.message:
                print("Message:", choice.message)
                if choice.message.tool_calls is None:
                    print("Assistant message:", choice.message.content)
                    return choice.message.content
                else:
                    print("Tool calls:", choice.message.tool_calls)
                    for tool_call in choice.message.tool_calls:
                        print("Tool call:", tool_call)
                        if tool_call.type == 'function':
                            print("Function call:", tool_call)
                            # Handle function call here if needed
                            # For example, you can call the function and return its result
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments) # Deserialize JSON string
                            print("==========function_args===============:", function_args)
                            result = await self.session.call_tool(function_name, function_args)

                            print("=======Tool call result======:", result)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": str(result.content[0].text)
                            })
                            return result.content[0].text
                    

        # # Process response and handle tool calls
        # final_text = []

        # assistant_message_content = []
        # for content in response.content:
        #     if content.type == 'text':
        #         final_text.append(content.text)
        #         assistant_message_content.append(content)
        #     elif content.type == 'tool_use':
        #         tool_name = content.name
        #         tool_args = content.input

        #         # Execute tool call
        #         result = await self.session.call_tool(tool_name, tool_args)
        #         final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

        #         assistant_message_content.append(content)
        #         messages.append({
        #             "role": "assistant",
        #             "content": assistant_message_content
        #         })
        #         messages.append({
        #             "role": "user",
        #             "content": [
        #                 {
        #                     "type": "tool_result",
        #                     "tool_use_id": content.id,
        #                     "content": result.content
        #                 }
        #             ]
        #         })

        #         # Get next response from Claude
        #         response = self.anthropic.messages.create(
        #             model="claude-3-5-sonnet-20241022",
        #             max_tokens=1000,
        #             messages=messages,
        #             tools=available_tools
        #         )

        #         final_text.append(response.content[0].text)

        # return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()    

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())        