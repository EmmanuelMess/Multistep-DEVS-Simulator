---
name: fit-spec
description: Allows for a piece of code to be updated to a specification. Called when a specification file was changed and those changes should be applied to code.
---

To update code at $ARGUMENTS[1] to fit the specification file $ARGUMENTS[0]:
1. First read the specification file $ARGUMENTS[0], then read all referenced files, all diagrams, and related information. Read the implementation give at $ARGUMENTS[1].
2. Review the generated implementation: Check that all points of the specification are met, if any are missing or contradicted by the implementation, inform the user in a list.
3. Generate a new tentative implementation plan, it should update the current implementation, taking into account previous design decision, changing them when needed.
4. Indicate to the user all lacking specifications, and all particular implementation pain points, propose a common sense solution (if available) of the previous points.
5. The user should read and address all previous issues, taking the new information into account, and repeat from point 1. When there are no more issues to deal with continue with point 4.
6. Apply the implementation corrections.
7. Review the generated implementation: reread all generated source files, and the specification $ARGUMENTS[0], check that all points of the specification are met, if any are missing or contradicted by the implementation, inform the user in a list and abort the implementation.
