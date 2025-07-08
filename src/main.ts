import { ItunesHelper, Workspace, FileManager } from 'jxa-lib';
const FILE_URI_PREFIX_RE = /^file:\/\//;

ObjC.import('AppKit');
ObjC.import('Foundation');
ObjC.import('stdlib');

export default function (): number {
  const possibleApps = {
    '/Applications/iTunes.app': 'com.apple.iTunes',
    '/Applications/Music.app': 'com.apple.Music',
  };
  const ws = Workspace.shared;
  const fm = new FileManager();
  let app: Application | undefined;
  for (const [path, bundleId] of Object.entries(possibleApps)) {
    if (fm.fileExists(path)) {
      if (ws.appIsRunning(bundleId)) {
        console.log(`Using running app at ${path}.`);
      } else {
        console.log(`Starting app at ${path}.`);
        ws.startApp(bundleId);
      }
      app = Application(bundleId);
      break;
    }
  }
  if (!app) {
    console.log('No iTunes or Music app found.');
    return 1;
  }
  const it = new ItunesHelper(app as ItunesApplication);
  // FIXME Read arguments
  const dir = Application('Finder').home().folders.byName('Music').folders.byName('import');
  console.log('Deleting orphaned tracks.');
  it.deleteOrphanedTracks();
  console.log('Updating iTunes track list.');
  it.addTracksAtPath(dir);
  const ratings: { [loc: string]: FileTrack } = {};
  console.log('Building basename:track hash.');
  for (const track of it.fileTracks) {
    const key = ObjC.unwrap(
      $.NSString.stringWithString(track.location().toString()).lastPathComponent,
    );
    ratings[key] = track;
  }
  console.log('Setting ratings.');
  for (const [rating, filename] of ObjC.unwrap(
    $.NSString.stringWithContentsOfFileUsedEncodingError(
      dir.items.byName('.ratings').url().replace(FILE_URI_PREFIX_RE, ''),
      $.NSUTF8StringEncoding,
      null,
    ),
  )
    .split('\n')
    .map((l) => l.trim())
    .filter((x) => !!x)
    .map((l) => l.split(' ', 2) as [string, string])
    .map(
      ([ratingStr, filename]) =>
        [(parseInt(ratingStr, 10) / 5) * 100, filename] as [number, string],
    )) {
    if (!(filename in ratings)) {
      throw new Error(`File not found: ${filename}.`);
    }
    ratings[filename]().rating = rating;
  }
  console.log('Syncing device if present.');
  try {
    it.syncDevice();
  } catch (_) {
    /* empty */
  }
  return 0;
}
