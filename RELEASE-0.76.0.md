## Itools 0.76.0 - 2017/01/18

### Added
- Translations : Support 'nl'
- Html parser : now supports html5
- Server: Add mecanism to do requests (to simplify unit tests):
  `server.do_request(method='GET', path='/', headers={}, body=None, context=None)`
- `CSV`: Declare more mimetypes
- `Context` : Add `accept_cors` in itools.web
- `Datetime` : Add microseconds support
- `Fields` : Add names
- `get_field` : Add `soft=True` as a default parameter (will be set to False in future)
- `copy_handler`: Can now take `exclude_paterns` parameter
- `GulpBuilder` : Created to launch gulp task on install (will be moved in ikaaro?)
- `STL`: Allow boolean and/or into stl:if

### Changed
- Server:  now raise error on unsupported content type
- Update : pygit2 to 0.24.2
- Update : requirements.txt
- Installation : Made easier with pip (now we don't have to install itools to install itools)
- `ipkg-build.py`: Removed (now we always build on install)
- `Views`: Schema could be composed of fields or datatypes
- Catalog: Allow to index decimal (as float)
- Catalog: Improve performances
- Core: better log errors on prototypes
- Errors : Improve error messages
- ABNF : Remove the package (not used & no time to maintain)
- PML : Remove the package (no time to maintain)

### Fixed
- Fix bad context.status in some strange cases (cf. 299741377694b31e9d01fba63be144e347eebd0d)
- Fix unit tests (clean tests if abort)

Thanks to:

- Florian Briand
- Florent Chenebault
- J. David Ibáñez
- Alexandre Mathieu