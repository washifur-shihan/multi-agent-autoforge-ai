class ContextBuilder:

    def build_context(self, user_prompt, document_context=None):

        system_instruction = """
You are Autoforge AI, an autonomous multi-agent AI engineering and research platform
capable of architecting software projects, writing automation scripts, synthesizing research,
and compiling executive reports. Return structured outputs when generating files.
"""

        context = ""

        if document_context:
            context += f"\nDOCUMENT CONTEXT:\n{document_context}\n"

        final_prompt = f"""
{system_instruction}

{context}

USER REQUEST:
{user_prompt}
"""

        return final_prompt

