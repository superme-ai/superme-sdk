# Content Quality Evaluation Prompt

## Overview

As an expert in knowledge assessment and communication effectiveness, thoroughly analyze the quality of the assistant's responses in this conversation.

## Evaluation Dimensions

Evaluate the response across these key aspects on a scale of 1-5:

### 1. COMPLETENESS (1-5)
- Does the response fully address all parts of the question?
- Are key points and sub-questions answered?
- Is there a logical flow from start to finish?

### 2. CLARITY (1-5)
- Is the information organized logically?
- Is the language clear and understandable?
- Are complex concepts explained well?

### 3. DEPTH (1-5)
- Does the response provide appropriate detail for the question's complexity?
- Are supporting examples or evidence provided?
- Does it go beyond surface-level information?

### 4. RELEVANCE (1-5)
- Does the response directly address what was asked?
- Is the information pertinent to the question?
- Does it stay focused on the topic?

### 5. HELPFULNESS (1-5)
- Does the response actually solve the user's problem?
- Would it likely satisfy the user's information need?
- Does it provide actionable or useful information?

## Classification Categories

After scoring each aspect, provide a final classification based on the overall quality:

### GOOD
The response scores high (4-5) across most aspects, providing clear, complete, and helpful information.

### SUGGEST_USER_FOLLOW_UP
The response is decent but has some gaps (scores 2-3 in some aspects) that might leave the user wanting more information.

### INCOMPLETE
The response has significant issues (scores 1-2 in multiple aspects) and fails to adequately address the question.

## Output Format

Return only the final classification label with no other text.
