import { beforeEach, describe, expect, it, jest } from '@jest/globals';

const mockObjC = {
  import: jest.fn(),
  unwrap: (x: unknown) => x,
};
global.ObjC = mockObjC as unknown as typeof ObjC;
import main from './main';
import { ItunesHelper, Workspace, FileManager } from 'jxa-lib';

jest.mock('jxa-lib', () => ({
  ItunesHelper: jest.fn(),
  Workspace: {
    shared: {
      appIsRunning: jest.fn(),
      startApp: jest.fn(),
    },
  },
  FileManager: jest.fn(),
}));

const mockApplication = jest.fn();
global.Application = mockApplication as unknown as typeof Application;

const mock$ = {
  NSString: {
    stringWithString: (s: string) => ({
      lastPathComponent: s.split('/').pop(),
    }),
    stringWithContentsOfFileUsedEncodingError: (_: string, __: unknown, ___: unknown) =>
      '100 song1.mp3\n80 song2.mp3\n',
  },
  NSUTF8StringEncoding: 4,
};
global.$ = mock$ as unknown as typeof $;

describe('main', () => {
  let mockFileManager: Record<string, jest.Mock>;
  let mockItunesHelper: Record<string, jest.Mock | jest.Mock[]>;
  let mockFinder: Record<string, jest.Mock>;
  let mockDir: Record<string, unknown>;
  /* eslint-disable @typescript-eslint/no-explicit-any */
  let mockWorkspace: any;
  let mockTrack1: any;
  let mockTrack2: any;
  /* eslint-enable @typescript-eslint/no-explicit-any */

  beforeEach(() => {
    jest.clearAllMocks();

    mockFileManager = {
      fileExists: jest.fn(),
    };
    (FileManager as jest.Mock).mockImplementation(() => mockFileManager);

    mockWorkspace = Workspace.shared;
    mockWorkspace.appIsRunning.mockReset();
    mockWorkspace.startApp.mockReset();

    mockTrack1 = jest.fn(() => ({}));
    mockTrack2 = jest.fn(() => ({}));
    mockTrack1.location = jest.fn(() => ({
      toString: () => '/Users/test/Music/import/song1.mp3',
    }));
    mockTrack2.location = jest.fn(() => ({
      toString: () => '/Users/test/Music/import/song2.mp3',
    }));

    mockItunesHelper = {
      fileTracks: [mockTrack1, mockTrack2],
      deleteOrphanedTracks: jest.fn(),
      addTracksAtPath: jest.fn(),
      syncDevice: jest.fn(),
    };
    (ItunesHelper as jest.Mock).mockImplementation(() => mockItunesHelper);

    mockDir = {
      items: {
        byName: jest.fn(() => ({
          url: () => 'file:///Users/test/Music/import/.ratings',
        })),
      },
    };
    mockFinder = {
      home: jest.fn(() => ({
        folders: {
          byName: jest.fn((name: string) =>
            name === 'Music'
              ? {
                  folders: {
                    byName: jest.fn(() => mockDir),
                  },
                }
              : mockDir,
          ),
        },
      })),
    };
    global.Application = jest.fn((name: string) => {
      if (name === 'Finder') return mockFinder;
      return {};
    }) as unknown as typeof Application;
  });

  it('returns 1 if no iTunes or Music app found', () => {
    mockFileManager.fileExists.mockReturnValue(false);
    const result = main();
    expect(result).toBe(1);
  });

  it('starts app if not running and processes tracks', () => {
    mockFileManager.fileExists.mockImplementation((path: string) =>
      path.endsWith('Music.app') ? true : false,
    );
    mockWorkspace.appIsRunning.mockReturnValue(false);
    global.Application = jest.fn((_bundleId: string) => ({})) as unknown as typeof Application;
    // Finder for dir
    (global.Application as jest.Mock).mockImplementation((name: string) => {
      if (name === 'Finder') return mockFinder;
      return {};
    });

    const result = main();

    expect(mockWorkspace.startApp).toHaveBeenCalled();
    expect(ItunesHelper).toHaveBeenCalled();
    expect(mockItunesHelper.deleteOrphanedTracks).toHaveBeenCalled();
    expect(mockItunesHelper.addTracksAtPath).toHaveBeenCalledWith(mockDir);
    expect(mockItunesHelper.syncDevice).toHaveBeenCalled();
    expect(result).toBe(0);
  });

  it('uses running app if already running', () => {
    mockFileManager.fileExists.mockImplementation((path: string) =>
      path.endsWith('iTunes.app') ? true : false,
    );
    mockWorkspace.appIsRunning.mockReturnValue(true);
    global.Application = jest.fn((_bundleId: string) => ({})) as unknown as typeof Application;
    (global.Application as jest.Mock).mockImplementation((name: string) => {
      if (name === 'Finder') return mockFinder;
      return {};
    });

    const result = main();

    expect(mockWorkspace.startApp).not.toHaveBeenCalled();
    expect(ItunesHelper).toHaveBeenCalled();
    expect(result).toBe(0);
  });

  it('throws error if rating file references missing track', () => {
    mockFileManager.fileExists.mockReturnValue(true);
    mockWorkspace.appIsRunning.mockReturnValue(true);
    (global.Application as jest.Mock).mockImplementation((name: string) => {
      if (name === 'Finder') return mockFinder;
      return {};
    });
    // Only one track, but .ratings references two
    mockItunesHelper.fileTracks = [mockTrack1];
    expect(() => main()).toThrow(/File not found: song2.mp3/);
  });

  it('catches error from syncDevice and continues', () => {
    mockFileManager.fileExists.mockReturnValue(true);
    mockWorkspace.appIsRunning.mockReturnValue(true);
    (global.Application as jest.Mock).mockImplementation((name: string) => {
      if (name === 'Finder') return mockFinder;
      return {};
    });

    (mockItunesHelper.syncDevice as jest.Mock).mockImplementation(() => {
      throw new Error('Device not present');
    });

    expect(() => main()).not.toThrow();
    expect(mockItunesHelper.syncDevice).toHaveBeenCalled();
  });
});
