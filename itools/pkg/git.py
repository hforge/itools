# Copyright (C) 2011 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
from datetime import datetime
from os.path import abspath
from subprocess import Popen, PIPE

# Import from pygit2
from pygit2 import Repository, GitError



def message_short(commit):
    """Helper function to get the subject line of the commit message.

    XXX This code is based on the 'message_short' value that was once
    available in libgit2 (and removed by 5ae2f0c0135). It should be removed
    once libgit2 gets the feature back, see issue #250 for the discussion:

      https://github.com/libgit2/libgit2/pull/250
    """
    message = commit.message
    message = message.split('\n\n')[0]
    message = message.replace('\n', ' ')
    return message.rstrip()



class Worktree:

    def __init__(self, path, repo):
        self.path = abspath(path) + '/'
        self.repo = repo
        self.cache = {} # {sha: object}


    #######################################################################
    # Internal utility functions
    #######################################################################
    def _call(self, command):
        """Interface to cal git.git for functions not yet implemented using
        libgit2.
        """
        popen = Popen(command, stdout=PIPE, stderr=PIPE, cwd=self.path)
        stdoutdata, stderrdata = popen.communicate()
        if popen.returncode != 0:
            raise OSError(popen.returncode, stderrdata)
        return stdoutdata.decode("utf-8")


    def _resolve_reference(self, reference):
        """This method returns the SHA the given reference points to. For now
        only HEAD is supported.

        FIXME This is quick & dirty. TODO Implement references in pygit2 and
        use them here.
        """
        # Case 1: SHA
        if len(reference) == 40:
            return reference

        # Case 2: reference
        reference = self.repo.lookup_reference(reference)
        try:
            reference = reference.resolve()
        except KeyError:
            return None

        return reference.target


    #######################################################################
    # External API
    #######################################################################
    def lookup(self, sha):
        """Return the object by the given SHA. We use a cache to warrant that
        two calls with the same SHA will resolve to the same object, so the
        'is' operator will work.
        """
        cache = self.cache
        if sha not in cache:
            cache[sha] = self.repo[sha]

        return cache[sha]


    @property
    def index(self):
        """Gives access to the index file. Reloads the index file if it has
        been modified in the filesystem.
        """
        index = self.repo.index
        # Bare repository
        if index is None:
            raise RuntimeError('expected standard repository, not bare')

        return index


    def git_describe(self):
        """Equivalent to 'git describe', returns a unique but short
        identifier for the current commit based on tags.

        TODO Implement using libgit2
        """
        # Call
        command = ['git', 'describe', '--tags', '--long']
        try:
            data = self._call(command)
        except OSError:
            return None

        # Parse
        print(data)
        tag, n, commit = data.rsplit('-', 2)
        return tag, int(n), commit


    def get_branch_name(self):
        """Returns the name of the current branch.
        """
        ref = open(f'{self.path}/.git/HEAD').read().rstrip()
        ref = ref.rsplit('/', 1)
        return ref[1] if len(ref) == 2 else None


    def get_filenames(self):
        """Returns the list of filenames tracked by git.
        """
        index = self.index
        return [ index[i].path for i in range(len(index)) ]


    def get_metadata(self, reference='HEAD'):
        """Resolves the given reference and returns metadata information
        about the commit in the form of a dict.
        """
        sha = self._resolve_reference(reference)
        commit = self.lookup(sha)
        parents = commit.parents
        author = commit.author
        committer = commit.committer

        # TODO Use the offset for the author/committer time
        return {
            'tree': commit.tree.hex,
            'parent': parents[0].hex if parents else None,
            'author_name': author.name,
            'author_email': author.email,
            'author_date': datetime.fromtimestamp(author.time),
            'committer_name': committer.name,
            'committer_email': committer.email,
            'committer_date': datetime.fromtimestamp(committer.time),
            'message': commit.message,
            'message_short': message_short(commit),
            }



def open_worktree(path, soft=False):
    try:
        repo = Repository(f'{path}/.git')
    except GitError:
        if soft:
            return None
        raise

    return Worktree(path, repo)
