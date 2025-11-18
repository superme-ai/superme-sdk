# Content Grounding Evaluation Prompt

## Overview

As an expert analyst in information sourcing and knowledge attribution, carefully examine how well the assistant's FINAL RESPONSE aligns with and utilizes the retrieved knowledge chunks.

## Evaluation Rules

CRITICAL EVALUATION RULES:
1. Focus primarily on analyzing the LAST ANSWER in the conversation
2. Use previous questions only for understanding context
3. Compare the final response against the retrieved knowledge chunks
4. Look for direct usage or paraphrasing of information from the chunks
5. Check if key concepts and examples in the final answer come from the chunks
6. Assess how much the final response relies on information outside the chunks or conversation history

## Key Indicators for the Final Answer

Consider these key indicators FOR THE FINAL ANSWER:
1. Direct matches between the final response and chunk content
2. Paraphrasing or reformulation of chunk information
3. Examples and specifics that appear in the chunks
4. Additional information not found in the chunks
5. How closely the response structure follows the chunks
6. Whether key points originate from chunks or general knowledge
7. Whether general concepts are supported by or grounded in the chunks

## Classification Categories

Based on your analysis of the FINAL ANSWER, classify into exactly one of these categories:

### MOSTLY_FROM_USER_CONTENT
The final response primarily uses information from the retrieved chunks (>70%) or is strongly grounded in the chunks. This includes:
- Direct quotes or close paraphrasing from chunks
- Examples and specifics that appear in chunks
- Following similar structure or organization as chunks
- Minimal addition of external information

### MIX_USER_CONTENT_GENERAL_KNOWLEDGE
The final response balances chunk information with general knowledge (30-70% from chunks).
- Some direct usage of chunk information
- Some general concepts supported by chunks
- Significant addition of relevant general knowledge
- Meaningful synthesis of both sources

### MOSTLY_GENERAL_KNOWLEDGE
The final response primarily uses information not found in the chunks or conversation history (<30% from chunks).
- Minimal usage of chunk information
- Mostly introduces new information
- Different examples or specifics than those in chunks
- General concepts not grounded in the chunks

### ANSWER_REFUSAL
The assistant refuses to answer substantively in the final response.

## Output Format

Return only the classification label with no other text.
