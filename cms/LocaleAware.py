# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from itools.web import get_context

# XXX Old versions of ikaaro implemented multilingual content with the
# metadata properties 'isVersionOf' and 'hasVersion'. These are obsoleted
# since ikaaro 0.14
#
# The new multilingual code is not finished.


class LocaleAware(object):

    def get_available_languages(self):
        master = self.get_master_handler()
        key = (None, 'hasVersion')
        translations = master.metadata.properties.get(key, {})
        translations = translations.keys()
        return [master.get_language()] + translations


    def get_master_language(self):
        metadata = self.metadata
        # Get the original handler
        original = metadata.get_property('isVersionOf')
        if original:
            original = self.parent.get_handler(original)
        else:
            original = self

        metadata = original.metadata
        return metadata.language


    def get_selected_language(self):
        context = get_context()
        request = context.request
        root = context.root
        # Language negotiation
        available_languages = self.get_available_languages()
        default_language = root.get_default_language()
        accept = request.accept_language
        return accept.select_language(available_languages) \
               or default_language


    # replacing non supported method: get_selected_handler.
    def get_version_handler(self, language=None):
        if language is None:
            language = self.get_selected_language()
        # Get the handler
        master = self.get_master_handler()
        key = (None, 'hasVersion')
        versions = master.metadata.properties.get(key, {})
        if language in versions:
            handler = master.parent.get_handler(versions[language])
        else:
            handler = master
        return handler


    def is_master(self):
        metadata = self.metadata
        if metadata is None:
            return True
        original = metadata.get_property('isVersionOf')
        return not bool(original)


    def get_master_handler(self):
        original = self.metadata.get_property('isVersionOf')
        if original:
            return self.parent.get_handler(original)
        return self


    def remove_translation(self):
        if self.is_master():
            # XXX Removing the master destroys the group of translations
            # Update translations
            if hasattr(self.metadata.properties, 'hasVersion'):
                has_version = getattr(self.metadata.properties, 'hasVersion')
                for language in has_version.keys():
                    handler = self.get_version_handler(language)
                    handler.metadata.del_property('isVersionOf')
            # Update master
            self.metadata.del_property('hasVersion')
        else:
            master = self.get_master_handler()
            # Update self
            self.metadata.del_property('isVersionOf')
            # Update master
            language = self.get_language()
            master.metadata.del_property('hasVersion', language=language)


    def get_property(self, name, language=None):
        if language is None:
            master = self.get_master_handler()
            master_language = master.metadata.get_property('dc:language')
            # Build the mapping: {language: handler}
            versions = getattr(master.metadata.properties, 'hasVersion', {})
            versions = versions.copy()
            for key, value in versions.items():
                handler = master.parent.get_handler(value)
                versions[key] = handler
            versions[master_language] = master
            # Filter non-public handlers
            for key, handler in versions.items():
                state = handler.metadata.get_property('state')
                if state != 'public':
                    del versions[key]
            # Build the mapping: {language: property value} (don't include
            # empty properties)
            for key, handler in versions.items():
                property = handler.metadata.get_property(name)
                if property:
                    versions[key] = property
                else:
                    del versions[key]
            # Language negotiation
            accept = get_context().request.accept_language
            language = accept.select_language(versions.keys())
            if language is None:
                language = master_language
            # Done
            if language in versions:
                return versions[language]
            else:
                return self.metadata.get_property(name)
        elif language == self.metadata.get_property('dc:language'):
            return self.metadata.get_property(name)
        else:
            master = self.get_master_handler()
            versions = getattr(master.metadata.properties, 'hasVersion', {})
            if language in versions:
                handler = master.parent.get_handler(versions[language])
                return handler.metadata.get_property(name)
            else:
                return master.metadata.get_property(name)
