"""
Large Language Model Service.

This service handles interactions with the Gemini LLM for invoice analysis
and chatbot functionality.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with Large Language Models.

    This class provides methods for invoice analysis and chatbot interactions
    using the Gemini LLM through the new Google Gen AI SDK.
    """

    def __init__(self):
        """Initialize the LLM service with Gemini configuration."""
        self.logger = logger

        # Initialize the Google GenAI client
        if settings.GOOGLE_API_KEY:
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        else:
            # If no API key provided, client will use environment variables
            self.client = genai.Client()

        # Set the model name
        self.model_name = settings.LLM_MODEL

        self.logger.info("LLM Service initialized with Google Gen AI SDK")

    async def analyze_invoice(
        self, invoice_text: str, policy_text: str, employee_name: str
    ) -> Dict[str, Any]:
        """
        Analyze an invoice against HR reimbursement policy.

        Args:
            invoice_text: Extracted text from the invoice PDF
            policy_text: HR reimbursement policy text
            employee_name: Name of the employee

        Returns:
            Dictionary containing analysis results with status, reason, and amounts
        """
        self.logger.info(f"Analyzing invoice for employee: {employee_name}")

        try:
            # Create analysis prompt
            system_prompt = self._get_invoice_analysis_prompt()
            user_prompt = self._format_invoice_analysis_input(
                invoice_text, policy_text, employee_name
            )

            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Get response from Gemini using the new SDK
            response = await self._generate_response(full_prompt)

            # Parse the response
            analysis_result = self._parse_invoice_analysis_response(response)

            self.logger.info(
                f"Invoice analysis completed for {employee_name}: {analysis_result.get('status')}"
            )
            return analysis_result

        except Exception as e:
            self.logger.error(f"Error analyzing invoice: {e}", exc_info=True)
            # Return a default error response
            return {
                "status": "declined",
                "reason": f"Error during analysis: {str(e)}",
                "total_amount": 0.0,
                "reimbursement_amount": 0.0,
                "currency": "INR",
                "categories": [],
                "policy_violations": [f"Analysis failed: {str(e)}"],
            }

    def _get_invoice_analysis_prompt(self) -> str:
        """
        Get the system prompt for invoice analysis.

        Returns:
            System prompt for invoice analysis
        """
        return """You are an expert invoice analyst for HR reimbursement processing. Your task is to analyze employee invoices against company reimbursement policies and determine the appropriate reimbursement status.

ANALYSIS REQUIREMENTS:
1. Carefully read the HR reimbursement policy provided
2. Analyze the invoice content for expense details, amounts, dates, and categories
3. Compare invoice items against policy guidelines
4. Determine reimbursement status: "fully_reimbursed", "partially_reimbursed", or "declined"
5. Provide detailed reasoning for your decision
6. Calculate exact reimbursement amounts when applicable
7. ALWAYS extract the total amount and currency from the invoice
8. ALWAYS identify expense categories based on the invoice content

OUTPUT FORMAT:
Return your analysis as a JSON object with the following structure:
{
    "status": "fully_reimbursed|partially_reimbursed|declined",
    "reason": "Detailed explanation of the decision",
    "total_amount": <total invoice amount as float - REQUIRED>,
    "reimbursement_amount": <amount to be reimbursed as float>,
    "currency": "<currency code (INR, USD, EUR, etc.) - REQUIRED>",
    "categories": ["<expense category 1>", "<expense category 2>"] - REQUIRED array,
    "policy_violations": ["<violation 1>", "<violation 2>"] or null if none
}

IMPORTANT EXTRACTION RULES:
- TOTAL_AMOUNT: Look for amounts like ₹233, $100, €50, Rs.150, etc. Extract the numeric value.
- CURRENCY: Based on currency symbol: ₹ or Rs. = "INR", $ = "USD", € = "EUR", £ = "GBP"
- CATEGORIES: Common categories include "travel", "meals", "office_supplies", "accommodation", "cab", "fuel", "communication", etc.
- If no amount is found, set total_amount to 0.0
- If no currency symbol found, default to "INR" for Indian companies
- Categories should be descriptive and based on expense type (e.g., ["travel", "cab"] for cab expenses)

ANALYSIS GUIDELINES:
- Be thorough and accurate in your analysis
- Consider all policy rules and restrictions
- Identify specific policy violations if any
- Calculate partial reimbursements when some items are approved and others are not
- Look for receipt dates, vendor information, and expense descriptions
- Consider spending limits, approval requirements, and eligible expense types
- Provide clear, professional reasoning that an HR representative could understand"""

    def _format_invoice_analysis_input(
        self, invoice_text: str, policy_text: str, employee_name: str
    ) -> str:
        """
        Format the input for invoice analysis.

        Args:
            invoice_text: Invoice content
            policy_text: Policy content
            employee_name: Employee name

        Returns:
            Formatted prompt for analysis
        """
        return f"""EMPLOYEE: {employee_name}
DATE: {datetime.now().strftime("%Y-%m-%d")}

HR REIMBURSEMENT POLICY:
{policy_text}

INVOICE TO ANALYZE:
{invoice_text}

Please analyze this invoice against the HR policy and provide your assessment in the required JSON format."""

    def _parse_invoice_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response for invoice analysis.

        Args:
            response: Raw LLM response

        Returns:
            Parsed analysis result
        """
        try:
            # Try to extract JSON from the response
            response = response.strip()

            # Look for JSON in the response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)

                # Validate required fields
                required_fields = ["status", "reason"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field: {field}")

                # Ensure proper data types and set defaults for optional fields
                result["total_amount"] = (
                    float(result.get("total_amount", 0.0))
                    if result.get("total_amount") is not None
                    else 0.0
                )
                result["reimbursement_amount"] = (
                    float(result.get("reimbursement_amount", 0.0))
                    if result.get("reimbursement_amount") is not None
                    else 0.0
                )
                result.setdefault("currency", "INR")
                result.setdefault("categories", [])
                result.setdefault("policy_violations", None)

                # Ensure categories is always a list
                if not isinstance(result.get("categories"), list):
                    result["categories"] = []

                return result
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            self.logger.error(f"Error parsing invoice analysis response: {e}")
            # Return a fallback response
            return {
                "status": "declined",
                "reason": f"Error parsing analysis: {str(e)}. Raw response: {response[:200]}...",
                "total_amount": 0.0,
                "reimbursement_amount": 0.0,
                "currency": "INR",
                "categories": [],
                "policy_violations": ["Response parsing failed"],
            }

    async def generate_chat_response(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a chatbot response using retrieved documents and conversation history.

        Args:
            query: User query
            context_documents: Retrieved documents from vector search
            conversation_history: Previous conversation messages

        Returns:
            Generated response
        """
        self.logger.info(f"Generating chat response for query: {query[:100]}...")

        try:
            # Create chat prompt
            system_prompt = self._get_chat_system_prompt()
            user_prompt = self._format_chat_input(
                query, context_documents, conversation_history
            )

            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Get response from Gemini
            response = await self._generate_response(full_prompt)

            self.logger.info("Chat response generated successfully")
            return response

        except Exception as e:
            self.logger.error(f"Error generating chat response: {e}", exc_info=True)
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

    def _get_chat_system_prompt(self) -> str:
        """
        Get the system prompt for chatbot interactions.

        Returns:
            System prompt for chatbot
        """
        return """You are an intelligent assistant for an Invoice Reimbursement System. Your role is to help users query and understand invoice reimbursement data using the provided context documents.

CAPABILITIES:
- Answer questions about invoice reimbursement status and details
- Search for specific invoices by employee name, date, amount, or status
- Explain reimbursement decisions and policy violations
- Provide summaries and statistics about processed invoices
- Help users understand reimbursement policies and procedures

RESPONSE GUIDELINES:
1. Always base your answers on the provided context documents
2. Use markdown formatting for better readability
3. Be accurate and cite specific information when available
4. If you don't have enough information, clearly state this
5. Provide helpful suggestions for alternative queries
6. Maintain a professional and helpful tone
7. Include relevant details like amounts, dates, and employee names
8. Use tables or lists to organize information clearly

RESPONSE FORMAT:
- Use **bold** for important information like amounts and statuses
- Use bullet points for lists
- Use tables for structured data
- Include relevant quotes from source documents when helpful
- End with suggestions for related queries if appropriate

Remember: Only provide information that can be found in the context documents. Do not make up or assume information."""

    def _format_chat_input(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Format the input for chat response generation.

        Args:
            query: User query
            context_documents: Retrieved context documents
            conversation_history: Previous conversation

        Returns:
            Formatted prompt for chat
        """
        prompt_parts = []

        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("CONVERSATION HISTORY:")
            for msg in conversation_history[-6:]:  # Include last 3 exchanges
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt_parts.append(f"{role.upper()}: {content}")
            prompt_parts.append("")

        # Add context documents
        if context_documents:
            prompt_parts.append("RELEVANT INVOICE DATA:")
            for i, doc in enumerate(
                context_documents[:5], 1
            ):  # Limit to top 5 documents
                metadata = doc.get("metadata", {})
                content = doc.get("content", "")

                prompt_parts.append(f"Document {i}:")
                prompt_parts.append(
                    f"- Employee: {metadata.get('employee_name', 'Unknown')}"
                )
                prompt_parts.append(
                    f"- Invoice: {metadata.get('invoice_filename', 'Unknown')}"
                )
                prompt_parts.append(f"- Status: {metadata.get('status', 'Unknown')}")
                prompt_parts.append(
                    f"- Amount: {metadata.get('reimbursement_amount', 'Unknown')}"
                )
                prompt_parts.append(f"- Date: {metadata.get('date', 'Unknown')}")
                prompt_parts.append(f"- Content: {content[:300]}...")
                prompt_parts.append("")
        else:
            prompt_parts.append("No relevant invoice data found for this query.")
            prompt_parts.append("")

        # Add current query
        prompt_parts.append(f"CURRENT QUERY: {query}")
        prompt_parts.append("")
        prompt_parts.append(
            "Please provide a helpful response based on the available information."
        )

        return "\n".join(prompt_parts)

    async def _generate_response(self, prompt: str) -> str:
        """
        Generate response using Google Gen AI SDK.

        Args:
            prompt: The full prompt to send to the model

        Returns:
            Generated response text
        """
        try:
            # Create the generation request using the new SDK
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.MAX_TOKENS,
                ),
            )

            # Extract text from response
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    text = candidate.content.parts[0].text
                    if text is not None:
                        return text
                    else:
                        raise ValueError("Response text is None")
                else:
                    raise ValueError("No content found in response")
            else:
                raise ValueError("No candidates in response")

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise

    async def generate_streaming_response(self, prompt: str):
        """
        Generate streaming response using Google Gen AI SDK with optimized streaming.

        Args:
            prompt: The full prompt to send to the model

        Yields:
            Generated response chunks as they are produced
        """
        try:
            # Create the streaming generation request using the new SDK
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.MAX_TOKENS,
                ),
            )

            # Track streaming metrics
            chunk_count = 0
            total_tokens = 0

            # Iterate through the stream and yield chunks
            async for chunk in stream:
                if chunk.candidates and len(chunk.candidates) > 0:
                    candidate = chunk.candidates[0]
                    if candidate.content and candidate.content.parts:
                        text = candidate.content.parts[0].text
                        if text is not None and text.strip():
                            chunk_count += 1
                            total_tokens += len(text.split())

                            # Log every 10th chunk for monitoring
                            if chunk_count % 10 == 0:
                                self.logger.debug(
                                    f"Streaming progress: {chunk_count} chunks, ~{total_tokens} tokens"
                                )

                            yield text

            self.logger.info(
                f"Streaming completed: {chunk_count} chunks, ~{total_tokens} tokens"
            )

        except Exception as e:
            self.logger.error(f"Error generating streaming response: {e}")
            # Yield error message
            yield f"Error: {str(e)}"

    async def generate_chat_response_streaming(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ):
        """
        Generate a streaming chatbot response using retrieved documents and conversation history.

        Args:
            query: User query
            context_documents: Retrieved documents from vector search
            conversation_history: Previous conversation messages

        Yields:
            Generated response chunks as they are produced
        """
        self.logger.info(
            f"Generating streaming chat response for query: {query[:100]}..."
        )

        try:
            # Create chat prompt
            system_prompt = self._get_chat_system_prompt()
            user_prompt = self._format_chat_input(
                query, context_documents, conversation_history
            )

            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Get streaming response from Gemini
            async for chunk in self.generate_streaming_response(full_prompt):
                yield chunk

            self.logger.info("Streaming chat response completed successfully")

        except Exception as e:
            self.logger.error(
                f"Error generating streaming chat response: {e}", exc_info=True
            )
            yield f"I apologize, but I encountered an error while processing your request: {str(e)}"

    async def generate_query_suggestions(
        self,
        original_query: str,
        context_documents: List[Dict[str, Any]],
        query_type: str = "general",
    ) -> List[str]:
        """
        Generate related query suggestions based on the current query and context.

        Args:
            original_query: The original user query
            context_documents: Retrieved context documents
            query_type: Type of the original query

        Returns:
            List of suggested related queries
        """
        try:
            # Create suggestion prompt
            system_prompt = self._get_suggestion_system_prompt()
            user_prompt = self._format_suggestion_input(
                original_query, context_documents, query_type
            )

            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Get suggestions from LLM
            response = await self._generate_response(full_prompt)

            # Parse suggestions from response
            suggestions = self._parse_suggestions_response(response)

            self.logger.info(f"Generated {len(suggestions)} query suggestions")
            return suggestions

        except Exception as e:
            self.logger.error(f"Error generating query suggestions: {e}", exc_info=True)
            # Return fallback suggestions based on query type
            return self._get_fallback_suggestions(query_type)

    def _get_suggestion_system_prompt(self) -> str:
        """
        Get the system prompt for generating query suggestions.

        Returns:
            System prompt for suggestion generation
        """
        return """You are an assistant that generates helpful query suggestions for an Invoice Reimbursement System. Based on the user's current query and the available data, suggest 3-5 related queries that the user might find useful.

GUIDELINES FOR SUGGESTIONS:
1. Make suggestions specific and actionable
2. Vary the type of queries (status filters, employee-specific, date ranges, amounts, categories)
3. Use the context to make relevant suggestions
4. Keep suggestions concise and clear
5. Include different perspectives on the same data
6. Suggest both broader and more specific queries

RESPONSE FORMAT:
Return only a JSON array of suggestion strings, nothing else:
["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4", "suggestion 5"]

EXAMPLE SUGGESTIONS:
- "Show me all approved invoices for [employee]"
- "What was the total amount of declined invoices last month?"
- "Which invoices had policy violations?"
- "Show me invoices over ₹5000"
- "List all travel expense invoices"
- "Show me partially reimbursed invoices"
- "What are the most common expense categories?"
- "Which employees have the most invoices?"
"""

    def _format_suggestion_input(
        self,
        original_query: str,
        context_documents: List[Dict[str, Any]],
        query_type: str,
    ) -> str:
        """
        Format the input for suggestion generation.

        Args:
            original_query: Original user query
            context_documents: Context documents
            query_type: Type of query

        Returns:
            Formatted prompt for suggestions
        """
        prompt_parts = []

        prompt_parts.append(f"ORIGINAL QUERY: {original_query}")
        prompt_parts.append(f"QUERY TYPE: {query_type}")
        prompt_parts.append("")

        # Add context summary
        if context_documents:
            prompt_parts.append("AVAILABLE DATA CONTEXT:")

            # Extract key information from context
            employees = set()
            statuses = set()
            categories = set()
            amounts = []

            for doc in context_documents[:5]:  # Limit context analysis
                metadata = doc.get("metadata", {})
                if metadata.get("employee_name"):
                    employees.add(metadata["employee_name"])
                if metadata.get("status"):
                    statuses.add(metadata["status"])
                if metadata.get("categories"):
                    if isinstance(metadata["categories"], list):
                        categories.update(metadata["categories"])
                if metadata.get("reimbursement_amount"):
                    amounts.append(metadata["reimbursement_amount"])

            if employees:
                prompt_parts.append(f"- Employees: {', '.join(list(employees)[:3])}")
            if statuses:
                prompt_parts.append(f"- Statuses: {', '.join(list(statuses))}")
            if categories:
                prompt_parts.append(f"- Categories: {', '.join(list(categories)[:5])}")
            if amounts:
                avg_amount = sum(amounts) / len(amounts)
                prompt_parts.append(f"- Average amount: ₹{avg_amount:.0f}")

            prompt_parts.append("")

        prompt_parts.append(
            "Generate 4-5 diverse and helpful query suggestions based on this context."
        )

        return "\n".join(prompt_parts)

    def _parse_suggestions_response(self, response: str) -> List[str]:
        """
        Parse the LLM response to extract suggestions.

        Args:
            response: Raw LLM response

        Returns:
            List of parsed suggestions
        """
        try:
            import json

            # Clean the response
            response = response.strip()

            # Look for JSON array in the response
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                suggestions = json.loads(json_str)

                # Validate and clean suggestions
                if isinstance(suggestions, list):
                    cleaned_suggestions = []
                    for suggestion in suggestions:
                        if isinstance(suggestion, str) and len(suggestion.strip()) > 5:
                            cleaned_suggestions.append(suggestion.strip())

                    return cleaned_suggestions[:5]  # Limit to 5 suggestions

            # If JSON parsing fails, try to extract from text
            lines = response.split("\n")
            suggestions = []
            for line in lines:
                line = line.strip()
                if line and (
                    line.startswith('"') or line.startswith("-") or line.startswith("•")
                ):
                    # Clean the line
                    suggestion = (
                        line.replace('"', "").replace("-", "").replace("•", "").strip()
                    )
                    if len(suggestion) > 5:
                        suggestions.append(suggestion)
                        if len(suggestions) >= 5:
                            break

            return suggestions

        except Exception as e:
            self.logger.error(f"Error parsing suggestions response: {e}")
            return []

    def _get_fallback_suggestions(self, query_type: str) -> List[str]:
        """
        Get fallback suggestions when generation fails.

        Args:
            query_type: Type of the original query

        Returns:
            List of fallback suggestions
        """
        fallback_suggestions = {
            "general": [
                "Show me all declined invoices",
                "What are the most common expense categories?",
                "List invoices over ₹10,000",
                "Show me this month's approved invoices",
            ],
            "employee_specific": [
                "Show me all invoices for this employee",
                "What was the total reimbursement amount?",
                "Show me declined invoices for this employee",
                "List the expense categories for this employee",
            ],
            "status_filter": [
                "Show me invoices with different status",
                "What was the total amount for this status?",
                "Which employees have this status most?",
                "Show me the reasons for this status",
            ],
            "date_range": [
                "Show me invoices from different time periods",
                "What was the monthly trend?",
                "Compare with previous period",
                "Show me recent invoices",
            ],
            "amount_filter": [
                "Show me invoices in different amount ranges",
                "What's the average invoice amount?",
                "Show me high-value invoices",
                "List low-amount invoices",
            ],
        }

        return fallback_suggestions.get(query_type, fallback_suggestions["general"])

    async def analyze_invoice_streaming(
        self, invoice_text: str, policy_text: str, employee_name: str
    ):
        """
        Analyze an invoice against HR reimbursement policy with streaming updates.

        Args:
            invoice_text: Extracted text from invoice PDF
            policy_text: HR reimbursement policy text
            employee_name: Name of the employee

        Yields:
            Streaming updates during invoice analysis process
        """
        self.logger.info(f"Starting streaming invoice analysis for {employee_name}")

        try:
            # Yield start signal
            yield {
                "type": "invoice_analysis",
                "data": {"status": "starting", "employee": employee_name},
            }

            # Create analysis prompt using existing methods
            system_prompt = self._get_invoice_analysis_prompt()
            user_prompt = self._format_invoice_analysis_input(
                invoice_text, policy_text, employee_name
            )
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Yield analysis in progress
            yield {
                "type": "invoice_analysis",
                "data": {"status": "analyzing", "stage": "llm_processing"},
            }

            # Get streaming response from LLM
            full_response = ""
            chunk_count = 0

            async for chunk in self.generate_streaming_response(full_prompt):
                chunk_count += 1
                full_response += chunk

                # Yield periodic progress updates
                if chunk_count % 5 == 0:
                    yield {
                        "type": "invoice_analysis",
                        "data": {
                            "status": "analyzing",
                            "stage": "llm_streaming",
                            "chunks_received": chunk_count,
                        },
                    }

            # Parse the response
            yield {
                "type": "invoice_analysis",
                "data": {"status": "parsing", "stage": "response_parsing"},
            }

            result = self._parse_invoice_analysis_response(full_response)

            # Yield completion
            yield {
                "type": "invoice_analysis",
                "data": {
                    "status": "completed",
                    "result": result,
                    "chunks_processed": chunk_count,
                },
            }

            self.logger.info(
                f"Streaming invoice analysis completed for {employee_name}"
            )

        except Exception as e:
            self.logger.error(
                f"Error in streaming invoice analysis: {e}", exc_info=True
            )
            yield {
                "type": "invoice_analysis",
                "data": {"status": "error", "error": str(e)},
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the LLM service.

        Returns:
            Dictionary with health status information

        Raises:
            Exception: If health check fails
        """
        try:
            # Test API connection with a simple request
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Health check test",
                config=types.GenerateContentConfig(
                    temperature=0.1, max_output_tokens=10
                ),
            )

            return {
                "status": "healthy",
                "model": self.model_name,
                "response_received": response.text is not None,
            }
        except Exception as e:
            self.logger.error(f"LLM service health check failed: {e}")
            raise Exception(f"LLM service unhealthy: {str(e)}")
