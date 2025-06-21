"""
Large Language Model Service.

This service handles interactions with the Gemini LLM for invoice analysis
and chatbot functionality using structured output schemas.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.schemas import LLMInvoiceAnalysisResponse, ReimbursementStatus

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with Large Language Models.

    This class provides methods for invoice analysis and chatbot interactions
    using the Gemini LLM through the Google Gen AI SDK.
    """

    def __init__(self):
        """Initialize the LLM service with Gemini configuration."""
        self.logger = logger

        if settings.GOOGLE_API_KEY:
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        else:
            self.client = genai.Client()

        self.model_name = settings.LLM_MODEL

        self.logger.info("LLM Service initialized with Google Gen AI SDK")

    async def analyze_invoice(
        self, invoice_text: str, policy_text: str, employee_name: str
    ) -> Dict[str, Any]:
        """
        Analyze an invoice against HR reimbursement policy using structured output.

        Args:
            invoice_text: Extracted text from the invoice PDF
            policy_text: HR reimbursement policy text
            employee_name: Name of the employee

        Returns:
            Dictionary containing analysis results with status, reason, and amounts
        """
        self.logger.info(f"Analyzing invoice for employee: {employee_name}")

        try:
            system_prompt = self._get_invoice_analysis_prompt()
            user_prompt = self._format_invoice_analysis_input(
                invoice_text, policy_text, employee_name
            )

            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            response = await self._generate_structured_invoice_response(full_prompt)

            analysis_result = response.model_dump()

            self.logger.info(
                f"Invoice analysis completed for {employee_name}: {analysis_result.get('status')}"
            )
            return analysis_result

        except Exception as e:
            self.logger.error(f"Error analyzing invoice: {e}", exc_info=True)
            return {
                "status": ReimbursementStatus.DECLINED.value,
                "reason": f"Error during analysis: {str(e)}",
                "total_amount": 0.0,
                "reimbursement_amount": 0.0,
                "currency": "INR",
                "categories": [],
                "policy_violations": [f"Analysis failed: {str(e)}"],
            }

    def _get_invoice_analysis_prompt(self) -> str:
        """
        Get the system prompt for structured invoice analysis.

        Returns:
            System prompt for structured invoice analysis
        """
        return """You are an expert invoice analyst for HR reimbursement processing. Your task is to analyze employee invoices against company reimbursement policies and provide a structured JSON response.

ANALYSIS REQUIREMENTS:
1. Carefully read the HR reimbursement policy provided
2. Analyze the invoice content for expense details, amounts, dates, and categories
3. Compare invoice items against policy guidelines
4. Determine reimbursement status: "fully_reimbursed", "partially_reimbursed", or "declined"
5. Provide detailed reasoning for your decision
6. Calculate exact reimbursement amounts when applicable
7. ALWAYS extract the total amount and currency from the invoice
8. ALWAYS identify expense categories based on the invoice content

STRUCTURED OUTPUT REQUIREMENT:
You MUST respond with a valid JSON object that matches this exact schema:
{
    "status": "fully_reimbursed|partially_reimbursed|declined",
    "reason": "Detailed explanation of the decision (10-1000 characters)",
    "total_amount": <total invoice amount as float - REQUIRED>,
    "reimbursement_amount": <amount to be reimbursed as float>,
    "currency": "<3-letter currency code (INR, USD, EUR, etc.) - REQUIRED>",
    "categories": ["<expense category 1>", "<expense category 2>"] - REQUIRED array with at least 1 item,
    "policy_violations": ["<violation 1>", "<violation 2>"] or null if none
}

CRITICAL EXTRACTION RULES:
- TOTAL_AMOUNT: Look for amounts like ₹233, $100, €50, Rs.150, etc. Extract the numeric value. Must be >= 0.
- REIMBURSEMENT_AMOUNT: Cannot exceed total_amount. Must be >= 0.
- CURRENCY: Based on currency symbol: ₹ or Rs. = "INR", $ = "USD", € = "EUR", £ = "GBP". UPPERCASE only.
- CATEGORIES: Common categories include "travel", "meals", "office_supplies", "accommodation", "cab", "fuel", "communication", etc. At least 1 required.
- STATUS: Must be exactly one of: "fully_reimbursed", "partially_reimbursed", "declined"
- If no amount is found, set total_amount to 0.0
- If no currency symbol found, default to "INR" for Indian companies
- Categories should be descriptive and based on expense type (e.g., ["travel", "cab"] for cab expenses)

VALIDATION REQUIREMENTS:
- All fields are mandatory except policy_violations
- Currency must be exactly 3 uppercase letters
- Categories array must contain at least 1 item
- Amounts must be non-negative numbers
- Reimbursement amount cannot exceed total amount
- Status must match exactly one of the allowed values

ANALYSIS GUIDELINES:
- Be thorough and accurate in your analysis
- Consider all policy rules and restrictions
- Identify specific policy violations if any
- Calculate partial reimbursements when some items are approved and others are not
- Look for receipt dates, vendor information, and expense descriptions
- Consider spending limits, approval requirements, and eligible expense types
- Provide clear, professional reasoning that an HR representative could understand

RESPONSE FORMAT: Return ONLY the JSON object, no additional text or formatting."""

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
            response = response.strip()

            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)

                required_fields = ["status", "reason"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field: {field}")

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

                if not isinstance(result.get("categories"), list):
                    result["categories"] = []

                return result
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            self.logger.error(f"Error parsing invoice analysis response: {e}")
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
            system_prompt = self._get_chat_system_prompt()
            user_prompt = self._format_chat_input(
                query, context_documents, conversation_history
            )

            full_prompt = f"{system_prompt}\n\n{user_prompt}"

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
        return """You are an intelligent assistant for an Invoice Reimbursement System. Your role is to help users query and understand invoice reimbursement data using the provided context documents and conversation history.

CAPABILITIES:
- Answer questions about invoice reimbursement status and details
- Search for specific invoices by employee name, date, amount, or status
- Explain reimbursement decisions and policy violations using BOTH invoice data and policy context
- Provide summaries and statistics about processed invoices
- Help users understand reimbursement policies and procedures
- Maintain context across conversation turns
- Reference previous questions and responses when relevant

CONTEXT DOCUMENTS:
You will receive two types of context documents:
1. **Invoice Documents**: Specific invoice analysis results with employee data, amounts, status, etc.
2. **Policy Documents**: HR reimbursement policy information that explains rules, limits, and procedures

CONTEXT AWARENESS:
- Pay attention to the conversation history for context
- Reference previous queries when they're related to the current question
- If a user asks follow-up questions, understand they may be referring to previous results
- When showing data, remember what filters or criteria were mentioned before
- Build upon previous responses rather than starting fresh each time
- Use BOTH invoice data and policy information to provide comprehensive answers

RESPONSE GUIDELINES:
1. Always base your answers on the provided context documents (both invoice and policy)
2. When explaining WHY an invoice was declined/approved, reference relevant policy information
3. Use conversation history to provide more relevant and contextual responses
4. Use markdown formatting for better readability (tables, bold, lists)
5. Be accurate and cite specific information when available
6. If you don't have enough information, clearly state this
7. Provide helpful suggestions for alternative queries
8. Maintain a professional and helpful tone
9. Include relevant details like amounts, dates, and employee names
10. When showing invoice data, use clear tables with all relevant information
11. Reference previous parts of the conversation when relevant
12. When explaining policy violations, quote specific policy sections when available

POLICY INTEGRATION:
- When discussing declined invoices, explain the policy reasons
- When asked about limits or rules, reference the policy documents
- Help users understand what expenses are reimbursable vs. non-reimbursable
- Explain approval processes and documentation requirements
- Provide context about spending limits and categories

RESPONSE FORMAT:
- Use **bold** for important information like amounts and statuses
- Use bullet points for lists
- Use tables for structured invoice data with columns: Employee Name, Invoice Name, Status, Amount, Date
- Include relevant quotes from source documents when helpful
- End with contextual suggestions based on current conversation
- Use status emojis: ✅ (fully_reimbursed), ⚠️ (partially_reimbursed), ❌ (declined)

CONTEXTUAL BEHAVIOR:
- If user asks "Show me more" or similar, reference previous query context
- If user mentions "these invoices", refer to previously discussed data
- Build progressive understanding through the conversation
- Provide more detailed analysis when users drill down into specific areas

Remember: Only provide information that can be found in the context documents. Use conversation history to provide more relevant and contextual responses."""

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

        if conversation_history:
            prompt_parts.append("CONVERSATION HISTORY:")
            prompt_parts.append(
                "(Use this to understand context and provide relevant follow-up responses)"
            )
            for msg in conversation_history[-5:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt_parts.append(f"{role.upper()}: {content}")
            prompt_parts.append("")

        if context_documents:
            invoice_docs = [
                doc
                for doc in context_documents
                if doc.get("type", "invoice") == "invoice"
                or doc.get("metadata", {}).get("doc_type") == "invoice_analysis"
            ]
            policy_docs = [
                doc
                for doc in context_documents
                if doc.get("type") == "policy"
                or doc.get("metadata", {}).get("doc_type") == "policy"
            ]

            if invoice_docs:
                prompt_parts.append("RELEVANT INVOICE DATA:")
                prompt_parts.append(
                    f"(Found {len(invoice_docs)} matching invoice documents)"
                )
                for i, doc in enumerate(invoice_docs[:6], 1):  # Limit to 6 invoices
                    metadata = doc.get("metadata", {})
                    content = doc.get("content", "")

                    prompt_parts.append(f"Invoice {i}:")
                    prompt_parts.append(
                        f"- Employee: {metadata.get('employee_name', 'Unknown')}"
                    )
                    prompt_parts.append(
                        f"- Invoice: {metadata.get('invoice_filename', 'Unknown')}"
                    )
                    prompt_parts.append(
                        f"- Status: {metadata.get('status', 'Unknown')}"
                    )
                    prompt_parts.append(
                        f"- Total Amount: {metadata.get('total_amount', 'Unknown')} {metadata.get('currency', '')}"
                    )
                    prompt_parts.append(
                        f"- Reimbursement Amount: {metadata.get('reimbursement_amount', 'Unknown')} {metadata.get('currency', '')}"
                    )
                    prompt_parts.append(f"- Date: {metadata.get('date', 'Unknown')}")
                    if metadata.get("reason"):
                        prompt_parts.append(f"- Reason: {metadata.get('reason')}")
                    if metadata.get("categories"):
                        prompt_parts.append(
                            f"- Categories: {', '.join(metadata.get('categories', []))}"
                        )
                    if metadata.get("policy_violations"):
                        prompt_parts.append(
                            f"- Policy Violations: {', '.join(metadata.get('policy_violations', []))}"
                        )
                    prompt_parts.append("")

            if policy_docs:
                prompt_parts.append("RELEVANT POLICY INFORMATION:")
                prompt_parts.append(
                    f"(Found {len(policy_docs)} matching policy sections)"
                )
                for i, doc in enumerate(policy_docs[:3], 1):
                    metadata = doc.get("metadata", {})
                    content = doc.get("content", "")

                    prompt_parts.append(f"Policy Section {i}:")
                    if metadata.get("policy_name"):
                        prompt_parts.append(f"- Policy: {metadata.get('policy_name')}")
                    if content:
                        prompt_parts.append(f"- Content: {content[:800]}...")
                    prompt_parts.append("")
        else:
            prompt_parts.append("No relevant documents found for this query.")
            prompt_parts.append(
                "Please inform the user and suggest alternative queries."
            )
            prompt_parts.append("")

        prompt_parts.append(f"CURRENT QUERY: {query}")
        prompt_parts.append("")
        prompt_parts.append("RESPONSE INSTRUCTIONS:")
        prompt_parts.append(
            "- Use conversation history to provide contextual responses"
        )
        prompt_parts.append("- Reference previous queries when relevant")
        prompt_parts.append(
            "- Format invoice data in clear tables when showing multiple records"
        )
        prompt_parts.append("- Provide contextually relevant suggestions")
        prompt_parts.append("- Be specific with amounts, dates, and employee names")
        prompt_parts.append("")

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
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.MAX_TOKENS,
                ),
            )

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
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.MAX_TOKENS,
                ),
            )

            chunk_count = 0
            total_tokens = 0

            async for chunk in stream:
                if chunk.candidates and len(chunk.candidates) > 0:
                    candidate = chunk.candidates[0]
                    if candidate.content and candidate.content.parts:
                        text = candidate.content.parts[0].text
                        if text is not None and text.strip():
                            chunk_count += 1
                            total_tokens += len(text.split())

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
            system_prompt = self._get_chat_system_prompt()
            user_prompt = self._format_chat_input(
                query, context_documents, conversation_history
            )

            full_prompt = f"{system_prompt}\n\n{user_prompt}"

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
            system_prompt = self._get_suggestion_system_prompt()
            user_prompt = self._format_suggestion_input(
                original_query, context_documents, query_type
            )

            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            response = await self._generate_response(full_prompt)

            suggestions = self._parse_suggestions_response(response)

            self.logger.info(f"Generated {len(suggestions)} query suggestions")
            return suggestions

        except Exception as e:
            self.logger.error(f"Error generating query suggestions: {e}", exc_info=True)
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

        if context_documents:
            prompt_parts.append("AVAILABLE DATA CONTEXT:")

            employees = set()
            statuses = set()
            categories = set()
            amounts = []

            for doc in context_documents[:5]:
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
            response = response.strip()

            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                suggestions = json.loads(json_str)

                if isinstance(suggestions, list):
                    cleaned_suggestions = []
                    for suggestion in suggestions:
                        if isinstance(suggestion, str) and len(suggestion.strip()) > 5:
                            cleaned_suggestions.append(suggestion.strip())

                    return cleaned_suggestions[:5]

            # If JSON parsing fails, try to extract from text
            lines = response.split("\n")
            suggestions = []
            for line in lines:
                line = line.strip()
                if line and (
                    line.startswith('"') or line.startswith("-") or line.startswith("•")
                ):
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
        Analyze an invoice against HR reimbursement policy with streaming updates using structured output.

        Args:
            invoice_text: Extracted text from invoice PDF
            policy_text: HR reimbursement policy text
            employee_name: Name of the employee

        Yields:
            Streaming updates during invoice analysis process
        """
        self.logger.info(f"Starting streaming invoice analysis for {employee_name}")

        try:
            yield {
                "type": "invoice_analysis",
                "data": {"status": "starting", "employee": employee_name},
            }

            system_prompt = self._get_invoice_analysis_prompt()
            user_prompt = self._format_invoice_analysis_input(
                invoice_text, policy_text, employee_name
            )
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            yield {
                "type": "invoice_analysis",
                "data": {"status": "analyzing", "stage": "llm_processing"},
            }

            try:
                result = await self._generate_structured_invoice_response(full_prompt)

                yield {
                    "type": "invoice_analysis",
                    "data": {
                        "status": "completed",
                        "result": result.model_dump(),
                        "structured": True,
                    },
                }

                self.logger.info(
                    f"Streaming invoice analysis completed for {employee_name} with structured output"
                )

            except Exception as structured_error:
                self.logger.warning(
                    f"Structured analysis failed, falling back to streaming: {structured_error}"
                )

                full_response = ""
                chunk_count = 0

                async for chunk in self.generate_streaming_response(full_prompt):
                    chunk_count += 1
                    full_response += chunk

                    if chunk_count % 5 == 0:
                        yield {
                            "type": "invoice_analysis",
                            "data": {
                                "status": "analyzing",
                                "stage": "llm_streaming",
                                "chunks_received": chunk_count,
                            },
                        }

                yield {
                    "type": "invoice_analysis",
                    "data": {"status": "parsing", "stage": "response_parsing"},
                }

                result = self._parse_invoice_analysis_response(full_response)

                yield {
                    "type": "invoice_analysis",
                    "data": {
                        "status": "completed",
                        "result": result,
                        "chunks_processed": chunk_count,
                        "structured": False,
                    },
                }

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

    async def _generate_structured_invoice_response(
        self, prompt: str
    ) -> LLMInvoiceAnalysisResponse:
        """
        Generate structured invoice analysis response using Google Gen AI SDK with response schema.

        Args:
            prompt: The full prompt to send to the model

        Returns:
            Validated LLMInvoiceAnalysisResponse object

        Raises:
            Exception: If the response doesn't conform to the schema or generation fails
        """
        try:
            response_schema = LLMInvoiceAnalysisResponse.model_json_schema()

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.MAX_TOKENS,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    response_text = candidate.content.parts[0].text
                    if response_text is not None:
                        try:
                            response_data = json.loads(response_text)
                            validated_response = LLMInvoiceAnalysisResponse(
                                **response_data
                            )
                            self.logger.info(
                                "Successfully generated and validated structured response"
                            )
                            return validated_response
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Failed to parse JSON response: {e}")
                            raise ValueError(f"Invalid JSON response: {e}")
                        except Exception as e:
                            self.logger.error(
                                f"Failed to validate response schema: {e}"
                            )
                            raise ValueError(f"Response validation failed: {e}")
                    else:
                        raise ValueError("Response text is None")
                else:
                    raise ValueError("No content found in response")
            else:
                raise ValueError("No candidates in response")

        except Exception as e:
            self.logger.error(f"Error generating structured response: {e}")
            try:
                fallback_response = LLMInvoiceAnalysisResponse(
                    status=ReimbursementStatus.DECLINED,
                    reason=f"Error during structured analysis: {str(e)}",
                    total_amount=0.0,
                    reimbursement_amount=0.0,
                    currency="INR",
                    categories=["unknown"],
                    policy_violations=[f"Analysis failed: {str(e)}"],
                )
                self.logger.warning(
                    "Using fallback structured response due to generation error"
                )
                return fallback_response
            except Exception as fallback_error:
                self.logger.error(
                    f"Failed to create fallback response: {fallback_error}"
                )
                raise Exception(f"Structured response generation failed: {str(e)}")
