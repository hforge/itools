## Itools 0.77.0 - 2017/03/10

### Added
- Add new URI dispatcher
- Build: Add mechanism to create "environment.json" file that describe environment (development/production)
- Build: Possibility to set development environment when installing with `setup.py install --development`
- Catalog: Add API to close catalog
- Catalog: `search.get_resources()` load resources from brain for better performances
- `Context` : Add method `return_json` (Method take status parameter)
- `Views`: Add method `is_access_allowed` to check access
- `Metadata`: `Property` has been duplicate and named `MetadataProperty` (so we can refactor it)
- `MetadataProperty`: Data are lazily encoded (for better performances)
- Xapian: First iteration on compatibility with xapian 1.4
- `FormError`: Add http status code on FormError exception

### Changed
- `GulpBuilder`: Intercept errors
- `GulpBuilder`: Now we always run gulp
- `Web`: Refactor web router
- `Web`: Now we raise `MethodNotAllowed` and not `NotImplementedError`
- `Web`: Check known methods before checking ACLs
- `Web`: Improve support of 'DELETE' and 'PATCH' methods
- `Web`: Do not return big 404 files on `/ui/` requests
- `Web`: Check "accept" header for sending JSON results
- `Website`: Remove some code linked to multi websites
- Database: Display an alert message when `context.commit=True` is used. This functionality will be removed
- Database: Remove synchronisation with FS, so performances are better
- Libsoup: Update code to last API version (2.57)
- Prototyping: Now even subclasses are prototypes
- Translations: Improve error reporting


Thanks to:

- Alexandre Mathieu
- Alexandre Bonny
- Florent Chenebault