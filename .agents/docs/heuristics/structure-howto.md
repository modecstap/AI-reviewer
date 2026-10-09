# How to Organize Modules, Files, and Names

Steps for creating and changing the structure. Target structure: [reference guide](structure-reference.md). Workflow for working with existing code: [changing code](change-howto.md).

## Add a New File

1. Describe the file's responsibility in one sentence.
2. Find a module with the same responsibility or subject area.
3. If a module is found and the file does not dilute its responsibility, place the file there.
4. If no module is found, check whether the parent module can accommodate the file without compromising its responsibility. If it can, place the file there.
5. If it cannot, create a module as described below.
6. Name the file after its functionality, without the module name.
7. If the name is not unambiguous without a prefix, see "Split a Module."

## Create a Module

1. Formulate the module's responsibility. If you cannot, do not create the module.
2. Make sure the responsibility reflects the subject domain, not a technical technique. Use `orders`, not `validators`.
3. If the module would contain a single file that logically belongs to a neighboring module, place the file in the neighboring module.
4. Name the module after its responsibility. Do not use generic names (`common`, `utils`, `helpers`, `misc`).
5. Define the public interface: only what consumers need.

## Split a Module

Signs: the module has several independent responsibilities, unrelated components, or files with the same prefix.

1. List the module's responsibilities.
2. Create a module for each independent responsibility.
3. Move files with a common prefix into a module named after that prefix, and remove the prefix from the file names.

```text
before:                      after:
billing/                     billing/
  invoice_create               invoice/
  invoice_cancel                 create
  invoice_render                 cancel
  tariff                         render
                               tariff
```

4. Update consumer imports. Do not change the public contract unless it is part of the task.
5. Check that no cycles have been introduced.

## Name an Entity

1. Describe the entity's purpose. Its name is a concise form of that description.
2. Name functions after actions: `reserveStock`, `calculateTax`. Name data using nouns: `reservedQuantity`.
3. Make sure the name is understandable without reading the implementation.
4. Find similar entities in the project. Follow their naming pattern.
5. Find the existing name for the same concept in the project. Use that name; do not introduce a new one.
6. If the name is generic (`Manager`, `process`, `data`), the purpose is poorly defined or the entity does several things. Return to step 1 or split the entity.

## Add a Dependency Between Modules

1. Check that the module's functionality is actually needed. If only one small function without a business rule is needed, consider whether keeping it local would be simpler.
2. Import only the public interface. If the required functionality is not exposed, extend the interface rather than bypassing it.
3. Check the dependency direction: the domain must not depend on transport or storage.
4. Check that no cycle has been introduced. If one has, extract the shared part into a module for its subject area or invert the dependency through an interface defined by the consumer.

## Extract Repeated Logic

1. Find the repetition.
2. Check the table in the [reference guide](structure-reference.md#duplication): is it the same rule, and does it change for the same reason?
3. If the rules or reasons for change differ, keep the copies.
4. If it is the same rule, identify its subject area.
5. Place the shared function in a module for that area. Do not create a `shared` or `common` module.
6. Replace all copies with calls to the function.
7. Check that the code has become simpler. If it has not, revert the extraction.

## Move Functionality

1. Move the code to the module whose responsibility it implements.
2. Rename the file and entities if their purpose has changed.
3. If the source module has lost its responsibility or contents, rename or delete it.
4. If the destination module has acquired a second independent responsibility, split it.
5. Update imports, tests, and documentation.
