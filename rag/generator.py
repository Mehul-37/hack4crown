import os
from typing import List, Dict, Any
from models.schemas import SourceCitation, ChatResponse

MEDICAL_RAG_PROMPT_TEMPLATE = """You are a helpful healthcare document assistant for a personal medical vault.
Your task is to answer the patient's question accurately using ONLY the provided medical context chunks below.

CRITICAL MEDICAL SAFETY & NON-DIAGNOSTIC RULES:
1. Ground your answer strictly in the provided medical records.
2. If the answer cannot be found in the provided context, state clearly: "I couldn't find that information in your uploaded medical records."
3. Do NOT hallucinate numerical values, lab results, dosages, or dates.
4. ABSOLUTE NO-DIAGNOSIS RULE: Do NOT issue medical diagnoses, medical opinions, or clinical conclusions (e.g., do NOT say "You have hypothyroidism" or "You should adjust your dose"). Describe ONLY factual numbers, dates, and value changes documented in the files.
5. Educational & Informational Only: Always note that numerical trends should be discussed with a licensed physician for clinical interpretation.
6. Always reference specific report dates or file names when citing facts.

CONTEXT CHUNKS:
{context}

PATIENT QUESTION:
{question}

ANSWER:"""

class RAGGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = None
        if self.api_key and self.api_key != "AQ.Ab8RN6LGkCVF0oLww_G4HplHvfnYewRaFIq55qdsos5deUkHmA":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self.model = None

    def generate_answer(self, question: str, patient_id: str, retrieved_chunks: List[Dict[str, Any]], doc_metadata_map: Dict[str, Dict[str, Any]]) -> ChatResponse:
        """
        Synthesizes RAG response with ground-truth context and builds precise source citations.
        """
        if not retrieved_chunks:
            return ChatResponse(
                question=question,
                answer="I couldn't find that information in your uploaded medical records.",
                patient_id=patient_id,
                sources=[]
            )

        # Build context string and citations
        context_parts = []
        citations: List[SourceCitation] = []

        for idx, chunk in enumerate(retrieved_chunks):
            doc_id = chunk["document_id"]
            doc_info = doc_metadata_map.get(doc_id, {})
            filename = doc_info.get("filename", chunk.get("metadata", {}).get("filename", "medical_record.pdf"))
            page = chunk.get("page_number", 1)
            content = chunk.get("content", "")

            context_parts.append(f"--- Document: {filename} (Page {page}) ---\n{content}")
            
            citations.append(SourceCitation(
                document_id=doc_id,
                filename=filename,
                page=page,
                snippet=content[:150] + "..." if len(content) > 150 else content
            ))

        formatted_context = "\n\n".join(context_parts)
        prompt = MEDICAL_RAG_PROMPT_TEMPLATE.format(context=formatted_context, question=question)

        answer_text = ""
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                answer_text = response.text.strip()
            except Exception as e:
                answer_text = self._synthesize_rule_based(question, retrieved_chunks, citations)
        else:
            answer_text = self._synthesize_rule_based(question, retrieved_chunks, citations)

        return ChatResponse(
            question=question,
            answer=answer_text,
            patient_id=patient_id,
            sources=citations
        )

    def _synthesize_rule_based(self, question: str, retrieved_chunks: List[Dict[str, Any]], citations: List[SourceCitation]) -> str:
        """Rule-based synthesis fallback when Gemini API is unconfigured/offline."""
        matched_sentences = []
        q_words = [w.lower() for w in question.split() if len(w) > 3]

        for chunk in retrieved_chunks:
            content = chunk.get("content", "")
            sentences = content.split(".")
            for s in sentences:
                if any(w in s.lower() for w in q_words):
                    clean_s = s.strip()
                    if clean_s and clean_s not in matched_sentences:
                        matched_sentences.append(clean_s)

        if matched_sentences:
            findings = ". ".join(matched_sentences[:3]) + "."
            source_file = citations[0].filename if citations else "your record"
            return f"Based on {source_file}: {findings}"
        
        chunk_preview = retrieved_chunks[0]["content"][:200]
        return f"Based on your uploaded medical records: {chunk_preview}..."

generator = RAGGenerator()
