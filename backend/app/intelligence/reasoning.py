import json
import re
from typing import List, Dict, Any, Tuple, Optional, Callable
from app.utils.logger import logger

class ReasoningEngine:
    """
    Multi-Step Reasoning Engine implementing ReAct (Reasoning + Acting),
    Chain-of-Thought (CoT) decomposition, and self-reflection loops.
    """

    ACTION_REGEX = re.compile(r"Action:\s*([a-zA-Z0-9_\-]+)", re.IGNORECASE)
    ACTION_INPUT_REGEX = re.compile(r"Action Input:\s*(\{.*?\}|\[.*?\]|.+)", re.DOTALL | re.IGNORECASE)
    THOUGHT_REGEX = re.compile(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", re.DOTALL | re.IGNORECASE)
    FINAL_ANSWER_REGEX = re.compile(r"Final Answer:\s*(.*)", re.DOTALL | re.IGNORECASE)

    def __init__(self, max_iterations: int = 4):
        self.max_iterations = max_iterations

    def parse_llm_step(self, text: str) -> Dict[str, Any]:
        """
        Parses LLM output into Thought, Action, Action Input, or Final Answer.
        """
        result = {
            "thought": None,
            "action": None,
            "action_input": None,
            "final_answer": None
        }

        # Check for Final Answer
        fa_match = self.FINAL_ANSWER_REGEX.search(text)
        if fa_match:
            result["final_answer"] = fa_match.group(1).strip()

        # Check for Thought
        th_match = self.THOUGHT_REGEX.search(text)
        if th_match:
            result["thought"] = th_match.group(1).strip()

        # Check for Action
        ac_match = self.ACTION_REGEX.search(text)
        if ac_match:
            result["action"] = ac_match.group(1).strip()

        # Check for Action Input
        ai_match = self.ACTION_INPUT_REGEX.search(text)
        if ai_match and result["action"]:
            raw_input = ai_match.group(1).strip()
            # Clean possible markdown json fences
            if raw_input.startswith("```json"):
                raw_input = raw_input[7:]
            if raw_input.startswith("```"):
                raw_input = raw_input[3:]
            if raw_input.endswith("```"):
                raw_input = raw_input[:-3]
            raw_input = raw_input.strip()

            try:
                result["action_input"] = json.loads(raw_input)
            except Exception:
                # If not JSON, treat as dict with single string param
                result["action_input"] = {"query": raw_input, "raw": raw_input}

        # Fallback: if no final answer and no action was detected, treat entire text as final answer
        if not result["action"] and not result["final_answer"]:
            result["final_answer"] = text.strip()

        return result

    def execute_react_loop(
        self,
        llm_fn: Callable[[List[Dict[str, str]]], Dict[str, Any]],
        system_prompt: str,
        user_message: str,
        tool_executor_fn: Callable[[str, Dict[str, Any]], Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Runs the full ReAct iterative reasoning loop:
        Thought -> Action -> Action Input -> Observation -> Thought -> Final Answer
        """
        trace: List[Dict[str, Any]] = []
        tool_calls: List[Dict[str, Any]] = []
        total_tokens = 0

        # Build initial messages
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            for hist in conversation_history[-6:]:
                messages.append({"role": hist["role"], "content": hist["content"]})
                
        messages.append({"role": "user", "content": user_message})

        current_iteration = 0
        final_answer = ""

        while current_iteration < self.max_iterations:
            current_iteration += 1
            logger.info(f"ReAct reasoning iteration {current_iteration}/{self.max_iterations}")

            # Call LLM
            llm_response = llm_fn(messages)
            total_tokens += llm_response.get("tokens_used", 0)
            llm_text = llm_response.get("content", "")

            parsed = self.parse_llm_step(llm_text)
            thought = parsed.get("thought") or f"Evaluating step {current_iteration}..."
            action = parsed.get("action")
            action_input = parsed.get("action_input")

            # Check if LLM determined final answer
            if parsed.get("final_answer"):
                final_answer = parsed["final_answer"]
                trace.append({
                    "step": current_iteration,
                    "type": "final_answer",
                    "thought": thought,
                    "content": final_answer
                })
                break

            # If an action was identified, execute the tool
            if action:
                logger.info(f"Executing tool '{action}' with input: {action_input}")
                try:
                    observation = tool_executor_fn(action, action_input or {})
                    obs_str = json.dumps(observation, default=str) if not isinstance(observation, str) else observation
                except Exception as e:
                    logger.error(f"Error executing tool '{action}': {str(e)}")
                    obs_str = f"Error executing tool {action}: {str(e)}. Self-reflection: I will adjust my approach or formulate a response."

                step_record = {
                    "step": current_iteration,
                    "type": "tool_execution",
                    "thought": thought,
                    "action": action,
                    "action_input": action_input,
                    "observation": obs_str[:1500]  # truncate to prevent context explosion
                }
                trace.append(step_record)
                tool_calls.append({
                    "tool": action,
                    "params": action_input,
                    "result": obs_str[:500]
                })

                # Append assistant step and observation back to prompt for next iteration
                messages.append({
                    "role": "assistant",
                    "content": f"Thought: {thought}\nAction: {action}\nAction Input: {json.dumps(action_input or {})}"
                })
                messages.append({
                    "role": "user",
                    "content": f"Observation: {obs_str}\nNow continue reasoning. Provide the next Thought and Action or 'Final Answer:'"
                })
            else:
                # Direct response
                final_answer = llm_text
                trace.append({
                    "step": current_iteration,
                    "type": "direct_answer",
                    "thought": thought,
                    "content": final_answer
                })
                break

        # Fallback if loop ended without final answer
        if not final_answer:
            final_answer = llm_text

        # Clean any trailing ReAct markers from final answer
        clean_answer = self._clean_final_output(final_answer)

        return {
            "final_answer": clean_answer,
            "reasoning_trace": trace,
            "tool_calls": tool_calls,
            "tokens_used": total_tokens
        }

    def _clean_final_output(self, text: str) -> str:
        """Removes leftover 'Final Answer:' prefixes"""
        clean = re.sub(r"^Final Answer:\s*", "", text, flags=re.IGNORECASE).strip()
        return clean
