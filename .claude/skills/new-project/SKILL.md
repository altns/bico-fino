---
name: new-project
description: Create a new bico-fino project folder (projects/<name>/ with original/, source/, final/ and a README) from a downloaded model, a commission or an idea. Use when the user starts working on a new part, imports a model to customize, or asks to organize files into a project.
---

# Create a new project

1. **Name.** Use the name the user gives (keep spaces and accents as typed). Letter-name projects go in `projects/Letter names/<name>/`. If the folder exists, stop and ask.
2. **Folders.** Create `original/`, `source/` and `final/` (only the ones that will have content right away; empty folders are not tracked by git).
3. **Original.** Copy the source file into `original/` unchanged. If it came from `models/downloads/`, copy it — don't move it. Record the author and link if known.
4. **README.md** in the project root:

   ```markdown
   # <Name>

   <What it is, base model and author/link, who it is for.>

   - **original/** — <file>: <what it is>.
   - **source/** — <scripts / working files>.
   - **final/** — <print-ready files>.

   ## Dimensions
   ## Filaments
   ## Printing
   ## Assembly
   ## History
   - <date>: project created.
   ```

5. **Where it lives.** `projects/` is a junction into the private repository (`C:\3D\private`); commit there with `git -C C:\3D\private ...` and only when the user asks. Never add project files to the public repo.
6. Then continue with the `prepare-print` skill if the user wants it printable.
