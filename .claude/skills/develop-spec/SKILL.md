---
name: develop-spec
description: Allows for the development of a specification. Called when a specification file should be applied.
---

To implement the specification file $ARGUMENTS[0]:
1. First read the specification file $ARGUMENTS[0], then read all referenced files, all diagrams, and related information.
2. Generate a new tentative implementation plan.
3. Indicate to the user all lacking specifications, and all particular implementation pain points, propose a common sense solution (if available) of the previous points.
4. The user should read and address all previous issues, taking the new information into account, and repeat from point 1. When there are no more issues to deal with continue with point 4.
5. Generate an implementation.
6. Review the generated implementation: reread all generated source files, and the specification $ARGUMENTS[0], check that all points of the specification are met, if any are missing or contradicted by the implementation, inform the user in a list and abort the implementation.
8. Run, execute tests and perform other necessary checks. Implement final cosmetic changes.
