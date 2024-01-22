# MoriEchoPy

A python port of [MoriEcho](https://github.com/rfsc-mori/mori_echo).

## Server plan:

- [ ] Provides a TCP server capable of asynchronous processing
- [ ] Validates messages as efficiently as possible
- [ ] Rejects invalid messages and attempts to fail fast
- [ ] Requires user authentication before echoing
- [ ] Accepts any combination of username and password
- [ ] Keeps a per-session user context, containing the username and password checksums
- [ ] Echoes the message from the request
- [ ] Decrypts client messages

# Attributions

This project uses Microsoft's Python DevContainer image for the development environment:  
https://github.com/devcontainers/images/blob/main/src/python/README.md

# License

MIT

# Author

Rafael Fillipe Silva (https://github.com/rfsc-mori)
