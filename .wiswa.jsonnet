local utils = import 'utils.libjsonnet';

{
  local top = self,
  description: 'Crazy way to synchronise a remote Strawberry rated library to Music.app using Python, JXA and SSH.',
  keywords: ['command line', 'file management', 'multimedia', 'macos', 'ssh', 'strawberry'],
  project_name: 'clem2itunes',
  version: '0.1.2',
  want_main: true,
  security_policy_supported_versions: { '0.1.x': ':white_check_mark:' },
  docs_conf+: {
    config+: {
      intersphinx_mapping+: {
        anyio: ['https://anyio.readthedocs.io/en/stable/', null],
        aiosqlite: ['https://aiosqlite.omnilib.dev/en/latest/', null],
        click: ['https://click.palletsprojects.com/en/latest/', null],
        platformdirs: ['https://platformdirs.readthedocs.io/en/latest/', null],
        'typing-extensions': ['https://typing-extensions.readthedocs.io/en/latest/', null],
      },
    },
  },
  package_json+: {
    dependencies: {
      'jxa-lib': utils.latestNpmPackageVersionCaret('jxa-lib'),
    },
    devDependencies+: {
      '@eslint/js': utils.latestNpmPackageVersionCaret('@eslint/js'),
      '@types/jest': utils.latestNpmPackageVersionCaret('@types/jest'),
      '@types/node': utils.latestNpmPackageVersionCaret('@types/node'),
      eslint: utils.latestNpmPackageVersionCaret('eslint'),
      jest: utils.latestNpmPackageVersionCaret('jest'),
      'jxa-types': utils.latestNpmPackageVersionCaret('jxa-types'),
      'ts-jest': utils.latestNpmPackageVersionCaret('ts-jest'),
      'ts-loader': utils.latestNpmPackageVersionCaret('ts-loader'),
      'ts-node': utils.latestNpmPackageVersionCaret('ts-node'),
      typescript: utils.latestNpmPackageVersionCaret('typescript'),
      'typescript-eslint': utils.latestNpmPackageVersionCaret('@typescript-eslint/eslint-plugin'),
      webpack: utils.latestNpmPackageVersionCaret('webpack'),
      'webpack-cli': utils.latestNpmPackageVersionCaret('webpack-cli'),
      'webpack-shebang-plugin': utils.latestNpmPackageVersionCaret('webpack-shebang-plugin'),
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
          aiosqlite: utils.latestPypiPackageVersionCaret('aiosqlite'),
          anyio: utils.latestPypiPackageVersionCaret('anyio'),
          'click-aliases': utils.latestPypiPackageVersionCaret('click-aliases'),
          platformdirs: utils.latestPypiPackageVersionCaret('platformdirs'),
        },
        group+: {
          tests+: {
            dependencies+: {
              'pytest-asyncio': utils.latestPypiPackageVersionCaret('pytest-asyncio'),
            },
          },
        },
      },
    },
  },
  copilot+: {
    intro: 'clem2itunes is a command line tool to synchronise a remote Strawberry rated library to Music.app using Python, JXA and SSH.',
  },
}
