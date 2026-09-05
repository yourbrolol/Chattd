# Tasks
## Rated by importance
### Critical

- None

### High

- Make messages preload in chunks, not all at once
- Review overall project safety
- Add basic E2EE
- Write proper documentation

### Medium

- Make rooms list update more often
- Stop using alert()s as they are synchronous and blocking
- Keep track of account pages by user ids rather than usernames
- Keep certain things (like tab contexts) in cache / user db for short time
- Add a DM (direct message) system

### Low

- Update username in logout when changing one
- Make clicking the avatars in chats (including the one near the message bar) open users' profiles
- Make inactive tabs' backgrounds be different from tab bar background
- Add bios and room descriptions
- Make overview preload n members, not everyone, move applications button to the top near open room btn

## Other
### Reserved (task -> contributor name)
**Tasks / issues that have been reserved to someone to complete later**

- Refactor CSS codebase, optimize it for most-to-any kind of devices (even super small / huge ones) -> yourbrolol

### Processing (task -> branch name)
**Tasks / issues that are being done / fixed**

- None

### Investigating
**Tasks / issues that are to be investigated deeper**

- Users logged out have incorrect behaviour, too restricted - should be able to access public resources (define)
- Make specific tabs optionally work in background if needed

### Implemented (task -> branch name)
**Tasks that were implemented**

- Add proper user detail / account frontend interface -> fix/app
- Make user profiles clickable in chats -> fix/app
- Scroll down **every time** when opening a room -> fix/scroll-down-in-chats
- Review and refactor tabs system (frontend)
- Add user-friendly error messages
- Add JWT blacklist -> refactor/jwt
- Make jwt tokens last longer -> refactor/jwt
