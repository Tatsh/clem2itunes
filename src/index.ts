#!/usr/bin/env osascript -l JavaScript
import { FILE_URI_PREFIX_RE } from './constants';
import ITunes from './itunes';

ObjC.import('AppKit');
ObjC.import('Foundation');
ObjC.import('stdlib');

const it = new ITunes();
// FIXME Read arguments
const dir = it.finder.home().folders.byName('Music').folders.byName('import');
console.log('Deleting orphaned tracks.');
it.deleteOrphanedTracks();
console.log('Updating iTunes track list.');
it.addTracksAtPath(dir);
const ratings: { [loc: string]: ITunesTrack } = {};
console.log('Building basename:track hash.');
for (const track of it.library.tracks()) {
  ratings[ObjC.unwrap($.NSString.stringWithString(track.location().toString()).lastPathComponent)] =
    track;
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
    ([ratingStr, filename]) => [(parseInt(ratingStr, 10) / 5) * 100, filename] as [number, string],
  )) {
  if (!(filename in ratings)) {
    throw new Error(`File not found: ${filename}.`);
  }
  ratings[filename]().rating = rating;
}
console.log('Syncing device if present.');
try {
  it.syncDevice();
} catch (error) {
  /* empty */
}
$.exit(0);
