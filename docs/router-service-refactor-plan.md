# Router-to-service refactor plan

## Goal

Move all business logic out of the API routers under [app/chat/routers/api](app/chat/routers/api) and into the service layer under [app/chat/services](app/chat/services). Routers should become thin request/response adapters.

## Scope

Refactor the current endpoint groups in:

- [app/chat/routers/api/auth.py](app/chat/routers/api/auth.py)
- [app/chat/routers/api/rooms.py](app/chat/routers/api/rooms.py)
- [app/chat/routers/api/applications.py](app/chat/routers/api/applications.py)
- [app/chat/routers/api/users.py](app/chat/routers/api/users.py)

## Refactor principles

1. Routers should only:
   - parse request data
   - call a service
   - map service outcomes to HTTP responses

2. Services should own:
   - validation rules
   - duplicate checks
   - permission checks
   - state changes
   - database operations
   - domain-specific error handling

3. No router should contain inline business logic such as:
   - password hashing or token creation
   - username uniqueness checks
   - room membership rules
   - application approval/rejection logic
   - avatar validation and file saving

## Implementation plan

### Phase 1: Audit and classify

- Review each router endpoint and list the business rules currently embedded there.
- Group logic by feature area: auth, users, rooms, applications.
- Identify the existing service modules that should absorb each feature.

### Phase 2: Move auth logic

- Create or expand the auth service to handle:
  - registration
  - duplicate username checks
  - password hashing
  - login validation
  - access token creation
- Keep the router responsible only for request parsing and HTTP response mapping.

Journal update:
- Added an auth service module and moved registration/login logic out of the router.
- The router now delegates to the service and only maps outcomes to HTTP responses.
- Next: move user settings/profile logic into the user service.

### Phase 3: Move user-profile and settings logic

- Move profile lookup, username uniqueness checks, avatar validation, file storage, and persistence rules into the user service.
- Keep the router focused on dependency injection and response formatting.

Journal update:
- Moved user settings/profile behavior into the users service module.
- The router now delegates settings updates to the service and only translates errors to HTTP responses.
- Next: move application submission and review logic into the applications service.

### Phase 4: Move room logic

- Move room creation, validation, duplicate-name checks, membership checks, join/leave/delete/edit/kick rules into the room service.
- Consolidate all database query and mutation logic in the service layer so the router just delegates.

Journal update:
- Moved room creation, room search/listing, join/leave/delete/edit, and kick-member logic into the room service.
- The room router now acts as a thin adapter and only remaps service results to HTTP responses.
- Next: finish the application-service migration and then run verification checks.

### Phase 5: Move application logic

- Move application submission, review actions, pending-list retrieval, and ownership checks into the application service.
- Standardize service return values so routers can simply translate them to HTTP status codes and payloads.

Journal update:
- Moved application submission, review, and pending-list retrieval into the applications service.
- The application router now uses service return values and only maps them to HTTP responses.
- Verification: the router and service modules compile successfully.

### Phase 6: Introduce a shared service-error pattern

- Use consistent service return values or custom exceptions so routers do not need to re-implement business decisions.
- Prefer a small set of domain-level errors such as invalid input, not found, forbidden, already exists, already pending, and auth required.

### Phase 7: Tighten tests

- Add or update service-level tests for each migrated behavior.
- Ensure router tests still pass with the new thin-controller structure.

## Suggested migration order

1. Auth endpoints
2. User endpoints
3. Application endpoints
4. Room endpoints

This order keeps the refactor low-risk and aligns with the current service module boundaries already present in [app/chat/services](app/chat/services).

## Definition of done

The refactor is complete when:

- routers contain no business rules beyond request parsing and HTTP mapping
- services own the full feature logic and persistence behavior
- endpoint behavior remains unchanged from the API consumer’s point of view
- tests cover the migrated service behavior
