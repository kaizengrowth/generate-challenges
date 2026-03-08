# generate-challenges

This repo contains a Claude skill that will generate **testable** coding challenges for students based on a README. It also contains several sample READMEs to use when trying out the skill.

## How To Use

First install the `generate_challenges` skill by copying the contents of this repo's `skill/` directory to your `/.claude/skills/` directory. Be sure to include both the `SKILL.md` file and the full `references/` folder.

The `sample-unit-readmes/` folder in this repo contains several sample READMEs. These are introductions to core concepts followed by _a list of challenges for the student_. The three samples I have included here are:

- React
- COBOL
- OOP Design Patterns (using Java)

To try out the skill, create a **new** repo with **just one** of the README.md files. I recommend first trying out one of these samples I've provided, but afterwards try it with a different topic and README that you generate.

In that repo with just a README, open Claude and run `/generate_challenges`. It will take a few minutes. Once it is done, give a few challenges a try and run the tests.

Keep in mind that the goal is not for this skill to create a perfect set of challenges that are 100% ready to send to students. The goal is to dramatically reduce the time needed to create them, especially the scaffolding. You will likely need to spend a few minutes finessing.
