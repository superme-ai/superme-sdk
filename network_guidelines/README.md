# SuperMe Network Guidelines

This directory contains the guidelines and prompt templates that define SuperMe's network standards and content evaluation criteria.

## Available Evaluation Prompts

### 1. Post Quality Evaluation (`post_quality_evaluation.md`)
Evaluates whether a post should be shared to the SuperMe network, kept to followers only, or flagged for human review.

**Three-step evaluation process:**
1. **Safety Review** - Blocks unsafe content (spam, harmful content, illegal activity)
2. **Content Type Assessment** - Ensures content is substantive and professional
3. **Content Quality Assessment** - Scores posts based on value and relevance

**Output categories:**
- `network` - High-quality posts distributed to the network (3+ quality points)
- `followers_only` - Default for most posts
- `trigger_review` - Safety violations requiring human review

### 2. Content Grounding (`content_grounding.md`)
Analyzes how well assistant responses are grounded in retrieved knowledge chunks vs. general knowledge.

**Classification categories:**
- `MOSTLY_FROM_USER_CONTENT` - Response primarily uses retrieved information (>70%)
- `MIX_USER_CONTENT_GENERAL_KNOWLEDGE` - Balanced mix (30-70%)
- `MOSTLY_GENERAL_KNOWLEDGE` - Primarily general knowledge (<30%)
- `ANSWER_REFUSAL` - Assistant refuses to answer

### 3. Content Quality (`content_quality.md`)
Evaluates response quality across five dimensions (1-5 scale):

1. **Completeness** - Fully addresses all parts of the question
2. **Clarity** - Logical organization and clear language
3. **Depth** - Appropriate detail and supporting evidence
4. **Relevance** - Directly addresses the question
5. **Helpfulness** - Solves the user's problem

**Classification categories:**
- `GOOD` - Scores 4-5 across most dimensions
- `SUGGEST_USER_FOLLOW_UP` - Some gaps (scores 2-3)
- `INCOMPLETE` - Significant issues (scores 1-2)

### 4. Trust and Safety (`trust_and_safety.md`)
Detects potential safety and policy violations in conversations.

**Detection areas:**
- **Jailbreak attempts** - Bypassing AI safety measures
- **Political manipulation** - Partisan agenda or misinformation
- **Harassment** - Abusive, threatening, or discriminatory content
- **Content policy violations** - Illegal activities, explicit content
- **Potential harm** - Self-harm, violence, dangerous behaviors

**Classification categories:**
- `SAFE` - No issues detected
- `JAILBREAK` - Safety bypass attempts
- `POLITICAL` - Political manipulation
- `HARASSMENT` - Abusive content
- `POLICY_VIOLATION` - Clear policy violations
- `UNCLEAR` - Ambiguous requests
- `POTENTIAL_HARM` - Harmful intent detected

## Usage

These prompts serve as reference documentation for SuperMe's content evaluation system. They define the criteria and processes used to maintain quality and safety on the network.

### For Developers
Use these guidelines when building content moderation, evaluation, or recommendation systems that integrate with SuperMe.

### For Content Creators
Understand how posts are evaluated and what makes content suitable for network distribution vs. followers-only visibility.

## Philosophy

SuperMe's network guidelines are designed to:

1. **Prioritize Safety** - Block harmful, unsafe, or inappropriate content
2. **Maintain Quality** - Only share substantive, valuable content to the network
3. **Default to Privacy** - Most posts stay with followers only
4. **Enable Professional Networking** - Focus on expertise, insights, and learnings
5. **Ensure Transparency** - Clear criteria and consistent evaluation

## Contributing

When proposing changes to network guidelines:

1. Consider the impact on user trust and safety
2. Maintain consistency with existing principles
3. Provide clear examples and criteria
4. Test with diverse content types
5. Document the reasoning for changes

## License

These guidelines are part of the SuperMe SDK and are licensed under the MIT License.
