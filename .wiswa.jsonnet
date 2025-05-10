(import 'defaults.libjsonnet') + {
  // Project-specific
  local top = self,
  description: 'Crazy way to synchronise a remote Strawberry rated library to Music.app using Python, JXA and SSH.',
  keywords: ['command line', 'file management', 'multimedia', 'macos', 'ssh', 'strawberry'],
  project_name: 'clem2itunes',
  version: '0.0.1',
  want_main: true,
  citation+: {
    'date-released': '2025-05-09',
  },
  docs_conf+: {
    config+: {
      intersphinx_mapping+: {
        anyio: ['https://anyio.readthedocs.io/en/stable/', null],
      },
    },
  },
  pyproject+: {
    project+: {
      scripts: {
        [top.project_name]: '%s.main:main' % top.project_name,
      },
    },
    tool+: {
      poetry+: {
        dependencies+: {
          aiosqlite: '^0.21.0',
          anyio: '^4.9.0',
          'click-aliases': '^1.0.5',
          platformdirs: '^4.3.6',
        },
        group+: {
          tests+: {
            dependencies+: {
              'pytest-asyncio': '^0',
            },
          },
        },
      },
    },
  },
  // Common
  authors: [
    {
      'family-names': 'Udvare',
      'given-names': 'Andrew',
      email: 'audvare@gmail.com',
      name: '%s %s' % [self['given-names'], self['family-names']],
    },
  ],
  local funding_name = '%s2' % std.asciiLower(self.github_username),
  github_username: 'Tatsh',
  github+: {
    funding+: {
      ko_fi: funding_name,
      liberapay: funding_name,
      patreon: funding_name,
    },
  },
}
