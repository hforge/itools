## Itools 0.78.0 - 2019/02/08

Itools 0.78.0 is a transitional version.
We've:
 - removed unused and unmaintained code to simplify migration to python3.
 - removed `C` server to avoid complex migration to python3.
 - removed `itools.vfs` to avoid complex dependency with GIO
 - fixed various bugs
The purpose is to prepare future:
 - Migration to python3
 - Increase performances of database
 - Possiblily to add an SQL backend (posgres json for example ?)
 - Allow to handle several requests at once on ikaaro webserver
 - Simplify build of javascript web applications with ikaaro

### Changes
- `Database`: Refactor code to ensure only one is opened at once
- `Database`: Add static database to save binaries
- `Database`: use `with` statement to open database
- `Database`: Add `Backend` cls to allow the creation of several backends
- `Database`: Add environment variable `TEST_DB_WITHOUT_COMMITS=1` to desactivate GIT commits and have faster commits
- `SoupServer`: Remove soup server, we'll use WSGI in ikaaro
- `Context`: Ensure only one context is used at once with `gevent.local`
- `Context`: Add `get_session_timeout` method
- `Context`: Add cache for cookies
- `Build`: `msgfmt`: Intercept build errors
- `Build`: `npm`: Intercept build errors
- `Scripts`: Remove old `iodf-greek` scripts
- `PIP`: Migrate to version 10
- `Loop`: Use `gevent` for cron
- `POHandler`: Keep references at loading
- `i18n`: only extract text from MSG not from unicode texts
- `build`: run `npm install' and `gulp build` only in `ui_dev/` folders
- Remove unmaintained `itools.vfs` package
- Now HTML files can be translated at build
- Now we can extract units from JS files
