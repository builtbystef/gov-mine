# 033: Make a project's materials its documents

Spec: docs/specification/ (sections 5.5, 5.6, 7 step 6, 14 decision 22)
Depends on: 023

## What to build

Each file a project lists in its `materials` becomes a `project_material` document belonging to that project, without asking the classifier.

## Acceptance criteria

- [ ] Extracting the saved Parkdale Hub project creates a `project_material` document for each material URL, with `parent_document_id` set to the project's document.
- [ ] A material file parsed after the project page is not classified.
- [ ] A material file already classified as another document type becomes `project_material` of the project.
- [ ] A file listed by two projects keeps the first project as its parent.
