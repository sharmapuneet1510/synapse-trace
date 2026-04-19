# AI Usage Instructions

## Objective
Use the right AI model for the right type of work. Model selection must be intentional and based on the task type, complexity, and required depth of reasoning.

Claude should always choose the most suitable model for planning, reasoning, coding, and execution instead of using the same model for everything.

---

## 1. Claude Model Usage Rules

### Use Opus for Thinking and Planning
Use **Opus** for:
- deep thinking
- requirement analysis
- solution design
- architecture planning
- execution planning
- breaking down complex scope
- difficult debugging strategy
- tradeoff analysis
- reviewing complicated implementation paths
- creating structured plans before coding

Opus should be the default choice when the task requires strong reasoning, planning, or careful decision-making.

### Use Sonnet for Very Complex Project Execution
Use **Sonnet** for:
- very complex project implementation
- large multi-step execution
- code generation across multiple files
- sustained development work
- implementation of bigger features after planning is complete
- refactoring or extending larger codebases

Sonnet should be used when the project is large enough that execution speed and sustained coding throughput matter after the thinking phase is clear.

---

## 2. Local Coding Model Usage Rules

Use local coding models when coding can be done effectively with them.

### Primary Recommended Coding Models
Preferred coding model order:

1. **Qwen2.5-Coder (14B or 32B)**
2. **DeepSeek-Coder V2 Lite**
3. **Gemma 3 (27B)**
4. **Llama 3.3 (70B)** if hardware or hosted setup supports it
5. **WizardLM-2 (7B)** for simple and fast generation

---

## 3. Model Selection Guidance

### Qwen2.5-Coder (14B or 32B)
Use as the primary local coding model.

Use **Qwen2.5-Coder 14B** for:
- general backend coding
- general frontend coding
- API work
- React components
- service implementation
- practical day-to-day coding tasks
- balanced speed and reasoning

Use **Qwen2.5-Coder 32B** for:
- more difficult backend logic
- larger context reasoning
- more complex refactoring
- database-heavy logic
- multi-file feature work
- deeper business logic implementation

This should be treated as the preferred local coding model family.

### DeepSeek-Coder V2 Lite
Use for:
- strong reasoning-heavy backend work
- debugging tricky issues
- architecture-sensitive backend tasks
- logic-heavy code generation
- complex technical problem solving

### Gemma 3 (27B)
Use for:
- general-purpose coding
- agentic workflows
- mixed frontend and backend tasks
- implementation where strong all-round behavior is needed

### Llama 3.3 (70B)
Use only when hardware or hosted infrastructure supports it.

Use for:
- complex multi-file reasoning
- large codebase understanding
- complex architecture-sensitive changes
- advanced cross-module reasoning

### WizardLM-2 (7B)
Use for:
- simple boilerplate
- quick frontend adjustments
- small utility functions
- rapid scaffolding
- lightweight coding tasks where speed matters more than deep reasoning

---

## 4. Frontend vs Backend Model Preference

### Backend Coding
Backend work usually needs stronger reasoning and larger context handling.

Prefer:
- Qwen2.5-Coder 32B
- Qwen2.5-Coder 14B
- DeepSeek-Coder V2 Lite
- Gemma 3 (27B)

Typical backend tasks:
- database schema work
- API contracts
- service architecture
- validation logic
- integration logic
- business rules
- debugging
- refactoring
- concurrency-sensitive work

### Frontend Coding
Frontend work can often be handled by lighter models unless the UI is very complex.

Prefer:
- Qwen2.5-Coder 14B
- lighter Qwen coding models
- WizardLM-2 (7B) for quick boilerplate
- Gemma 3 (27B) when more capability is needed

Typical frontend tasks:
- CSS
- HTML boilerplate
- React components
- UI state wiring
- form handling
- layout adjustments
- simple interactive behavior

For very complex frontend architecture or multi-screen workflows, move back to stronger models.

---

## 5. Practical Usage Rules

### Planning First, Coding Second
Always do:
1. use Opus for analysis and planning
2. define the implementation path
3. then use the most suitable coding model for execution

Do not jump into generation with a weaker coding model before the plan is clear when the task is complex.

### Prefer Simpler Models When Sufficient
Do not use the heaviest model for simple tasks.
Use lighter or faster models when the job is:
- small
- repetitive
- boilerplate-heavy
- low-risk
- visually focused
- localized to one file or one component

### Escalate Model Strength When Needed
If a task is failing due to:
- reasoning weakness
- context loss
- poor architecture decisions
- multi-file inconsistency
- repeated incorrect outputs

Then move to a stronger model rather than repeatedly retrying with the wrong one.

---

## 6. Fallback Rule
If local coding models cannot complete the task well enough, escalate to stronger Claude usage based on complexity.

Preferred escalation:
1. local lightweight model
2. stronger local coding model
3. Sonnet for complex implementation
4. Opus for difficult reasoning, design, or recovery planning

---

## 7. Non-Negotiable Rules
- Use **Opus** for thinking and planning
- Use **Sonnet** for very complex project implementation
- Prefer **Qwen2.5-Coder 14B or 32B** as the default local coding model
- Use stronger models for backend-heavy or multi-file reasoning
- Use lighter models for simple frontend or boilerplate work
- Do not use oversized models for trivial tasks
- Do not keep retrying the wrong model when a stronger one is clearly needed
- Always match model choice to task complexity

---

## 8. Recommended Decision Pattern

### Use Opus when:
- the problem is unclear
- planning is needed
- architecture decisions are needed
- the scope must be broken down
- tradeoffs must be analyzed

### Use Sonnet when:
- implementation is large
- there are many files
- execution will be lengthy
- the project is very complex

### Use Qwen2.5-Coder 14B when:
- general coding is needed
- speed and quality balance matters
- both frontend and backend work are in scope

### Use Qwen2.5-Coder 32B when:
- backend complexity is high
- reasoning depth matters
- multi-file logic is difficult

### Use DeepSeek-Coder V2 Lite when:
- debugging is difficult
- backend logic is tricky
- reasoning quality matters

### Use WizardLM-2 7B when:
- work is simple
- quick scaffolding is enough
- speed matters most

---

## 9. Final Rule
Model choice is part of engineering discipline.
Always choose the model deliberately based on:
- task type
- complexity
- reasoning depth
- number of files involved
- frontend vs backend focus
- speed vs quality tradeoff
