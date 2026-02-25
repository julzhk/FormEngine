# FormEngine Spike Experiment

How to capture a typed form submission as an immutable event but also allow evolution of the form definition over time? How to support event driven audit log in a Django application?

---

This project is a spike experiment for a dynamic form engine using event sourcing. It allows for dynamic questionnaire creation, JSON-based event capture, and asynchronous event processing.

## Architecture (C4 Model Style)

### Level 1: System Context
The FormEngine system allows Users to fill out dynamic questionnaires. Submissions are captured as events, which are then processed by various Processors for downstream tasks (e.g., logging, integration with third-party services like DocuSign).

```mermaid
graph TD
    User((User)) -->|Fills out Questionnaire| FormEngine[FormEngine System]
    FormEngine -->|Writes Data to| Output[(Output Files/Logs)]
    Admin((Admin)) -->|Defines Questionnaires| FormEngine
```

### Level 2: Containers
The system is built as a Django 'modulith' containing several primary Django Apps:

```mermaid
graph LR
    subgraph FormEngine Monolith
        Q[Questionnaire]
        EM[EventManager]
        DI[DocuSignIntegration]
    end

    User --> Q
    Q -->|Creates Events| EM
    EM -->|Processed by| DI
```

1.  **Questionnaire**: The user-facing application for defining and rendering multi-page forms.
2.  **EventManager**: The event store that records all submissions as immutable events.
3.  **DocuSignIntegration**: A processor that maps event data to DocuSign payloads.

---

## Django Apps & Data Models

```mermaid
classDiagram
    class Questionnaire {
        +String name
        +String description
        +String completed_content
    }
    class Page {
        +String title
        +Integer order
        +String content
    }
    class QuestionnaireSubmission {
        +JSON responses
        +DateTime submitted_at
    }
    class Event {
        +JSON data
        +JSON metadata
        +DateTime created_at
    }
    class ConsumerOffset {
        +String processor_class
        +DateTime updated_at
    }
    class DocuSignFieldMapping {
        +String name
        +JSON template_string
        +render(data_dict)
    }

    Questionnaire "1" *-- "*" Page : contains
    Questionnaire "1" -- "*" QuestionnaireSubmission : has
    ConsumerOffset o-- Event : tracks
    Questionnaire "1" -- "0..1" DocuSignFieldMapping : mapped by
```

### 1. Questionnaire
Responsible for the structure of questionnaires and rendering them using Jinja2 templates.

*   **Models**:
    *   `Questionnaire`: The top-level entity.
    *   `Page`: Individual pages of a questionnaire, containing Jinja2 template content.
    *   `QuestionnaireSubmission`: Records the raw JSON response of a submission.
*   **Key Logic**:
    *   Multi-page navigation and validation.
    *   Custom validators (e.g., `required`, `is_number`) defined in `views.py`.

### 2. EventManager
The backbone of the event-driven architecture.

*   **Models**:
    *   `Event`: An immutable record of a submission. Stores data and metadata as `JSONField`.
    *   `ConsumerOffset`: Tracks the last processed `Event` for each specific `Processor` class.

### 3. DocuSignIntegration
Provides integration with DocuSign by mapping form data to DocuSign payloads.

*   **Models**:
    *   `DocuSignFieldMapping`: Defines how submission data should be transformed into a DocuSign JSON payload using Jinja2 templates.
*   **Key Logic**:
    *   **DocuSignProcessor**: A specialized processor that renders the mapping's template using the event data and writes the result to a file (simulating an API call).

---

## Data Flow

```mermaid
sequenceDiagram
    participant Admin
    participant User
    participant Q as Questionnaire
    participant EM as EventManager
    participant Proc as Processor (Management Command)

    Note over Admin, Q: 1. Questionnaire Definition
    Admin->>Q: Create/Update Questionnaire & Pages
    
    Note over User, EM: 2. Submission
    User->>Q: Submit Page Data
    Q->>Q: Validate Data
    Note over Q, EM: On Last Page Submit
    Q->>EM: Create Event (JSON Data + Metadata)
    
    Note over Proc, EM: 3. Processing
    Proc->>EM: Fetch New Events
    loop For Each Event
        Proc->>Proc: Execute do_process()
        Proc->>EM: Update ConsumerOffset
    end
```

1.  **Questionnaire Definition**: An admin creates a `Questionnaire` and its `Page`s in the Django Admin.
2.  **Submission**: A user fills out the questionnaire. On the final page submission:
    *   Data is validated.
    *   A `QuestionnaireSubmission` is created.
    *   An `Event` is created in the `EventManager` with the submission data.
3.  **Processing**: The `process_events` management command is executed:
    *   It identifies all active `Processor` subclasses.
    *   Each processor checks its `ConsumerOffset` for new events.
    *   For each new event, `do_process()` is called (e.g., `DocuSignProcessor` generates a JSON payload).
    *   The `ConsumerOffset` is updated.

---

## Technical Stack
*   **Language**: Python 3.13
*   **Framework**: Django
*   **Frontend**: HTMX (for multi-page form navigation), Jinja2 (for dynamic content)
*   **Database**: SQLite (default for spike)

## Future Roadmap (Todo)
* Only really supports one consumer rn. it's a POC.  
* Add transactions for consumers to ensure atomic processing and offset updates.
* Implement a dead-letter queue for failed events.
* Enhance consumer exception handling and retry logic.
* Integrate metrics and structured logging.
* Evaluate dedicated queue backends (e.g., `pgmq` or `pgqueuer`).
