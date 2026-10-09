# Reference Guide: Modules, Files, Names, Dependencies

The target form of the code structure. How to achieve it: [instructions](structure-howto.md). Rules for code inside a module: [code reference](code-reference.md).

A module is a unit for grouping files: a package, namespace, or directory with a public interface.

## Module

* Has one clearly defined responsibility. The module's name identifies it.
* Groups files belonging to the same subject area or serving the same functional responsibility.
* The module structure mirrors the structure of the subject domain. Development history and the order in which files were added do not affect it.
* A module without a defined responsibility is not created.

Signs of a poorly designed module:

| Sign                                                  | What's wrong                                                      |
| ----------------------------------------------------- | ----------------------------------------------------------------- |
| Files from different subject areas in one module      | Grouping things together just to reduce the number of modules     |
| Many unrelated components                             | The module is too large                                           |
| A file that logically belongs to a neighboring module | An unnecessary boundary                                           |
| The name does not describe the contents               | The responsibility has changed, but the name has not been updated |

Example. Bad:

```text
app/
  common/
    order_validator
    user_formatter
    date_utils
  orders/
    orders_repository
    orders_service
```

Good:

```text
app/
  orders/
    validation
    repository
    service
  users/
    formatting
  calendar/
    date_range
```

`common` mixes orders, users, and dates. The `orders_` prefix repeats the module name.

## File

* A file name is unambiguous within its module and describes its functionality.
* A file name does not repeat the module name: `orders/service`, not `orders/orders_service`.
* If a file needs a qualifying prefix to distinguish it from neighboring files, that prefix represents a hidden module. Extract it: `orders/payment_refund` and `orders/payment_capture` become `orders/payment/refund` and `orders/payment/capture`.

Exception: repeating the name is acceptable if it eliminates ambiguity or is required by a project convention (for example, a module's entry point must have a fixed name).

## Naming

Rules for modules, files, classes, functions, and variables.

* A name indicates the purpose without requiring the implementation to be read.
* Generic names such as `Common`, `Utils`, `Helpers`, `Manager`, `Base`, and `Misc` are prohibited when the purpose can be described more precisely.
* An entity with a specific responsibility gets a specific name.
* Entities of the same kind follow the same naming pattern. Example: all repositories use `<Entity>Repository`, and all commands use `<Verb><Entity>`.
* One concept has one name throughout the project. Using `customer`, `client`, and `buyer` for the same concept is prohibited.

| Bad                   | Good                                 |
| --------------------- | ------------------------------------ |
| `DataManager`         | `InvoiceRepository`                  |
| `utils.calc(x)`       | `price.applyDiscount(x)`             |
| `process()`           | `reserveStock()`                     |
| `data`, `info`, `tmp` | `unpaidInvoices`, `reservedQuantity` |

## Dependencies Between Modules

* Dependencies are explicit: they are visible in imports or parameters.
* A module imports only what it needs to function.
* There are no cycles: if A depends on B, B must not depend on A, either directly or through a third module.
* Another module is used only through its public interface. Internal files of neighboring modules are not imported.
* The public interface exports only what external consumers need. Everything else remains hidden.
* Changing a module's implementation without changing its contract does not require changes in other modules.

Dependency direction:

```text
transport (http, cli)  ->  use cases  ->  domain
storage                ->  domain
domain                 ->  (none of the above)
```

## Shared Code

* A shared module is created only when there are actual consumers and a clearly defined responsibility. A module is not created "for the future."
* Shared functionality belongs in a module for its own subject area: tax calculation belongs in `tax`, not in `shared`.
* Reuse reduces complexity. If extracting code adds a layer of indirection without simplifying anything, the code stays where it is.

## Duplication

A piece of business logic lives in one place.

Similar code is not always duplication. Check:

| Question                            | Yes                      | No            |
| ----------------------------------- | ------------------------ | ------------- |
| Is this the same business rule?     | Candidate for extraction | Keep separate |
| Does it change for the same reason? | Candidate for extraction | Keep separate |
| Does extraction reduce complexity?  | Extract                  | Keep separate |

A few similar lines are not a reason to introduce an abstraction.

Example. Two rules look identical but change for different reasons, so they are not combined:

```text
// orders: minimum order amount — a marketing requirement
func isOrderAllowed(total) = total >= 100

// refunds: minimum refund amount — an accounting requirement
func isRefundAllowed(amount) = amount >= 100
```
