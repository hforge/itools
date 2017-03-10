## Itools 0.77.0 - 2017/03/10

### Added

- Add new URI dispatcher
- Catalog: Add API to close catalog
- Add method `return_json` in context (Method take status parameter)
- Views: Add method `is_access_allowed` to chack access
- Build mechanism create "environment.json" file that describe environment (development/production)
- Build: Allow to set development environment by installing with `setup.py install --development`
- Gulp:  Now we always run gulp
- Database: Display alert msg if developer do 'context.commit=True'. Functionnality will be removed
- Web: Do not return big 404 files on /ui/ requests
- Database: remove synchronisation with FS, so performances are better
- Metadata: Property has been duplicate and named MetadataProperty (so we can refactor it)
- Xapian: First iteration on compatibility with xapian 1.4
- Translations: Improve error reporting
- MetadataProperty: Data are lazyly encoded (for better performances)
- FormError: Add http status code to FormError exception
- Web: Check "accept" header for sending json results
- Web: improve support of 'DELETE', 'PATCH' methods
- Gulp: Intercept errors

### Changed

- Web: Refactor web router
- Web: Now we raise MethodNotAllowed not NotImplementedError
- Libsoup: Update code to last API version
- `is_prototype`: even subclasses are prototypes
- Web: Check known methods before checking ACLS
- Remove some code linked to multi websites

Thanks to:

- Alexandre Mathieu
- Alexandre Bonny
