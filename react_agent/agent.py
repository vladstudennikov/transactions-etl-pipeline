"""
ReACT Agent Implementation
Uses Ollama LLM to reason and act using available tools
"""

import json
import re
from typing import Dict, List, Any, Optional
import requests
from agent_functions.agent_tools import TOOLS


class ReACTAgent:
    """
    ReACT (Reasoning and Acting) Agent

    The agent follows a loop:
    1. Thought: Reasons about what to do next
    2. Action: Calls a tool/function
    3. Observation: Receives the result
    4. Repeat until task is complete
    """

    def __init__(
        self,
        model: str = "llama3.1",
        ollama_url: str = "https://ollama.com",
        max_iterations: int = 10,
        verbose: bool = True,
        api_key: str = ""
    ):
        """
        Initialize the ReACT agent

        Args:
            model: Ollama model name (e.g., 'llama3.1', 'mistral', 'mixtral')
            ollama_url: Ollama API base URL
            max_iterations: Maximum number of reasoning loops
            verbose: Whether to print detailed execution logs
            api_key: Ollama API key for cloud models (optional)
        """
        self.model = model
        self.ollama_url = ollama_url
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.api_key = api_key
        self.tools = TOOLS

        # Build tool descriptions for the prompt
        self.tool_descriptions = self._build_tool_descriptions()

    def _build_tool_descriptions(self) -> str:
        """Build formatted tool descriptions for the system prompt"""
        descriptions = []

        descriptions.append("""
parse_transaction:
  Description: Parse an ISO 20022 XML transaction string and extract key fields
  Parameters:
    - xml_string (str): The XML transaction as a string
  Returns: JSON string with transaction details (msg_id, debtor_iban, creditor_iban, amount, currency, etc.)
  Example: parse_transaction(xml_string="<Document>...</Document>")
""")

        descriptions.append("""
get_client_by_iban:
  Description: Retrieve client information from the database by IBAN
  Parameters:
    - iban (str): The IBAN to look up
  Returns: JSON string with client details (risk_score, mean_sum, account_status, etc.) or {"found": false}
  Example: get_client_by_iban(iban="GB29NWBK60161331926819")
""")

        descriptions.append("""
score_transaction:
  Description: Calculate a fraud risk score for a transaction based on amount, client history, and risk factors
  Parameters:
    - tx_json (str): JSON string from parse_transaction
    - client_json (str, optional): JSON string from get_client_by_iban
  Returns: JSON string with score (0-100), classification (ok/suspicious/fraud), and reasons
  Example: score_transaction(tx_json="{...}", client_json="{...}")
""")

        descriptions.append("""
create_alert:
  Description: Create a fraud alert in the database for suspicious transactions
  Parameters:
    - tx_json (str): JSON string with transaction summary
    - client_json (str): JSON string with client summary
    - reason (str): Human-readable reason for the alert
  Returns: JSON string with alert_id and created_at timestamp
  Example: create_alert(tx_json="{...}", client_json="{...}", reason="High value transaction from suspended account")
""")

        return "\n".join(descriptions)

    def _build_system_prompt(self) -> str:
        """Build the system prompt that instructs the LLM on ReACT format"""
        return f"""You are a fraud detection AI agent. You analyze banking transactions and create alerts for suspicious activity.

You have access to these tools:
{self.tool_descriptions}

You must use the ReACT (Reasoning and Acting) format:

Thought: [your reasoning about what to do next]
Action: [tool_name(param1="value1", param2="value2")]
Observation: [result will be provided by the system]
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to provide a final answer
Final Answer: [your conclusion]

IMPORTANT RULES:
1. Always start with "Thought:" to reason about the next step
2. Use "Action:" to call exactly ONE tool at a time
3. Wait for "Observation:" before proceeding (the system will provide this)
4. Use the EXACT tool names and parameter names shown above
5. When calling actions, use this exact format: tool_name(param1="value", param2="value")
6. Parameter values must be properly escaped strings
7. When you have a final answer, use "Final Answer:" to conclude

Example flow for analyzing a transaction:
Thought: I need to first parse the XML transaction to extract details
Action: parse_transaction(xml_string="<Document>...</Document>")
Observation: {{"debtor_iban": "GB29...", "amount": 15000, ...}}
Thought: Now I should check if the debtor client exists in our database
Action: get_client_by_iban(iban="GB29...")
Observation: {{"found": true, "client": {{"risk_score": 75, ...}}}}
Thought: I have the transaction and client data, let me calculate the risk score
Action: score_transaction(tx_json="{{...}}", client_json="{{...}}")
Observation: {{"score": 85, "classification": "fraud", ...}}
Thought: The score is 85 (fraud level), I should create an alert
Action: create_alert(tx_json="{{...}}", client_json="{{...}}", reason="High risk score of 85")
Observation: {{"alert_id": 123, ...}}
Thought: I have completed the analysis and created an alert
Final Answer: Transaction analyzed. Fraud score: 85. Alert #123 created.

Begin!"""

    def _call_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Call Ollama API to generate a response"""
        try:
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Construct proper API endpoint
            # For Ollama Cloud: https://ollama.com/api/chat
            # For local Ollama: http://localhost:11434/api/chat
            api_endpoint = f"{self.ollama_url.rstrip('/')}/api/chat"

            response = requests.post(
                api_endpoint,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for more deterministic reasoning
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Ollama API HTTP error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.JSONDecodeError as e:
            raise RuntimeError(f"Ollama API returned invalid JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")

    def _parse_action(self, text: str) -> Optional[tuple[str, Dict[str, Any]]]:
        """
        Parse an action from the LLM response

        Expected format: tool_name(param1="value1", param2="value2")

        Returns: (tool_name, {param_dict}) or None if no valid action found
        """
        # Look for Action: line
        action_match = re.search(r'Action:\s*(\w+)\((.*?)\)\s*$', text, re.MULTILINE)
        if not action_match:
            return None

        tool_name = action_match.group(1)
        params_str = action_match.group(2)

        if tool_name not in self.tools:
            return None

        # Parse parameters - handle both named and simple formats
        params = {}

        # Try to parse named parameters: param="value"
        param_matches = re.findall(r'(\w+)="((?:[^"\\]|\\.)*)"', params_str)
        if param_matches:
            for param_name, param_value in param_matches:
                # Unescape the value
                param_value = param_value.replace('\\"', '"').replace('\\n', '\n')
                params[param_name] = param_value

        return (tool_name, params)

    def _execute_action(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Execute a tool and return the result"""
        try:
            tool_func = self.tools[tool_name]
            result = tool_func(**params)
            return result
        except Exception as e:
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})

    def run(self, task: str) -> str:
        """
        Run the ReACT agent on a task

        Args:
            task: The task description (e.g., "Analyze this transaction: <XML>...")

        Returns:
            The final answer from the agent
        """
        # Initialize conversation with system prompt and user task
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": task}
        ]

        if self.verbose:
            print(f"\n{'='*80}")
            print(f"TASK: {task}")
            print(f"{'='*80}\n")

        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n--- Iteration {iteration + 1} ---")

            # Get LLM response
            response = self._call_ollama(messages)

            if self.verbose:
                print(f"\nLLM Response:\n{response}")

            # Check if we have a final answer
            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[-1].strip()
                if self.verbose:
                    print(f"\n{'='*80}")
                    print(f"FINAL ANSWER: {final_answer}")
                    print(f"{'='*80}\n")
                return final_answer

            # Try to parse and execute an action
            action_result = self._parse_action(response)

            if action_result:
                tool_name, params = action_result

                if self.verbose:
                    print(f"\nExecuting: {tool_name}({params})")

                # Execute the tool
                observation = self._execute_action(tool_name, params)

                if self.verbose:
                    print(f"Observation: {observation}")

                # Add the assistant's response and the observation to messages
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                # No action found, just continue the conversation
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": "Please provide your next Thought and Action, or a Final Answer if you're done."
                })

        # Max iterations reached
        return "Maximum iterations reached without a final answer."


if __name__ == "__main__":
    # Example usage
    agent = ReACTAgent(model="llama3.1", verbose=True)

    # Example transaction XML (you can replace with actual XML)
    example_task = """
    Analyze this banking transaction for fraud:

    Transaction details:
    - Debtor IBAN: GB29NWBK60161331926819
    - Creditor IBAN: FR1420041010050500013M02606
    - Amount: 25000 EUR

    Please:
    1. Check if the debtor exists in our database
    2. Calculate a fraud risk score
    3. Create an alert if the score is suspicious or fraudulent
    """

    result = agent.run(example_task)
    print(f"\nFinal Result: {result}")
