"""
LangChain agent orchestrator with tool calling
"""
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.llm import get_llm
from app.tools import TOOLS_LIST
from app.logger import logger
from app.schemas import QueryResponse, CandidateMatch
from typing import Optional, Dict, Any


# System prompt for HR agent
SYSTEM_PROMPT = """You are an expert HR assistant specializing in candidate evaluation and recruitment.

Your responsibilities:
1. Help find the best candidates for open positions
2. Compare candidates based on job requirements
3. Provide detailed analysis of candidate fit
4. Make evidence-based recommendations

IMPORTANT GUIDELINES:
- Always use the available tools to search and compare candidates
- When asked to find candidates, use search_candidate or compare_candidates
- Provide specific evidence from candidate profiles (skills, experience, years)
- When mentioning candidates, always include their ID in brackets [candidate_id]
- Structure your response with clear reasoning
- Be concise but thorough
- If there are no matching candidates, suggest uploading more CVs

AVAILABLE TOOLS:
- search_candidate: Search for candidates matching specific skills/experience
- compare_candidates: Compare multiple candidates for a role
- get_candidate_details: Get full details for a specific candidate
- list_all_candidates: See all available candidates

When you have enough information to answer the user's question, provide:
1. Which tool you used and why
2. The candidates found
3. Your recommendation with evidence
4. Any relevant warnings or caveats
"""


class HRAgent:
    """LangChain agent for HR queries with structured tool calling"""
    
    def __init__(self):
        """Initialize the HR agent"""
        logger.info("Initializing HR Agent")
        
        # Get LLM
        self.llm = get_llm()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        self.agent = create_tool_calling_agent(
            self.llm,
            TOOLS_LIST,
            self.prompt
        )
        
        # Create executor with error handling
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=TOOLS_LIST,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            return_intermediate_steps=True
        )
        
        logger.info("HR Agent initialized successfully")
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        chat_history: Optional[list] = None
    ) -> QueryResponse:
        """
        Process an HR query using the agent
        
        Args:
            question: HR question or task
            top_k: Number of top results to consider
            chat_history: Optional conversation history
        
        Returns:
            QueryResponse with structured results
        """
        try:
            logger.info(f"Processing query: {question}")
            
            # Prepare input with top_k context
            input_text = question
            if "top_k" not in question.lower():
                input_text = f"{question}\n\n(Consider top {top_k} candidates)"
            
            # Prepare chat history if provided
            messages = []
            if chat_history:
                for msg in chat_history:
                    if msg.get("role") == "user":
                        messages.append(("human", msg.get("content")))
                    elif msg.get("role") == "assistant":
                        messages.append(("assistant", msg.get("content")))
            
            # Invoke agent
            result = self.executor.invoke({
                "input": input_text,
                "chat_history": messages
            })
            
            # Extract response and intermediate steps
            answer = result.get("output", "")
            steps = result.get("intermediate_steps", [])
            
            # Identify which tool was used
            tool_used = "none"
            candidates_found = 0
            
            if steps:
                # Last action is the tool used
                last_action = steps[-1][0]
                tool_used = last_action.tool
                logger.info(f"Agent used tool: {tool_used}")
            
            # Try to extract candidate info from answer
            import re
            candidate_ids = re.findall(r'\[([a-f0-9]{8})\]', answer)
            candidates_found = len(set(candidate_ids))  # Unique candidates
            
            # Parse structured results if available
            structured_results = []
            if candidate_ids:
                from app.vector_store import get_vector_store
                vs = get_vector_store()
                all_candidates = vs.get_all_candidates()
                
                for cid in set(candidate_ids):
                    candidate = next(
                        (c for c in all_candidates if c["candidate_id"] == cid),
                        None
                    )
                    if candidate:
                        match = CandidateMatch(
                            candidate_id=cid,
                            relevance_score=0.85,  # Placeholder
                            matched_criteria=[],
                            evidence=f"Mentioned in agent response",
                            metadata={
                                "candidate_id": cid,
                                "name": candidate.get("name"),
                                "email": candidate.get("email"),
                                "years_experience": candidate.get("years_experience"),
                                "skills": candidate.get("skills")
                            }
                        )
                        structured_results.append(match)
            
            # Determine reasoning from steps
            reasoning = None
            if steps:
                reasoning_parts = []
                for action, observation in steps:
                    reasoning_parts.append(f"- Used {action.tool}: {action.tool_input}")
                reasoning = " → ".join(reasoning_parts) if reasoning_parts else None
            
            response = QueryResponse(
                query=question,
                tool_used=tool_used,
                candidates_found=candidates_found,
                structured_results=structured_results,
                answer=answer,
                reasoning=reasoning
            )
            
            logger.info(f"Query processed successfully: {candidates_found} candidates found")
            return response
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            
            # Return error response
            return QueryResponse(
                query=question,
                tool_used="error",
                candidates_found=0,
                structured_results=[],
                answer=f"I encountered an error processing your query: {str(e)}. Please try again or rephrase your question.",
                reasoning=None
            )


# Global agent instance
_agent: Optional[HRAgent] = None


def get_hr_agent() -> HRAgent:
    """Get or create global HR agent instance"""
    global _agent
    if _agent is None:
        _agent = HRAgent()
    return _agent
